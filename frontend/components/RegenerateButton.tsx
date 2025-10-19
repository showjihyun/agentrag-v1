'use client';

import React, { useState } from 'react';

interface RegenerateButtonProps {
  onRegenerate: (options?: RegenerateOptions) => void;
  isProcessing?: boolean;
  disabled?: boolean;
}

export interface RegenerateOptions {
  mode?: 'same' | 'different' | 'better';
  temperature?: number;
}

const RegenerateButton: React.FC<RegenerateButtonProps> = ({
  onRegenerate,
  isProcessing = false,
  disabled = false,
}) => {
  const [showOptions, setShowOptions] = useState(false);

  const handleRegenerate = (mode: 'same' | 'different' | 'better' = 'same') => {
    setShowOptions(false);
    onRegenerate({ mode });
  };

  return (
    <div className="relative inline-block">
      <div className="flex items-center gap-2">
        <button
          onClick={() => handleRegenerate('same')}
          disabled={disabled || isProcessing}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
          title="Regenerate response"
        >
          {isProcessing ? (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-4 h-4 group-hover:rotate-180 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          )}
          <span className="hidden sm:inline">Regenerate</span>
        </button>

        <button
          onClick={() => setShowOptions(!showOptions)}
          disabled={disabled || isProcessing}
          className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          title="More options"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {showOptions && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowOptions(false)}
          />
          <div className="absolute left-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-20 animate-slideDown">
            <div className="p-2 space-y-1">
              <button
                onClick={() => handleRegenerate('same')}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <div className="font-medium">🔄 Same approach</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Use the same method
                </div>
              </button>

              <button
                onClick={() => handleRegenerate('different')}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <div className="font-medium">🎲 Different approach</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Try a different method
                </div>
              </button>

              <button
                onClick={() => handleRegenerate('better')}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <div className="font-medium">⚡ Better quality</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Use more resources for better answer
                </div>
              </button>
            </div>
          </div>
        </>
      )}

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
};

export default RegenerateButton;
