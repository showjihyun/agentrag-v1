'use client';

/**
 * HttpRequestConfig - HTTP Request Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Globe, TestTube, Settings, Shield } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  TextField,
  NumberField,
  TextareaField,
  SelectField,
  SwitchField,
  KeyValueListField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'] as const;

const CONTENT_TYPES = [
  { value: 'application/json', label: 'application/json' },
  { value: 'application/x-www-form-urlencoded', label: 'application/x-www-form-urlencoded' },
  { value: 'multipart/form-data', label: 'multipart/form-data' },
  { value: 'text/plain', label: 'text/plain' },
  { value: 'text/html', label: 'text/html' },
  { value: 'application/xml', label: 'application/xml' },
] as const;

const AUTH_TYPES = [
  { value: 'none', label: 'No Auth' },
  { value: 'bearer', label: 'Bearer Token' },
  { value: 'basic', label: 'Basic Auth' },
  { value: 'api_key', label: 'API Key' },
] as const;

const RESPONSE_TYPES = [
  { value: 'json', label: 'JSON' },
  { value: 'text', label: 'Text' },
  { value: 'binary', label: 'Binary' },
  { value: 'auto', label: 'Auto-detect' },
] as const;

const API_KEY_LOCATIONS = [
  { value: 'header', label: 'Header' },
  { value: 'query', label: 'Query Parameter' },
] as const;

// ============================================
// Types
// ============================================

interface KeyValueItem {
  key: string;
  value: string;
}

interface HttpRequestConfigData {
  method: string;
  url: string;
  headers: KeyValueItem[];
  query_params: KeyValueItem[];
  body: string;
  body_type: string;
  timeout: number;
  follow_redirects: boolean;
  auth_type: string;
  auth_token: string;
  auth_username: string;
  auth_password: string;
  api_key_name: string;
  api_key_value: string;
  api_key_location: string;
  retry_count: number;
  retry_delay: number;
  verify_ssl: boolean;
  response_type: string;
}

const DEFAULTS: HttpRequestConfigData = {
  method: 'GET',
  url: '',
  headers: [],
  query_params: [],
  body: '',
  body_type: 'application/json',
  timeout: 30,
  follow_redirects: true,
  auth_type: 'none',
  auth_token: '',
  auth_username: '',
  auth_password: '',
  api_key_name: 'X-API-Key',
  api_key_value: '',
  api_key_location: 'header',
  retry_count: 0,
  retry_delay: 1000,
  verify_ssl: true,
  response_type: 'json',
};

// ============================================
// Component
// ============================================

export default function HttpRequestConfig({ data, onChange, onTest }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<HttpRequestConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  // Header handlers
  const addHeader = useCallback(() => {
    updateField('headers', [...config.headers, { key: '', value: '' }]);
  }, [config.headers, updateField]);

  const updateHeader = useCallback((index: number, field: 'key' | 'value', value: string) => {
    const newHeaders = [...config.headers];
    newHeaders[index] = { ...newHeaders[index], [field]: value };
    updateField('headers', newHeaders);
  }, [config.headers, updateField]);

  const removeHeader = useCallback((index: number) => {
    updateField('headers', config.headers.filter((_, i) => i !== index));
  }, [config.headers, updateField]);

  // Query param handlers
  const addQueryParam = useCallback(() => {
    updateField('query_params', [...config.query_params, { key: '', value: '' }]);
  }, [config.query_params, updateField]);

  const updateQueryParam = useCallback((index: number, field: 'key' | 'value', value: string) => {
    const newParams = [...config.query_params];
    newParams[index] = { ...newParams[index], [field]: value };
    updateField('query_params', newParams);
  }, [config.query_params, updateField]);

  const removeQueryParam = useCallback((index: number) => {
    updateField('query_params', config.query_params.filter((_, i) => i !== index));
  }, [config.query_params, updateField]);

  const showBody = ['POST', 'PUT', 'PATCH'].includes(config.method);

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Globe}
          {...TOOL_HEADER_PRESETS.http}
          title="HTTP Request"
          description="Make API calls to any endpoint"
          badge="Popular"
        />

        {/* Method & URL */}
        <div className="space-y-2">
          <Label>Request</Label>
          <div className="flex gap-2">
            <Select value={config.method} onValueChange={(v) => updateField('method', v)}>
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
              onChange={(e) => updateField('url', e.target.value)}
              className="flex-1 font-mono text-sm"
            />
          </div>
          <p className="text-xs text-muted-foreground">
            Use <code className="px-1 py-0.5 bg-muted rounded">{'{{variables}}'}</code> for dynamic values
          </p>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="headers" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="headers">Headers ({config.headers.length})</TabsTrigger>
            <TabsTrigger value="query">Query ({config.query_params.length})</TabsTrigger>
            <TabsTrigger value="body">Body</TabsTrigger>
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
          <TabsContent value="headers" className="space-y-3 mt-4">
            <KeyValueListField
              label="Headers"
              items={config.headers}
              onAdd={addHeader}
              onUpdate={updateHeader}
              onRemove={removeHeader}
              keyPlaceholder="Header name"
              valuePlaceholder="Value"
              addButtonText="Add Header"
            />
          </TabsContent>

          {/* Query Params Tab */}
          <TabsContent value="query" className="space-y-3 mt-4">
            <KeyValueListField
              label="Query Parameters"
              items={config.query_params}
              onAdd={addQueryParam}
              onUpdate={updateQueryParam}
              onRemove={removeQueryParam}
              keyPlaceholder="Parameter name"
              valuePlaceholder="Value"
              addButtonText="Add Query Parameter"
            />
          </TabsContent>

          {/* Body Tab */}
          <TabsContent value="body" className="space-y-4 mt-4">
            {showBody ? (
              <>
                <SelectField
                  label="Content Type"
                  value={config.body_type}
                  onChange={(v) => updateField('body_type', v)}
                  options={CONTENT_TYPES.map(t => ({ value: t.value, label: t.label }))}
                />
                <TextareaField
                  label="Body"
                  value={config.body}
                  onChange={(v) => updateField('body', v)}
                  placeholder={config.body_type === 'application/json' ? '{\n  "key": "value"\n}' : 'Request body...'}
                  rows={8}
                  mono
                />
              </>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                Body is not available for {config.method} requests
              </p>
            )}
          </TabsContent>

          {/* Auth Tab */}
          <TabsContent value="auth" className="space-y-4 mt-4">
            <SelectField
              label="Authentication Type"
              value={config.auth_type}
              onChange={(v) => updateField('auth_type', v)}
              options={AUTH_TYPES.map(a => ({ value: a.value, label: a.label }))}
            />

            {config.auth_type === 'bearer' && (
              <TextField
                label="Bearer Token"
                value={config.auth_token}
                onChange={(v) => updateField('auth_token', v)}
                type="password"
                placeholder="Enter your bearer token"
                hint="Token will be sent as: Authorization: Bearer <token>"
              />
            )}

            {config.auth_type === 'basic' && (
              <>
                <TextField
                  label="Username"
                  value={config.auth_username}
                  onChange={(v) => updateField('auth_username', v)}
                  placeholder="Username"
                />
                <TextField
                  label="Password"
                  value={config.auth_password}
                  onChange={(v) => updateField('auth_password', v)}
                  type="password"
                  placeholder="Password"
                />
              </>
            )}

            {config.auth_type === 'api_key' && (
              <>
                <TextField
                  label="API Key Name"
                  value={config.api_key_name}
                  onChange={(v) => updateField('api_key_name', v)}
                  placeholder="X-API-Key"
                />
                <TextField
                  label="API Key Value"
                  value={config.api_key_value}
                  onChange={(v) => updateField('api_key_value', v)}
                  type="password"
                  placeholder="Your API key"
                />
                <SelectField
                  label="Send In"
                  value={config.api_key_location}
                  onChange={(v) => updateField('api_key_location', v)}
                  options={API_KEY_LOCATIONS.map(l => ({ value: l.value, label: l.label }))}
                />
              </>
            )}

            {config.auth_type === 'none' && (
              <p className="text-sm text-muted-foreground text-center py-4">
                No authentication configured
              </p>
            )}
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-4 mt-4">
            <NumberField
              label="Timeout (seconds)"
              value={config.timeout}
              onChange={(v) => updateField('timeout', v)}
              min={1}
              max={300}
              hint="Maximum time to wait for response (1-300 seconds)"
            />

            <SelectField
              label="Response Type"
              value={config.response_type}
              onChange={(v) => updateField('response_type', v)}
              options={RESPONSE_TYPES.map(r => ({ value: r.value, label: r.label }))}
            />

            <NumberField
              label="Retry Count"
              value={config.retry_count}
              onChange={(v) => updateField('retry_count', v)}
              min={0}
              max={5}
              hint="Number of retries on failure (0-5)"
            />

            {config.retry_count > 0 && (
              <NumberField
                label="Retry Delay (ms)"
                value={config.retry_delay}
                onChange={(v) => updateField('retry_delay', v)}
                min={100}
                max={10000}
                step={100}
              />
            )}

            <SwitchField
              label="Follow Redirects"
              description="Automatically follow HTTP redirects"
              checked={config.follow_redirects}
              onChange={(v) => updateField('follow_redirects', v)}
            />

            <SwitchField
              label="Verify SSL"
              description="Verify SSL certificates"
              checked={config.verify_ssl}
              onChange={(v) => updateField('verify_ssl', v)}
            />
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
    </TooltipProvider>
  );
}
