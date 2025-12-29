'use client';

import React, { useState, useCallback } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface Document {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
}

const DocumentUpload = React.forwardRef<HTMLDivElement>((props, ref) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      // Handle file upload logic here
      console.log('Files selected:', files);
    }
  }, []);

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
    const files = event.dataTransfer.files;
    if (files) {
      // Handle file drop logic here
      console.log('Files dropped:', files);
    }
  }, []);

  const loadDocuments = useCallback(() => {
    setIsLoading(true);
    // Load documents logic here
    setTimeout(() => setIsLoading(false), 1000);
  }, []);

  const removeDocument = useCallback((id: string) => {
    setDocuments(prev => prev.filter(doc => doc.id !== id));
  }, []);

  return (
    <Card ref={ref} title="Document Upload">
      <div className="space-y-4">
        {/* Upload Area */}
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
          {/* Uploading Overlay */}
          {uploading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/90 dark:bg-gray-900/90 rounded-lg z-10">
              <div className="text-center space-y-4">
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
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-20 h-20 border-4 border-blue-200 dark:border-blue-800 border-t-blue-600 rounded-full animate-spin"></div>
                  </div>
                </div>
                <div className="space-y-2">
                  <p className="text-lg font-semibold text-blue-600 dark:text-blue-400 animate-pulse">
                    Uploading...
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Processing your document
                  </p>
                </div>
              </div>
            </div>
          )}
          
          {/* File Input */}
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
          
          {/* Upload Label */}
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

        {/* Documents List */}
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

          {/* Document Items */}
          <div className="space-y-2">
            {documents.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <p className="text-sm">No documents uploaded yet</p>
                <p className="text-xs mt-1">Upload your first document to get started</p>
              </div>
            ) : (
              documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <svg className="h-8 w-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {doc.name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {(doc.size / 1024 / 1024).toFixed(2)} MB • {doc.type}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeDocument(doc.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
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

DocumentUpload.displayName = 'DocumentUpload';

export default DocumentUpload;