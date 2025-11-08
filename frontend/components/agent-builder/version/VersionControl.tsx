'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { BranchManager } from './BranchManager';
import { DiffViewer } from './DiffViewer';
import { RollbackDialog } from './RollbackDialog';
import { VersionHistory } from './VersionHistory';
import { GitBranch, History, GitCompare, RotateCcw } from 'lucide-react';

interface VersionControlProps {
  resourceType: 'agent' | 'workflow' | 'block';
  resourceId: string;
}

export function VersionControl({ resourceType, resourceId }: VersionControlProps) {
  const [currentVersion, setCurrentVersion] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCurrentVersion();
  }, [resourceType, resourceId]);

  const loadCurrentVersion = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getCurrentVersion(resourceType, resourceId);
      setCurrentVersion(data);
    } catch (error) {
      console.error('Failed to load current version:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Version Control
          </CardTitle>
          <CardDescription>
            Manage versions, branches, and rollbacks for your {resourceType}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="history" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="history" className="gap-2">
                <History className="h-4 w-4" />
                History
              </TabsTrigger>
              <TabsTrigger value="branches" className="gap-2">
                <GitBranch className="h-4 w-4" />
                Branches
              </TabsTrigger>
              <TabsTrigger value="compare" className="gap-2">
                <GitCompare className="h-4 w-4" />
                Compare
              </TabsTrigger>
              <TabsTrigger value="rollback" className="gap-2">
                <RotateCcw className="h-4 w-4" />
                Rollback
              </TabsTrigger>
            </TabsList>

            <TabsContent value="history">
              <VersionHistory
                resourceType={resourceType}
                resourceId={resourceId}
                onVersionSelect={(version) => setCurrentVersion(version)}
              />
            </TabsContent>

            <TabsContent value="branches">
              <BranchManager
                resourceType={resourceType}
                resourceId={resourceId}
                currentVersion={currentVersion}
              />
            </TabsContent>

            <TabsContent value="compare">
              <DiffViewer
                resourceType={resourceType}
                resourceId={resourceId}
              />
            </TabsContent>

            <TabsContent value="rollback">
              <RollbackDialog
                resourceType={resourceType}
                resourceId={resourceId}
                currentVersion={currentVersion}
                onRollback={loadCurrentVersion}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
