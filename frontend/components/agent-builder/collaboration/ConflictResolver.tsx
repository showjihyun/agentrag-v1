'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertTriangle, Check, X } from 'lucide-react';

interface Conflict {
  id: string;
  type: 'content' | 'structure' | 'metadata';
  path: string;
  localVersion: any;
  remoteVersion: any;
  remoteUser: {
    id: string;
    name: string;
  };
  timestamp: string;
}

interface ConflictResolverProps {
  conflicts: Conflict[];
  onResolve: (conflictId: string, resolution: 'local' | 'remote' | 'merge') => void;
  onResolveAll: (resolution: 'local' | 'remote') => void;
}

export function ConflictResolver({ conflicts, onResolve, onResolveAll }: ConflictResolverProps) {
  const [selectedConflict, setSelectedConflict] = useState<Conflict | null>(
    conflicts[0] || null
  );

  if (conflicts.length === 0) return null;

  const handleResolve = (resolution: 'local' | 'remote' | 'merge') => {
    if (selectedConflict) {
      onResolve(selectedConflict.id, resolution);
      // Move to next conflict
      const currentIndex = conflicts.findIndex((c) => c.id === selectedConflict.id);
      if (currentIndex < conflicts.length - 1) {
        setSelectedConflict(conflicts[currentIndex + 1]);
      } else {
        setSelectedConflict(null);
      }
    }
  };

  const formatValue = (value: any): string => {
    if (typeof value === 'string') return value;
    return JSON.stringify(value, null, 2);
  };

  return (
    <Dialog open={conflicts.length > 0} onOpenChange={() => {}}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            <DialogTitle>Resolve Conflicts</DialogTitle>
          </div>
          <DialogDescription>
            {conflicts.length} {conflicts.length === 1 ? 'conflict' : 'conflicts'} detected.
            Choose which version to keep.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-4 gap-4">
          {/* Conflict List */}
          <div className="col-span-1 border-r pr-4">
            <h3 className="text-sm font-semibold mb-2">Conflicts</h3>
            <ScrollArea className="h-[400px]">
              <div className="space-y-2">
                {conflicts.map((conflict) => (
                  <div
                    key={conflict.id}
                    className={`p-2 rounded cursor-pointer transition-colors ${
                      selectedConflict?.id === conflict.id
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted'
                    }`}
                    onClick={() => setSelectedConflict(conflict)}
                  >
                    <div className="text-xs font-medium truncate">{conflict.path}</div>
                    <Badge variant="outline" className="text-xs mt-1">
                      {conflict.type}
                    </Badge>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>

          {/* Conflict Details */}
          {selectedConflict && (
            <div className="col-span-3 space-y-4">
              <div>
                <h3 className="text-sm font-semibold mb-1">Path</h3>
                <code className="text-xs bg-muted px-2 py-1 rounded">
                  {selectedConflict.path}
                </code>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Your Version */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold">Your Version</h3>
                    <Badge variant="default">Local</Badge>
                  </div>
                  <ScrollArea className="h-[250px] border rounded-md p-3 bg-muted/50">
                    <pre className="text-xs font-mono whitespace-pre-wrap">
                      {formatValue(selectedConflict.localVersion)}
                    </pre>
                  </ScrollArea>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full mt-2"
                    onClick={() => handleResolve('local')}
                  >
                    <Check className="mr-2 h-4 w-4" />
                    Keep Your Version
                  </Button>
                </div>

                {/* Their Version */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold">
                      {selectedConflict.remoteUser.name}'s Version
                    </h3>
                    <Badge variant="secondary">Remote</Badge>
                  </div>
                  <ScrollArea className="h-[250px] border rounded-md p-3 bg-muted/50">
                    <pre className="text-xs font-mono whitespace-pre-wrap">
                      {formatValue(selectedConflict.remoteVersion)}
                    </pre>
                  </ScrollArea>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full mt-2"
                    onClick={() => handleResolve('remote')}
                  >
                    <Check className="mr-2 h-4 w-4" />
                    Keep Their Version
                  </Button>
                </div>
              </div>

              <div className="text-xs text-muted-foreground">
                Conflict occurred at {new Date(selectedConflict.timestamp).toLocaleString()}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <div className="flex items-center justify-between w-full">
            <div className="text-sm text-muted-foreground">
              {conflicts.length} remaining
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => onResolveAll('local')}>
                Keep All Local
              </Button>
              <Button variant="outline" onClick={() => onResolveAll('remote')}>
                Keep All Remote
              </Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
