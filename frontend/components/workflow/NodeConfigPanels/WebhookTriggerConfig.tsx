'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Copy, RefreshCw } from 'lucide-react';

interface WebhookTriggerConfigProps {
  data: {
    webhookId?: string;
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    authentication?: 'none' | 'header' | 'query';
    authKey?: string;
  };
  onChange: (data: any) => void;
}

export default function WebhookTriggerConfig({ data, onChange }: WebhookTriggerConfigProps) {
  const [webhookId, setWebhookId] = useState(
    data.webhookId || `wh_${Math.random().toString(36).substr(2, 9)}`
  );
  const [method, setMethod] = useState<'GET' | 'POST' | 'PUT' | 'DELETE'>(
    data.method || 'POST'
  );
  const [authentication, setAuthentication] = useState<'none' | 'header' | 'query'>(
    data.authentication || 'none'
  );
  const [authKey, setAuthKey] = useState(data.authKey || '');

  const webhookUrl = `${typeof window !== 'undefined' ? window.location.origin : ''}/api/webhooks/${webhookId}`;

  const handleWebhookIdChange = (value: string) => {
    setWebhookId(value);
    onChange({ ...data, webhookId: value });
  };

  const handleMethodChange = (value: 'GET' | 'POST' | 'PUT' | 'DELETE') => {
    setMethod(value);
    onChange({ ...data, method: value });
  };

  const handleAuthenticationChange = (value: 'none' | 'header' | 'query') => {
    setAuthentication(value);
    onChange({ ...data, authentication: value });
  };

  const handleAuthKeyChange = (value: string) => {
    setAuthKey(value);
    onChange({ ...data, authKey: value });
  };

  const generateNewId = () => {
    const newId = `wh_${Math.random().toString(36).substr(2, 9)}`;
    setWebhookId(newId);
    onChange({ ...data, webhookId: newId });
  };

  const generateAuthKey = () => {
    const newKey = `sk_${Math.random().toString(36).substr(2, 16)}`;
    setAuthKey(newKey);
    onChange({ ...data, authKey: newKey });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-4">
      <div>
        <Label>Webhook URL</Label>
        <div className="flex gap-2 mt-2">
          <Input
            value={webhookUrl}
            readOnly
            className="font-mono text-sm flex-1"
          />
          <Button
            onClick={() => copyToClipboard(webhookUrl)}
            size="sm"
            variant="outline"
          >
            <Copy className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div>
        <Label>Webhook ID</Label>
        <div className="flex gap-2 mt-2">
          <Input
            value={webhookId}
            onChange={(e) => handleWebhookIdChange(e.target.value)}
            className="font-mono text-sm flex-1"
          />
          <Button onClick={generateNewId} size="sm" variant="outline">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Unique identifier for this webhook
        </p>
      </div>

      <div>
        <Label>HTTP Method</Label>
        <div className="flex gap-2 mt-2">
          {(['GET', 'POST', 'PUT', 'DELETE'] as const).map((m) => (
            <button
              key={m}
              onClick={() => handleMethodChange(m)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                method === m
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      <div>
        <Label>Authentication</Label>
        <div className="space-y-2 mt-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="auth"
              value="none"
              checked={authentication === 'none'}
              onChange={() => handleAuthenticationChange('none')}
            />
            <div>
              <div className="font-medium text-sm">None</div>
              <div className="text-xs text-gray-500">No authentication required</div>
            </div>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="auth"
              value="header"
              checked={authentication === 'header'}
              onChange={() => handleAuthenticationChange('header')}
            />
            <div>
              <div className="font-medium text-sm">Header Authentication</div>
              <div className="text-xs text-gray-500">
                Require X-Webhook-Key header
              </div>
            </div>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="auth"
              value="query"
              checked={authentication === 'query'}
              onChange={() => handleAuthenticationChange('query')}
            />
            <div>
              <div className="font-medium text-sm">Query Parameter</div>
              <div className="text-xs text-gray-500">Require ?key= parameter</div>
            </div>
          </label>
        </div>
      </div>

      {authentication !== 'none' && (
        <div>
          <Label>Authentication Key</Label>
          <div className="flex gap-2 mt-2">
            <Input
              value={authKey}
              onChange={(e) => handleAuthKeyChange(e.target.value)}
              placeholder="Enter or generate key"
              className="font-mono text-sm flex-1"
              type="password"
            />
            <Button onClick={generateAuthKey} size="sm" variant="outline">
              Generate
            </Button>
            <Button
              onClick={() => copyToClipboard(authKey)}
              size="sm"
              variant="outline"
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <p className="text-xs text-green-800 font-medium mb-2">
          Example cURL Request:
        </p>
        <pre className="text-xs text-green-700 font-mono bg-green-100 p-2 rounded overflow-x-auto">
          {`curl -X ${method} \\
  ${webhookUrl}${authentication === 'query' && authKey ? `?key=${authKey}` : ''} \\${
            authentication === 'header' && authKey
              ? `\n  -H "X-Webhook-Key: ${authKey}" \\`
              : ''
          }${
            method !== 'GET'
              ? `\n  -H "Content-Type: application/json" \\\n  -d '{"data": "value"}'`
              : ''
          }`}
        </pre>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800">
          <strong>Note:</strong> The webhook will receive the request body as input
          data and can be accessed in subsequent nodes using{' '}
          <code className="bg-blue-100 px-1 rounded">{'{{$json}}'}</code>
        </p>
      </div>
    </div>
  );
}
