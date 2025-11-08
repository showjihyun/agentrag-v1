'use client';

import React, { useState, useRef, useEffect, useCallback, memo, useMemo } from 'react';
import { MessageResponse, SearchResult } from '@/lib/types';
import { Card } from './Card';
import MessageList, { Message } from './MessageList';
import { useChatStore } from '@/lib/stores/useChatStore';
import { generateId } from '@/lib/utils';
import { useSmartMode } from '@/lib/hooks/useSmartMode';
import { useChatInput } from '@/lib/hooks/useChatInput';
import { useChatSubmit } from '@/lib/hooks/useChatSubmit';
import { useLoadingState } from '@/lib/hooks/useLoadingState';
import { useToggle } from '@/hooks/useToggle';
import { measurePerformance } from '@/lib/performance';
import FirstVisitGuide from './FirstVisitGuide';
import MobileBottomSheet from './MobileBottomSheet';
import ChatInputArea from './ChatInputArea';
import { StageStreamingIndicator } from './StreamingIndicator';
import DocumentViewer from './DocumentViewer';
import DocumentUpload from './DocumentUpload';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';

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
  const { isOpen: showMobileSheet, setIsOpen: setShowMobileSheet } = useToggle(false);
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const { isOpen: showDocViewer, setIsOpen: setShowDocViewer } = useToggle(true);
  const [selectedChunkId, setSelectedChunkId] = useState<string | undefined>();
  const [allSources, setAllSources] = useState<SearchResult[]>([]);
  
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

  // Memoize sources extraction for performance
  const extractedSources = useMemo(() => {
    return messages
      .filter(msg => msg.role === 'assistant' && msg.sources && msg.sources.length > 0)
      .flatMap(msg => msg.sources || []);
  }, [messages]);

  // Update sources when extracted sources change
  useEffect(() => {
    setAllSources(extractedSources);
  }, [extractedSources]);
  
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
    
    // Collect all sources from messages
    const sources = convertedMessages
      .filter(msg => msg.sources && msg.sources.length > 0)
      .flatMap(msg => msg.sources || []);
    setAllSources(sources);
    setShowDocViewer(sources.length > 0);
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
      
      <div className="relative h-full">
        {/* Desktop: Resizable 3-panel layout */}
        <div className="hidden lg:block h-full">
          <PanelGroup direction="horizontal" className="h-full">
            {/* Upload Panel - Fixed width */}
            <Panel defaultSize={20} minSize={15} maxSize={25} className="flex flex-col">
              <Card className="h-full overflow-x-auto overflow-y-auto">
                <DocumentUpload />
              </Card>
            </Panel>

            {/* Resize Handle 1 */}
            <PanelResizeHandle className="w-2 bg-gray-200 dark:bg-gray-700 hover:bg-blue-400 dark:hover:bg-blue-600 transition-colors cursor-col-resize flex items-center justify-center group">
              <div className="w-1 h-12 bg-gray-400 dark:bg-gray-500 rounded-full group-hover:bg-blue-500 transition-colors" />
            </PanelResizeHandle>

            {/* Chat Panel - Reduced default width */}
            <Panel defaultSize={35} minSize={25} maxSize={50} className="flex flex-col overflow-hidden">
              <Card className="flex flex-col h-full min-h-[600px] overflow-x-auto">
                <MessageList 
                  messages={messages} 
                  isProcessing={isProcessing}
                  onRegenerate={handleRegenerate}
                  onRelatedQuestionClick={handleRelatedQuestionClick}
                  onChunkClick={setSelectedChunkId}
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
            </Panel>

            {/* Resize Handle 2 - Always show document viewer */}
            {showDocViewer && (
              <>
                <PanelResizeHandle className="w-2 bg-gray-200 dark:bg-gray-700 hover:bg-blue-400 dark:hover:bg-blue-600 transition-colors cursor-col-resize flex items-center justify-center group">
                  <div className="w-1 h-12 bg-gray-400 dark:bg-gray-500 rounded-full group-hover:bg-blue-500 transition-colors" />
                </PanelResizeHandle>

                {/* Document Viewer Panel - Expanded default width */}
                <Panel defaultSize={45} minSize={30} maxSize={60} className="flex flex-col overflow-hidden">
                  <Card className="h-full overflow-x-auto overflow-y-auto">
                    <DocumentViewer
                      sources={allSources}
                      selectedChunkId={selectedChunkId}
                      onChunkSelect={setSelectedChunkId}
                    />
                  </Card>
                </Panel>
              </>
            )}
          </PanelGroup>
        </div>

        {/* Mobile: Tab-based layout */}
        <div className="lg:hidden h-full">
          <div className="h-full flex flex-col">
            {/* Mobile Tabs */}
            <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-2">
              <div className="flex gap-2">
                <button
                  onClick={() => setShowMobileSheet(true)}
                  className="flex-1 px-4 py-2 rounded-lg bg-blue-500 text-white font-medium text-sm flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  Upload
                </button>
                {allSources.length > 0 && (
                  <button
                    onClick={() => setShowDocViewer(!showDocViewer)}
                    className="flex-1 px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium text-sm flex items-center justify-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                    </svg>
                    Docs ({allSources.length})
                  </button>
                )}
              </div>
            </div>

            {/* Mobile Content */}
            <div className="flex-1 overflow-hidden">
              {showDocViewer && allSources.length > 0 ? (
                <Card className="h-full overflow-hidden">
                  <DocumentViewer
                    sources={allSources}
                    selectedChunkId={selectedChunkId}
                    onChunkSelect={setSelectedChunkId}
                  />
                </Card>
              ) : (
                <Card className="flex flex-col h-full overflow-hidden">
                  <MessageList 
                    messages={messages} 
                    isProcessing={isProcessing}
                    onRegenerate={handleRegenerate}
                    onRelatedQuestionClick={handleRelatedQuestionClick}
                    onChunkClick={setSelectedChunkId}
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
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
});

ChatInterface.displayName = 'ChatInterface';

export default ChatInterface;
