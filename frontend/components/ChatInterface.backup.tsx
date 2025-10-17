'use client';

import React, { useState, useRef, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { AgentStep, SearchResult, MessageResponse } from '@/lib/types';
import { Card } from './Card';
import { Button } from './Button';
import { Input } from './Input';
import MessageList, { Message } from './MessageList';
import { useToast } from './Toast';
import { useChatStore } from '@/lib/stores/useChatStore';
import { generateId } from '@/lib/utils';
import ModeSelector from './ModeSelector';
import ModeRecommendation from './ModeRecommendation';
import QueryComplexityIndicator from './QueryComplexityIndicator';
import { useQueryMode } from '@/lib/hooks/useQueryMode';

interface ChatInterfaceProps {
  sessionId?: string;
  initialMessages?: MessageResponse[];
  isLoadingMessages?: boolean;
  onNewMessage?: (message: Message) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  initialMessages,
  isLoadingMessages = false,
  onNewMessage,
}) => {
  const [input, setInput] = useState('');
  const [autoMode, setAutoMode] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useToast();
  const { mode, setMode } = useQueryMode();
  
  const {
    messages,
    isProcessing,
    addMessage,
    updateMessage,
    setProcessing,
    setMessages,
  } = useChatStore();

  // Load initial messages when sessionId or initialMessages change
  useEffect(() => {
    if (initialMessages && initialMessages.length > 0) {
      // Convert MessageResponse to Message format
      const convertedMessages: Message[] = initialMessages.map(msg => ({
        id: msg.id || generateId(),
        role: msg.role as 'user' | 'assistant',
        content: msg.content,
        timestamp: new Date(msg.created_at),
        reasoningSteps: msg.reasoning_steps,
        sources: msg.sources,
        responseType: msg.response_type,
        pathSource: msg.path_source,
        confidenceScore: msg.confidence_score,
      }));
      setMessages(convertedMessages);
    } else if (!sessionId) {
      // Clear messages if no session
      setMessages([]);
    }
  }, [sessionId, initialMessages, setMessages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isProcessing) {
      return;
    }

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInput('');
    setProcessing(true);

    // Notify parent component of new message
    if (onNewMessage) {
      onNewMessage(userMessage);
    }

    // Create placeholder for assistant message
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
      let finalResponse = '';
      const reasoningSteps: AgentStep[] = [];
      let sources: SearchResult[] = [];
      let responseType: 'preliminary' | 'refinement' | 'final' | undefined;
      let pathSource: 'speculative' | 'agentic' | 'hybrid' | undefined;
      let confidenceScore: number | undefined;
      let previousContent = '';

      for await (const chunk of apiClient.queryStream(userMessage.content, { mode })) {
        if (chunk.type === 'chunk') {
          // Handle progressive response chunks
          const responseChunk = chunk.data as any;
          
          // Store previous content for comparison
          if (finalResponse) {
            previousContent = finalResponse;
          }
          
          finalResponse = responseChunk.content || '';
          responseType = responseChunk.type;
          pathSource = responseChunk.path_source;
          confidenceScore = responseChunk.confidence_score;
          
          // Merge sources
          if (responseChunk.sources && responseChunk.sources.length > 0) {
            sources = [...sources, ...responseChunk.sources];
          }
          
          // Merge reasoning steps
          if (responseChunk.reasoning_steps && responseChunk.reasoning_steps.length > 0) {
            reasoningSteps.push(...responseChunk.reasoning_steps);
          }
          
          // Update message with progressive content
          updateMessage(assistantMessageId, {
            content: finalResponse,
            responseType,
            pathSource,
            confidenceScore,
            isRefining: responseType === 'preliminary' || responseType === 'refinement',
            sources: sources.filter((s, i, arr) => 
              arr.findIndex(t => t.chunk_id === s.chunk_id) === i
            ), // Deduplicate sources
            reasoningSteps: [...reasoningSteps],
            previousContent: previousContent || undefined,
          });
        } else if (chunk.type === 'step') {
          const step = chunk.data as AgentStep;
          reasoningSteps.push(step);
          
          // Update message with new reasoning steps
          updateMessage(assistantMessageId, {
            reasoningSteps: [...reasoningSteps],
          });
        } else if (chunk.type === 'response') {
          const response = chunk.data as any;
          finalResponse = response.response || response.final_response || '';
          sources = response.sources || [];
          responseType = 'final';
        } else if (chunk.type === 'error') {
          const errorData = chunk.data as { message: string };
          finalResponse = `Error: ${errorData.message}`;
          showToast('error', errorData.message);
        }
      }

      // Update final message
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
        showToast('success', 'Response generated successfully');
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error occurred';
      
      updateMessage(assistantMessageId, {
        content: `Error: ${errorMsg}`,
      });
      
      showToast('error', `Failed to process query: ${errorMsg}`);
    } finally {
      setProcessing(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <Card className="flex flex-col h-[calc(100vh-12rem)]">
      <MessageList messages={messages} isProcessing={isProcessing} />
      
      <div id="chat-input-area" className="border-t border-gray-200 dark:border-gray-700 p-4 space-y-3">
        {/* Query Complexity Indicator */}
        {input.length > 10 && (
          <QueryComplexityIndicator
            query={input}
            onAnalysisComplete={(analysis) => {
              // Optionally auto-select mode based on recommendation
              if (autoMode) {
                setMode(analysis.recommended_mode);
              }
            }}
            className="mb-2"
          />
        )}
        
        {/* Adaptive Mode Recommendation */}
        <ModeRecommendation
          query={input}
          onModeSelect={setMode}
          currentMode={mode}
          autoMode={autoMode}
          onAutoModeChange={setAutoMode}
        />
        
        {/* Manual Mode Selector */}
        {!autoMode && (
          <div id="mode-selector-area">
            <ModeSelector
              selectedMode={mode}
              onModeChange={setMode}
              disabled={isProcessing}
            />
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents..."
            disabled={isProcessing}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={isProcessing || !input.trim()}
            variant="primary"
          >
            {isProcessing ? (
              <svg
                className="w-5 h-5 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            ) : (
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            )}
          </Button>
        </form>
      </div>
    </Card>
  );
};

export default ChatInterface;
