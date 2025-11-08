'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/Toast';
import {
  Briefcase,
  Plus,
  Check,
  Settings,
  Users,
  ChevronDown,
} from 'lucide-react';

interface Workspace {
  id: string;
  name: string;
  description?: string;
  role: 'owner' | 'admin' | 'member';
  memberCount: number;
  createdAt: string;
}

interface WorkspaceManagerProps {
  currentWorkspace?: Workspace;
  workspaces?: Workspace[];
  onWorkspaceChange?: (workspaceId: string) => void;
  onCreateWorkspace?: (workspace: Omit<Workspace, 'id' | 'createdAt'>) => Promise<void>;
}

export function WorkspaceManager({
  currentWorkspace,
  workspaces = [],
  onWorkspaceChange,
  onCreateWorkspace,
}: WorkspaceManagerProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [isCreateDialogOpen, setIsCreateDialogOpen] = React.useState(false);
  const [formData, setFormData] = React.useState({
    name: '',
    description: '',
  });

  const handleWorkspaceSwitch = (workspaceId: string) => {
    onWorkspaceChange?.(workspaceId);
    toast({
      title: 'Workspace switched',
      description: 'You are now working in a different workspace',
    });
  };

  const handleCreateWorkspace = async () => {
    if (!formData.name.trim()) {
      toast({
        variant: 'destructive',
        title: 'Name required',
        description: 'Please enter a workspace name',
      });
      return;
    }

    try {
      await onCreateWorkspace?.({
        name: formData.name,
        description: formData.description,
        role: 'owner',
        memberCount: 1,
      });

      toast({
        title: 'Workspace created',
        description: `${formData.name} has been created successfully`,
      });

      setIsCreateDialogOpen(false);
      setFormData({ name: '', description: '' });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to create workspace',
        description: 'Could not create workspace',
      });
    }
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="w-full justify-between">
            <div className="flex items-center gap-2">
              <Briefcase className="h-4 w-4" />
              <span className="truncate">
                {currentWorkspace?.name || 'Select Workspace'}
              </span>
            </div>
            <ChevronDown className="h-4 w-4 ml-2" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-[300px]">
          <DropdownMenuLabel>Workspaces</DropdownMenuLabel>
          <DropdownMenuSeparator />

          {workspaces.map((workspace) => (
            <DropdownMenuItem
              key={workspace.id}
              onClick={() => handleWorkspaceSwitch(workspace.id)}
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <Briefcase className="h-4 w-4 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="truncate">{workspace.name}</span>
                    {workspace.id === currentWorkspace?.id && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Badge variant="outline" className="text-xs">
                      {workspace.role}
                    </Badge>
                    <span className="flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      {workspace.memberCount}
                    </span>
                  </div>
                </div>
              </div>
            </DropdownMenuItem>
          ))}

          <DropdownMenuSeparator />

          <DropdownMenuItem onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Workspace
          </DropdownMenuItem>

          {currentWorkspace && (
            <DropdownMenuItem
              onClick={() =>
                router.push(`/agent-builder/workspaces/${currentWorkspace.id}/settings`)
              }
            >
              <Settings className="h-4 w-4 mr-2" />
              Workspace Settings
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Create Workspace Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Workspace</DialogTitle>
            <DialogDescription>
              Create a new workspace to organize your agents and workflows
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="workspace-name">Workspace Name</Label>
              <Input
                id="workspace-name"
                placeholder="My Workspace"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="workspace-description">
                Description (optional)
              </Label>
              <Textarea
                id="workspace-description"
                placeholder="What is this workspace for?"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsCreateDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleCreateWorkspace} disabled={!formData.name.trim()}>
              Create Workspace
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
