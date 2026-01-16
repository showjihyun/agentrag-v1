'use client';

/**
 * ContextManager Component
 * 
 * Agent에 Context(Text, PDF 등)를 추가하는 직관적인 UI 컴포넌트
 * - Text 직접 입력
 * - PDF/문서 업로드 (기존 DocumentUpload 재사용)
 * - Context 목록 관리
 */

import React, { useState, useCallback } from 'react';
import {
  FileText,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  Upload,
  Type,
  Link,
  GripVertical,
  ChevronDown,
  ChevronUp,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';

export interface ContextItem {
  id: string;
  type: 'text' | 'file' | 'url';
  name: string;
  content: string;
  metadata?: {
    fileType?: string;
    fileSize?: number;
    url?: string;
  };
  createdAt: Date;
  priority?: number; // 우선순위 (낮을수록 먼저 처리)
}

interface ContextManagerProps {
  contexts: ContextItem[];
  onContextsChange: (contexts: ContextItem[]) => void;
  maxContexts?: number;
}

export function ContextManager({
  contexts,
  onContextsChange,
  maxContexts = 10,
}: ContextManagerProps) {
  const [activeTab, setActiveTab] = useState<'text' | 'file' | 'url'>('text');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  
  // Text input state
  const [textName, setTextName] = useState('');
  const [textContent, setTextContent] = useState('');
  
  // URL input state
  const [urlName, setUrlName] = useState('');
  const [urlValue, setUrlValue] = useState('');
  
  // File upload state
  const [isDragging, setIsDragging] = useState(false);

  const generateId = () => `ctx_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  const handleAddTextContext = () => {
    if (!textContent.trim()) return;
    
    const newContext: ContextItem = {
      id: generateId(),
      type: 'text',
      name: textName.trim() || `텍스트 ${contexts.filter(c => c.type === 'text').length + 1}`,
      content: textContent.trim(),
      createdAt: new Date(),
    };
    
    onContextsChange([...contexts, newContext]);
    setTextName('');
    setTextContent('');
    setIsAddDialogOpen(false);
  };

  const handleAddUrlContext = () => {
    if (!urlValue.trim()) return;
    
    const newContext: ContextItem = {
      id: generateId(),
      type: 'url',
      name: urlName.trim() || new URL(urlValue).hostname,
      content: urlValue.trim(),
      metadata: { url: urlValue.trim() },
      createdAt: new Date(),
    };
    
    onContextsChange([...contexts, newContext]);
    setUrlName('');
    setUrlValue('');
    setIsAddDialogOpen(false);
  };

  const handleFileUpload = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);
    
    fileArray.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const newContext: ContextItem = {
          id: generateId(),
          type: 'file',
          name: file.name,
          content: e.target?.result as string || '',
          metadata: {
            fileType: file.type,
            fileSize: file.size,
          },
          createdAt: new Date(),
        };
        
        onContextsChange(prev => [...prev, newContext]);
      };
      
      if (file.type === 'application/pdf') {
        // PDF는 base64로 저장
        reader.readAsDataURL(file);
      } else {
        // 텍스트 파일은 텍스트로 읽기
        reader.readAsText(file);
      }
    });
    
    setIsAddDialogOpen(false);
  }, [onContextsChange]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileUpload(e.dataTransfer.files);
  };

  const handleRemoveContext = (id: string) => {
    onContextsChange(contexts.filter(c => c.id !== id));
  };

  const handleUpdateContext = (id: string, updates: Partial<ContextItem>) => {
    onContextsChange(
      contexts.map(c => c.id === id ? { ...c, ...updates } : c)
    );
    setEditingId(null);
  };

  const handleMovePriority = (id: string, direction: 'up' | 'down') => {
    const index = contexts.findIndex(c => c.id === id);
    if (index === -1) return;
    
    const newContexts = [...contexts];
    if (direction === 'up' && index > 0) {
      // Swap with previous item
      [newContexts[index - 1], newContexts[index]] = [newContexts[index], newContexts[index - 1]];
    } else if (direction === 'down' && index < contexts.length - 1) {
      // Swap with next item
      [newContexts[index], newContexts[index + 1]] = [newContexts[index + 1], newContexts[index]];
    }
    
    // Update priorities
    const updatedContexts = newContexts.map((ctx, idx) => ({
      ...ctx,
      priority: idx
    }));
    
    onContextsChange(updatedContexts);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getTypeIcon = (type: ContextItem['type']) => {
    switch (type) {
      case 'text': return <Type className="h-4 w-4" />;
      case 'file': return <FileText className="h-4 w-4" />;
      case 'url': return <Link className="h-4 w-4" />;
    }
  };

  const getTypeBadgeColor = (type: ContextItem['type']) => {
    switch (type) {
      case 'text': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'file': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'url': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Context 관리
            </CardTitle>
            <CardDescription>
              Agent가 참조할 텍스트, 문서, URL을 추가하세요
            </CardDescription>
          </div>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button 
                size="sm" 
                disabled={contexts.length >= maxContexts}
              >
                <Plus className="h-4 w-4 mr-1" />
                추가
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>Context 추가</DialogTitle>
                <DialogDescription>
                  Agent가 참조할 컨텍스트를 추가합니다
                </DialogDescription>
              </DialogHeader>
              
              <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="text" className="flex items-center gap-1">
                    <Type className="h-4 w-4" />
                    텍스트
                  </TabsTrigger>
                  <TabsTrigger value="file" className="flex items-center gap-1">
                    <Upload className="h-4 w-4" />
                    파일
                  </TabsTrigger>
                  <TabsTrigger value="url" className="flex items-center gap-1">
                    <Link className="h-4 w-4" />
                    URL
                  </TabsTrigger>
                </TabsList>
                
                <TabsContent value="text" className="space-y-4 mt-4">
                  <div>
                    <label className="text-sm font-medium">이름 (선택)</label>
                    <Input
                      placeholder="컨텍스트 이름"
                      value={textName}
                      onChange={(e) => setTextName(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">내용 *</label>
                    <Textarea
                      placeholder="Agent가 참조할 텍스트를 입력하세요..."
                      value={textContent}
                      onChange={(e) => setTextContent(e.target.value)}
                      className="mt-1 min-h-[200px]"
                    />
                  </div>
                  <Button 
                    onClick={handleAddTextContext}
                    disabled={!textContent.trim()}
                    className="w-full"
                  >
                    텍스트 추가
                  </Button>
                </TabsContent>
                
                <TabsContent value="file" className="mt-4">
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={cn(
                      "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
                      isDragging 
                        ? "border-primary bg-primary/5" 
                        : "border-muted-foreground/25 hover:border-primary/50"
                    )}
                    onClick={() => document.getElementById('context-file-input')?.click()}
                  >
                    <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
                    <p className="text-sm font-medium mb-1">
                      파일을 드래그하거나 클릭하여 업로드
                    </p>
                    <p className="text-xs text-muted-foreground">
                      PDF, TXT, DOCX, MD 지원 (최대 10MB)
                    </p>
                    <input
                      id="context-file-input"
                      type="file"
                      multiple
                      accept=".pdf,.txt,.docx,.md,.json"
                      className="hidden"
                      onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                    />
                  </div>
                </TabsContent>
                
                <TabsContent value="url" className="space-y-4 mt-4">
                  <div>
                    <label className="text-sm font-medium">이름 (선택)</label>
                    <Input
                      placeholder="URL 이름"
                      value={urlName}
                      onChange={(e) => setUrlName(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">URL *</label>
                    <Input
                      placeholder="https://example.com/document"
                      value={urlValue}
                      onChange={(e) => setUrlValue(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                  <Button 
                    onClick={handleAddUrlContext}
                    disabled={!urlValue.trim()}
                    className="w-full"
                  >
                    URL 추가
                  </Button>
                </TabsContent>
              </Tabs>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      
      <CardContent>
        {contexts.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="text-sm">아직 추가된 Context가 없습니다</p>
            <p className="text-xs mt-1">위의 추가 버튼을 클릭하여 시작하세요</p>
          </div>
        ) : (
          <ScrollArea className="h-[400px] pr-4">
            <div className="space-y-3">
              {contexts.map((context, index) => (
                <ContextItemCard
                  key={context.id}
                  context={context}
                  isEditing={editingId === context.id}
                  isFirst={index === 0}
                  isLast={index === contexts.length - 1}
                  onEdit={() => setEditingId(context.id)}
                  onCancelEdit={() => setEditingId(null)}
                  onUpdate={(updates) => handleUpdateContext(context.id, updates)}
                  onRemove={() => handleRemoveContext(context.id)}
                  onMoveUp={() => handleMovePriority(context.id, 'up')}
                  onMoveDown={() => handleMovePriority(context.id, 'down')}
                  getTypeIcon={getTypeIcon}
                  getTypeBadgeColor={getTypeBadgeColor}
                  formatFileSize={formatFileSize}
                />
              ))}
            </div>
          </ScrollArea>
        )}
        
        {contexts.length > 0 && (
          <div className="mt-4 pt-4 border-t flex items-center justify-between text-sm text-muted-foreground">
            <span>{contexts.length} / {maxContexts} Context</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onContextsChange([])}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-1" />
              모두 삭제
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Context Item Card Component
interface ContextItemCardProps {
  context: ContextItem;
  isEditing: boolean;
  isFirst: boolean;
  isLast: boolean;
  onEdit: () => void;
  onCancelEdit: () => void;
  onUpdate: (updates: Partial<ContextItem>) => void;
  onRemove: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  getTypeIcon: (type: ContextItem['type']) => React.ReactNode;
  getTypeBadgeColor: (type: ContextItem['type']) => string;
  formatFileSize: (bytes?: number) => string;
}

function ContextItemCard({
  context,
  isEditing,
  isFirst,
  isLast,
  onEdit,
  onCancelEdit,
  onUpdate,
  onRemove,
  onMoveUp,
  onMoveDown,
  getTypeIcon,
  getTypeBadgeColor,
  formatFileSize,
}: ContextItemCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [editName, setEditName] = useState(context.name);
  const [editContent, setEditContent] = useState(context.content);

  const handleSave = () => {
    onUpdate({ name: editName, content: editContent });
  };

  return (
    <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
      <Card className="border">
        <div className="p-3">
          <div className="flex items-center gap-3">
            {/* Priority indicator */}
            <div className="flex flex-col items-center gap-0.5">
              <div className="text-xs font-medium text-muted-foreground">
                #{(context.priority ?? 0) + 1}
              </div>
              <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab" />
            </div>
            
            <div className={cn("p-2 rounded", getTypeBadgeColor(context.type))}>
              {getTypeIcon(context.type)}
            </div>
            
            <div className="flex-1 min-w-0">
              {isEditing ? (
                <Input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="h-7 text-sm"
                />
              ) : (
                <p className="font-medium text-sm truncate">{context.name}</p>
              )}
              <div className="flex items-center gap-2 mt-0.5">
                <Badge variant="outline" className="text-xs">
                  {context.type === 'text' ? '텍스트' : context.type === 'file' ? '파일' : 'URL'}
                </Badge>
                {context.metadata?.fileSize && (
                  <span className="text-xs text-muted-foreground">
                    {formatFileSize(context.metadata.fileSize)}
                  </span>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-1">
              {isEditing ? (
                <>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleSave}>
                    <Check className="h-4 w-4 text-green-600" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onCancelEdit}>
                    <X className="h-4 w-4" />
                  </Button>
                </>
              ) : (
                <>
                  {/* Priority buttons */}
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-7 w-7" 
                    onClick={onMoveUp}
                    disabled={isFirst}
                    title="우선순위 올리기"
                  >
                    <ArrowUp className="h-4 w-4" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-7 w-7" 
                    onClick={onMoveDown}
                    disabled={isLast}
                    title="우선순위 내리기"
                  >
                    <ArrowDown className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onEdit}>
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-7 w-7 text-destructive hover:text-destructive"
                    onClick={onRemove}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </>
              )}
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="icon" className="h-7 w-7">
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </div>
          </div>
        </div>
        
        <CollapsibleContent>
          <div className="px-3 pb-3 pt-0">
            <div className="bg-muted rounded p-3">
              {isEditing && context.type === 'text' ? (
                <Textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="min-h-[100px] text-sm"
                />
              ) : (
                <pre className="text-xs whitespace-pre-wrap break-words max-h-[200px] overflow-auto">
                  {context.type === 'file' && context.content.startsWith('data:') 
                    ? '[PDF 파일 - 미리보기 불가]'
                    : context.content.slice(0, 500) + (context.content.length > 500 ? '...' : '')
                  }
                </pre>
              )}
            </div>
          </div>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

export default ContextManager;
