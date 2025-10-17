'use client';

import React, { useState, useRef, useEffect, useCallback, useMemo, memo } from 'react';
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
import ModelSelector from './ModelSelector';
import { useQueryMode } from '@/lib/hooks/useQueryMode';

interface ChatInterfaceProps {
  sessionId?: string;
  initialMessages?: MessageResponse[];
  isLoadingMessages?: boolean;
  onNewMessage?: (message: Message) => void;
}

/**
 * Optimized ChatInterface with React.memo, useMemo, and useCallback
 * 
 * Performance improvements:
 * - Memoized component to prevent unnecessary re-renders
 * - Memoized callbacks to prevent child re-renders
 * - Memoized expensive computations
 * - Optimized message conversion
 */
const ChatInterface: React.FC<ChatInterfaceProps> = memo(({
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

  // Track if we've loaded messages for this session
  const loadedSessionRef = useRef<string | null>(null);
  const initialMessagesLengthRef = useRef<number>(0);
  
  // Load initial messages when sessionId changes
  useEffect(() => {
    const currentSessionId = sessionId || null;
    const currentLength = initialMessages?.length || 0;
    
    // Skip if same session and same message count
    if (loadedSessionRef.current === currentSessionId && 
        initialMessagesLengthRef.current === currentLength) {
      return;
    }
    
    loadedSessionRef.current = currentSessionId;
    initialMessagesLengthRef.current = currentLength;
    
    // Clear messages if no session
    if (!sessionId) {
      setMessages([]);
      return;
    }
    
    // Skip if no messages to load
    if (!initialMessages || initialMessages.length === 0) {
      return;
    }
    
    // Convert and set messages
    const convertedMessages = initialMessages.map(msg => ({
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
  }, [sessionId, initialMessages?.length]); // Depend on sessionId and message count only

  // Memoize submit handler to prevent recreation
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
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
    onNewMessage?.(userMessage);

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

      for await (const chunk of apiClient.queryStream(userMessage.content, { mode: mode.toLowerCase() })) {
        if (chunk.type === 'chunk' || chunk.type === 'preliminary' || chunk.type === 'refinement' || chunk.type === 'final') {
          const responseChunk = chunk.data as any;
          
          if (finalResponse) {
            previousContent = finalResponse;
          }
          
          finalResponse = responseChunk.content || '';
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
          
          // Log for debugging
          console.log('📝 New reasoning step:', step.type, step.content.substring(0, 50));
          
          updateMessage(assistantMessageId, {
            reasoningSteps: [...reasoningSteps],
            isRefining: true, // Keep processing state for live updates
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
        } else if (chunk.type === 'done') {
          // Handle completion with processing time
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
  }, [input, isProcessing, mode, addMessage, updateMessage, setProcessing, showToast, onNewMessage]);

  // Memoize key down handler
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);

  // Memoize input change handler
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  }, []);

  // Memoize analysis complete handler
  const handleAnalysisComplete = useCallback((analysis: any) => {
    if (autoMode) {
      setMode(analysis.recommended_mode);
    }
  }, [autoMode, setMode]);

  // Memoize mode select handler
  const handleModeSelect = useCallback((newMode: string) => {
    setMode(newMode);
  }, [setMode]);

  // Memoize auto mode change handler
  const handleAutoModeChange = useCallback((newAutoMode: boolean) => {
    setAutoMode(newAutoMode);
  }, []);

  // Memoize whether to show complexity indicator
  const showComplexityIndicator = useMemo(() => input.length > 10, [input.length]);

  // Memoize button disabled state
  const isSubmitDisabled = useMemo(() => 
    isProcessing || !input.trim(), 
    [isProcessing, input]
  );

  return (
    <Card className="flex flex-col h-full min-h-[600px] overflow-hidden">
      <MessageList messages={messages} isProcessing={isProcessing} />
      
      <div id="chat-input-area" className="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 space-y-3 shadow-lg"
        style={{
          position: 'sticky',
          bottom: 0,
          zIndex: 10
        }}
      >
        {/* Query Complexity Indicator */}
        {showComplexityIndicator && (
          <QueryComplexityIndicator
            query={input}
            onAnalysisComplete={handleAnalysisComplete}
            className="mb-2"
          />
        )}
        
        {/* Adaptive Mode Recommendation */}
        <ModeRecommendation
          query={input}
          onModeSelect={handleModeSelect}
          currentMode={mode}
          autoMode={autoMode}
          onAutoModeChange={handleAutoModeChange}
        />
        
        {/* Manual Mode Selector and Model Selector */}
        <div className="flex items-center gap-3">
          {!autoMode && (
            <div id="mode-selector-area">
              <ModeSelector
                selectedMode={mode}
                onModeChange={handleModeSelect}
                disabled={isProcessing}
              />
            </div>
          )}
          
          {/* Model Selector */}
          <ModelSelector />
        </div>
        
        <form onSubmit={handleSubmit} className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              type="text"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              disabled={isProcessing}
              className="flex-1 pr-12 py-3 text-base rounded-xl border-2 border-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-400 transition-all duration-200"
            />
            {input && (
              <button
                type="button"
                onClick={() => setInput('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                aria-label="Clear input"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
          <Button
            type="submit"
            disabled={isSubmitDisabled}
            variant="primary"
            className="px-6 py-3 rounded-xl font-medium shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isProcessing ? (
              <div className="flex items-center gap-2">
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
                <span className="hidden sm:inline">Processing...</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="hidden sm:inline">Send</span>
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
              </div>
            )}
          </Button>
        </form>
        
        {/* Keyboard shortcut hint */}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 px-1">
          <span>Press Enter to send, Shift+Enter for new line</span>
          {isProcessing && (
            <span className="flex items-center gap-1 text-blue-600 dark:text-blue-400 animate-pulse">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              Generating response...
            </span>
          )}
        </div>
      </div>
    </Card>
  );
});

ChatInterface.displayName = 'ChatInterface';

export default ChatInterface;
