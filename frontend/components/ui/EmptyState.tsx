'use client';

import React from 'react';
import { Button } from '../Button';
import { cn } from '@/lib/utils';

interface EmptyStateAction {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  icon?: React.ReactNode;
}

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  actions?: EmptyStateAction[];
  examples?: string[];
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actions,
  examples,
  className
}: EmptyStateProps) {
  return (
    <div className={cn('flex items-center justify-center min-h-[400px] p-8', className)}>
      <div className="text-center max-w-md">
        {/* Icon */}
        {icon && (
          <div className="mx-auto w-16 h-16 mb-6 text-gray-400 dark:text-gray-600 flex items-center justify-center">
            {icon}
          </div>
        )}

        {/* Title */}
        <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
          {title}
        </h3>

        {/* Description */}
        {description && (
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {description}
          </p>
        )}

        {/* Actions */}
        {actions && actions.length > 0 && (
          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
            {actions.map((action, index) => (
              <Button
                key={index}
                onClick={action.onClick}
                variant={action.variant || 'primary'}
                className="flex items-center gap-2"
              >
                {action.icon}
                {action.label}
              </Button>
            ))}
          </div>
        )}

        {/* Examples */}
        {examples && examples.length > 0 && (
          <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Try these examples:
            </p>
            <div className="space-y-2">
              {examples.map((example, index) => (
                <button
                  key={index}
                  onClick={() => {
                    // Parent component should handle this
                    const event = new CustomEvent('example-selected', { detail: example });
                    window.dispatchEvent(event);
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  "{example}"
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
