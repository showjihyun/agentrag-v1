'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Plus, Trash2 } from 'lucide-react';

interface HumanApprovalConfigProps {
  data: {
    approvers?: string[];
    requireAll?: boolean;
    timeout?: number;
    message?: string;
    notificationMethod?: 'email' | 'slack' | 'webhook';
    autoApproveAfterTimeout?: boolean;
  };
  onChange: (data: any) => void;
}

export default function HumanApprovalConfig({ data, onChange }: HumanApprovalConfigProps) {
  const [approvers, setApprovers] = useState<string[]>(data.approvers || ['']);
  const [requireAll, setRequireAll] = useState(data.requireAll !== false);
  const [timeout, setTimeout] = useState(data.timeout || 24);
  const [message, setMessage] = useState(data.message || '');
  const [notificationMethod, setNotificationMethod] = useState<'email' | 'slack' | 'webhook'>(
    data.notificationMethod || 'email'
  );
  const [autoApproveAfterTimeout, setAutoApproveAfterTimeout] = useState(
    data.autoApproveAfterTimeout || false
  );

  const handleApproverChange = (index: number, value: string) => {
    const newApprovers = [...approvers];
    newApprovers[index] = value;
    setApprovers(newApprovers);
    onChange({ ...data, approvers: newApprovers.filter((a) => a.trim()) });
  };

  const addApprover = () => {
    const newApprovers = [...approvers, ''];
    setApprovers(newApprovers);
  };

  const removeApprover = (index: number) => {
    const newApprovers = approvers.filter((_, i) => i !== index);
    setApprovers(newApprovers);
    onChange({ ...data, approvers: newApprovers.filter((a) => a.trim()) });
  };

  const handleRequireAllChange = (value: boolean) => {
    setRequireAll(value);
    onChange({ ...data, requireAll: value });
  };

  const handleTimeoutChange = (value: string) => {
    const num = parseInt(value) || 24;
    setTimeout(num);
    onChange({ ...data, timeout: num });
  };

  const handleMessageChange = (value: string) => {
    setMessage(value);
    onChange({ ...data, message: value });
  };

  const handleNotificationMethodChange = (value: 'email' | 'slack' | 'webhook') => {
    setNotificationMethod(value);
    onChange({ ...data, notificationMethod: value });
  };

  const handleAutoApproveChange = (value: boolean) => {
    setAutoApproveAfterTimeout(value);
    onChange({ ...data, autoApproveAfterTimeout: value });
  };

  const MESSAGE_TEMPLATES = [
    'Please review and approve: {{$json.title}}',
    'Approval required for {{$workflow.name}}',
    'New request pending your approval',
    'Action needed: {{$json.action}}',
  ];

  return (
    <div className="space-y-4">
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
        <p className="text-xs text-amber-800 mb-2">
          <strong>Human-in-the-Loop:</strong>
        </p>
        <p className="text-xs text-amber-700">
          Workflow execution pauses until a human approver reviews and approves/rejects the request.
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <Label>Approvers</Label>
          <Button onClick={addApprover} size="sm" variant="outline">
            <Plus className="w-4 h-4 mr-1" />
            Add Approver
          </Button>
        </div>
        <div className="space-y-2">
          {approvers.map((approver, index) => (
            <div key={index} className="flex gap-2">
              <Input
                value={approver}
                onChange={(e) => handleApproverChange(index, e.target.value)}
                placeholder="email@example.com or user_id"
                className="flex-1"
              />
              {approvers.length > 1 && (
                <Button
                  onClick={() => removeApprover(index)}
                  size="sm"
                  variant="ghost"
                  className="px-2"
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div>
        <Label>Approval Mode</Label>
        <div className="flex gap-2 mt-2">
          <button
            onClick={() => handleRequireAllChange(false)}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              !requireAll
                ? 'bg-amber-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Any Approver
          </button>
          <button
            onClick={() => handleRequireAllChange(true)}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              requireAll
                ? 'bg-amber-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Approvers
          </button>
        </div>
      </div>

      <div>
        <Label>Timeout</Label>
        <div className="flex gap-2 items-center">
          <Input
            type="number"
            min="1"
            value={timeout}
            onChange={(e) => handleTimeoutChange(e.target.value)}
            className="w-24"
          />
          <span className="text-sm text-gray-600">hours</span>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          How long to wait before timing out
        </p>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="autoApprove"
          checked={autoApproveAfterTimeout}
          onChange={(e) => handleAutoApproveChange(e.target.checked)}
          className="rounded"
        />
        <Label htmlFor="autoApprove" className="cursor-pointer">
          Auto-approve after timeout
        </Label>
      </div>

      <div>
        <Label>Notification Method</Label>
        <div className="grid grid-cols-3 gap-2 mt-2">
          {(['email', 'slack', 'webhook'] as const).map((method) => (
            <button
              key={method}
              onClick={() => handleNotificationMethodChange(method)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                notificationMethod === method
                  ? 'bg-amber-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {method}
            </button>
          ))}
        </div>
      </div>

      <div>
        <Label>Approval Message</Label>
        <textarea
          value={message}
          onChange={(e) => handleMessageChange(e.target.value)}
          className="w-full h-24 p-3 border rounded-lg text-sm resize-none"
          placeholder="Message to show to approvers..."
        />
        <div className="flex gap-1 mt-2 flex-wrap">
          {MESSAGE_TEMPLATES.map((template, idx) => (
            <button
              key={idx}
              onClick={() => handleMessageChange(template)}
              className="px-2 py-1 text-xs rounded border hover:bg-gray-50"
            >
              Template {idx + 1}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800 font-medium mb-2">
          How it works:
        </p>
        <ul className="text-xs text-blue-700 space-y-1 ml-4 list-disc">
          <li>Workflow pauses at this node</li>
          <li>Notification sent to approvers</li>
          <li>Approvers review via approval UI</li>
          <li>On approval: continues to "approved" output</li>
          <li>On rejection: continues to "rejected" output</li>
          <li>On timeout: follows configured behavior</li>
        </ul>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <p className="text-xs text-green-800 font-medium mb-2">
          Use Cases:
        </p>
        <ul className="text-xs text-green-700 space-y-1 ml-4 list-disc">
          <li>Financial transactions above threshold</li>
          <li>Content moderation and publishing</li>
          <li>User account changes</li>
          <li>Data deletion requests</li>
          <li>Critical system operations</li>
        </ul>
      </div>
    </div>
  );
}
