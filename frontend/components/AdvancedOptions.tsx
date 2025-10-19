import React, { memo } from 'react';
import ModeSelector from './ModeSelector';
import ModeRecommendation from './ModeRecommendation';
import QueryComplexityIndicator from './QueryComplexityIndicator';
import ModelSelector from './ModelSelector';

interface AdvancedOptionsProps {
  input: string;
  mode: string;
  autoMode: boolean;
  isProcessing: boolean;
  onModeSelect: (mode: any) => void;
  onAutoModeChange: (autoMode: boolean) => void;
  onAnalysisComplete: (analysis: any) => void;
  setMode: (mode: any) => void;
}

const AdvancedOptions: React.FC<AdvancedOptionsProps> = memo(({
  input,
  mode,
  autoMode,
  isProcessing,
  onModeSelect,
  onAutoModeChange,
  onAnalysisComplete,
  setMode,
}) => {
  const showComplexityIndicator = input.length > 10;

  return (
    <div className="hidden md:block space-y-2 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700 animate-slideDown">
      {showComplexityIndicator && (
        <QueryComplexityIndicator
          query={input}
          onAnalysisComplete={onAnalysisComplete}
          className="mb-2"
        />
      )}
      
      <ModeRecommendation
        query={input}
        onModeSelect={onModeSelect}
        currentMode={mode}
        autoMode={autoMode}
        onAutoModeChange={onAutoModeChange}
      />
      
      {!autoMode && (
        <div id="mode-selector-area">
          <ModeSelector
            selectedMode={mode}
            onModeChange={onModeSelect}
            disabled={isProcessing}
          />
        </div>
      )}
      
      <ModelSelector />
      
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => {
            const newMode = mode === 'WEB_SEARCH' ? 'BALANCED' : 'WEB_SEARCH';
            setMode(newMode);
            onAutoModeChange(false);
          }}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
            mode === 'WEB_SEARCH'
              ? 'bg-blue-500 text-white shadow-sm hover:bg-blue-600'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
          }`}
          disabled={isProcessing}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
          <span>Web Search</span>
          {mode === 'WEB_SEARCH' && <span className="text-xs">✓</span>}
        </button>
      </div>
    </div>
  );
});

AdvancedOptions.displayName = 'AdvancedOptions';

export default AdvancedOptions;
