'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Globe, Copy, Check, Shield, Plus, Trash, Key } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function WebhookTriggerConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    webhook_id: data.webhook_id || `wh_${Date.now()}`,
    path: data.path || '',
    http_method: data.http_method || 'POST',
    // Authentication
    auth_type: data.auth_type || 'none',
    auth_header: data.auth_header || 'Authorization',
    auth_value: data.auth_value || '',
    // Validation
    validate_payload: data.validate_payload || false,
    payload_schema: data.payload_schema || '',
    required_headers: data.required_headers || [],
    // Response
    response_mode: data.response_mode || 'immediate',
    success_response: data.success_response || '{"status": "ok"}',
    // Rate Limiting
    rate_limit_enabled: data.rate_limit_enabled || false,
    rate_limit_requests: data.rate_limit_requests || 100,
    rate_limit_window: data.rate_limit_window || 60,
    // IP Whitelist
    ip_whitelist_enabled: data.ip_whitelist_enabled || false,
    ip_whitelist: data.ip_whitelist || '',
    ...data
  });
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const webhookUrl = typeof window !== 'undefined' 
    ? `${window.location.origin}/api/webhooks/${config.webhook_id}${config.path ? `/${config.path}` : ''}`
    : `/api/webhooks/${config.webhook_id}${config.path ? `/${config.path}` : ''}`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(webhookUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const addRequiredHeader = () => {
    updateConfig('required_headers', [...config.required_headers, { name: '', value: '' }]);
  };

  const updateRequiredHeader = (index: number, field: string, value: string) => {
    const newHeaders = [...config.required_headers];
    newHeaders[index][field] = value;
    updateConfig('required_headers', newHeaders);
  };

  const removeRequiredHeader = (index: number) => {
    updateConfig('required_headers', config.required_headers.filter((_: any, i: number) => i !== index));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-green-100 dark:bg-green-950">
          <Globe className="h-5 w-5 text-green-600 dark:text-green-400" />
        </div>
        <div>
          <h3 className="font-semibold">Webhook Trigger</h3>
          <p className="text-sm text-muted-foreground">Trigger workflow via HTTP webhook</p>
        </div>
        <Badge variant="secondary" className="ml-auto">Popular</Badge>
      </div>

      {/* Webhook URL */}
      <div className="space-y-2">
        <Label>Webhook URL</Label>
        <div className="flex gap-2">
          <Input
            value={webhookUrl}
            readOnly
            className="font-mono text-sm"
          />
          <Button variant="outline" size="icon" onClick={copyToClipboard}>
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Custom Path */}
      <div className="space-y-2">
        <Label>Custom Path (optional)</Label>
        <Input
          placeholder="my-endpoint"
          value={config.path}
          onChange={(e) => updateConfig('path', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Add a custom path segment to the webhook URL
        </p>
      </div>

      {/* HTTP Method */}
      <div className="space-y-2">
        <Label>HTTP Method</Label>
        <Select value={config.http_method} onValueChange={(v) => updateConfig('http_method', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="POST">POST</SelectItem>
            <SelectItem value="GET">GET</SelectItem>
            <SelectItem value="PUT">PUT</SelectItem>
            <SelectItem value="PATCH">PATCH</SelectItem>
            <SelectItem value="DELETE">DELETE</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Authentication Section */}
      <div className="space-y-4 pt-4 border-t">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4" />
          <Label className="text-base font-semibold">Authentication</Label>
        </div>

        <div className="space-y-2">
          <Label>Auth Type</Label>
          <Select value={config.auth_type} onValueChange={(v) => updateConfig('auth_type', v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None (Public)</SelectItem>
              <SelectItem value="api_key">API Key</SelectItem>
              <SelectItem value="bearer">Bearer Token</SelectItem>
              <SelectItem value="basic">Basic Auth</SelectItem>
              <SelectItem value="hmac">HMAC Signature</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {config.auth_type !== 'none' && (
          <>
            <div className="space-y-2">
              <Label>Header Name</Label>
              <Input
                placeholder="Authorization or X-API-Key"
                value={config.auth_header}
                onChange={(e) => updateConfig('auth_header', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label>Expected Value / Secret</Label>
              <Input
                type="password"
                placeholder={config.auth_type === 'hmac' ? 'HMAC Secret' : 'Token or API Key'}
                value={config.auth_value}
                onChange={(e) => updateConfig('auth_value', e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Use environment variable: {'{{env.WEBHOOK_SECRET}}'}
              </p>
            </div>
          </>
        )}
      </div>

      {/* Required Headers */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Key className="h-4 w-4" />
          <Label>Required Headers</Label>
        </div>
        <p className="text-xs text-muted-foreground">
          Headers that must be present in the request
        </p>
        {config.required_headers.map((header: any, index: number) => (
          <div key={index} className="flex gap-2">
            <Input
              placeholder="Header name"
              value={header.name}
              onChange={(e) => updateRequiredHeader(index, 'name', e.target.value)}
              className="flex-1"
            />
            <Input
              placeholder="Expected value (optional)"
              value={header.value}
              onChange={(e) => updateRequiredHeader(index, 'value', e.target.value)}
              className="flex-1"
            />
            <Button variant="ghost" size="icon" onClick={() => removeRequiredHeader(index)}>
              <Trash className="h-4 w-4" />
            </Button>
          </div>
        ))}
        <Button variant="outline" size="sm" onClick={addRequiredHeader} className="w-full">
          <Plus className="h-4 w-4 mr-2" />
          Add Required Header
        </Button>
      </div>

      {/* Payload Validation */}
      <div className="space-y-4 pt-4 border-t">
        <div className="flex items-center justify-between">
          <div>
            <Label>Validate Payload</Label>
            <p className="text-xs text-muted-foreground">Validate incoming JSON against schema</p>
          </div>
          <Switch
            checked={config.validate_payload}
            onCheckedChange={(checked) => updateConfig('validate_payload', checked)}
          />
        </div>

        {config.validate_payload && (
          <div className="space-y-2">
            <Label>JSON Schema</Label>
            <Textarea
              placeholder='{"type": "object", "required": ["name"], "properties": {"name": {"type": "string"}}}'
              value={config.payload_schema}
              onChange={(e) => updateConfig('payload_schema', e.target.value)}
              rows={4}
              className="font-mono text-sm"
            />
          </div>
        )}
      </div>

      {/* Response Mode */}
      <div className="space-y-2">
        <Label>Response Mode</Label>
        <Select value={config.response_mode} onValueChange={(v) => updateConfig('response_mode', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="immediate">Immediate (respond before workflow completes)</SelectItem>
            <SelectItem value="wait">Wait (respond after workflow completes)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Success Response</Label>
        <Textarea
          placeholder='{"status": "ok", "message": "Workflow triggered"}'
          value={config.success_response}
          onChange={(e) => updateConfig('success_response', e.target.value)}
          rows={2}
          className="font-mono text-sm"
        />
      </div>

      {/* Rate Limiting */}
      <div className="space-y-4 pt-4 border-t">
        <div className="flex items-center justify-between">
          <div>
            <Label>Rate Limiting</Label>
            <p className="text-xs text-muted-foreground">Limit incoming requests</p>
          </div>
          <Switch
            checked={config.rate_limit_enabled}
            onCheckedChange={(checked) => updateConfig('rate_limit_enabled', checked)}
          />
        </div>

        {config.rate_limit_enabled && (
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Max Requests</Label>
              <Input
                type="number"
                min="1"
                value={config.rate_limit_requests}
                onChange={(e) => updateConfig('rate_limit_requests', parseInt(e.target.value) || 100)}
              />
            </div>
            <div className="space-y-2">
              <Label>Time Window (seconds)</Label>
              <Input
                type="number"
                min="1"
                value={config.rate_limit_window}
                onChange={(e) => updateConfig('rate_limit_window', parseInt(e.target.value) || 60)}
              />
            </div>
          </div>
        )}
      </div>

      {/* IP Whitelist */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>IP Whitelist</Label>
            <p className="text-xs text-muted-foreground">Only allow specific IPs</p>
          </div>
          <Switch
            checked={config.ip_whitelist_enabled}
            onCheckedChange={(checked) => updateConfig('ip_whitelist_enabled', checked)}
          />
        </div>

        {config.ip_whitelist_enabled && (
          <div className="space-y-2">
            <Label>Allowed IPs</Label>
            <Textarea
              placeholder="192.168.1.1&#10;10.0.0.0/8&#10;2001:db8::/32"
              value={config.ip_whitelist}
              onChange={(e) => updateConfig('ip_whitelist', e.target.value)}
              rows={3}
              className="font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground">
              One IP or CIDR range per line
            </p>
          </div>
        )}
      </div>

      {/* Output Variables */}
      <div className="p-3 bg-muted rounded-lg space-y-2">
        <p className="text-xs font-medium">Available Output Variables:</p>
        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
          <div><Badge variant="outline">{'{{webhook.body}}'}</Badge></div>
          <div><Badge variant="outline">{'{{webhook.headers}}'}</Badge></div>
          <div><Badge variant="outline">{'{{webhook.query}}'}</Badge></div>
          <div><Badge variant="outline">{'{{webhook.method}}'}</Badge></div>
          <div><Badge variant="outline">{'{{webhook.path}}'}</Badge></div>
          <div><Badge variant="outline">{'{{webhook.ip}}'}</Badge></div>
        </div>
      </div>

      {/* Example Request */}
      <div className="space-y-2">
        <Label>Example Request</Label>
        <pre className="p-3 bg-muted rounded-lg text-xs font-mono overflow-x-auto whitespace-pre-wrap">
{`curl -X ${config.http_method} "${webhookUrl}" \\
  -H "Content-Type: application/json" \\${config.auth_type !== 'none' ? `
  -H "${config.auth_header}: ${config.auth_type === 'bearer' ? 'Bearer ' : ''}YOUR_TOKEN" \\` : ''}
  -d '{"message": "Hello!"}'`}
        </pre>
      </div>
    </div>
  );
}
