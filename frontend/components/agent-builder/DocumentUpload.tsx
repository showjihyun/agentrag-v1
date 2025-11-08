'use client';

import { useState, useCallback } from 'react';
import { Upload, X, FileText, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, DocumentUploadProgress } from '@/lib/api/agent-builder';

interface DocumentUploadProps {
  knowledgebaseId: string;
  onUploadComplete?: () => void;
}

interface FileWithProgress extends File {
  id: string;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';
  error?: string;
}

export default function DocumentUpload({ knowledgebaseId, onUploadComplete }: DocumentUploadProps) {
  const { toast } = useToast();
  const [files, setFiles] = useState<FileWithProgress[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      addFiles(selectedFiles);
    }
  };

  const addFiles = (newFiles: File[]) => {
    const filesWithProgress: FileWithProgress[] = newFiles.map((file) => ({
      ...file,
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      progress: 0,
      status: 'pending' as const,
    }));

    setFiles((prev) => [...prev, ...filesWithProgress]);
  };

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    try {
      setUploading(true);

      // Update all files to uploading status
      setFiles((prev) =>
        prev.map((f) => ({ ...f, status: 'uploading' as const, progress: 0 }))
      );

      // Convert FileWithProgress back to File for upload
      const filesToUpload = files.map((f) => {
        const file = new File([f], f.name, { type: f.type });
        return file;
      });

      // Upload files
      const results = await agentBuilderAPI.uploadDocuments(knowledgebaseId, filesToUpload);

      // Update file statuses based on results
      setFiles((prev) =>
        prev.map((file) => {
          const result = results.find((r) => r.filename === file.name);
          if (result) {
            return {
              ...file,
              status: result.status,
              progress: result.progress,
              error: result.error,
            };
          }
          return file;
        })
      );

      // Check if all uploads were successful
      const allSuccessful = results.every((r) => r.status === 'completed');
      
      if (allSuccessful) {
        toast({
          title: 'Success',
          description: `${results.length} document(s) uploaded successfully`,
        });
        
        if (onUploadComplete) {
          onUploadComplete();
        }
      } else {
        const failedCount = results.filter((r) => r.status === 'failed').length;
        toast({
          title: 'Partial Success',
          description: `${results.length - failedCount} of ${results.length} documents uploaded successfully`,
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to upload documents',
        variant: 'destructive',
      });

      // Mark all files as failed
      setFiles((prev) =>
        prev.map((f) => ({
          ...f,
          status: 'failed' as const,
          error: 'Upload failed',
        }))
      );
    } finally {
      setUploading(false);
    }
  };

  const getStatusIcon = (status: FileWithProgress['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-destructive" />;
      case 'uploading':
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      default:
        return <FileText className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: FileWithProgress['status']) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default">Completed</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'uploading':
        return <Badge variant="secondary">Uploading</Badge>;
      case 'processing':
        return <Badge variant="secondary">Processing</Badge>;
      default:
        return <Badge variant="outline">Pending</Badge>;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const totalFiles = files.length;
  const completedFiles = files.filter((f) => f.status === 'completed').length;
  const failedFiles = files.filter((f) => f.status === 'failed').length;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Documents</CardTitle>
        <CardDescription>
          Add documents to your knowledgebase
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-lg p-12 text-center transition-colors
            ${isDragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
            ${uploading ? 'opacity-50 pointer-events-none' : 'cursor-pointer hover:border-primary/50'}
          `}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">
            {isDragging ? 'Drop files here' : 'Drag and drop files'}
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            or click to browse
          </p>
          <p className="text-xs text-muted-foreground">
            Supports PDF, DOCX, TXT, and more
          </p>
          <input
            id="file-input"
            type="file"
            multiple
            className="hidden"
            onChange={handleFileSelect}
            disabled={uploading}
          />
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h4 className="font-semibold">
                  Files ({totalFiles})
                </h4>
                {uploading && (
                  <p className="text-sm text-muted-foreground">
                    {completedFiles} completed, {failedFiles} failed
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFiles([])}
                  disabled={uploading}
                >
                  Clear All
                </Button>
                <Button
                  size="sm"
                  onClick={handleUpload}
                  disabled={uploading || files.length === 0}
                >
                  {uploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      Upload All
                    </>
                  )}
                </Button>
              </div>
            </div>

            <ScrollArea className="h-[400px] rounded-md border">
              <div className="p-4 space-y-3">
                {files.map((file) => (
                  <Card key={file.id}>
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="mt-1">
                          {getStatusIcon(file.status)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <p className="font-medium truncate">{file.name}</p>
                            {getStatusBadge(file.status)}
                          </div>
                          <p className="text-xs text-muted-foreground mb-2">
                            {formatFileSize(file.size)}
                          </p>
                          {(file.status === 'uploading' || file.status === 'processing') && (
                            <Progress value={file.progress} className="h-1" />
                          )}
                          {file.error && (
                            <p className="text-xs text-destructive mt-2">{file.error}</p>
                          )}
                        </div>
                        {!uploading && file.status === 'pending' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => removeFile(file.id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
