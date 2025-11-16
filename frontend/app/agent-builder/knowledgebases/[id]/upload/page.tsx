'use client';

import { useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Upload, FileText, X, CheckCircle, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { Badge } from '@/components/ui/badge';

interface UploadFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  error?: string;
}

export default function DocumentUploadPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const kbId = params.id as string;

  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

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

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      addFiles(selectedFiles);
    }
  }, []);

  const addFiles = (newFiles: File[]) => {
    const uploadFiles: UploadFile[] = newFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending',
      progress: 0,
    }));

    setFiles(prev => [...prev, ...uploadFiles]);
  };

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setIsUploading(true);

    for (const uploadFile of files) {
      if (uploadFile.status === 'completed') continue;

      try {
        // Update status to uploading
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id ? { ...f, status: 'uploading', progress: 0 } : f
        ));

        // Create FormData
        const formData = new FormData();
        formData.append('files', uploadFile.file);  // Backend expects 'files' (plural)

        // Upload file
        const response = await fetch(
          `http://localhost:8000/api/agent-builder/knowledgebases/${kbId}/documents`,
          {
            method: 'POST',
            body: formData,
          }
        );

        if (!response.ok) {
          throw new Error('Upload failed');
        }

        const result = await response.json();
        
        // Backend returns an array of documents, get the first one
        const document = Array.isArray(result) ? result[0] : result;
        const documentId = document?.id;

        // Update status to processing
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id ? { ...f, status: 'processing', progress: 50 } : f
        ));

        // Poll for processing status if we have a document ID
        if (documentId) {
          await pollProcessingStatus(uploadFile.id, documentId);
        } else {
          // If no document ID, mark as completed immediately
          setFiles(prev => prev.map(f => 
            f.id === uploadFile.id ? { ...f, status: 'completed', progress: 100 } : f
          ));
        }

      } catch (error: any) {
        console.error(`Failed to upload ${uploadFile.file.name}:`, error);
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id 
            ? { ...f, status: 'error', error: error.message } 
            : f
        ));
      }
    }

    setIsUploading(false);

    // Show completion toast
    const completed = files.filter(f => f.status === 'completed').length;
    const failed = files.filter(f => f.status === 'error').length;

    if (completed > 0) {
      toast({
        title: '✅ Upload Complete',
        description: `${completed} document${completed > 1 ? 's' : ''} uploaded successfully${failed > 0 ? `, ${failed} failed` : ''}`,
      });
    }
  };

  const pollProcessingStatus = async (fileId: string, documentId: string) => {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;

    while (attempts < maxAttempts) {
      try {
        const response = await fetch(
          `http://localhost:8000/api/agent-builder/knowledgebases/${kbId}/documents/${documentId}/status`
        );

        if (response.ok) {
          const status = await response.json();

          if (status.status === 'completed') {
            setFiles(prev => prev.map(f => 
              f.id === fileId ? { ...f, status: 'completed', progress: 100 } : f
            ));
            return;
          } else if (status.status === 'failed') {
            throw new Error(status.error || 'Processing failed');
          }

          // Update progress
          setFiles(prev => prev.map(f => 
            f.id === fileId 
              ? { ...f, progress: 50 + (status.progress || 0) * 0.5 } 
              : f
          ));
        }

        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
        attempts++;

      } catch (error: any) {
        setFiles(prev => prev.map(f => 
          f.id === fileId 
            ? { ...f, status: 'error', error: error.message } 
            : f
        ));
        return;
      }
    }

    // Timeout
    setFiles(prev => prev.map(f => 
      f.id === fileId 
        ? { ...f, status: 'error', error: 'Processing timeout' } 
        : f
    ));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'pending':
        return <FileText className="h-5 w-5 text-muted-foreground" />;
      case 'uploading':
      case 'processing':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
  };

  const getStatusText = (status: UploadFile['status']) => {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'uploading':
        return 'Uploading...';
      case 'processing':
        return 'Processing (OCR & Embedding)...';
      case 'completed':
        return 'Completed';
      case 'error':
        return 'Failed';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push('/agent-builder/knowledgebases')}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Upload Documents</h1>
          <p className="text-muted-foreground">
            Upload documents to your knowledgebase. Supports PDF, DOCX, TXT, and images.
          </p>
        </div>
      </div>

      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle>Select Files</CardTitle>
          <CardDescription>
            Drag and drop files or click to browse. Files will be processed with OCR and embedded into Milvus.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              isDragging
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25 hover:border-primary/50'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">
              Drop files here or click to browse
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              Supported formats: PDF, DOCX, TXT, PNG, JPG, JPEG
            </p>
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
              onChange={handleFileSelect}
              className="hidden"
              id="file-input"
            />
            <Button asChild>
              <label htmlFor="file-input" className="cursor-pointer">
                Browse Files
              </label>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Files ({files.length})</CardTitle>
                <CardDescription>
                  {files.filter(f => f.status === 'completed').length} completed,{' '}
                  {files.filter(f => f.status === 'error').length} failed
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setFiles([])}
                  disabled={isUploading}
                >
                  Clear All
                </Button>
                <Button
                  onClick={uploadFiles}
                  disabled={isUploading || files.every(f => f.status === 'completed')}
                >
                  {isUploading ? (
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
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {files.map(file => (
                <div
                  key={file.id}
                  className="flex items-center gap-4 p-4 border rounded-lg"
                >
                  {getStatusIcon(file.status)}
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium truncate">{file.file.name}</p>
                      <Badge variant="outline" className="text-xs">
                        {formatFileSize(file.file.size)}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <p className="text-sm text-muted-foreground">
                        {getStatusText(file.status)}
                      </p>
                      {file.error && (
                        <p className="text-sm text-red-500">- {file.error}</p>
                      )}
                    </div>
                    
                    {(file.status === 'uploading' || file.status === 'processing') && (
                      <Progress value={file.progress} className="mt-2 h-1" />
                    )}
                  </div>

                  {file.status === 'pending' && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeFile(file.id)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
