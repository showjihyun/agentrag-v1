'use client';

/**
 * Node Configuration Panel
 * 
 * Accessible configuration panel with:
 * - Shadcn UI components (no native selects)
 * - Confirm dialog for destructive actions
 * - Keyboard navigation
 * - Screen reader support
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Node } from 'reactflow';
import { X, Settings, Trash2, Eye, EyeOff, Save, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { RetryConfig } from './RetryConfig';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { cn } from '@/lib/utils';

interface NodeConfigPanelProps {
  node: Node | null;
  onClose: () => void;
  onUpdate: (nodeId: string, data: any) => void;
  onDelete: (nodeId: string) => void;
}

// Node type badge colors
const nodeTypeColors: Record<string, string> = {
  agent: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  block: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  condition: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  trigger: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
  start: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  end: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  loop: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  parallel: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300',
  delay: 'bg-slate-100 text-slate-700 dark:bg-slate-800/50 dark:text-slate-300',
  http_request: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
  switch: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  merge: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300',
  code: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
};


export function NodeConfigPanel({ node, onClose, onUpdate, onDelete }: NodeConfigPanelProps) {
  const [config, setConfig] = useState<any>({});
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    if (node) {
      setConfig(node.data || {});
      setHasUnsavedChanges(false);
    }
  }, [node]);

  const updateConfig = useCallback((updates: Partial<any>) => {
    setConfig((prev: any) => ({ ...prev, ...updates }));
    setHasUnsavedChanges(true);
  }, []);

  if (!node) return null;

  const handleUpdate = () => {
    onUpdate(node.id, config);
    setHasUnsavedChanges(false);
  };

  const handleDelete = () => {
    setShowDeleteDialog(true);
  };

  const confirmDelete = () => {
    onDelete(node.id);
    setShowDeleteDialog(false);
    onClose();
  };

  // Keyboard shortcut handler
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      handleUpdate();
    }
    if (e.key === 'Escape') {
      onClose();
    }
  };

  const renderConfigFields = () => {
    switch (node.type) {
      case 'agent':
        return (
          <div className="space-y-4" role="group" aria-label="Agent configuration">
            <div className="space-y-2">
              <Label htmlFor="agent-name">Agent Name</Label>
              <Input
                id="agent-name"
                value={config.name || ''}
                onChange={(e) => updateConfig({ name: e.target.value })}
                placeholder="Enter agent name"
                aria-describedby="agent-name-hint"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="agent-description">Description</Label>
              <Textarea
                id="agent-description"
                value={config.description || ''}
                onChange={(e) => updateConfig({ description: e.target.value })}
                placeholder="Describe what this agent does"
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="agent-prompt">System Prompt</Label>
              <Textarea
                id="agent-prompt"
                value={config.systemPrompt || ''}
                onChange={(e) => updateConfig({ systemPrompt: e.target.value })}
                placeholder="Enter system prompt for the agent"
                rows={5}
              />
            </div>
            <RetryConfig 
              data={config} 
              onChange={(field, value) => updateConfig({ [field]: value })} 
            />
          </div>
        );

      case 'condition':
        return (
          <div className="space-y-4" role="group" aria-label="Condition configuration">
            <div className="space-y-2">
              <Label htmlFor="condition-label">Label</Label>
              <Input
                id="condition-label"
                value={config.label || ''}
                onChange={(e) => updateConfig({ label: e.target.value })}
                placeholder="Condition name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="condition-expression">Condition Expression</Label>
              <Textarea
                id="condition-expression"
                value={config.condition || ''}
                onChange={(e) => updateConfig({ condition: e.target.value })}
                placeholder="e.g., output.confidence > 0.8"
                rows={3}
                aria-describedby="condition-help"
              />
              <div id="condition-help" className="text-xs text-muted-foreground">
                <p className="font-medium mb-1">Available variables:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>input - Input data from previous node</li>
                  <li>output - Output from previous node</li>
                  <li>context - Workflow context variables</li>
                </ul>
              </div>
            </div>
          </div>
        );

      case 'trigger':
        return (
          <div className="space-y-4" role="group" aria-label="Trigger configuration">
            <div className="space-y-2">
              <Label htmlFor="trigger-name">Trigger Name</Label>
              <Input
                id="trigger-name"
                value={config.name || ''}
                onChange={(e) => updateConfig({ name: e.target.value })}
                placeholder="Enter trigger name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="trigger-description">Description</Label>
              <Textarea
                id="trigger-description"
                value={config.description || ''}
                onChange={(e) => updateConfig({ description: e.target.value })}
                placeholder="Describe when this trigger fires"
                rows={3}
              />
            </div>
            
            {config.triggerType === 'database' && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="table-name">Table Name</Label>
                  <Input
                    id="table-name"
                    value={config.tableName || ''}
                    onChange={(e) => updateConfig({ tableName: e.target.value })}
                    placeholder="users"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="event-type">Event Type</Label>
                  <Select
                    value={config.eventType || 'insert'}
                    onValueChange={(value) => updateConfig({ eventType: value })}
                  >
                    <SelectTrigger id="event-type">
                      <SelectValue placeholder="Select event type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="insert">INSERT</SelectItem>
                      <SelectItem value="update">UPDATE</SelectItem>
                      <SelectItem value="delete">DELETE</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
          </div>
        );

      case 'loop':
        return (
          <div className="space-y-4" role="group" aria-label="Loop configuration">
            <div className="space-y-2">
              <Label htmlFor="loop-label">Label</Label>
              <Input
                id="loop-label"
                value={config.label || ''}
                onChange={(e) => updateConfig({ label: e.target.value })}
                placeholder="Loop name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="loop-type">Loop Type</Label>
              <Select
                value={config.loopType || 'forEach'}
                onValueChange={(value) => updateConfig({ loopType: value })}
              >
                <SelectTrigger id="loop-type">
                  <SelectValue placeholder="Select loop type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="forEach">For Each (iterate over array)</SelectItem>
                  <SelectItem value="while">While (condition-based)</SelectItem>
                  <SelectItem value="count">Count (fixed iterations)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {config.loopType === 'count' && (
              <div className="space-y-2">
                <Label htmlFor="iterations">Iterations</Label>
                <Input
                  id="iterations"
                  type="number"
                  value={config.iterations || 1}
                  onChange={(e) => updateConfig({ iterations: parseInt(e.target.value) })}
                  min={1}
                  aria-describedby="iterations-hint"
                />
                <p id="iterations-hint" className="text-xs text-muted-foreground">
                  Number of times to repeat
                </p>
              </div>
            )}
            {config.loopType === 'while' && (
              <div className="space-y-2">
                <Label htmlFor="loop-condition">Condition</Label>
                <Textarea
                  id="loop-condition"
                  value={config.condition || ''}
                  onChange={(e) => updateConfig({ condition: e.target.value })}
                  placeholder="e.g., index < items.length"
                  rows={2}
                />
              </div>
            )}
          </div>
        );

      case 'delay':
        return (
          <div className="space-y-4" role="group" aria-label="Delay configuration">
            <div className="space-y-2">
              <Label htmlFor="delay-label">Label</Label>
              <Input
                id="delay-label"
                value={config.label || ''}
                onChange={(e) => updateConfig({ label: e.target.value })}
                placeholder="Delay"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="duration">Duration</Label>
              <Input
                id="duration"
                type="number"
                value={config.duration || 1}
                onChange={(e) => updateConfig({ duration: parseInt(e.target.value) })}
                min={1}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="unit">Unit</Label>
              <Select
                value={config.unit || 'seconds'}
                onValueChange={(value) => updateConfig({ unit: value })}
              >
                <SelectTrigger id="unit">
                  <SelectValue placeholder="Select time unit" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="seconds">Seconds</SelectItem>
                  <SelectItem value="minutes">Minutes</SelectItem>
                  <SelectItem value="hours">Hours</SelectItem>
                  <SelectItem value="days">Days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case 'parallel':
        return (
          <div className="space-y-4" role="group" aria-label="Parallel configuration">
            <div className="space-y-2">
              <Label htmlFor="parallel-label">Label</Label>
              <Input
                id="parallel-label"
                value={config.label || ''}
                onChange={(e) => updateConfig({ label: e.target.value })}
                placeholder="Parallel execution"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="branches">Number of Branches</Label>
              <Input
                id="branches"
                type="number"
                value={config.branches || 2}
                onChange={(e) => updateConfig({ branches: parseInt(e.target.value) })}
                min={2}
                max={10}
                aria-describedby="branches-hint"
              />
              <p id="branches-hint" className="text-xs text-muted-foreground">
                Execute multiple branches simultaneously (2-10)
              </p>
            </div>
          </div>
        );

      case 'block':
        return (
          <div className="space-y-4" role="group" aria-label="Block configuration">
            <div className="space-y-2">
              <Label htmlFor="block-name">Block Name</Label>
              <Input
                id="block-name"
                value={config.name || ''}
                onChange={(e) => updateConfig({ name: e.target.value })}
                placeholder="Enter block name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="block-description">Description</Label>
              <Textarea
                id="block-description"
                value={config.description || ''}
                onChange={(e) => updateConfig({ description: e.target.value })}
                placeholder="Describe what this block does"
                rows={3}
              />
            </div>
          </div>
        );

      case 'start':
      case 'end':
        return (
          <div className="p-4 rounded-lg bg-muted/50" role="note">
            <p className="text-sm text-muted-foreground">
              {node.type === 'start' 
                ? 'This is the starting point of your workflow. All workflows must have exactly one start node.'
                : 'This is the ending point of your workflow. You can have multiple end nodes for different outcomes.'}
            </p>
          </div>
        );

      default:
        // Try to load dynamic config components
        try {
          if (node.type === 'http_request') {
            const { HttpRequestNodeConfig } = require('./NodeConfigPanels/HttpRequestNodeConfig');
            return <HttpRequestNodeConfig nodeId={node.id} data={config} onChange={(id: string, data: any) => setConfig(data)} />;
          }
          if (node.type === 'switch') {
            const { default: SwitchNodeConfig } = require('./NodeConfigPanels/SwitchNodeConfig');
            return <SwitchNodeConfig data={config} onChange={setConfig} />;
          }
          if (node.type === 'merge') {
            const { default: MergeNodeConfig } = require('./NodeConfigPanels/MergeNodeConfig');
            return <MergeNodeConfig data={config} onChange={setConfig} />;
          }
          if (node.type === 'code') {
            const { default: CodeNodeConfig } = require('./NodeConfigPanels/CodeNodeConfig');
            return <CodeNodeConfig data={config} onChange={setConfig} />;
          }
        } catch {
          // Component not found
        }
        
        return (
          <div className="p-4 rounded-lg bg-muted/50 text-center" role="note">
            <p className="text-sm text-muted-foreground">
              No configuration available for this node type.
            </p>
          </div>
        );
    }
  };

  const nodeTypeColor = nodeTypeColors[node.type || ''] || 'bg-gray-100 text-gray-700';

  return (
    <>
      <div 
        className="w-80 border-l bg-background flex flex-col h-full"
        role="dialog"
        aria-label={`Configure ${config.name || node.type} node`}
        onKeyDown={handleKeyDown}
      >
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5" aria-hidden="true" />
            <h2 className="font-semibold">Node Configuration</h2>
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onClose}
            aria-label="Close configuration panel"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-4">
            {/* Node Type Badge */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className={cn('px-3 py-1 rounded-full text-xs font-medium', nodeTypeColor)}>
                {node.type?.toUpperCase().replace('_', ' ')}
              </span>
              <span className="text-xs text-muted-foreground font-mono">
                ID: {node.id.slice(0, 8)}...
              </span>
            </div>

            <Separator />

            {/* Node Enable/Disable Toggle */}
            {node.type !== 'start' && node.type !== 'end' && (
              <>
                <div 
                  className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                  role="group"
                  aria-label="Node status"
                >
                  <div className="flex items-center gap-2">
                    {config.disabled ? (
                      <EyeOff className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                    ) : (
                      <Eye className="h-4 w-4 text-primary" aria-hidden="true" />
                    )}
                    <div>
                      <Label htmlFor="node-enabled" className="cursor-pointer font-medium">
                        {config.disabled ? 'Node Disabled' : 'Node Enabled'}
                      </Label>
                      <p className="text-xs text-muted-foreground">
                        {config.disabled 
                          ? 'This node will be skipped during execution' 
                          : 'This node will execute normally'}
                      </p>
                    </div>
                  </div>
                  <Switch
                    id="node-enabled"
                    checked={!config.disabled}
                    onCheckedChange={(checked) => {
                      const newConfig = { ...config, disabled: !checked };
                      setConfig(newConfig);
                      onUpdate(node.id, newConfig);
                    }}
                    aria-describedby="node-enabled-description"
                  />
                </div>
                <Separator />
              </>
            )}

            {/* Configuration Fields */}
            {renderConfigFields()}

            <Separator />

            {/* Position Info */}
            <div className="space-y-2">
              <Label className="text-xs text-muted-foreground">Position</Label>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 bg-muted/50 rounded">
                  <span className="text-muted-foreground">X:</span> {Math.round(node.position.x)}
                </div>
                <div className="p-2 bg-muted/50 rounded">
                  <span className="text-muted-foreground">Y:</span> {Math.round(node.position.y)}
                </div>
              </div>
            </div>
          </div>
        </ScrollArea>

        {/* Footer Actions */}
        <div className="p-4 border-t space-y-2">
          {hasUnsavedChanges && (
            <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400 mb-2" role="status">
              <AlertTriangle className="h-3 w-3" aria-hidden="true" />
              <span>You have unsaved changes</span>
            </div>
          )}
          <Button 
            onClick={handleUpdate} 
            className="w-full gap-2"
            disabled={!hasUnsavedChanges}
          >
            <Save className="h-4 w-4" aria-hidden="true" />
            Apply Changes
            <kbd className="ml-auto text-xs opacity-60">Ctrl+S</kbd>
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            className="w-full gap-2"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Delete Node
          </Button>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="Delete Node?"
        description={`This will permanently delete "${config.name || config.label || node.type}" and remove all its connections.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="destructive"
        onConfirm={confirmDelete}
        undoable={true}
        undoDuration={5}
        onUndo={() => {
          // Undo logic would restore the node
          console.log('Undo delete');
        }}
      />
    </>
  );
}
