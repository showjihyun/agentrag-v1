'use client';

import React from 'react';
import { Node, useReactFlow } from 'reactflow';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Group, Ungroup } from 'lucide-react';

interface NodeGroupingProps {
  selectedNodes: Node[];
  onGroup: (groupName: string, nodeIds: string[]) => void;
  onUngroup: (groupId: string) => void;
}

export function NodeGrouping({ selectedNodes, onGroup, onUngroup }: NodeGroupingProps) {
  const [isGroupDialogOpen, setIsGroupDialogOpen] = React.useState(false);
  const [groupName, setGroupName] = React.useState('');

  const handleGroup = () => {
    if (groupName.trim() && selectedNodes.length > 1) {
      onGroup(groupName, selectedNodes.map(n => n.id));
      setGroupName('');
      setIsGroupDialogOpen(false);
    }
  };

  const canGroup = selectedNodes.length > 1;
  const canUngroup = selectedNodes.length === 1 && selectedNodes[0].type === 'group';

  return (
    <>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={!canGroup}
          onClick={() => setIsGroupDialogOpen(true)}
          aria-label="Group selected nodes"
        >
          <Group className="h-4 w-4 mr-2" />
          Group ({selectedNodes.length})
        </Button>

        {canUngroup && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onUngroup(selectedNodes[0].id)}
            aria-label="Ungroup nodes"
          >
            <Ungroup className="h-4 w-4 mr-2" />
            Ungroup
          </Button>
        )}
      </div>

      <Dialog open={isGroupDialogOpen} onOpenChange={setIsGroupDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Node Group</DialogTitle>
            <DialogDescription>
              Group {selectedNodes.length} nodes together with a name
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="group-name">Group Name</Label>
              <Input
                id="group-name"
                placeholder="e.g., Data Processing"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleGroup();
                  }
                }}
              />
            </div>

            <div className="text-sm text-muted-foreground">
              Selected nodes:
              <ul className="list-disc list-inside mt-2">
                {selectedNodes.slice(0, 5).map((node) => (
                  <li key={node.id}>{node.data.label || node.id}</li>
                ))}
                {selectedNodes.length > 5 && (
                  <li>... and {selectedNodes.length - 5} more</li>
                )}
              </ul>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsGroupDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleGroup} disabled={!groupName.trim()}>
              Create Group
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
