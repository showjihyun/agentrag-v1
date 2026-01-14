'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import {
  ChevronDown,
  Copy,
  Download,
  Trash,
  Archive,
  Share,
  Tag,
  Loader2,
  CheckCircle,
  XCircle,
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  description?: string;
  agent_type: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

interface AgentBatchActionsProps {
  agents: Agent[];
  selectedAgents: string[];
  onSelectionChange: (selectedIds: string[]) => void;
  onAgentsUpdated: () => void;
}

export function AgentBatchActions({
  agents,
  selectedAgents,
  onSelectionChange,
  onAgentsUpdated,
}: AgentBatchActionsProps) {
  const { toast } = useToast();
  const [isProcessing, setIsProcessing] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showArchiveDialog, setShowArchiveDialog] = useState(false);
  const [processingResults, setProcessingResults] = useState<{
    success: string[];
    failed: string[];
  }>({ success: [], failed: [] });

  const selectedCount = selectedAgents.length;
  const allSelected = agents.length > 0 && selectedAgents.length === agents.length;
  const someSelected = selectedAgents.length > 0 && selectedAgents.length < agents.length;

  const handleSelectAll = () => {
    if (allSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(agents.map(agent => agent.id));
    }
  };

  const handleBatchClone = async () => {
    if (selectedAgents.length === 0) return;

    setIsProcessing(true);
    const results: { success: string[]; failed: string[] } = { success: [], failed: [] };

    try {
      for (const agentId of selectedAgents) {
        try {
          await agentBuilderAPI.cloneAgent(agentId);
          results.success.push(agentId);
        } catch (error) {
          results.failed.push(agentId);
        }
      }

      setProcessingResults(results);
      
      toast({
        title: 'Batch Duplication Complete',
        description: `${results.success.length} succeeded, ${results.failed.length} failed`,
        ...(results.failed.length > 0 && { variant: 'destructive' as const }),
      });

      onAgentsUpdated();
      onSelectionChange([]);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'An error occurred during batch duplication',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBatchExport = async () => {
    if (selectedAgents.length === 0) return;

    setIsProcessing(true);
    
    try {
      const exportData = [];
      
      for (const agentId of selectedAgents) {
        try {
          const data = await agentBuilderAPI.exportAgent(agentId);
          exportData.push(data);
        } catch (error) {
          console.error(`Failed to export agent ${agentId}:`, error);
        }
      }

      // Create and download ZIP-like JSON file
      const blob = new Blob([JSON.stringify({
        agents: exportData,
        exported_at: new Date().toISOString(),
        count: exportData.length
      }, null, 2)], { type: 'application/json' });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `agents-batch-export-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);

      toast({
        title: 'Batch Export Complete',
        description: `${exportData.length} agents exported`,
      });

      onSelectionChange([]);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'An error occurred during batch export',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBatchDelete = async () => {
    if (selectedAgents.length === 0) return;

    setIsProcessing(true);
    const results: { success: string[]; failed: string[] } = { success: [], failed: [] };

    try {
      for (const agentId of selectedAgents) {
        try {
          await agentBuilderAPI.deleteAgent(agentId);
          results.success.push(agentId);
        } catch (error) {
          results.failed.push(agentId);
        }
      }

      setProcessingResults(results);
      
      toast({
        title: 'Batch Delete Complete',
        description: `${results.success.length} deleted, ${results.failed.length} failed`,
        ...(results.failed.length > 0 && { variant: 'destructive' as const }),
      });

      onAgentsUpdated();
      onSelectionChange([]);
      setShowDeleteDialog(false);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'An error occurred during batch deletion',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBatchMakePublic = async () => {
    if (selectedAgents.length === 0) return;

    setIsProcessing(true);
    const results: { success: string[]; failed: string[] } = { success: [], failed: [] };

    try {
      for (const agentId of selectedAgents) {
        try {
          await agentBuilderAPI.updateAgent(agentId, { is_public: true });
          results.success.push(agentId);
        } catch (error) {
          results.failed.push(agentId);
        }
      }

      toast({
        title: '배치 공개 설정 완료',
        description: `${results.success.length}개 공개됨, ${results.failed.length}개 실패`,
        ...(results.failed.length > 0 && { variant: 'destructive' as const }),
      });

      onAgentsUpdated();
      onSelectionChange([]);
    } catch (error) {
      toast({
        title: '오류',
        description: '배치 공개 설정 중 오류가 발생했습니다',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  if (agents.length === 0) {
    return null;
  }

  return (
    <>
      <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Checkbox
              checked={allSelected}
              ref={(el) => {
                if (el) (el as any).indeterminate = someSelected;
              }}
              onCheckedChange={handleSelectAll}
            />
            <span className="text-sm font-medium">
              {selectedCount > 0 ? `${selectedCount}개 선택됨` : '전체 선택'}
            </span>
          </div>

          {selectedCount > 0 && (
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
                {selectedCount}개 에이전트
              </Badge>
            </div>
          )}
        </div>

        {selectedCount > 0 && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleBatchClone}
              disabled={isProcessing}
              className="gap-2"
            >
              {isProcessing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              복제
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleBatchExport}
              disabled={isProcessing}
              className="gap-2"
            >
              {isProcessing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              내보내기
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                  더보기
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem 
                  onClick={isProcessing ? undefined : handleBatchMakePublic}
                  className={isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
                >
                  <Share className="mr-2 h-4 w-4" />
                  공개로 설정
                </DropdownMenuItem>
                <DropdownMenuItem 
                  onClick={isProcessing ? undefined : () => setShowArchiveDialog(true)}
                  className={isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
                >
                  <Archive className="mr-2 h-4 w-4" />
                  아카이브
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={isProcessing ? undefined : () => setShowDeleteDialog(true)} 
                  className={`text-destructive ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <Trash className="mr-2 h-4 w-4" />
                  삭제
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
      </div>

      {/* Processing Results */}
      {processingResults.success.length > 0 || processingResults.failed.length > 0 ? (
        <div className="p-4 bg-muted/30 rounded-lg border space-y-2">
          <h4 className="font-medium text-sm">처리 결과</h4>
          {processingResults.success.length > 0 && (
            <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-300">
              <CheckCircle className="h-4 w-4" />
              <span>{processingResults.success.length}개 성공</span>
            </div>
          )}
          {processingResults.failed.length > 0 && (
            <div className="flex items-center gap-2 text-sm text-red-700 dark:text-red-300">
              <XCircle className="h-4 w-4" />
              <span>{processingResults.failed.length}개 실패</span>
            </div>
          )}
        </div>
      ) : null}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>에이전트 삭제 확인</AlertDialogTitle>
            <AlertDialogDescription>
              선택한 {selectedCount}개의 에이전트를 삭제하시겠습니까? 
              이 작업은 되돌릴 수 없습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBatchDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={isProcessing}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  삭제 중...
                </>
              ) : (
                '삭제'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Archive Confirmation Dialog */}
      <AlertDialog open={showArchiveDialog} onOpenChange={setShowArchiveDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>에이전트 아카이브</AlertDialogTitle>
            <AlertDialogDescription>
              선택한 {selectedCount}개의 에이전트를 아카이브하시겠습니까? 
              아카이브된 에이전트는 목록에서 숨겨지지만 나중에 복원할 수 있습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction onClick={() => setShowArchiveDialog(false)}>
              아카이브
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}