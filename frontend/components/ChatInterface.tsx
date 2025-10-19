'use client';

import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import { MessageResponse } from '@/lib/types';
import { Card } from './Card';
import MessageList, { Message } from './MessageList';
import { useChatStore } from '@/lib/stores/useChatStore';
import { generateId } from '@/lib/utils';
import { useSmartMode } from '@/lib/hooks/useSmartMode';
import { useChatInput } from '@/lib/hooks/useChatInput';
import { useChatSubmit } from '@/lib/hooks/useChatSubmit';
import { useLoadingState } from '@/lib/hooks/useLoadingState';
import FirstVisitGuide from './FirstVisitGuide';
import MobileBottomSheet from './MobileBottomSheet';
import ChatInputArea from './ChatInputArea';
import { StageStreamingIndicator } from './StreamingIndicator';

interface ChatInterfaceProps {
  sessionId?: string;
  initialMessages?: MessageResponse[];
  onNewMessage?: (message: Message) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = memo(({
  sessionId,
  initialMessages,
  onNewMessage,
}) => {
  const [showMobileSheet, setShowMobileSheet] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  
  const { 
    autoMode, 
    setAutoMode, 
    mode, 
    setMode, 
    isFirstVisit, 
    completeFirstVisit 
  } = useSmartMode();
  
  const { messages, isProcessing, setMessages } = useChatStore();
  
  const {
    loadingStage,
    setLoadingStage,
    showSuccess,
    lastProcessingTime,
    handleSuccess,
    hideSuccess,
  } = useLoadingState();
  
  // Track elapsed time during processing
  useEffect(() => {
    if (isProcessing) {
      setElapsedTime(0);
      const timer = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
      return () => clearInterval(timer);
    } else {
      setElapsedTime(0);
    }
  }, [isProcessing]);
  
  const { submitMessage } = useChatSubmit({
    mode,
    onNewMessage,
    onLoadingStageChange: setLoadingStage,
    onSuccess: handleSuccess,
  });
  
  const {
    input,
    inputRef,
    handleSubmit: handleFormSubmit,
    handleKeyDown,
    handleInputChange,
    clearInput,
    focusInput,
  } = useChatInput({
    onSubmit: submitMessage,
    isProcessing,
  });

  const loadedSessionRef = useRef<string | null>(null);
  const initialMessagesLengthRef = useRef<number>(0);
  
  useEffect(() => {
    const currentSessionId = sessionId || null;
    const currentLength = initialMessages?.length || 0;
    
    if (loadedSessionRef.current === currentSessionId && 
        initialMessagesLengthRef.current === currentLength) {
      return;
    }
    
    loadedSessionRef.current = currentSessionId;
    initialMessagesLengthRef.current = currentLength;
    
    if (!sessionId) {
      setMessages([]);
      return;
    }
    
    if (!initialMessages || initialMessages.length === 0) {
      return;
    }
    
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
  }, [sessionId, initialMessages?.length, setMessages]);
  
  useEffect(() => {
    if (!isProcessing) {
      focusInput();
    }
  }, [isProcessing, focusInput]);

  const handleAnalysisComplete = useCallback((analysis: any) => {
    if (autoMode) {
      setMode(analysis.recommended_mode);
    }
  }, [autoMode, setMode]);

  const handleModeSelect = useCallback((newMode: any) => {
    setMode(newMode);
  }, [setMode]);

  const handleAutoModeChange = useCallback((newAutoMode: boolean) => {
    setAutoMode(newAutoMode);
  }, [setAutoMode]);

  // Handle regenerate button click
  const handleRegenerate = useCallback((messageId: string) => {
    const messageIndex = messages.findIndex(m => m.id === messageId);
    if (messageIndex === -1 || messageIndex === 0) return;
    
    // Find the user message before this assistant message
    const userMessage = messages[messageIndex - 1];
    if (userMessage && userMessage.role === 'user') {
      // Remove the old assistant message
      const newMessages = messages.filter(m => m.id !== messageId);
      setMessages(newMessages);
      
      // Resubmit the user's question
      submitMessage(userMessage.content);
    }
  }, [messages, setMessages, submitMessage]);

  // Handle related question click
  const handleRelatedQuestionClick = useCallback((question: string) => {
    // Directly submit the question
    submitMessage(question);
    // Focus input after submission
    setTimeout(() => {
      focusInput();
    }, 100);
  }, [submitMessage, focusInput]);

  return (
    <>
      {isFirstVisit && (
        <FirstVisitGuide onComplete={completeFirstVisit} />
      )}
      
      <MobileBottomSheet
        isOpen={showMobileSheet}
        onClose={() => setShowMobileSheet(false)}
        mode={mode}
        onModeChange={handleModeSelect}
        autoMode={autoMode}
        onAutoModeChange={handleAutoModeChange}
        isProcessing={isProcessing}
      />
      
      <Card className="flex flex-col h-full min-h-[600px] overflow-hidden">
        <MessageList 
          messages={messages} 
          isProcessing={isProcessing}
          onRegenerate={handleRegenerate}
          onRelatedQuestionClick={handleRelatedQuestionClick}
        />
        
        {isProcessing && loadingStage && (
          <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
            <StageStreamingIndicator 
              currentStage={loadingStage}
              className="justify-center"
            />
          </div>
        )}
        
        <ChatInputArea
          input={input}
          inputRef={inputRef}
          mode={mode}
          autoMode={autoMode}
          isProcessing={isProcessing}
          showSuccess={showSuccess}
          lastProcessingTime={lastProcessingTime}
          loadingStage={loadingStage}
          elapsedTime={elapsedTime}
          onSubmit={handleFormSubmit}
          onInputChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onClearInput={clearInput}
          onModeSelect={handleModeSelect}
          onAutoModeChange={handleAutoModeChange}
          onAnalysisComplete={handleAnalysisComplete}
          onSuccessClose={hideSuccess}
          setMode={setMode}
          onMobileSheetOpen={() => setShowMobileSheet(true)}
        />
      </Card>
    </>
  );
});

ChatInterface.displayName = 'ChatInterface';

export default ChatInterface;
