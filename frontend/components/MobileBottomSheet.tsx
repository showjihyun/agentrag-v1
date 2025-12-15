'use client';

import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import ModeSelector from './ModeSelector';
import DocumentUpload from './DocumentUpload';
import { QueryMode } from '@/lib/types';

interface MobileBottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  mode: QueryMode;
  onModeChange: (mode: QueryMode) => void;
  autoMode: boolean;
  onAutoModeChange: (enabled: boolean) => void;
  isProcessing: boolean;
}

/**
 * Mobile Bottom Sheet Component
 * 
 * Provides a mobile-optimized settings panel that slides up from the bottom.
 * Contains all advanced options in a touch-friendly interface.
 */
export default function MobileBottomSheet({
  isOpen,
  onClose,
  mode,
  onModeChange,
  autoMode,
  onAutoModeChange,
  isProcessing
}: MobileBottomSheetProps) {
  // Prevent body scroll when sheet is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40 animate-fadeIn md:hidden"
        onClick={onClose}
      />

      {/* Bottom Sheet */}
      <div
        className={`
          fixed inset-x-0 bottom-0 z-50
          bg-white dark:bg-gray-800
          rounded-t-2xl shadow-2xl
          transform transition-transform duration-300 ease-out
          md:hidden
          ${isOpen ? 'translate-y-0' : 'translate-y-full'}
        `}
      >
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-2">
          <div className="w-12 h-1 bg-gray-300 dark:bg-gray-600 rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-4 pb-3 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Settings
          </h3>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            aria-label="Close settings"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4 max-h-[70vh] overflow-y-auto">
          {/* Workflow Platform Notice */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Workflow Platform
            </h4>
            <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-xs text-blue-700 dark:text-blue-300 mb-2">
                Document processing is now available through workflows
              </p>
              <button
                onClick={() => window.location.href = '/agent-builder'}
                className="w-full text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded transition-colors"
              >
                Open Workflow Builder
              </button>
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-gray-200 dark:border-gray-700 my-4" />

          {/* Smart Mode Toggle */}
          <div className="space-y-2">
            <label className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  🤖 Smart Mode
                </span>
              </div>
              <div className="relative inline-block w-12 h-6">
                <input
                  type="checkbox"
                  checked={autoMode}
                  onChange={(e) => onAutoModeChange(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-12 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-6 peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </div>
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              AI automatically selects the best mode for your question
            </p>
          </div>

          {/* Mode Selector */}
          {!autoMode && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Processing Mode
              </label>
              <ModeSelector
                selectedMode={mode}
                onModeChange={onModeChange}
                disabled={isProcessing}
                className="w-full"
              />
            </div>
          )}

          {/* Web Search Toggle */}
          <div className="space-y-2">
            <label className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  🌐 Web Search
                </span>
              </div>
              <div className="relative inline-block w-12 h-6">
                <input
                  type="checkbox"
                  checked={mode === 'WEB_SEARCH'}
                  onChange={(e) => {
                    const newMode: QueryMode = e.target.checked ? 'WEB_SEARCH' : 'BALANCED';
                    onModeChange(newMode);
                    if (e.target.checked) {
                      onAutoModeChange(false);
                    }
                  }}
                  className="sr-only peer"
                  disabled={isProcessing}
                />
                <div className="w-12 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-6 peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </div>
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Search both your documents and the web
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="w-full px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors shadow-md"
          >
            Apply Settings
          </button>
        </div>
      </div>

      {/* CSS Animations */}
      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        .animate-fadeIn {
          animation: fadeIn 0.2s ease-out;
        }
      `}</style>
    </>
  );
}
