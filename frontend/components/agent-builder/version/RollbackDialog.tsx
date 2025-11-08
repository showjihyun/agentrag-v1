'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { RotateCcw, AlertTriangle, CheckCircle } from 'lucide-react';
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

interface RollbackDialogProps {
  resourceType: 'agent' | 'workflow' | 'block';
  resourceId: string;
  currentVersion: any;
  onRollback?: () => void;
}

interface Version {
  id: string;
  version_number: number;
  created_at: string;
  created_by: string;
  description?: string;
  metrics?: {
    success_rate?: number;
    avg_response_time?: number;
    execution_count?: number;
  };
}

export function RollbackDialog({
  resourceType,
  resourceId,
  currentVersion,
  onRollback,
}: RollbackDialogProps) {
  const { toast } = useToast();
  const [versions, setVersions] = useState<Version[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<Version | null>(null);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [rolling, setRolling] = useState(false);

  useEffect(() => {
    loadVersions();
  }, [resourceType, resourceId]);

  const loadVersions = async () => {
    try {
      const data = await agentBuilderAPI.getVersions(resourceType, resourceId);
      setVersions(data.versions || []);
    } catch (error) {
      console.error('Failed to load versions:', error);
    }
  };

  const handleRollback = async () => {
    if (!selectedVersion) return;

    setRolling(true);
    try {
      await agentBuilderAPI.rollbackToVersion(
        resourceType,
        resourceId,
        selectedVersion.id
      );

      toast({
        title: 'Rollback Successful',
        description: `Rolled back to version ${selectedVersion.version_number}`,
      });

      setConfirmDialogOpen(false);
      setSelectedVersion(null);
      
      if (onRollback) onRollback();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to rollback',
        variant: 'destructive',
      });
    } finally {
      setRolling(false);
    }
  };

  const isCurrentVersion = (version: Version) => {
    return currentVersion && version.id === currentVersion.id;
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 p-4 bg-yellow-50 dark:bg-yellow-950/50 border border-yellow-200 dark:border-yellow-900 rounded-md mb-4">
            <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            <div>
              <p className="font-semibold text-yellow-800 dark:text-yellow-200">
                Warning: Rollback Action
              </p>
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                Rolling back will immediately switch to the selected version. This action can be
                undone by rolling back again.
              </p>
            </div>
          </div>

          <h3 className="text-lg font-semibold mb-4">Select Version to Rollback</h3>

          <ScrollArea className="h-[400px]">
            <div className="space-y-3">
              {versions.map((version) => (
                <Card
                  key={version.id}
                  className={`cursor-pointer transition-colors ${
                    selectedVersion?.id === version.id
                      ? 'border-primary'
                      : isCurrentVersion(version)
                      ? 'border-green-500'
                      : ''
                  }`}
                  onClick={() => !isCurrentVersion(version) && setSelectedVersion(version)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="font-semibold">Version {version.version_number}</h4>
                          {isCurrentVersion(version) && (
                            <Badge variant="default">
                              <CheckCircle className="mr-1 h-3 w-3" />
                              Current
                            </Badge>
                          )}
                        </div>
                        {version.description && (
                          <p className="text-sm text-muted-foreground mb-2">
                            {version.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span>
                            Created {new Date(version.created_at).toLocaleDateString()}
                          </span>
                          <span>•</span>
                          <span>By {version.created_by}</span>
                        </div>

                        {version.metrics && (
                          <div className="flex items-center gap-4 mt-2 text-xs">
                            {version.metrics.success_rate !== undefined && (
                              <span>
                                Success: {version.metrics.success_rate.toFixed(1)}%
                              </span>
                            )}
                            {version.metrics.avg_response_time !== undefined && (
                              <span>
                                Avg Time: {version.metrics.avg_response_time.toFixed(2)}s
                              </span>
                            )}
                            {version.metrics.execution_count !== undefined && (
                              <span>{version.metrics.execution_count} executions</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>

          <Button
            onClick={() => setConfirmDialogOpen(true)}
            disabled={!selectedVersion}
            className="w-full mt-4"
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            Rollback to Selected Version
          </Button>
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <AlertDialog open={confirmDialogOpen} onOpenChange={setConfirmDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm Rollback</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to rollback to version {selectedVersion?.version_number}?
              <br />
              <br />
              This will immediately switch your {resourceType} to the selected version. All
              current changes will be preserved in the version history.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRollback} disabled={rolling}>
              {rolling ? 'Rolling back...' : 'Confirm Rollback'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
