'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { useToast } from '@/hooks/use-toast';
import { GitCompare, TrendingUp, TrendingDown } from 'lucide-react';

interface DiffViewerProps {
  resourceType: 'agent' | 'workflow' | 'block';
  resourceId: string;
}

interface Version {
  id: string;
  version_number: number;
  created_at: string;
  created_by: string;
  description?: string;
}

interface Diff {
  path: string;
  type: 'added' | 'removed' | 'modified';
  old_value?: any;
  new_value?: any;
}

export function DiffViewer({ resourceType, resourceId }: DiffViewerProps) {
  const { toast } = useToast();
  const [versions, setVersions] = useState<Version[]>([]);
  const [versionA, setVersionA] = useState<string>('');
  const [versionB, setVersionB] = useState<string>('');
  const [diffs, setDiffs] = useState<Diff[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadVersions();
  }, [resourceType, resourceId]);

  const loadVersions = async () => {
    try {
      const data = await agentBuilderAPI.getVersions(resourceType, resourceId);
      setVersions(data.versions || []);
      
      if (data.versions && data.versions.length >= 2) {
        setVersionA(data.versions[1].id);
        setVersionB(data.versions[0].id);
      }
    } catch (error) {
      console.error('Failed to load versions:', error);
    }
  };

  const handleCompare = async () => {
    if (!versionA || !versionB) {
      toast({
        title: 'Validation Error',
        description: 'Please select two versions to compare',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      const data = await agentBuilderAPI.compareVersions(
        resourceType,
        resourceId,
        versionA,
        versionB
      );
      setDiffs(data.diffs || []);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to compare versions',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const getDiffTypeColor = (type: string) => {
    switch (type) {
      case 'added':
        return 'text-green-500 bg-green-50 dark:bg-green-950/50';
      case 'removed':
        return 'text-red-500 bg-red-50 dark:bg-red-950/50';
      case 'modified':
        return 'text-yellow-500 bg-yellow-50 dark:bg-yellow-950/50';
      default:
        return '';
    }
  };

  const getDiffIcon = (type: string) => {
    switch (type) {
      case 'added':
        return <TrendingUp className="h-4 w-4" />;
      case 'removed':
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <GitCompare className="h-4 w-4" />;
    }
  };

  const formatValue = (value: any): string => {
    if (typeof value === 'string') return value;
    return JSON.stringify(value, null, 2);
  };

  return (
    <div className="space-y-4">
      {/* Version Selectors */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div className="space-y-2">
              <label className="text-sm font-medium">Version A (Old)</label>
              <Select value={versionA} onValueChange={setVersionA}>
                <SelectTrigger>
                  <SelectValue placeholder="Select version" />
                </SelectTrigger>
                <SelectContent>
                  {versions.map((version) => (
                    <SelectItem key={version.id} value={version.id}>
                      v{version.version_number} -{' '}
                      {new Date(version.created_at).toLocaleDateString()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-center">
              <GitCompare className="h-6 w-6 text-muted-foreground" />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Version B (New)</label>
              <Select value={versionB} onValueChange={setVersionB}>
                <SelectTrigger>
                  <SelectValue placeholder="Select version" />
                </SelectTrigger>
                <SelectContent>
                  {versions.map((version) => (
                    <SelectItem key={version.id} value={version.id}>
                      v{version.version_number} -{' '}
                      {new Date(version.created_at).toLocaleDateString()}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button onClick={handleCompare} disabled={loading} className="w-full mt-4">
            {loading ? 'Comparing...' : 'Compare Versions'}
          </Button>
        </CardContent>
      </Card>

      {/* Diff Results */}
      {diffs.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Changes</h3>
              <Badge variant="outline">{diffs.length} differences</Badge>
            </div>

            <ScrollArea className="h-[500px]">
              <div className="space-y-3">
                {diffs.map((diff, index) => (
                  <Card key={index} className={getDiffTypeColor(diff.type)}>
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="mt-1">{getDiffIcon(diff.type)}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <code className="text-sm font-mono">{diff.path}</code>
                            <Badge variant="outline" className="text-xs">
                              {diff.type}
                            </Badge>
                          </div>

                          {diff.type === 'modified' && (
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-xs font-medium mb-1">Old Value</p>
                                <pre className="text-xs bg-background/50 p-2 rounded overflow-auto max-h-[200px]">
                                  {formatValue(diff.old_value)}
                                </pre>
                              </div>
                              <div>
                                <p className="text-xs font-medium mb-1">New Value</p>
                                <pre className="text-xs bg-background/50 p-2 rounded overflow-auto max-h-[200px]">
                                  {formatValue(diff.new_value)}
                                </pre>
                              </div>
                            </div>
                          )}

                          {diff.type === 'added' && (
                            <div>
                              <p className="text-xs font-medium mb-1">Added Value</p>
                              <pre className="text-xs bg-background/50 p-2 rounded overflow-auto max-h-[200px]">
                                {formatValue(diff.new_value)}
                              </pre>
                            </div>
                          )}

                          {diff.type === 'removed' && (
                            <div>
                              <p className="text-xs font-medium mb-1">Removed Value</p>
                              <pre className="text-xs bg-background/50 p-2 rounded overflow-auto max-h-[200px]">
                                {formatValue(diff.old_value)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {diffs.length === 0 && !loading && versionA && versionB && (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            <GitCompare className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No differences found between the selected versions</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
