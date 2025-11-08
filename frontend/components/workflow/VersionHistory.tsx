'use client';

import React, { useState, useEffect } from 'react';
import { Clock, RotateCcw, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';

export interface WorkflowVersion {
  id: string;
  version: number;
  created_at: string;
  created_by?: string;
  changes_summary?: string;
  is_current: boolean;
}

interface VersionHistoryProps {
  workflowId: string;
  onRestore?: (versionId: string) => void;
  onPreview?: (versionId: string) => void;
}

export function VersionHistory({ workflowId, onRestore, onPreview }: VersionHistoryProps) {
  const { toast } = useToast();
  const [versions, setVersions] = useState<WorkflowVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<WorkflowVersion | null>(null);

  useEffect(() => {
    loadVersions();
  }, [workflowId]);

  const loadVersions = async () => {
    try {
      setLoading(true);
      // TODO: Implement API call to get versions
      // const data = await agentBuilderAPI.getWorkflowVersions(workflowId);
      // setVersions(data);
      
      // Mock data for now
      setVersions([
        {
          id: '1',
          version: 3,
          created_at: new Date().toISOString(),
          created_by: 'Current User',
          changes_summary: 'Added HTTP block and updated OpenAI configuration',
          is_current: true,
        },
        {
          id: '2',
          version: 2,
          created_at: new Date(Date.now() - 3600000).toISOString(),
          created_by: 'Current User',
          changes_summary: 'Initial workflow setup',
          is_current: false,
        },
      ]);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to load version history',
        variant: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async () => {
    if (!selectedVersion) return;

    try {
      await onRestore?.(selectedVersion.id);
      toast({
        title: 'Success',
        description: `Restored to version ${selectedVersion.version}`,
        variant: 'success',
      });
      setRestoreDialogOpen(false);
      loadVersions();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to restore version',
        variant: 'error',
      });
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          <h3 className="font-semibold">Version History</h3>
        </div>

        <ScrollArea className="h-[400px]">
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-3 border rounded-lg">
                  <Skeleton className="h-4 w-24 mb-2" />
                  <Skeleton className="h-3 w-full mb-2" />
                  <Skeleton className="h-3 w-32" />
                </div>
              ))}
            </div>
          ) : versions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Clock className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No version history available</p>
            </div>
          ) : (
            <div className="space-y-3">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className="p-3 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">Version {version.version}</span>
                      {version.is_current && (
                        <Badge variant="default" className="text-xs">
                          Current
                        </Badge>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatDate(version.created_at)}
                    </span>
                  </div>

                  {version.changes_summary && (
                    <p className="text-sm text-muted-foreground mb-2">
                      {version.changes_summary}
                    </p>
                  )}

                  {version.created_by && (
                    <p className="text-xs text-muted-foreground mb-2">
                      By {version.created_by}
                    </p>
                  )}

                  {!version.is_current && (
                    <div className="flex gap-2 mt-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onPreview?.(version.id)}
                        className="gap-1"
                      >
                        <Eye className="h-3 w-3" />
                        Preview
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedVersion(version);
                          setRestoreDialogOpen(true);
                        }}
                        className="gap-1"
                      >
                        <RotateCcw className="h-3 w-3" />
                        Restore
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>

      <Dialog open={restoreDialogOpen} onOpenChange={setRestoreDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Restore Version</DialogTitle>
            <DialogDescription>
              Are you sure you want to restore to version {selectedVersion?.version}? This will
              create a new version with the restored content.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRestoreDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleRestore}>Restore</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
