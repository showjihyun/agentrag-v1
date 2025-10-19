import React, { memo, useState, useMemo } from 'react';
import { Input } from './Input';
import { Button } from './Button';
import AdvancedOptions from './AdvancedOptions';
import LoadingProgress from './LoadingProgress';
import SuccessFeedback from './SuccessFeedback';

interface ChatInputAreaProps {
  input: string;
  inputRef: React.RefObject<HTMLInputElement | null>;
  mode: string;
  autoMode: boolean;
  isProcessing: boolean;
  showSuccess: boolean;
  lastProcessingTime?: number;
  loadingStage: 'analyzing' | 'searching' | 'generating' | 'finalizing';
  elapsedTime?: number;
  onSubmit: (e: React.FormEvent) => void;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onClearInput: () => void;
  onModeSelect: (mode: any) => void;
  onAutoModeChange: (autoMode: boolean) => void;
  onAnalysisComplete: (analysis: any) => void;
  onSuccessClose: () => void;
  setMode: (mode: any) => void;
  onMobileSheetOpen: () => void;
}

const ChatInputArea: React.FC<ChatInputAreaProps> = memo(({
  input,
  inputRef,
  mode,
  autoMode,
  isProcessing,
  showSuccess,
  lastProcessingTime,
  loadingStage,
  elapsedTime = 0,
  onSubmit,
  onInputChange,
  onKeyDown,
  onClearInput,
  onModeSelect,
  onAutoModeChange,
  onAnalysisComplete,
  onSuccessClose,
  setMode,
  onMobileSheetOpen,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const isWebSearch = mode.toLowerCase() === 'web_search';

  const isSubmitDisabled = useMemo(() => 
    isProcessing || !input.trim(), 
    [isProcessing, input]
  );

  return (
    <div 
      id="chat-input-area" 
      className="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4 space-y-2 shadow-lg"
      style={{
        position: 'sticky',
        bottom: 0,
        zIndex: 10
      }}
    >
      {showSuccess && lastProcessingTime !== undefined && (
        <SuccessFeedback
          processingTime={lastProcessingTime}
          onClose={onSuccessClose}
        />
      )}
      
      {isProcessing && (
        <LoadingProgress 
          stage={loadingStage} 
          isWebSearch={isWebSearch}
          elapsedTime={elapsedTime}
        />
      )}
      
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {autoMode ? (
            <div 
              className="flex items-center gap-2 px-2 py-1 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm group relative cursor-help"
              title="AI automatically selects the best mode for your question"
            >
              <span className="text-blue-600 dark:text-blue-400">🤖 Smart Mode</span>
              {mode !== 'BALANCED' && (
                <span className="text-xs text-blue-500 dark:text-blue-300">
                  → {mode}
                </span>
              )}
              <div className="absolute bottom-full left-0 mb-2 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-20">
                AI picks the best mode automatically
                <div className="absolute top-full left-4 -mt-1">
                  <div className="border-4 border-transparent border-t-gray-900 dark:border-t-gray-700"></div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <span>Mode: {mode}</span>
            </div>
          )}
          
          {mode === 'WEB_SEARCH' && (
            <span className="px-2 py-1 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 text-xs rounded-lg flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
              Web
            </span>
          )}
        </div>
        
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="hidden md:flex text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 items-center gap-1 transition-colors"
        >
          <svg className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          <span>{showAdvanced ? 'Less' : 'Options'}</span>
        </button>
        
        <button
          type="button"
          onClick={onMobileSheetOpen}
          className="md:hidden text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 flex items-center gap-1 transition-colors px-2 py-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
          <span>Settings</span>
        </button>
      </div>
      
      {showAdvanced && (
        <AdvancedOptions
          input={input}
          mode={mode}
          autoMode={autoMode}
          isProcessing={isProcessing}
          onModeSelect={onModeSelect}
          onAutoModeChange={onAutoModeChange}
          onAnalysisComplete={onAnalysisComplete}
          setMode={setMode}
        />
      )}
      
      <form onSubmit={onSubmit} className="flex gap-2 items-end">
        <div className="flex-1 relative">
          <Input
            ref={inputRef}
            type="text"
            value={input}
            onChange={onInputChange}
            onKeyDown={onKeyDown}
            placeholder={mode === 'WEB_SEARCH' ? "Ask anything..." : "Ask about your documents..."}
            disabled={isProcessing}
            className="flex-1 pr-10 py-2.5 text-base rounded-xl border-2 border-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-400 transition-all duration-200"
            aria-label="Chat message input"
            aria-describedby="input-hint"
            autoComplete="off"
          />
          {input && (
            <button
              type="button"
              onClick={onClearInput}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1"
              aria-label="Clear input"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        <Button
          type="submit"
          disabled={isSubmitDisabled}
          variant="primary"
          className="px-4 sm:px-6 py-2.5 rounded-xl font-medium shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label={isProcessing ? "Processing message" : "Send message"}
        >
          {isProcessing ? (
            <div className="flex items-center gap-2">
              <svg
                className="w-4 h-4 animate-spin"
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
              <span className="hidden sm:inline text-sm">...</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              <span className="hidden sm:inline text-sm">Send</span>
              <svg
                className="w-4 h-4"
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
      
      <div id="input-hint" className="flex items-center justify-between text-xs text-gray-400 dark:text-gray-500 px-1">
        <span>Enter to send • Shift+Enter for new line</span>
        {isProcessing && (
          <span className="flex items-center gap-1 text-blue-500 dark:text-blue-400 animate-pulse">
            <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span className="hidden sm:inline">Thinking...</span>
          </span>
        )}
      </div>
      
      <style jsx>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-slideDown {
          animation: slideDown 0.2s ease-out;
        }
      `}</style>
    </div>
  );
});

ChatInputArea.displayName = 'ChatInputArea';

export default ChatInputArea;
