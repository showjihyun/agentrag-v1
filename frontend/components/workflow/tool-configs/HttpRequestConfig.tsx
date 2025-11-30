'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Globe, Plus, Trash, TestTube, Key, Settings, Shield } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'];

const CONTENT_TYPES = [
  'application/json',
  'application/x-www-form-urlencoded',
  'multipart/form-data',
  'text/plain',
  'text/html',
  'application/xml',
];

const AUTH_TYPES = [
  { value: 'none', label: 'No Auth' },
  { value: 'bearer', label: 'Bearer Token' },
  { value: 'basic', label: 'Basic Auth' },
  { value: 'api_key', label: 'API Key' },
];

export default function HttpRequestConfig({ data, onChange, onTest }: ToolConfigProps) {
  const [config, setConfig] = useState({
    method: data.method || 'GET',
    url: data.url || '',
    headers: data.headers || [],
    query_params: data.query_params || [],
    body: data.body || '',
    body_type: data.body_type || 'application/json',
    timeout: data.timeout || 30,
    follow_redirects: data.follow_redirects !== false,
    // Authentication
    auth_type: data.auth_type || 'none',
    auth_token: data.auth_token || '',
    auth_username: data.auth_username || '',
    auth_password: data.auth_password || '',
    api_key_name: data.api_key_name || 'X-API-Key',
    api_key_value: data.api_key_value || '',
    api_key_location: data.api_key_location || 'header',
    // Advanced options
    retry_count: data.retry_count || 0,
    retry_delay: data.retry_delay || 1000,
    verify_ssl: data.verify_ssl !== false,
    response_type: data.response_type || 'json',
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const addHeader = () => {
    updateConfig('headers', [...config.headers, { key: '', value: '' }]);
  };

  const updateHeader = (index: number, field: 'key' | 'value', value: string) => {
    const newHeaders = [...config.headers];
    newHeaders[index][field] = value;
    updateConfig('headers', newHeaders);
  };

  const removeHeader = (index: number) => {
    updateConfig('headers', config.headers.filter((_: any, i: number) => i !== index));
  };

  const addQueryParam = () => {
    updateConfig('query_params', [...config.query_params, { key: '', value: '' }]);
  };

  const updateQueryParam = (index: number, field: 'key' | 'value', value: string) => {
    const newParams = [...config.query_params];
    newParams[index][field] = value;
    updateConfig('query_params', newParams);
  };

  const removeQueryParam = (index: number) => {
    updateConfig('query_params', config.query_params.filter((_: any, i: number) => i !== index));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-950">
          <Globe className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h3 className="font-semibold">HTTP Request</h3>
          <p className="text-sm text-muted-foreground">Make API calls to any endpoint</p>
        </div>
        <Badge variant="secondary" className="ml-auto">Popular</Badge>
      </div>

      {/* Method & URL */}
      <div className="space-y-2">
        <Label>Request</Label>
        <div className="flex gap-2">
          <Select value={config.method} onValueChange={(v) => updateConfig('method', v)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {HTTP_METHODS.map(method => (
                <SelectItem key={method} value={method}>
                  <Badge variant={method === 'GET' ? 'default' : method === 'POST' ? 'secondary' : 'outline'}>
                    {method}
                  </Badge>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            placeholder="https://api.example.com/endpoint"
            value={config.url}
            onChange={(e) => updateConfig('url', e.target.value)}
            className="flex-1 font-mono text-sm"
          />
        </div>
        <p className="text-xs text-muted-foreground">
          Use <code className="px-1 py-0.5 bg-muted rounded">{'{{variables}}'}</code> for dynamic values
        </p>
      </div>

      {/* Tabs for Headers, Query, Body, Auth, Settings */}
      <Tabs defaultValue="headers" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="headers">
            Headers ({config.headers.length})
          </TabsTrigger>
          <TabsTrigger value="query">
            Query ({config.query_params.length})
          </TabsTrigger>
          <TabsTrigger value="body">
            Body
          </TabsTrigger>
          <TabsTrigger value="auth">
            <Shield className="h-3 w-3 mr-1" />
            Auth
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="h-3 w-3 mr-1" />
            Settings
          </TabsTrigger>
        </TabsList>

        {/* Headers Tab */}
        <TabsContent value="headers" className="space-y-3">
          {config.headers.map((header: any, index: number) => (
            <div key={index} className="flex gap-2">
              <Input
                placeholder="Header name"
                value={header.key}
                onChange={(e) => updateHeader(index, 'key', e.target.value)}
                className="flex-1"
              />
              <Input
                placeholder="Value"
                value={header.value}
                onChange={(e) => updateHeader(index, 'value', e.target.value)}
                className="flex-1"
              />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => removeHeader(index)}
              >
                <Trash className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button
            variant="outline"
            size="sm"
            onClick={addHeader}
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Header
          </Button>
        </TabsContent>

        {/* Query Params Tab */}
        <TabsContent value="query" className="space-y-3">
          {config.query_params.map((param: any, index: number) => (
            <div key={index} className="flex gap-2">
              <Input
                placeholder="Parameter name"
                value={param.key}
                onChange={(e) => updateQueryParam(index, 'key', e.target.value)}
                className="flex-1"
              />
              <Input
                placeholder="Value"
                value={param.value}
                onChange={(e) => updateQueryParam(index, 'value', e.target.value)}
                className="flex-1"
              />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => removeQueryParam(index)}
              >
                <Trash className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button
            variant="outline"
            size="sm"
            onClick={addQueryParam}
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Query Parameter
          </Button>
        </TabsContent>

        {/* Body Tab */}
        <TabsContent value="body" className="space-y-3">
          {(config.method === 'POST' || config.method === 'PUT' || config.method === 'PATCH') ? (
            <>
              <div className="space-y-2">
                <Label>Content Type</Label>
                <Select value={config.body_type} onValueChange={(v) => updateConfig('body_type', v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CONTENT_TYPES.map(type => (
                      <SelectItem key={type} value={type}>
                        {type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Body</Label>
                <Textarea
                  placeholder={config.body_type === 'application/json' ? '{\n  "key": "value"\n}' : 'Request body...'}
                  value={config.body}
                  onChange={(e) => updateConfig('body', e.target.value)}
                  rows={8}
                  className="font-mono text-sm"
                />
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-8">
              Body is not available for {config.method} requests
            </p>
          )}
        </TabsContent>

        {/* Authentication Tab */}
        <TabsContent value="auth" className="space-y-4">
          <div className="space-y-2">
            <Label>Authentication Type</Label>
            <Select value={config.auth_type} onValueChange={(v) => updateConfig('auth_type', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {AUTH_TYPES.map(auth => (
                  <SelectItem key={auth.value} value={auth.value}>
                    {auth.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {config.auth_type === 'bearer' && (
            <div className="space-y-2">
              <Label>Bearer Token</Label>
              <Input
                type="password"
                placeholder="Enter your bearer token"
                value={config.auth_token}
                onChange={(e) => updateConfig('auth_token', e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Token will be sent as: Authorization: Bearer {'<token>'}
              </p>
            </div>
          )}

          {config.auth_type === 'basic' && (
            <>
              <div className="space-y-2">
                <Label>Username</Label>
                <Input
                  placeholder="Username"
                  value={config.auth_username}
                  onChange={(e) => updateConfig('auth_username', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Password</Label>
                <Input
                  type="password"
                  placeholder="Password"
                  value={config.auth_password}
                  onChange={(e) => updateConfig('auth_password', e.target.value)}
                />
              </div>
            </>
          )}

          {config.auth_type === 'api_key' && (
            <>
              <div className="space-y-2">
                <Label>API Key Name</Label>
                <Input
                  placeholder="X-API-Key"
                  value={config.api_key_name}
                  onChange={(e) => updateConfig('api_key_name', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>API Key Value</Label>
                <Input
                  type="password"
                  placeholder="Your API key"
                  value={config.api_key_value}
                  onChange={(e) => updateConfig('api_key_value', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Send In</Label>
                <Select value={config.api_key_location} onValueChange={(v) => updateConfig('api_key_location', v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="header">Header</SelectItem>
                    <SelectItem value="query">Query Parameter</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          {config.auth_type === 'none' && (
            <p className="text-sm text-muted-foreground text-center py-4">
              No authentication configured
            </p>
          )}
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <div className="space-y-2">
            <Label>Timeout (seconds)</Label>
            <Input
              type="number"
              min="1"
              max="300"
              value={config.timeout}
              onChange={(e) => updateConfig('timeout', parseInt(e.target.value) || 30)}
            />
            <p className="text-xs text-muted-foreground">
              Maximum time to wait for response (1-300 seconds)
            </p>
          </div>

          <div className="space-y-2">
            <Label>Response Type</Label>
            <Select value={config.response_type} onValueChange={(v) => updateConfig('response_type', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="text">Text</SelectItem>
                <SelectItem value="binary">Binary</SelectItem>
                <SelectItem value="auto">Auto-detect</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Retry Count</Label>
            <Input
              type="number"
              min="0"
              max="5"
              value={config.retry_count}
              onChange={(e) => updateConfig('retry_count', parseInt(e.target.value) || 0)}
            />
            <p className="text-xs text-muted-foreground">
              Number of retries on failure (0-5)
            </p>
          </div>

          {config.retry_count > 0 && (
            <div className="space-y-2">
              <Label>Retry Delay (ms)</Label>
              <Input
                type="number"
                min="100"
                max="10000"
                step="100"
                value={config.retry_delay}
                onChange={(e) => updateConfig('retry_delay', parseInt(e.target.value) || 1000)}
              />
            </div>
          )}

          <div className="flex items-center justify-between py-2">
            <div>
              <Label>Follow Redirects</Label>
              <p className="text-xs text-muted-foreground">Automatically follow HTTP redirects</p>
            </div>
            <Switch
              checked={config.follow_redirects}
              onCheckedChange={(checked) => updateConfig('follow_redirects', checked)}
            />
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <Label>Verify SSL</Label>
              <p className="text-xs text-muted-foreground">Verify SSL certificates</p>
            </div>
            <Switch
              checked={config.verify_ssl}
              onCheckedChange={(checked) => updateConfig('verify_ssl', checked)}
            />
          </div>
        </TabsContent>
      </Tabs>

      {/* Test Button */}
      {onTest && (
        <Button 
          onClick={onTest} 
          variant="outline" 
          className="w-full"
          disabled={!config.url}
        >
          <TestTube className="h-4 w-4 mr-2" />
          Test Request
        </Button>
      )}
    </div>
  );
}
