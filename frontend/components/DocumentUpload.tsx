'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { Document } from '@/lib/types';
import { Card } from './Card';
import { Button } from './Button';
import { useToast } from './Toast';
import { SkeletonDocumentList } from './Skeleton';
import { useDocumentStore } from '@/lib/stores/useDocumentStore';
import { formatFileSize, formatRelativeTime } from '@/lib/utils';
import { retryWithBackoff, isRetryableError } from '@/lib/utils/retry';
import SearchWithSuggestions from './SearchWithSuggestions';

const DocumentUpload: React.FC = React.memo(() => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'processing' | 'failed'>('all');
  
  const { showToast } = useToast();
  const {
    documents,
    isLoading,
    setDocuments,
    addDocument,
    removeDocument,
    setLoading,
    setError,
  } = useDocumentStore();

  useEffect(() => {
    loadDocuments();
  }, []);

  // Filter documents based on search and status
  const filteredDocs = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || doc.processing_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await apiClient.getDocuments();
      
      // Map API response to match Document interface
      const mappedDocs = (response.documents || []).map(doc => ({
        document_id: doc.document_id,
        filename: doc.filename,
        file_type: doc.file_type,
        file_size: doc.file_size,
        created_at: doc.created_at,
        processing_status: doc.status,
        chunk_count: doc.chunk_count || 0,
        metadata: {},
      }));
      
      setDocuments(mappedDocs);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load documents';
      console.error('Failed to load documents:', err);
      setError(errorMsg);
      showToast('error', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      // Upload files sequentially
      for (const file of files) {
        await uploadFile(file);
      }
    }
  }, []);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      // Upload files sequentially
      for (let i = 0; i < files.length; i++) {
        await uploadFile(files[i]);
      }
    }
  };

  const uploadFile = async (file: File) => {
    // Check file size (50MB limit)
    const MAX_FILE_SIZE_MB = 50;
    const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
    
    if (file.size > MAX_FILE_SIZE_BYTES) {
      const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);
      showToast(
        'error', 
        `File "${file.name}" (${fileSizeMB}MB) exceeds the maximum size of ${MAX_FILE_SIZE_MB}MB and will be skipped.`,
        5000
      );
      return;
    }
    
    // Check if HWP/HWPX and show recommendation
    const fileExt = file.name.split('.').pop()?.toLowerCase();
    if (fileExt === 'hwp' || fileExt === 'hwpx') {
      showToast(
        'info',
        `📄 HWP/HWPX file detected. For better text and table extraction, consider converting to PDF format.`,
        5000
      );
    }
    
    setUploading(true);
    let retryCount = 0;

    try {
      showToast('info', `Uploading ${file.name}...`, 0);
      
      // Upload with automatic retry
      const response = await retryWithBackoff(
        () => apiClient.uploadDocument(file),
        {
          maxRetries: 3,
          initialDelay: 1000,
          onRetry: (attempt, error) => {
            retryCount = attempt;
            showToast('info', `Retrying upload (${attempt}/3)...`, 0);
          },
        }
      );
      
      // Add document to store immediately (optimistic update)
      const newDoc: Document = {
        document_id: response.document_id,
        filename: response.filename,
        file_type: file.name.split('.').pop() || 'unknown',
        file_size: file.size,
        created_at: response.created_at || new Date().toISOString(),
        processing_status: response.status,
        chunk_count: response.chunk_count,
      };
      
      addDocument(newDoc);
      
      const successMsg = retryCount > 0 
        ? `Successfully uploaded ${file.name} after ${retryCount} ${retryCount === 1 ? 'retry' : 'retries'}!`
        : `Successfully uploaded ${file.name}!`;
      showToast('success', successMsg, 5000);
      
      // Reload to get updated status
      setTimeout(() => loadDocuments(), 1000);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Upload failed';
      const isRetryable = isRetryableError(err);
      
      setError(errorMsg);
      
      const errorToastMsg = isRetryable
        ? `Failed to upload ${file.name} after 3 retries. Please check your connection and try again.`
        : `Failed to upload ${file.name}: ${errorMsg}`;
      
      showToast('error', errorToastMsg, 7000);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (documentId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }

    try {
      // Optimistic update
      removeDocument(documentId);
      showToast('info', `Deleting ${filename}...`, 0);
      
      await apiClient.deleteDocument(documentId);
      
      showToast('success', `Successfully deleted ${filename}`, 5000);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Delete failed';
      setError(errorMsg);
      showToast('error', `Failed to delete ${filename}: ${errorMsg}`, 7000);
      
      // Reload to restore state
      await loadDocuments();
    }
  };

  return (
    <Card title="Document Upload">
      <div className="space-y-4">
        <div
          id="document-upload-area"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-300 ${
            uploading
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 animate-pulse'
              : isDragging
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 scale-105'
              : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 hover:bg-gray-50 dark:hover:bg-gray-800/50'
          }`}
          role="button"
          aria-label="File upload area. Click or drag and drop files here"
          tabIndex={0}
        >
          {/* Uploading Overlay with Animation */}
          {uploading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/90 dark:bg-gray-900/90 rounded-lg z-10">
              <div className="text-center space-y-4">
                {/* Spinning Upload Icon */}
                <div className="relative">
                  <svg
                    className="mx-auto h-16 w-16 text-blue-600 animate-bounce"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  {/* Rotating Ring */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-20 h-20 border-4 border-blue-200 dark:border-blue-800 border-t-blue-600 rounded-full animate-spin"></div>
                  </div>
                </div>
                
                {/* Upload Text with Typing Animation */}
                <div className="space-y-2">
                  <p className="text-lg font-semibold text-blue-600 dark:text-blue-400 animate-pulse">
                    Uploading...
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Processing your document
                  </p>
                  {/* Progress Dots */}
                  <div className="flex justify-center space-x-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <input
            type="file"
            id="file-upload"
            className="hidden"
            onChange={handleFileSelect}
            accept=".pdf,.txt,.docx,.hwp,.hwpx,.ppt,.pptx,.md,.xlsx,.xls,.csv,.json,.png,.jpg,.jpeg,.gif,.bmp,.webp"
            disabled={uploading}
            multiple
            aria-label="Choose files to upload"
          />
          <label
            htmlFor="file-upload"
            className={`cursor-pointer ${uploading ? 'pointer-events-none' : ''}`}
          >
            <div className="space-y-2">
              <svg
                className={`mx-auto h-12 w-12 text-gray-400 transition-transform duration-300 ${
                  isDragging ? 'scale-110' : ''
                }`}
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                <span className="font-medium text-blue-600 hover:text-blue-500 transition-colors">
                  Click to upload
                </span>{' '}
                or drag and drop
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                PDF, TXT, DOCX, PPT, PPTX, HWP, HWPX, MD, XLSX, XLS, CSV, JSON, PNG, JPG, GIF, BMP, WEBP (max 50MB)
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-600 mt-1">
                💡 Tip: Convert HWP/HWPX to PDF for better accuracy
              </p>
            </div>
          </label>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Uploaded Documents ({documents.length})
            </h4>
            {documents.length > 0 && (
              <button
                onClick={loadDocuments}
                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                disabled={isLoading}
              >
                Refresh
              </button>
            )}
          </div>

          {/* Search and Filter */}
          {documents.length > 0 && (
            <div className="space-y-2">
              {/* Search Bar with Suggestions */}
              <SearchWithSuggestions
                value={searchQuery}
                onChange={setSearchQuery}
                onSubmit={(query) => setSearchQuery(query)}
                placeholder="Search documents..."
                suggestions={documents.map(d => d.filename)}
              />

              {/* Status Filter */}
              <div className="flex gap-2">
                {(['all', 'completed', 'processing', 'failed'] as const).map((status) => (
                  <button
                    key={status}
                    onClick={() => setStatusFilter(status)}
                    className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                      statusFilter === status
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          )}
          
          <div className="max-h-96 overflow-y-auto space-y-2">
            {isLoading ? (
              <SkeletonDocumentList count={3} />
            ) : filteredDocs.length === 0 ? (
              <div className="text-center py-8">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  No documents uploaded yet
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  Upload your first document to get started
                </p>
              </div>
            ) : (
              filteredDocs.map((doc, index) => (
                <div
                  key={`${doc.document_id}-${doc.filename}-${index}`}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                      {doc.filename}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mt-1">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>•</span>
                      <span>{doc.chunk_count || 0} chunks</span>
                      <span>•</span>
                      <span title={doc.created_at ? new Date(doc.created_at).toLocaleString() : 'Unknown'}>
                        {formatRelativeTime(doc.created_at)}
                      </span>
                    </div>
                    <div className="mt-1">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          doc.processing_status === 'completed'
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                            : doc.processing_status === 'failed'
                            ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                            : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300'
                        }`}
                      >
                        {doc.processing_status === 'completed' && '✓ '}
                        {doc.processing_status === 'failed' && '✗ '}
                        {doc.processing_status === 'processing' && '⟳ '}
                        {doc.processing_status}
                      </span>
                    </div>
                  </div>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleDelete(doc.document_id, doc.filename)}
                    className="ml-2 shrink-0"
                    disabled={uploading}
                    isIconOnly
                    aria-label={`Delete ${doc.filename}`}
                    title={`Delete ${doc.filename}`}
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </Button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </Card>
  );
});

export default DocumentUpload;
