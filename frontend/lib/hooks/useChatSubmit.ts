import { useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { AgentStep, SearchResult } from '@/lib/types';
import { Message } from '@/components/MessageList';
import { useChatStore } from '@/lib/stores/useChatStore';
import { generateId } from '@/lib/utils';
import { useToast } from '@/components/Toast';
import { useRetry } from './useRetry';

interface UseChatSubmitOptions {
  mode: string;
  onNewMessage?: (message: Message) => void;
  onLoadingStageChange?: (stage: 'analyzing' | 'searching' | 'generating' | 'finalizing') => void;
  onSuccess?: (processingTime: number) => void;
}

export function useChatSubmit({ mode, onNewMessage, onLoadingStageChange, onSuccess }: UseChatSubmitOptions) {
  const { addMessage, updateMessage, setProcessing } = useChatStore();
  const { showToast } = useToast();

  const submitMessage = useCallback(async (content: string) => {
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setProcessing(true);
    onNewMessage?.(userMessage);

    const assistantMessageId = generateId();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      reasoningSteps: [],
      sources: [],
    };
    addMessage(assistantMessage);

    try {
      const startTime = Date.now();
      let finalResponse = '';
      const reasoningSteps: AgentStep[] = [];
      let sources: SearchResult[] = [];
      let responseType: 'preliminary' | 'refinement' | 'final' | undefined;
      let pathSource: 'speculative' | 'agentic' | 'hybrid' | undefined;
      let confidenceScore: number | undefined;
      let previousContent = '';

      onLoadingStageChange?.('analyzing');

      for await (const chunk of apiClient.queryStream(content, { mode })) {
        // Handle streaming response chunks (token by token)
        if (chunk.type === 'response') {
          const responseChunk = chunk.data as any;
          
          // Accumulate streaming tokens
          if (responseChunk.content) {
            finalResponse += responseChunk.content;
            pathSource = responseChunk.path_source;
            
            // Update message in real-time for streaming effect
            updateMessage(assistantMessageId, {
              content: finalResponse,
              responseType: 'refinement',
              pathSource,
              isRefining: true,
            });
          }
        }
        // Handle complete response chunks
        else if (chunk.type === 'chunk' || chunk.type === 'preliminary' || chunk.type === 'refinement' || chunk.type === 'final') {
          const responseChunk = chunk.data as any;
          
          if (responseChunk.type === 'preliminary') {
            onLoadingStageChange?.('searching');
          } else if (responseChunk.type === 'refinement' || responseChunk.type === 'final') {
            onLoadingStageChange?.('generating');
          }
          
          if (finalResponse) {
            previousContent = finalResponse;
          }
          
          // Handle both 'content' and 'response' fields (web search uses 'response')
          const newContent = responseChunk.content || responseChunk.response || '';
          if (newContent) {
            finalResponse = newContent;
          }
          
          responseType = responseChunk.type || chunk.type;
          pathSource = responseChunk.path_source;
          confidenceScore = responseChunk.confidence_score;
          
          if (responseChunk.sources && responseChunk.sources.length > 0) {
            sources = [...sources, ...responseChunk.sources];
          }
          
          if (responseChunk.reasoning_steps && responseChunk.reasoning_steps.length > 0) {
            reasoningSteps.push(...responseChunk.reasoning_steps);
          }
          
          updateMessage(assistantMessageId, {
            content: finalResponse,
            responseType,
            pathSource,
            confidenceScore,
            isRefining: responseType === 'preliminary' || responseType === 'refinement',
            sources: sources.filter((s, i, arr) => 
              arr.findIndex(t => t.chunk_id === s.chunk_id) === i
            ),
            reasoningSteps: [...reasoningSteps],
            previousContent: previousContent || undefined,
          });
        } else if (chunk.type === 'step') {
          const step = chunk.data as AgentStep;
          reasoningSteps.push(step);
          
          updateMessage(assistantMessageId, {
            reasoningSteps: [...reasoningSteps],
            isRefining: true,
          });
        } else if (chunk.type === 'error') {
          const errorData = chunk.data as { message: string };
          finalResponse = `Error: ${errorData.message}`;
          showToast('error', errorData.message);
        } else if (chunk.type === 'done') {
          const doneData = chunk.data as { processing_time?: number; status?: string };
          if (doneData.processing_time !== undefined) {
            updateMessage(assistantMessageId, {
              processingTime: doneData.processing_time,
            });
          }
        }
      }

      updateMessage(assistantMessageId, {
        content: finalResponse || 'No response generated',
        responseType: responseType || 'final',
        pathSource,
        confidenceScore,
        isRefining: false,
        reasoningSteps,
        sources: sources.filter((s, i, arr) => 
          arr.findIndex(t => t.chunk_id === s.chunk_id) === i
        ),
      });

      if (finalResponse) {
        const endTime = Date.now();
        const processingTime = (endTime - startTime) / 1000;
        onSuccess?.(processingTime);
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error occurred';
      
      // Check if it's a network error
      const isNetworkError = errorMsg.includes('network') || 
                            errorMsg.includes('fetch') || 
                            errorMsg.includes('timeout');
      
      if (isNetworkError) {
        updateMessage(assistantMessageId, {
          content: '⚠️ Network error occurred. Please check your connection and try again.',
        });
        showToast('error', 'Network error. Please check your connection.');
      } else {
        updateMessage(assistantMessageId, {
          content: `❌ Error: ${errorMsg}`,
        });
        showToast('error', errorMsg);
      }
    } finally {
      setProcessing(false);
    }
  }, [mode, addMessage, updateMessage, setProcessing, showToast, onNewMessage, onLoadingStageChange, onSuccess]);

  return { submitMessage };
}
