'use client';

import React, { useState, useEffect } from 'react';
import { CheckCircle, Clock, Zap } from 'lucide-react';

interface SuccessFeedbackProps {
  message?: string;
  processingTime?: number;
  autoHide?: boolean;
  autoHideDelay?: number;
  onClose?: () => void;
  className?: string;
}

/**
 * Success Feedback Component
 * 
 * Shows positive feedback with processing time and performance indicators.
 */
export default function SuccessFeedback({
  message = 'Response generated successfully!',
  processingTime,
  autoHide = true,
  autoHideDelay = 3000,
  onClose,
  className = ''
}: SuccessFeedbackProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (autoHide) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        onClose?.();
      }, autoHideDelay);

      return () => clearTimeout(timer);
    }
  }, [autoHide, autoHideDelay, onClose]);

  // Get performance indicator
  const getPerformanceIndicator = (time?: number) => {
    if (!time) return null;

    if (time < 2) {
      return {
        icon: <Zap className="w-4 h-4 text-green-600 dark:text-green-400" />,
        label: 'Lightning fast!',
        color: 'text-green-600 dark:text-green-400'
      };
    } else if (time < 5) {
      return {
        icon: <CheckCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />,
        label: 'Quick response',
        color: 'text-blue-600 dark:text-blue-400'
      };
    } else {
      return {
        icon: <Clock className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />,
        label: 'Detailed analysis',
        color: 'text-yellow-600 dark:text-yellow-400'
      };
    }
  };

  const performance = getPerformanceIndicator(processingTime);

  if (!isVisible) return null;

  return (
    <div className={`bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3 animate-slideIn ${className}`}>
      <div className="flex items-center gap-3">
        {/* Success Icon */}
        <div className="flex-shrink-0">
          <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-green-800 dark:text-green-300">
            {message}
          </p>

          {/* Performance Info */}
          {processingTime !== undefined && performance && (
            <div className="flex items-center gap-2 mt-1">
              {performance.icon}
              <span className={`text-xs ${performance.color}`}>
                {performance.label} • {processingTime.toFixed(2)}s
              </span>
            </div>
          )}
        </div>

        {/* Close Button */}
        {onClose && (
          <button
            onClick={() => {
              setIsVisible(false);
              onClose();
            }}
            className="flex-shrink-0 text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200 transition-colors"
            aria-label="Close"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* CSS Animation */}
      <style jsx>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-slideIn {
          animation: slideIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}
