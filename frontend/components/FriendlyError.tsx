'use client';

import React from 'react';
import { AlertCircle, RefreshCw, HelpCircle } from 'lucide-react';
import { Button } from './Button';

interface FriendlyErrorProps {
  error: string;
  onRetry?: () => void;
  onHelp?: () => void;
  className?: string;
}

/**
 * Friendly Error Component
 * 
 * Converts technical error messages into user-friendly explanations
 * with actionable suggestions.
 */
export default function FriendlyError({
  error,
  onRetry,
  onHelp,
  className = ''
}: FriendlyErrorProps) {
  // Convert technical errors to friendly messages
  const getFriendlyMessage = (errorMsg: string): { title: string; message: string; suggestion: string } => {
    const lowerError = errorMsg.toLowerCase();
    
    // Network errors
    if (lowerError.includes('network') || lowerError.includes('fetch') || lowerError.includes('connection')) {
      return {
        title: "Connection Issue",
        message: "We couldn't reach the server. Please check your internet connection.",
        suggestion: "Try refreshing the page or checking your network settings."
      };
    }
    
    // Timeout errors
    if (lowerError.includes('timeout') || lowerError.includes('timed out')) {
      return {
        title: "Taking Too Long",
        message: "The request is taking longer than expected.",
        suggestion: "The server might be busy. Please try again in a moment."
      };
    }
    
    // Authentication errors
    if (lowerError.includes('auth') || lowerError.includes('unauthorized') || lowerError.includes('forbidden')) {
      return {
        title: "Access Issue",
        message: "You don't have permission to access this resource.",
        suggestion: "Try logging in again or contact support if the problem persists."
      };
    }
    
    // Not found errors
    if (lowerError.includes('not found') || lowerError.includes('404')) {
      return {
        title: "Not Found",
        message: "We couldn't find what you're looking for.",
        suggestion: "The resource might have been moved or deleted."
      };
    }
    
    // Server errors
    if (lowerError.includes('500') || lowerError.includes('server error') || lowerError.includes('internal')) {
      return {
        title: "Server Issue",
        message: "Something went wrong on our end.",
        suggestion: "Our team has been notified. Please try again later."
      };
    }
    
    // Rate limit errors
    if (lowerError.includes('rate limit') || lowerError.includes('too many requests')) {
      return {
        title: "Slow Down",
        message: "You're sending requests too quickly.",
        suggestion: "Please wait a moment before trying again."
      };
    }
    
    // Default friendly message
    return {
      title: "Something Went Wrong",
      message: "We encountered an unexpected issue.",
      suggestion: "Please try again. If the problem continues, contact support."
    };
  };

  const friendly = getFriendlyMessage(error);

  return (
    <div className={`bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 ${className}`}>
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          <h4 className="text-sm font-semibold text-red-800 dark:text-red-300 mb-1">
            {friendly.title}
          </h4>

          {/* Message */}
          <p className="text-sm text-red-700 dark:text-red-400 mb-2">
            {friendly.message}
          </p>

          {/* Suggestion */}
          <p className="text-xs text-red-600 dark:text-red-500 mb-3">
            💡 {friendly.suggestion}
          </p>

          {/* Actions */}
          <div className="flex flex-wrap gap-2">
            {onRetry && (
              <Button
                onClick={onRetry}
                variant="secondary"
                className="text-xs px-3 py-1.5 bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/60 border-red-300 dark:border-red-700"
              >
                <RefreshCw className="w-3 h-3 mr-1" />
                Try Again
              </Button>
            )}
            
            {onHelp && (
              <Button
                onClick={onHelp}
                variant="ghost"
                className="text-xs px-3 py-1.5 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40"
              >
                <HelpCircle className="w-3 h-3 mr-1" />
                Get Help
              </Button>
            )}
          </div>

          {/* Technical details (collapsible) */}
          <details className="mt-3">
            <summary className="text-xs text-red-600 dark:text-red-500 cursor-pointer hover:underline">
              Technical details
            </summary>
            <pre className="mt-2 text-xs text-red-700 dark:text-red-400 bg-red-100 dark:bg-red-900/30 p-2 rounded overflow-x-auto">
              {error}
            </pre>
          </details>
        </div>
      </div>
    </div>
  );
}
