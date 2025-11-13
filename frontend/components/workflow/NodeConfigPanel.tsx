'use client';

import React, { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import { X, Settings, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { RetryConfig } from './RetryConfig';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

interface NodeConfigPanelProps {
  node: Node | null;
  onClose: () => void;
  onUpdate: (nodeId: string, data: any) => void;
  onDelete: (nodeId: string) => void;
}

export function NodeConfigPanel({ node, onClose, onUpdate, onDelete }: NodeConfigPanelProps) {
  const [config, setConfig] = useState<any>({});

  useEffect(() => {
    if (node) {
      setConfig(node.data || {});
    }
  }, [node]);

  if (!node) return null;

  const handleUpdate = () => {
    onUpdate(node.id, config);
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this node?')) {
      onDelete(node.id);
      onClose();
    }
  };

  const renderConfigFields = () => {
    switch (node.type) {
      case 'agent':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="agent-name">Agent Name</Label>
              <Input
                id="agent-name"
                value={config.name || ''}
                onChange={(e) => setConfig({ ...config, name: e.target.value })}
                placeholder="Enter agent name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="agent-description">Description</Label>
              <Textarea
                id="agent-description"
                value={config.description || ''}
                onChange={(e) => setConfig({ ...config, description: e.target.value })}
                placeholder="Describe what this agent does"
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="agent-prompt">System Prompt</Label>
              <Textarea
                id="agent-prompt"
                value={config.systemPrompt || ''}
                onChange={(e) => setConfig({ ...config, systemPrompt: e.target.value })}
                placeholder="Enter system prompt for the agent"
                rows={5}
              />
            </div>
            <RetryConfig 
              data={config} 
              onChange={(field, value) => setConfig({ ...config, [field]: value })} 
            />
          </div>
        );

      case 'condition':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="condition-label">Label</Label>
              <Input
                id="condition-label"
                value={config.label || ''}
                onChange={(e) => setConfig({ ...config, label: e.target.value })}
                placeholder="Condition name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="condition-expression">Condition Expression</Label>
              <Textarea
                id="condition-expression"
                value={config.condition || ''}
                onChange={(e) => setConfig({ ...config, condition: e.target.value })}
                placeholder="e.g., output.confidence > 0.8"
                rows={3}
              />
            </div>
            <div className="text-xs text-muted-foreground">
              <p className="font-medium mb-1">Available variables:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>input - Input data from previous node</li>
                <li>output - Output from previous node</li>
                <li>context - Workflow context variables</li>
              </ul>
            </div>
          </div>
        );

      case 'block':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="block-name">Block Name</Label>
              <Input
                id="block-name"
                value={config.name || ''}
                onChange={(e) => setConfig({ ...config, name: e.target.value })}
                placeholder="Enter block name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="block-description">Description</Label>
              <Textarea
                id="block-description"
                value={config.description || ''}
                onChange={(e) => setConfig({ ...config, description: e.target.value })}
                placeholder="Describe what this block does"
                rows={3}
              />
            </div>
            {config.inputs && (
              <div className="space-y-2">
                <Label>Input Parameters</Label>
                <div className="text-xs text-muted-foreground">
                  {Object.keys(config.inputs).length > 0 ? (
                    <ul className="list-disc list-inside">
                      {Object.keys(config.inputs).map((key) => (
                        <li key={key}>{key}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No input parameters defined</p>
                  )}
                </div>
              </div>
            )}
          </div>
        );

      case 'trigger':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="trigger-name">Trigger Name</Label>
              <Input
                id="trigger-name"
                value={config.name || ''}
                onChange={(e) => setConfig({ ...config, name: e.target.value })}
                placeholder="Enter trigger name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="trigger-description">Description</Label>
              <Textarea
                id="trigger-description"
                value={config.description || ''}
                onChange={(e) => setConfig({ ...config, description: e.target.value })}
                placeholder="Describe when this trigger fires"
                rows={3}
              />
            </div>
            
            {/* Trigger Type Specific Configuration */}
            {config.triggerType === 'schedule' && (
              <div className="space-y-2">
                <Label htmlFor="cron-expression">Cron Expression</Label>
                <Input
                  id="cron-expression"
                  value={config.cronExpression || ''}
                  onChange={(e) => setConfig({ ...config, cronExpression: e.target.value })}
                  placeholder="0 0 * * * (every day at midnight)"
                />
                <div className="text-xs text-muted-foreground">
                  <p>Examples:</p>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    <li>0 0 * * * - Every day at midnight</li>
                    <li>0 */6 * * * - Every 6 hours</li>
                    <li>0 9 * * 1 - Every Monday at 9 AM</li>
                  </ul>
                </div>
              </div>
            )}
            
            {config.triggerType === 'webhook' && (
              <div className="space-y-2">
                <Label htmlFor="webhook-url">Webhook URL</Label>
                <Input
                  id="webhook-url"
                  value={config.webhookUrl || '/api/webhooks/...'}
                  readOnly
                  className="bg-muted"
                />
                <div className="text-xs text-muted-foreground">
                  This URL will be generated when you save the workflow
                </div>
              </div>
            )}
            
            {config.triggerType === 'email' && (
              <div className="space-y-2">
                <Label htmlFor="email-address">Email Address</Label>
                <Input
                  id="email-address"
                  value={config.emailAddress || ''}
                  onChange={(e) => setConfig({ ...config, emailAddress: e.target.value })}
                  placeholder="workflow@yourdomain.com"
                />
                <div className="text-xs text-muted-foreground">
                  Emails sent to this address will trigger the workflow
                </div>
              </div>
            )}
            
            {config.triggerType === 'database' && (
              <div className="space-y-2">
                <Label htmlFor="table-name">Table Name</Label>
                <Input
                  id="table-name"
                  value={config.tableName || ''}
                  onChange={(e) => setConfig({ ...config, tableName: e.target.value })}
                  placeholder="users"
                />
                <Label htmlFor="event-type">Event Type</Label>
                <select
                  id="event-type"
                  value={config.eventType || 'insert'}
                  onChange={(e) => setConfig({ ...config, eventType: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="insert">INSERT</option>
                  <option value="update">UPDATE</option>
                  <option value="delete">DELETE</option>
                </select>
              </div>
            )}
          </div>
        );

      case 'loop':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="loop-label">Label</Label>
              <Input
                id="loop-label"
                value={config.label || ''}
                onChange={(e) => setConfig({ ...config, label: e.target.value })}
                placeholder="Loop name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="loop-type">Loop Type</Label>
              <select
                id="loop-type"
                value={config.loopType || 'forEach'}
                onChange={(e) => setConfig({ ...config, loopType: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="forEach">For Each (iterate over array)</option>
                <option value="while">While (condition-based)</option>
                <option value="count">Count (fixed iterations)</option>
              </select>
            </div>
            {config.loopType === 'count' && (
              <div className="space-y-2">
                <Label htmlFor="iterations">Iterations</Label>
                <Input
                  id="iterations"
                  type="number"
                  value={config.iterations || 1}
                  onChange={(e) => setConfig({ ...config, iterations: parseInt(e.target.value) })}
                  min="1"
                />
              </div>
            )}
            {config.loopType === 'while' && (
              <div className="space-y-2">
                <Label htmlFor="loop-condition">Condition</Label>
                <Textarea
                  id="loop-condition"
                  value={config.condition || ''}
                  onChange={(e) => setConfig({ ...config, condition: e.target.value })}
                  placeholder="e.g., index < items.length"
                  rows={2}
                />
              </div>
            )}
          </div>
        );

      case 'parallel':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="parallel-label">Label</Label>
              <Input
                id="parallel-label"
                value={config.label || ''}
                onChange={(e) => setConfig({ ...config, label: e.target.value })}
                placeholder="Parallel execution"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="branches">Number of Branches</Label>
              <Input
                id="branches"
                type="number"
                value={config.branches || 2}
                onChange={(e) => setConfig({ ...config, branches: parseInt(e.target.value) })}
                min="2"
                max="10"
              />
            </div>
            <div className="text-xs text-muted-foreground">
              Execute multiple branches simultaneously and wait for all to complete.
            </div>
          </div>
        );

      case 'delay':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="delay-label">Label</Label>
              <Input
                id="delay-label"
                value={config.label || ''}
                onChange={(e) => setConfig({ ...config, label: e.target.value })}
                placeholder="Delay"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="duration">Duration</Label>
              <Input
                id="duration"
                type="number"
                value={config.duration || 1}
                onChange={(e) => setConfig({ ...config, duration: parseInt(e.target.value) })}
                min="1"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="unit">Unit</Label>
              <select
                id="unit"
                value={config.unit || 'seconds'}
                onChange={(e) => setConfig({ ...config, unit: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="seconds">Seconds</option>
                <option value="minutes">Minutes</option>
                <option value="hours">Hours</option>
                <option value="days">Days</option>
              </select>
            </div>
          </div>
        );

      case 'http_request':
        // Import and use the dedicated config component
        const { HttpRequestNodeConfig } = require('./NodeConfigPanels/HttpRequestNodeConfig');
        return (
          <HttpRequestNodeConfig
            nodeId={node.id}
            data={config}
            onChange={(nodeId: string, data: any) => setConfig(data)}
          />
        );

      case 'switch':
        const { default: SwitchNodeConfig } = require('./NodeConfigPanels/SwitchNodeConfig');
        return <SwitchNodeConfig data={config} onChange={setConfig} />;

      case 'merge':
        const { default: MergeNodeConfig } = require('./NodeConfigPanels/MergeNodeConfig');
        return <MergeNodeConfig data={config} onChange={setConfig} />;

      case 'code':
        const { default: CodeNodeConfig } = require('./NodeConfigPanels/CodeNodeConfig');
        return <CodeNodeConfig data={config} onChange={setConfig} />;

      case 'schedule_trigger':
        const { default: ScheduleTriggerConfig } = require('./NodeConfigPanels/ScheduleTriggerConfig');
        return <ScheduleTriggerConfig data={config} onChange={setConfig} />;

      case 'webhook_trigger':
        const { default: WebhookTriggerConfig } = require('./NodeConfigPanels/WebhookTriggerConfig');
        return <WebhookTriggerConfig data={config} onChange={setConfig} />;

      case 'webhook_response':
        const { default: WebhookResponseConfig } = require('./NodeConfigPanels/WebhookResponseConfig');
        return <WebhookResponseConfig data={config} onChange={setConfig} />;

      case 'slack':
        const { default: SlackNodeConfig } = require('./NodeConfigPanels/SlackNodeConfig');
        return <SlackNodeConfig data={config} onChange={setConfig} />;

      case 'discord':
        const { default: DiscordNodeConfig } = require('./NodeConfigPanels/DiscordNodeConfig');
        return <DiscordNodeConfig data={config} onChange={setConfig} />;

      case 'email':
        const { default: EmailNodeConfig } = require('./NodeConfigPanels/EmailNodeConfig');
        return <EmailNodeConfig data={config} onChange={setConfig} />;

      case 'google_drive':
        const { default: GoogleDriveNodeConfig } = require('./NodeConfigPanels/GoogleDriveNodeConfig');
        return <GoogleDriveNodeConfig data={config} onChange={setConfig} />;

      case 's3':
        const { default: S3NodeConfig } = require('./NodeConfigPanels/S3NodeConfig');
        return <S3NodeConfig data={config} onChange={setConfig} />;

      case 'database':
        const { default: DatabaseNodeConfig } = require('./NodeConfigPanels/DatabaseNodeConfig');
        return <DatabaseNodeConfig data={config} onChange={setConfig} />;

      case 'manager_agent':
        const { default: ManagerAgentConfig } = require('./NodeConfigPanels/ManagerAgentConfig');
        return <ManagerAgentConfig data={config} onChange={setConfig} />;

      case 'memory':
        const { default: MemoryNodeConfig } = require('./NodeConfigPanels/MemoryNodeConfig');
        return <MemoryNodeConfig data={config} onChange={setConfig} />;

      case 'consensus':
        const { default: ConsensusNodeConfig } = require('./NodeConfigPanels/ConsensusNodeConfig');
        return <ConsensusNodeConfig data={config} onChange={setConfig} />;

      case 'human_approval':
        const { default: HumanApprovalConfig } = require('./NodeConfigPanels/HumanApprovalConfig');
        return <HumanApprovalConfig data={config} onChange={setConfig} />;

      case 'start':
      case 'end':
        return (
          <div className="space-y-4">
            <div className="text-sm text-muted-foreground">
              {node.type === 'start' 
                ? 'This is the starting point of your workflow. All workflows must have exactly one start node.'
                : 'This is the ending point of your workflow. You can have multiple end nodes for different outcomes.'}
            </div>
          </div>
        );

      default:
        return (
          <div className="text-sm text-muted-foreground">
            No configuration available for this node type.
          </div>
        );
    }
  };

  return (
    <div className="w-80 border-l bg-background flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          <h3 className="font-semibold">Node Configuration</h3>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {/* Node Type Badge */}
          <div className="flex items-center gap-2">
            <div
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium',
                node.type === 'agent' && 'bg-purple-100 text-purple-700',
                node.type === 'block' && 'bg-blue-100 text-blue-700',
                node.type === 'condition' && 'bg-amber-100 text-amber-700',
                node.type === 'trigger' && 'bg-yellow-100 text-yellow-700',
                node.type === 'start' && 'bg-green-100 text-green-700',
                node.type === 'end' && 'bg-red-100 text-red-700',
                node.type === 'loop' && 'bg-purple-100 text-purple-700',
                node.type === 'parallel' && 'bg-cyan-100 text-cyan-700',
                node.type === 'delay' && 'bg-slate-100 text-slate-700',
                node.type === 'try_catch' && 'bg-red-100 text-red-700',
                node.type === 'switch' && 'bg-purple-100 text-purple-700',
                node.type === 'merge' && 'bg-indigo-100 text-indigo-700',
                node.type === 'code' && 'bg-green-100 text-green-700',
                node.type === 'schedule_trigger' && 'bg-purple-100 text-purple-700',
                node.type === 'webhook_trigger' && 'bg-blue-100 text-blue-700',
                node.type === 'webhook_response' && 'bg-purple-100 text-purple-700',
                node.type === 'http_request' && 'bg-orange-100 text-orange-700',
                node.type === 'slack' && 'bg-purple-100 text-purple-700',
                node.type === 'discord' && 'bg-indigo-100 text-indigo-700',
                node.type === 'email' && 'bg-blue-100 text-blue-700',
                node.type === 'google_drive' && 'bg-red-100 text-red-700',
                node.type === 's3' && 'bg-orange-100 text-orange-700',
                node.type === 'database' && 'bg-cyan-100 text-cyan-700',
                node.type === 'manager_agent' && 'bg-yellow-100 text-yellow-700',
                node.type === 'memory' && 'bg-pink-100 text-pink-700',
                node.type === 'consensus' && 'bg-teal-100 text-teal-700',
                node.type === 'human_approval' && 'bg-amber-100 text-amber-700'
              )}
            >
              {node.type?.toUpperCase().replace('_', '-')}
            </div>
            <span className="text-sm text-muted-foreground">ID: {node.id}</span>
          </div>

          <Separator />

          {/* Configuration Fields */}
          {renderConfigFields()}

          <Separator />

          {/* Position Info */}
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">Position</Label>
            <div className="grid grid-cols-2 gap-2">
              <div className="text-xs">
                <span className="text-muted-foreground">X:</span> {Math.round(node.position.x)}
              </div>
              <div className="text-xs">
                <span className="text-muted-foreground">Y:</span> {Math.round(node.position.y)}
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>

      {/* Footer Actions */}
      <div className="p-4 border-t space-y-2">
        <Button onClick={handleUpdate} className="w-full">
          Apply Changes
        </Button>
        <Button
          variant="destructive"
          onClick={handleDelete}
          className="w-full"
        >
          <Trash2 className="h-4 w-4 mr-2" />
          Delete Node
        </Button>
      </div>
    </div>
  );
}
