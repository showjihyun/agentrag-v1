'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { UserCheck, Plus, Trash } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function HumanApprovalConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    title: data.title || 'Approval Required',
    description: data.description || '',
    approval_type: data.approval_type || 'single',
    approvers: data.approvers || [],
    timeout: data.timeout || 0,
    timeout_action: data.timeout_action || 'reject',
    require_comment: data.require_comment || false,
    show_data: data.show_data !== false,
    data_fields: data.data_fields || '',
    approval_options: data.approval_options || [
      { value: 'approve', label: 'Approve', color: 'green' },
      { value: 'reject', label: 'Reject', color: 'red' }
    ],
    notification_method: data.notification_method || 'email',
    reminder_interval: data.reminder_interval || 0,
    escalation_after: data.escalation_after || 0,
    escalation_to: data.escalation_to || '',
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const addApprover = () => {
    updateConfig('approvers', [...config.approvers, { email: '', name: '' }]);
  };

  const updateApprover = (index: number, field: string, value: string) => {
    const newApprovers = [...config.approvers];
    newApprovers[index][field] = value;
    updateConfig('approvers', newApprovers);
  };

  const removeApprover = (index: number) => {
    updateConfig('approvers', config.approvers.filter((_: any, i: number) => i !== index));
  };

  const addOption = () => {
    updateConfig('approval_options', [
      ...config.approval_options,
      { value: '', label: '', color: 'gray' }
    ]);
  };

  const updateOption = (index: number, field: string, value: string) => {
    const newOptions = [...config.approval_options];
    newOptions[index][field] = value;
    updateConfig('approval_options', newOptions);
  };

  const removeOption = (index: number) => {
    updateConfig('approval_options', config.approval_options.filter((_: any, i: number) => i !== index));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-950">
          <UserCheck className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
        </div>
        <div>
          <h3 className="font-semibold">Human Approval</h3>
          <p className="text-sm text-muted-foreground">Wait for human decision</p>
        </div>
      </div>

      {/* Title & Description */}
      <div className="space-y-2">
        <Label>Approval Title</Label>
        <Input
          placeholder="Review and approve this request"
          value={config.title}
          onChange={(e) => updateConfig('title', e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label>Description</Label>
        <Textarea
          placeholder="Please review the following data and make a decision..."
          value={config.description}
          onChange={(e) => updateConfig('description', e.target.value)}
          rows={3}
        />
        <p className="text-xs text-muted-foreground">
          Use {'{{variables}}'} to include dynamic content
        </p>
      </div>

      {/* Approval Type */}
      <div className="space-y-2">
        <Label>Approval Type</Label>
        <Select value={config.approval_type} onValueChange={(v) => updateConfig('approval_type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="single">Single Approver (any one)</SelectItem>
            <SelectItem value="all">All Approvers Required</SelectItem>
            <SelectItem value="majority">Majority Vote</SelectItem>
            <SelectItem value="sequential">Sequential (in order)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Approvers */}
      <div className="space-y-3">
        <Label>Approvers</Label>
        {config.approvers.map((approver: any, index: number) => (
          <div key={index} className="flex gap-2">
            <Input
              placeholder="Email"
              value={approver.email}
              onChange={(e) => updateApprover(index, 'email', e.target.value)}
              className="flex-1"
            />
            <Input
              placeholder="Name (optional)"
              value={approver.name}
              onChange={(e) => updateApprover(index, 'name', e.target.value)}
              className="flex-1"
            />
            <Button variant="ghost" size="icon" onClick={() => removeApprover(index)}>
              <Trash className="h-4 w-4" />
            </Button>
          </div>
        ))}
        <Button variant="outline" size="sm" onClick={addApprover} className="w-full">
          <Plus className="h-4 w-4 mr-2" />
          Add Approver
        </Button>
        <p className="text-xs text-muted-foreground">
          Leave empty to use workflow owner as approver
        </p>
      </div>

      {/* Approval Options */}
      <div className="space-y-3">
        <Label>Approval Options</Label>
        {config.approval_options.map((option: any, index: number) => (
          <div key={index} className="flex gap-2">
            <Input
              placeholder="Value"
              value={option.value}
              onChange={(e) => updateOption(index, 'value', e.target.value)}
              className="w-24"
            />
            <Input
              placeholder="Label"
              value={option.label}
              onChange={(e) => updateOption(index, 'label', e.target.value)}
              className="flex-1"
            />
            <Select
              value={option.color}
              onValueChange={(v) => updateOption(index, 'color', v)}
            >
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="green">Green</SelectItem>
                <SelectItem value="red">Red</SelectItem>
                <SelectItem value="yellow">Yellow</SelectItem>
                <SelectItem value="blue">Blue</SelectItem>
                <SelectItem value="gray">Gray</SelectItem>
              </SelectContent>
            </Select>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => removeOption(index)}
              disabled={config.approval_options.length <= 2}
            >
              <Trash className="h-4 w-4" />
            </Button>
          </div>
        ))}
        <Button variant="outline" size="sm" onClick={addOption} className="w-full">
          <Plus className="h-4 w-4 mr-2" />
          Add Option
        </Button>
      </div>

      {/* Timeout */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Timeout (hours, 0 = no timeout)</Label>
          <Input
            type="number"
            min="0"
            value={config.timeout}
            onChange={(e) => updateConfig('timeout', parseInt(e.target.value) || 0)}
          />
        </div>
        <div className="space-y-2">
          <Label>On Timeout</Label>
          <Select value={config.timeout_action} onValueChange={(v) => updateConfig('timeout_action', v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="reject">Auto Reject</SelectItem>
              <SelectItem value="approve">Auto Approve</SelectItem>
              <SelectItem value="escalate">Escalate</SelectItem>
              <SelectItem value="fail">Fail Workflow</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Notification */}
      <div className="space-y-2">
        <Label>Notification Method</Label>
        <Select value={config.notification_method} onValueChange={(v) => updateConfig('notification_method', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="email">Email</SelectItem>
            <SelectItem value="slack">Slack</SelectItem>
            <SelectItem value="both">Email + Slack</SelectItem>
            <SelectItem value="none">None (UI only)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Reminder & Escalation */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Reminder Interval (hours)</Label>
          <Input
            type="number"
            min="0"
            value={config.reminder_interval}
            onChange={(e) => updateConfig('reminder_interval', parseInt(e.target.value) || 0)}
          />
        </div>
        <div className="space-y-2">
          <Label>Escalate After (hours)</Label>
          <Input
            type="number"
            min="0"
            value={config.escalation_after}
            onChange={(e) => updateConfig('escalation_after', parseInt(e.target.value) || 0)}
          />
        </div>
      </div>

      {config.escalation_after > 0 && (
        <div className="space-y-2">
          <Label>Escalate To (email)</Label>
          <Input
            placeholder="manager@example.com"
            value={config.escalation_to}
            onChange={(e) => updateConfig('escalation_to', e.target.value)}
          />
        </div>
      )}

      {/* Options */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>Require Comment</Label>
            <p className="text-xs text-muted-foreground">Approver must provide a comment</p>
          </div>
          <Switch
            checked={config.require_comment}
            onCheckedChange={(checked) => updateConfig('require_comment', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Show Data to Approver</Label>
            <p className="text-xs text-muted-foreground">Display workflow data in approval request</p>
          </div>
          <Switch
            checked={config.show_data}
            onCheckedChange={(checked) => updateConfig('show_data', checked)}
          />
        </div>

        {config.show_data && (
          <div className="space-y-2">
            <Label>Data Fields to Show</Label>
            <Input
              placeholder="field1, field2, nested.field (empty = all)"
              value={config.data_fields}
              onChange={(e) => updateConfig('data_fields', e.target.value)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
