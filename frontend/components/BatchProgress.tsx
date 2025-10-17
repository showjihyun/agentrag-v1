'use client';

/**
 * BatchProgress Component
 * Displays real-time progress updates for batch file uploads via SSE.
 * Shows file-by-file status with icons and provides a summary of success/failure.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { BatchProgressResponse } from '@/lib/types';
import { Button } from './Button';

interface BatchProgressProps {
  batchId: string;
  onClose: () => void;
  autoCloseOnSuccess?: boolean;
  autoCloseDelay?: number; // milliseconds
}

type FileStatus = 'pending' | 'processing' | 'completed' | 'failed';

interface FileProgress {
  filename: string;
  status: FileStatus;
  error_message?: string;
}

export default function BatchProgress({
  batchId,
  onClose,
  autoCloseOnSuccess = true,
  autoCloseDelay = 3000,
}: BatchProgressProps) {
  const [progress, setProgress] = useState<BatchProgressResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  /**
   * Get status icon for file status.
   */
  const getStatusIcon = (status: FileStatus): string => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'processing':
        return '🔄';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      default:
        return '❓';
    }
  };

  /**
   * Get status color class for file status.
   */
  const getStatusColor = (status: FileStatus): string => {
    switch (status) {
      case 'pending':
        return 'text-gray-500';
      case 'processing':
        return 'text-blue-500';
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-500';
    }
  };

  /**
   * Handle SSE connection and progress updates.
   */
  useEffect(() => {
    let eventSource: EventSource | null = null;
    let autoCloseTimer: NodeJS.Timeout | null = null;

    try {
      // Create SSE connection
      eventSource = apiClient.streamBatchProgress(batchId);

      // Handle progress updates
      eventSource.onmessage = (event) => {
        try {
          const data: BatchProgressResponse = JSON.parse(event.data);
          setProgress(data);

          // Check if batch is complete
          if (data.status === 'completed' || data.status === 'failed') {
            setIsComplete(true);

            // Auto-close on success if enabled
            if (autoCloseOnSuccess && data.status === 'completed') {
              autoCloseTimer = setTimeout(() => {
                onClose();
              }, autoCloseDelay);
            }
          }
        } catch (err) {
          console.error('Failed to parse progress data:', err);
        }
      };

      // Handle errors
      eventSource.onerror = (err) => {
        console.error('SSE connection error:', err);
        setError('Failed to connect to progress stream');
        eventSource?.close();
      };
    } catch (err) {
      console.error('Failed to create SSE connection:', err);
      setError('Failed to start progress tracking');
    }

    // Cleanup on unmount
    return () => {
      if (eventSource) {
        eventSource.close();
      }
      if (autoCloseTimer) {
        clearTimeout(autoCloseTimer);
      }
    };
  }, [batchId, onClose, autoCloseOnSuccess, autoCloseDelay]);

  /**
   * Calculate progress percentage.
   */
  const progressPercentage = progress
    ? Math.round((progress.completed_files / progress.total_files) * 100)
    : 0;

  /**
   * Get summary message.
   */
  const getSummaryMessage = (): string => {
    if (!progress) return 'Loading...';

    const { completed_files, failed_files, total_files, status } = progress;

    if (status === 'completed') {
      if (failed_files === 0) {
        return `✅ All ${total_files} files uploaded successfully!`;
      } else {
        return `⚠️ ${completed_files} of ${total_files} files uploaded successfully. ${failed_files} failed.`;
      }
    }

    if (status === 'failed') {
      return `❌ Batch upload failed. ${completed_files} of ${total_files} files completed.`;
    }

    return `Uploading... ${completed_files} of ${total_files} files completed`;
  };

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Batch Upload Progress
          </h2>
          {isComplete && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error ? (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-300">
              {error}
            </div>
          ) : progress ? (
            <>
              {/* Progress Bar */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {getSummaryMessage()}
                  </span>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {progressPercentage}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${
                      progress.status === 'failed'
                        ? 'bg-red-500'
                        : progress.status === 'completed'
                        ? 'bg-green-500'
                        : 'bg-blue-500'
                    }`}
                    style={{ width: `${progressPercentage}%` }}
                  />
                </div>
              </div>

              {/* Success/Failure Summary */}
              {isComplete && (
                <div className="mb-6 p-4 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                        {progress.total_files}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Total Files</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                        {progress.completed_files}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Successful</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                        {progress.failed_files}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Failed</div>
                    </div>
                  </div>
                </div>
              )}

              {/* File List */}
              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  File Status
                </h3>
                {progress.files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  >
                    <span className="text-2xl flex-shrink-0">
                      {getStatusIcon(file.status)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                          {file.filename}
                        </span>
                        <span
                          className={`text-xs font-medium ${getStatusColor(
                            file.status
                          )}`}
                        >
                          {file.status}
                        </span>
                      </div>
                      {file.error_message && (
                        <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                          {file.error_message}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400 mb-4"></div>
                <p className="text-gray-600 dark:text-gray-400">Loading progress...</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {isComplete && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
            <Button
              onClick={onClose}
              variant="primary"
            >
              Close
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
