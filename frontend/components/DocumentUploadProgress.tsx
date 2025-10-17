'use client';

/**
 * Enhanced Document Upload Progress Component
 * Shows detailed upload progress with stages, estimated time, and file size
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface DocumentUploadProgressProps {
  fileName: string;
  fileSize?: number;
  progress: number;
  status: 'uploading' | 'processing' | 'indexing' | 'complete' | 'error';
  error?: string;
  estimatedTime?: number;
  uploadSpeed?: number;
  currentStage?: string;
  onCancel?: () => void;
  onRetry?: () => void;
}

export default function DocumentUploadProgress({
  fileName,
  fileSize,
  progress,
  status,
  error,
  estimatedTime,
  uploadSpeed,
  currentStage,
  onCancel,
  onRetry,
}: DocumentUploadProgressProps) {
  const stages = [
    { key: 'uploading', label: 'Uploading', icon: '📤', threshold: 0 },
    { key: 'processing', label: 'Processing', icon: '⚙️', threshold: 30 },
    { key: 'indexing', label: 'Indexing', icon: '🔍', threshold: 60 },
    { key: 'complete', label: 'Complete', icon: '✅', threshold: 100 },
  ];

  const getCurrentStageIndex = () => {
    if (status === 'error') return -1;
    if (status === 'complete') return stages.length - 1;
    
    for (let i = stages.length - 1; i >= 0; i--) {
      if (progress >= stages[i].threshold) {
        return i;
      }
    }
    return 0;
  };

  const currentStageIndex = getCurrentStageIndex();

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatSpeed = (bytesPerSecond?: number) => {
    if (!bytesPerSecond) return '';
    if (bytesPerSecond < 1024) return `${bytesPerSecond.toFixed(0)} B/s`;
    if (bytesPerSecond < 1024 * 1024) return `${(bytesPerSecond / 1024).toFixed(1)} KB/s`;
    return `${(bytesPerSecond / (1024 * 1024)).toFixed(1)} MB/s`;
  };

  const formatTime = (seconds?: number) => {
    if (!seconds) return '';
    if (seconds < 60) return `${Math.ceil(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.ceil(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  const getStageIcon = () => {
    if (status === 'error') {
      return (
        <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
          <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
      );
    }
    
    if (status === 'complete') {
      return (
        <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
          <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      );
    }

    return (
      <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-blue-600 dark:border-blue-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  };

  const getProgressColor = () => {
    if (status === 'error') return 'bg-red-500';
    if (status === 'complete') return 'bg-green-500';
    return 'bg-blue-500';
  };

  const getStatusMessage = () => {
    if (status === 'error') return error || 'Upload failed';
    if (status === 'complete') return 'Upload complete!';
    
    if (currentStage) return currentStage;
    
    if (progress < 30) return 'Uploading file to server...';
    if (progress < 60) return 'Processing document and extracting text...';
    if (progress < 90) return 'Creating embeddings and indexing...';
    return 'Finalizing upload...';
  };

  return (
    <div className={cn(
      'bg-white dark:bg-gray-800 rounded-lg p-4 shadow-md border-2 transition-all duration-200',
      status === 'error' ? 'border-red-300 dark:border-red-700' :
      status === 'complete' ? 'border-green-300 dark:border-green-700' :
      'border-blue-300 dark:border-blue-700'
    )}>
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        {getStageIcon()}
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                {fileName}
              </p>
              {fileSize && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {formatFileSize(fileSize)}
                </p>
              )}
            </div>
            
            {onCancel && status !== 'complete' && status !== 'error' && (
              <button
                onClick={onCancel}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1"
                aria-label="Cancel upload"
                title="Cancel upload"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
          
          <p className={cn(
            'text-xs mt-1.5',
            status === 'error' ? 'text-red-600 dark:text-red-400' :
            status === 'complete' ? 'text-green-600 dark:text-green-400' :
            'text-blue-600 dark:text-blue-400'
          )}>
            {getStatusMessage()}
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      {status !== 'error' && (
        <div className="space-y-2 mb-3">
          <div className="flex justify-between items-center text-xs">
            <span className="text-gray-600 dark:text-gray-400">Progress</span>
            <div className="flex items-center gap-2">
              {uploadSpeed && status !== 'complete' && (
                <span className="text-gray-500 dark:text-gray-400">
                  {formatSpeed(uploadSpeed)}
                </span>
              )}
              <span className="font-semibold text-gray-900 dark:text-gray-100">
                {progress}%
              </span>
            </div>
          </div>
          <div className="relative w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
            <div
              className={cn(
                'h-2.5 rounded-full transition-all duration-300',
                getProgressColor(),
                status !== 'complete' && 'animate-pulse'
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Stage Indicators */}
      {status !== 'error' && status !== 'complete' && (
        <div className="mb-3 py-2 px-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
          <div className="flex items-center justify-between">
            {stages.slice(0, -1).map((stage, index) => (
              <React.Fragment key={stage.key}>
                <div className="flex flex-col items-center gap-1">
                  <div className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all duration-200',
                    index <= currentStageIndex 
                      ? 'bg-blue-500 text-white scale-110' 
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-400'
                  )}>
                    {stage.icon}
                  </div>
                  <span className={cn(
                    'text-xs font-medium transition-colors',
                    index <= currentStageIndex 
                      ? 'text-blue-600 dark:text-blue-400' 
                      : 'text-gray-500 dark:text-gray-400'
                  )}>
                    {stage.label}
                  </span>
                </div>
                {index < stages.length - 2 && (
                  <div className={cn(
                    'flex-1 h-0.5 mx-2 transition-colors',
                    index < currentStageIndex 
                      ? 'bg-blue-500' 
                      : 'bg-gray-300 dark:bg-gray-600'
                  )} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {/* Estimated Time */}
      {estimatedTime && status !== 'complete' && status !== 'error' && (
        <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400 mb-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Estimated time remaining: <span className="font-medium">{formatTime(estimatedTime)}</span></span>
        </div>
      )}

      {/* Error Message */}
      {status === 'error' && (
        <div className="space-y-2">
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-start gap-2">
              <svg className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-xs text-red-700 dark:text-red-300 flex-1">
                {error || 'An error occurred during upload'}
              </p>
            </div>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="w-full px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Retry Upload
            </button>
          )}
        </div>
      )}

      {/* Success Message */}
      {status === 'complete' && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-xs text-green-700 dark:text-green-300 font-medium">
              Document successfully uploaded and indexed!
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
