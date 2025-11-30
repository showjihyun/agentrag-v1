'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { ShieldAlert, Plus, Trash } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function TryCatchConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    retry_count: data.retry_count || 0,
    retry_delay: data.retry_delay || 1000,
    retry_backoff: data.retry_backoff || 'fixed',
    catch_errors: data.catch_errors || ['all'],
    error_output: data.error_output || 'error',
    continue_on_error: data.continue_on_error || false,
    fallback_value: data.fallback_value || '',
    log_errors: data.log_errors !== false,
    notify_on_error: data.notify_on_error || false,
    notification_channel: data.notification_channel || '',
    custom_error_handlers: data.custom_error_handlers || [],
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const addErrorHandler = () => {
    updateConfig('custom_error_handlers', [
      ...config.custom_error_handlers,
      { error_type: '', action: 'continue', value: '' }
    ]);
  };

  const updateErrorHandler = (index: number, field: string, value: string) => {
    const newHandlers = [...config.custom_error_handlers];
    newHandlers[index][field] = value;
    updateConfig('custom_error_handlers', newHandlers);
  };

  const removeErrorHandler = (index: number) => {
    updateConfig('custom_error_handlers', 
      config.custom_error_handlers.filter((_: any, i: number) => i !== index)
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-red-100 dark:bg-red-950">
          <ShieldAlert className="h-5 w-5 text-red-600 dark:text-red-400" />
        </div>
        <div>
          <h3 className="font-semibold">Try/Catch</h3>
          <p className="text-sm text-muted-foreground">Error handling and recovery</p>
        </div>
      </div>

      {/* Retry Settings */}
      <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
        <h4 className="font-medium text-sm">Retry Settings</h4>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Retry Count</Label>
            <Input
              type="number"
              min="0"
              max="10"
              value={config.retry_count}
              onChange={(e) => updateConfig('retry_count', parseInt(e.target.value) || 0)}
            />
          </div>
          <div className="space-y-2">
            <Label>Retry Delay (ms)</Label>
            <Input
              type="number"
              min="0"
              step="100"
              value={config.retry_delay}
              onChange={(e) => updateConfig('retry_delay', parseInt(e.target.value) || 1000)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label>Backoff Strategy</Label>
          <Select value={config.retry_backoff} onValueChange={(v) => updateConfig('retry_backoff', v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="fixed">Fixed Delay</SelectItem>
              <SelectItem value="linear">Linear (delay * attempt)</SelectItem>
              <SelectItem value="exponential">Exponential (delay * 2^attempt)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Error Types to Catch */}
      <div className="space-y-2">
        <Label>Catch Error Types</Label>
        <Select 
          value={config.catch_errors[0] || 'all'} 
          onValueChange={(v) => updateConfig('catch_errors', [v])}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Errors</SelectItem>
            <SelectItem value="timeout">Timeout Errors</SelectItem>
            <SelectItem value="network">Network Errors</SelectItem>
            <SelectItem value="validation">Validation Errors</SelectItem>
            <SelectItem value="auth">Authentication Errors</SelectItem>
            <SelectItem value="rate_limit">Rate Limit Errors</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Error Output */}
      <div className="space-y-2">
        <Label>Error Output Name</Label>
        <Input
          placeholder="error"
          value={config.error_output}
          onChange={(e) => updateConfig('error_output', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Variable name to store error details (accessible as {'{{error}}'})
        </p>
      </div>

      {/* Fallback Value */}
      <div className="space-y-2">
        <Label>Fallback Value (on error)</Label>
        <Textarea
          placeholder='{"status": "failed", "data": null}'
          value={config.fallback_value}
          onChange={(e) => updateConfig('fallback_value', e.target.value)}
          rows={3}
          className="font-mono text-sm"
        />
      </div>

      {/* Custom Error Handlers */}
      <div className="space-y-3">
        <Label>Custom Error Handlers</Label>
        {config.custom_error_handlers.map((handler: any, index: number) => (
          <div key={index} className="p-3 border rounded-lg bg-muted/30 space-y-2">
            <div className="flex gap-2">
              <Input
                placeholder="Error type or message pattern"
                value={handler.error_type}
                onChange={(e) => updateErrorHandler(index, 'error_type', e.target.value)}
                className="flex-1"
              />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => removeErrorHandler(index)}
              >
                <Trash className="h-4 w-4" />
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Select
                value={handler.action}
                onValueChange={(v) => updateErrorHandler(index, 'action', v)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="continue">Continue</SelectItem>
                  <SelectItem value="retry">Retry</SelectItem>
                  <SelectItem value="skip">Skip</SelectItem>
                  <SelectItem value="fail">Fail</SelectItem>
                  <SelectItem value="goto">Go to Node</SelectItem>
                </SelectContent>
              </Select>
              <Input
                placeholder="Value or node ID"
                value={handler.value}
                onChange={(e) => updateErrorHandler(index, 'value', e.target.value)}
              />
            </div>
          </div>
        ))}
        <Button variant="outline" size="sm" onClick={addErrorHandler} className="w-full">
          <Plus className="h-4 w-4 mr-2" />
          Add Error Handler
        </Button>
      </div>

      {/* Options */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>Continue on Error</Label>
            <p className="text-xs text-muted-foreground">Continue workflow even if error occurs</p>
          </div>
          <Switch
            checked={config.continue_on_error}
            onCheckedChange={(checked) => updateConfig('continue_on_error', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Log Errors</Label>
            <p className="text-xs text-muted-foreground">Log error details for debugging</p>
          </div>
          <Switch
            checked={config.log_errors}
            onCheckedChange={(checked) => updateConfig('log_errors', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Notify on Error</Label>
            <p className="text-xs text-muted-foreground">Send notification when error occurs</p>
          </div>
          <Switch
            checked={config.notify_on_error}
            onCheckedChange={(checked) => updateConfig('notify_on_error', checked)}
          />
        </div>

        {config.notify_on_error && (
          <div className="space-y-2">
            <Label>Notification Channel</Label>
            <Select 
              value={config.notification_channel} 
              onValueChange={(v) => updateConfig('notification_channel', v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select channel" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="email">Email</SelectItem>
                <SelectItem value="slack">Slack</SelectItem>
                <SelectItem value="webhook">Webhook</SelectItem>
              </SelectContent>
            </Select>
          </div>
        )}
      </div>
    </div>
  );
}
