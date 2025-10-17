'use client';

import React from 'react';
import { Button } from '../Button';
import { cn } from '@/lib/utils';

interface ErrorAction {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
}

interface ErrorDetails {
  errorCode?: string;
  timestamp?: string;
  canRetry?: boolean;
}

interface ErrorStateProps {
  title: string;
  message: string;
  icon?: React.ReactNode;
  actions?: ErrorAction[];
  details?: ErrorDetails;
  className?: string;
}

export function ErrorState({
  title,
  message,
  icon,
  actions,
  details,
  className
}: ErrorStateProps) {
  const [showDetails, setShowDetails] = React.useState(false);

  const defaultIcon = (
    <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  );

  return (
    <div className={cn('flex items-center justify-center min-h-[300px] p-8', className)}>
      <div className="text-center max-w-md">
        {/* Icon */}
        <div className="mx-auto w-16 h-16 mb-6 text-red-500 dark:text-red-400 flex items-center justify-center">
          {icon || defaultIcon}
        </div>

        {/* Title */}
        <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
          {title}
        </h3>

        {/* Message */}
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          {message}
        </p>

        {/* Actions */}
        {actions && actions.length > 0 && (
          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-4">
            {actions.map((action, index) => (
              <Button
                key={index}
                onClick={action.onClick}
                variant={action.variant || 'primary'}
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}

        {/* Error Details */}
        {details && (
          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1 mx-auto"
            >
              {showDetails ? 'Hide' : 'Show'} technical details
              <svg
                className={cn('w-4 h-4 transition-transform', showDetails && 'rotate-180')}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {showDetails && (
              <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-left">
                <dl className="space-y-2 text-xs">
                  {details.errorCode && (
                    <>
                      <dt className="font-medium text-gray-700 dark:text-gray-300">Error Code:</dt>
                      <dd className="text-gray-600 dark:text-gray-400 font-mono">{details.errorCode}</dd>
                    </>
                  )}
                  {details.timestamp && (
                    <>
                      <dt className="font-medium text-gray-700 dark:text-gray-300">Timestamp:</dt>
                      <dd className="text-gray-600 dark:text-gray-400">{details.timestamp}</dd>
                    </>
                  )}
                  {details.canRetry !== undefined && (
                    <>
                      <dt className="font-medium text-gray-700 dark:text-gray-300">Can Retry:</dt>
                      <dd className="text-gray-600 dark:text-gray-400">{details.canRetry ? 'Yes' : 'No'}</dd>
                    </>
                  )}
                </dl>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
