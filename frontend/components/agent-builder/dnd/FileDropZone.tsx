'use client';

import React from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Upload, File, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { useToast } from '@/components/Toast';

interface FileWithProgress {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

interface FileDropZoneProps {
  onFilesAccepted?: (files: File[]) => void;
  onUploadComplete?: (files: File[]) => void;
  maxFiles?: number;
  maxSize?: number; // in bytes
  accept?: Record<string, string[]>;
  multiple?: boolean;
}

export function FileDropZone({
  onFilesAccepted,
  onUploadComplete,
  maxFiles = 10,
  maxSize = 10 * 1024 * 1024, // 10MB
  accept = {
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'text/plain': ['.txt'],
    'text/markdown': ['.md'],
  },
  multiple = true,
}: FileDropZoneProps) {
  const { toast } = useToast();
  const [files, setFiles] = React.useState<FileWithProgress[]>([]);

  const onDrop = React.useCallback(
    (acceptedFiles: File[]) => {
      const newFiles = acceptedFiles.map((file) => ({
        file,
        progress: 0,
        status: 'pending' as const,
      }));

      setFiles((prev) => [...prev, ...newFiles]);
      onFilesAccepted?.(acceptedFiles);

      // Simulate upload
      newFiles.forEach((fileWithProgress, index) => {
        simulateUpload(fileWithProgress.file, index);
      });
    },
    [onFilesAccepted]
  );

  const simulateUpload = async (file: File, index: number) => {
    const fileIndex = files.length + index;

    // Update status to uploading
    setFiles((prev) => {
      const updated = [...prev];
      updated[fileIndex] = { ...updated[fileIndex], status: 'uploading' };
      return updated;
    });

    // Simulate progress
    for (let progress = 0; progress <= 100; progress += 10) {
      await new Promise((resolve) => setTimeout(resolve, 200));
      setFiles((prev) => {
        const updated = [...prev];
        if (updated[fileIndex]) {
          updated[fileIndex] = { ...updated[fileIndex], progress };
        }
        return updated;
      });
    }

    // Complete
    setFiles((prev) => {
      const updated = [...prev];
      if (updated[fileIndex]) {
        updated[fileIndex] = { ...updated[fileIndex], status: 'completed' };
      }
      return updated;
    });

    toast({
      title: 'Upload complete',
      description: `${file.name} uploaded successfully`,
    });
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles,
    maxSize,
    accept,
    multiple,
    onDropRejected: (rejections) => {
      rejections.forEach((rejection) => {
        const errors = rejection.errors.map((e) => e.message).join(', ');
        toast({
          variant: 'destructive',
          title: 'Upload failed',
          description: `${rejection.file.name}: ${errors}`,
        });
      });
    },
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <Card
        {...getRootProps()}
        className={`border-2 border-dashed cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-primary/50'
        }`}
      >
        <CardContent className="flex flex-col items-center justify-center py-12">
          <input {...getInputProps()} />
          <Upload
            className={`h-12 w-12 mb-4 ${
              isDragActive ? 'text-primary' : 'text-muted-foreground'
            }`}
          />
          {isDragActive ? (
            <p className="text-lg font-semibold text-primary">Drop files here</p>
          ) : (
            <>
              <p className="text-lg font-semibold mb-2">
                Drag & drop files here
              </p>
              <p className="text-sm text-muted-foreground mb-4">
                or click to browse
              </p>
              <Button variant="outline" size="sm">
                Browse Files
              </Button>
            </>
          )}
          <p className="text-xs text-muted-foreground mt-4">
            Max {maxFiles} files, {formatFileSize(maxSize)} each
          </p>
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold">
              Files ({files.length}/{maxFiles})
            </h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setFiles([])}
            >
              Clear All
            </Button>
          </div>

          <div className="space-y-2">
            {files.map((fileWithProgress, index) => (
              <Card key={index}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <File className="h-5 w-5 mt-0.5 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {fileWithProgress.file.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {formatFileSize(fileWithProgress.file.size)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 ml-2">
                          {fileWithProgress.status === 'completed' && (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          )}
                          {fileWithProgress.status === 'error' && (
                            <AlertCircle className="h-4 w-4 text-red-500" />
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={() => removeFile(index)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      {fileWithProgress.status === 'uploading' && (
                        <div className="space-y-1">
                          <Progress value={fileWithProgress.progress} />
                          <p className="text-xs text-muted-foreground">
                            {fileWithProgress.progress}%
                          </p>
                        </div>
                      )}

                      {fileWithProgress.status === 'error' && (
                        <p className="text-xs text-destructive">
                          {fileWithProgress.error}
                        </p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
