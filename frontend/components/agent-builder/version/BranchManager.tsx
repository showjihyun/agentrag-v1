'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import {
  GitBranch,
  Plus,
  GitMerge,
  Trash2,
  Check,
  Star,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

interface BranchManagerProps {
  resourceType: 'agent' | 'workflow' | 'block';
  resourceId: string;
  currentVersion: any;
}

interface Branch {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  created_by: string;
  is_main: boolean;
  is_active: boolean;
  commit_count: number;
  last_commit_at?: string;
}

export function BranchManager({ resourceType, resourceId, currentVersion }: BranchManagerProps) {
  const { toast } = useToast();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [mergeDialogOpen, setMergeDialogOpen] = useState(false);
  const [newBranchName, setNewBranchName] = useState('');
  const [newBranchDescription, setNewBranchDescription] = useState('');
  const [selectedBranch, setSelectedBranch] = useState<Branch | null>(null);

  useEffect(() => {
    loadBranches();
  }, [resourceType, resourceId]);

  const loadBranches = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getBranches(resourceType, resourceId);
      setBranches(data.branches || []);
    } catch (error) {
      console.error('Failed to load branches:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBranch = async () => {
    if (!newBranchName.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Branch name is required',
        variant: 'destructive',
      });
      return;
    }

    try {
      await agentBuilderAPI.createBranch(resourceType, resourceId, {
        name: newBranchName,
        description: newBranchDescription,
        source_version: currentVersion?.id,
      });

      toast({
        title: 'Branch Created',
        description: `Branch "${newBranchName}" has been created`,
      });

      setCreateDialogOpen(false);
      setNewBranchName('');
      setNewBranchDescription('');
      loadBranches();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create branch',
        variant: 'destructive',
      });
    }
  };

  const handleMergeBranch = async () => {
    if (!selectedBranch) return;

    try {
      await agentBuilderAPI.mergeBranch(resourceType, resourceId, {
        source_branch: selectedBranch.id,
        target_branch: 'main',
      });

      toast({
        title: 'Branch Merged',
        description: `Branch "${selectedBranch.name}" has been merged into main`,
      });

      setMergeDialogOpen(false);
      setSelectedBranch(null);
      loadBranches();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to merge branch',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteBranch = async (branchId: string, branchName: string) => {
    if (!confirm(`Are you sure you want to delete branch "${branchName}"?`)) {
      return;
    }

    try {
      await agentBuilderAPI.deleteBranch(resourceType, resourceId, branchId);

      toast({
        title: 'Branch Deleted',
        description: `Branch "${branchName}" has been deleted`,
      });

      loadBranches();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete branch',
        variant: 'destructive',
      });
    }
  };

  const handleSwitchBranch = async (branchId: string) => {
    try {
      await agentBuilderAPI.switchBranch(resourceType, resourceId, branchId);

      toast({
        title: 'Branch Switched',
        description: 'Successfully switched to the selected branch',
      });

      loadBranches();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to switch branch',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Branches</h3>
          <p className="text-sm text-muted-foreground">
            {branches.length} {branches.length === 1 ? 'branch' : 'branches'}
          </p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Branch
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Branch</DialogTitle>
              <DialogDescription>
                Create a new branch from the current version
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="branch-name">Branch Name *</Label>
                <Input
                  id="branch-name"
                  value={newBranchName}
                  onChange={(e) => setNewBranchName(e.target.value)}
                  placeholder="feature/new-capability"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="branch-description">Description</Label>
                <Input
                  id="branch-description"
                  value={newBranchDescription}
                  onChange={(e) => setNewBranchDescription(e.target.value)}
                  placeholder="Describe the purpose of this branch..."
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateBranch}>Create Branch</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <ScrollArea className="h-[500px]">
        <div className="space-y-3">
          {branches.map((branch) => (
            <Card key={branch.id} className={branch.is_active ? 'border-primary' : ''}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <GitBranch className="h-4 w-4" />
                      <h4 className="font-semibold">{branch.name}</h4>
                      {branch.is_main && (
                        <Badge variant="default">
                          <Star className="mr-1 h-3 w-3" />
                          Main
                        </Badge>
                      )}
                      {branch.is_active && (
                        <Badge variant="outline">
                          <Check className="mr-1 h-3 w-3" />
                          Active
                        </Badge>
                      )}
                    </div>
                    {branch.description && (
                      <p className="text-sm text-muted-foreground mb-2">
                        {branch.description}
                      </p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>{branch.commit_count} commits</span>
                      <span>•</span>
                      <span>Created {new Date(branch.created_at).toLocaleDateString()}</span>
                      {branch.last_commit_at && (
                        <>
                          <span>•</span>
                          <span>
                            Last commit {new Date(branch.last_commit_at).toLocaleDateString()}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {!branch.is_active && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleSwitchBranch(branch.id)}
                      >
                        Switch
                      </Button>
                    )}
                    {!branch.is_main && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedBranch(branch);
                            setMergeDialogOpen(true);
                          }}
                        >
                          <GitMerge className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDeleteBranch(branch.id, branch.name)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>

      {/* Merge Dialog */}
      <Dialog open={mergeDialogOpen} onOpenChange={setMergeDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Merge Branch</DialogTitle>
            <DialogDescription>
              Merge "{selectedBranch?.name}" into main branch
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm">
              This will merge all changes from "{selectedBranch?.name}" into the main branch.
              This action cannot be undone.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMergeDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleMergeBranch}>
              <GitMerge className="mr-2 h-4 w-4" />
              Merge Branch
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
