'use client';

/**
 * BatchUpload Component
 * Allows users to upload multiple files at once with drag-and-drop support.
 * Shows real-time progress and handles errors with retry functionality.
 */

import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api-client';
import { BatchUploadResponse } from '@/lib/types';

// File validation constants
const ALLOWED_FILE_TYPES = ['.pdf', '.txt', '.docx', '.md'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB per file
const MAX_TOTAL_SIZE = 100 * 1024 * 1024; // 100MB total
const MAX_FILES = 100;

interface FileWithStatus {
  file: File;
  status: 'pending' | 'uploading' | 'completed' | 'failed';
  error?: string;
  progress?: number;
}

export default function BatchUpload() {
  const { isAuthenticated } = useAuth();
  const [files, setFiles] = useState<FileWithStatus[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({ completed: 0, total: 0 });
  const [batchId, setBatchId] = useState<string | null>(null);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Don't render if user is not authenticated
  if (!isAuthenticated) {
    return null;
  }

  /**
   * Validate file type and size.
   */
  const validateFile = (file: File): string | null => {
    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_FILE_TYPES.includes(fileExtension)) {
      return `Invalid file type. Allowed types: ${ALLOWED_FILE_TYPES.join(', ')}`;
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Maximum size: ${MAX_FILE_SIZE / 1024 / 1024}MB`;
    }

    return null;
  };

  /**
   * Add files to the upload list.
   */
  const addFiles = (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);

    // Check total file count
    if (files.length + fileArray.length > MAX_FILES) {
      alert(`Maximum ${MAX_FILES} files allowed`);
      return;
    }

    // Validate and add files
    const validatedFiles: FileWithStatus[] = [];
    let totalSize = files.reduce((sum, f) => sum + f.file.size, 0);

    for (const file of fileArray) {
      const error = validateFile(file);
      
      // Check total size
      if (totalSize + file.size > MAX_TOTAL_SIZE) {
        alert(`Total size exceeds ${MAX_TOTAL_SIZE / 1024 / 1024}MB limit`);
        break;
      }

      validatedFiles.push({
        file,
        status: error ? 'failed' : 'pending',
        error: error || undefined,
      });

      totalSize += file.size;
    }

    setFiles([...files, ...validatedFiles]);
  };

  /**
   * Handle file input change.
   */
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
    }
  };

  /**
   * Handle drag over event.
   */
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  /**
   * Handle drag leave event.
   */
  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  /**
   * Handle drop event.
   */
  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  };

  /**
   * Remove a file from the list.
   */
  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  /**
   * Retry a failed file upload.
   */
  const retryFile = async (index: number) => {
    const fileToRetry = files[index];
    if (!fileToRetry || fileToRetry.status !== 'failed') return;

    // Reset file status
    const updatedFiles = [...files];
    updatedFiles[index] = {
      ...fileToRetry,
      status: 'pending',
      error: undefined,
    };
    setFiles(updatedFiles);

    // Upload single file
    try {
      updatedFiles[index].status = 'uploading';
      setFiles([...updatedFiles]);

      await apiClient.uploadDocument(fileToRetry.file);

      updatedFiles[index].status = 'completed';
      setFiles([...updatedFiles]);
    } catch (error) {
      updatedFiles[index].status = 'failed';
      updatedFiles[index].error = error instanceof Error ? error.message : 'Upload failed';
      setFiles([...updatedFiles]);
    }
  };

  /**
   * Upload all files as a batch.
   */
  const handleUpload = async () => {
    // Filter out failed files (validation errors)
    const validFiles = files.filter(f => f.status === 'pending');
    
    if (validFiles.length === 0) {
      alert('No valid files to upload');
      return;
    }

    setIsUploading(true);
    setUploadProgress({ completed: 0, total: validFiles.length });

    try {
      // Update all files to uploading status
      const updatedFiles = files.map(f => 
        f.status === 'pending' ? { ...f, status: 'uploading' as const } : f
      );
      setFiles(updatedFiles);

      // Upload batch
      const response: BatchUploadResponse = await apiClient.uploadBatch(
        validFiles.map(f => f.file)
      );

      setBatchId(response.id);

      // Listen to progress updates via SSE
      const es = apiClient.streamBatchProgress(response.id);
      setEventSource(es);

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Update progress
          setUploadProgress({
            completed: data.completed_files || 0,
            total: data.total_files || validFiles.length,
          });

          // Update individual file statuses based on failed_file_names
          if (data.failed_file_names && Array.isArray(data.failed_file_names)) {
            const updatedFiles = files.map(f => {
              // If file is in failed list, mark as failed
              if (data.failed_file_names.includes(f.file.name)) {
                return {
                  ...f,
                  status: 'failed' as const,
                  error: 'Upload failed'
                };
              }
              
              // If file was uploading and not in failed list, check if completed
              if (f.status === 'uploading') {
                const totalProcessed = data.completed_files + data.failed_files;
                const fileIndex = files.findIndex(file => file.file.name === f.file.name);
                
                // Simple heuristic: if we've processed enough files, mark as completed
                if (fileIndex < totalProcessed && !data.failed_file_names.includes(f.file.name)) {
                  return {
                    ...f,
                    status: 'completed' as const
                  };
                }
              }
              
              return f;
            });
            setFiles(updatedFiles);
          }

          // Close connection when complete
          if (data.status === 'completed' || data.status === 'failed') {
            es.close();
            setEventSource(null);
            setIsUploading(false);
            
            // Final update: mark all non-failed uploading files as completed
            const finalFiles = files.map(f => {
              if (f.status === 'uploading' && 
                  (!data.failed_file_names || !data.failed_file_names.includes(f.file.name))) {
                return { ...f, status: 'completed' as const };
              }
              return f;
            });
            setFiles(finalFiles);
            
            // Show completion notification
            const completedCount = data.completed_files || 0;
            const failedCount = data.failed_files || 0;
            
            if (failedCount === 0) {
              alert(`✅ All ${completedCount} files uploaded successfully!`);
            } else if (completedCount > 0) {
              alert(`⚠️ Upload completed: ${completedCount} succeeded, ${failedCount} failed`);
            } else {
              alert(`❌ Upload failed: All ${failedCount} files failed to upload`);
            }
          }
        } catch (error) {
          console.error('Failed to parse progress update:', error);
        }
      };

      es.onerror = (error) => {
        console.error('SSE error:', error);
        es.close();
        setEventSource(null);
        setIsUploading(false);
      };

    } catch (error) {
      console.error('Batch upload failed:', error);
      alert(error instanceof Error ? error.message : 'Batch upload failed');
      
      // Mark all uploading files as failed
      const updatedFiles = files.map(f => 
        f.status === 'uploading' 
          ? { ...f, status: 'failed' as const, error: 'Upload failed' }
          : f
      );
      setFiles(updatedFiles);
      setIsUploading(false);
      
      // Close event source if open
      if (eventSource) {
        eventSource.close();
        setEventSource(null);
      }
    }
  };

  /**
   * Cancel ongoing upload.
   */
  const handleCancelUpload = () => {
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }
    
    setIsUploading(false);
    
    // Mark all uploading files as failed
    const updatedFiles = files.map(f => 
      f.status === 'uploading' 
        ? { ...f, status: 'failed' as const, error: 'Upload cancelled by user' }
        : f
    );
    setFiles(updatedFiles);
  };

  /**
   * Format file size for display.
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  /**
   * Get status icon for file.
   */
  const getStatusIcon = (status: FileWithStatus['status']) => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'uploading':
        return '⏫';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
    }
  };

  /**
   * Get status color for file.
   */
  const getStatusColor = (status: FileWithStatus['status']) => {
    switch (status) {
      case 'pending':
        return 'text-gray-500';
      case 'uploading':
        return 'text-blue-500';
      case 'completed':
        return 'text-green-500';
      case 'failed':
        return 'text-red-500';
    }
  };

  const hasValidFiles = files.some(f => f.status === 'pending');
  const totalSize = files.reduce((sum, f) => sum + f.file.size, 0);

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4">Batch Upload</h2>

      {/* Drag and Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ${
          isDragging
            ? 'border-blue-500 bg-blue-50 scale-[1.02] shadow-lg'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        } ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="mb-4">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
            aria-hidden="true"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <p className="text-lg mb-2">
          {isDragging ? (
            <span className="text-blue-600 font-semibold">Drop files here</span>
          ) : (
            <>
              Drag and drop files here, or{' '}
              <button
                type="button"
                className="text-blue-600 hover:text-blue-700 font-medium disabled:text-gray-400 disabled:cursor-not-allowed"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
              >
                browse
              </button>
            </>
          )}
        </p>
        <p className="text-sm text-gray-500">
          Supported formats: {ALLOWED_FILE_TYPES.join(', ')}
        </p>
        <p className="text-sm text-gray-500">
          Max {MAX_FILES} files, {MAX_FILE_SIZE / 1024 / 1024}MB per file, {MAX_TOTAL_SIZE / 1024 / 1024}MB total
        </p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ALLOWED_FILE_TYPES.join(',')}
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">
              Files ({files.length}) - {formatFileSize(totalSize)}
            </h3>
            <button
              onClick={() => setFiles([])}
              className="text-sm text-red-600 hover:text-red-700"
              disabled={isUploading}
            >
              Clear All
            </button>
          </div>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {files.map((fileWithStatus, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center flex-1 min-w-0">
                  <span className={`text-2xl mr-3 ${getStatusColor(fileWithStatus.status)}`}>
                    {getStatusIcon(fileWithStatus.status)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {fileWithStatus.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatFileSize(fileWithStatus.file.size)} • {fileWithStatus.file.type || 'Unknown type'}
                    </p>
                    {fileWithStatus.error && (
                      <p className="text-xs text-red-600 mt-1">
                        {fileWithStatus.error}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center ml-4">
                  {fileWithStatus.status === 'failed' && (
                    <button
                      onClick={() => retryFile(index)}
                      className="text-sm text-blue-600 hover:text-blue-700 mr-3"
                      disabled={isUploading}
                    >
                      Retry
                    </button>
                  )}
                  {(fileWithStatus.status === 'pending' || fileWithStatus.status === 'failed') && (
                    <button
                      onClick={() => removeFile(index)}
                      className="text-gray-400 hover:text-gray-600"
                      disabled={isUploading}
                    >
                      <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Progress Bar */}
          {isUploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Uploading...</span>
                <span>
                  {uploadProgress.completed} / {uploadProgress.total} files
                  {uploadProgress.total > 0 && (
                    <span className="ml-2 font-semibold">
                      ({Math.round((uploadProgress.completed / uploadProgress.total) * 100)}%)
                    </span>
                  )}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300 flex items-center justify-center"
                  style={{
                    width: `${uploadProgress.total > 0 ? (uploadProgress.completed / uploadProgress.total) * 100 : 0}%`,
                  }}
                >
                  {uploadProgress.total > 0 && uploadProgress.completed > 0 && (
                    <span className="text-xs text-white font-medium px-2">
                      {Math.round((uploadProgress.completed / uploadProgress.total) * 100)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Upload/Cancel Buttons */}
          <div className="mt-6 flex gap-3">
            {!isUploading ? (
              <button
                onClick={handleUpload}
                disabled={!hasValidFiles}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-colors ${
                  hasValidFiles
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                Upload {files.filter(f => f.status === 'pending').length} Files
              </button>
            ) : (
              <>
                <button
                  disabled
                  className="flex-1 py-3 px-4 rounded-lg font-medium bg-blue-600 text-white opacity-70 cursor-not-allowed"
                >
                  Uploading...
                </button>
                <button
                  onClick={handleCancelUpload}
                  className="px-6 py-3 rounded-lg font-medium bg-red-600 text-white hover:bg-red-700 transition-colors"
                >
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
