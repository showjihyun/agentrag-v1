'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Trash2, Eye, EyeOff } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { RetryConfig } from '../RetryConfig';

interface HttpRequestNodeConfigProps {
  nodeId: string;
  data: any;
  onChange: (nodeId: string, data: any) => void;
}

export function HttpRequestNodeConfig({
  nodeId,
  data,
  onChange,
}: HttpRequestNodeConfigProps) {
  const [showAuthPassword, setShowAuthPassword] = useState(false);
  const [headers, setHeaders] = useState<Array<{ key: string; value: string }>>(
    Object.entries(data.headers || {}).map(([key, value]) => ({ key, value: value as string }))
  );
  const [queryParams, setQueryParams] = useState<Array<{ key: string; value: string }>>(
    Object.entries(data.queryParams || {}).map(([key, value]) => ({ key, value: value as string }))
  );

  const handleChange = (field: string, value: any) => {
    onChange(nodeId, { ...data, [field]: value });
  };

  const handleHeaderChange = (index: number, field: 'key' | 'value', value: string) => {
    const newHeaders = [...headers];
    newHeaders[index][field] = value;
    setHeaders(newHeaders);
    
    const headersObj = newHeaders.reduce((acc, { key, value }) => {
      if (key) acc[key] = value;
      return acc;
    }, {} as Record<string, string>);
    
    handleChange('headers', headersObj);
  };

  const addHeader = () => {
    setHeaders([...headers, { key: '', value: '' }]);
  };

  const removeHeader = (index: number) => {
    const newHeaders = headers.filter((_, i) => i !== index);
    setHeaders(newHeaders);
    
    const headersObj = newHeaders.reduce((acc, { key, value }) => {
      if (key) acc[key] = value;
      return acc;
    }, {} as Record<string, string>);
    
    handleChange('headers', headersObj);
  };

  const handleQueryParamChange = (index: number, field: 'key' | 'value', value: string) => {
    const newParams = [...queryParams];
    newParams[index][field] = value;
    setQueryParams(newParams);
    
    const paramsObj = newParams.reduce((acc, { key, value }) => {
      if (key) acc[key] = value;
      return acc;
    }, {} as Record<string, string>);
    
    handleChange('queryParams', paramsObj);
  };

  const addQueryParam = () => {
    setQueryParams([...queryParams, { key: '', value: '' }]);
  };

  const removeQueryParam = (index: number) => {
    const newParams = queryParams.filter((_, i) => i !== index);
    setQueryParams(newParams);
    
    const paramsObj = newParams.reduce((acc, { key, value }) => {
      if (key) acc[key] = value;
      return acc;
    }, {} as Record<string, string>);
    
    handleChange('queryParams', paramsObj);
  };

  return (
    <div className="space-y-4">
      <div>
        <Label htmlFor="label">Label</Label>
        <Input
          id="label"
          value={data.label || ''}
          onChange={(e) => handleChange('label', e.target.value)}
          placeholder="HTTP Request"
        />
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="col-span-1">
          <Label htmlFor="method">Method</Label>
          <Select
            value={data.method || 'GET'}
            onValueChange={(value) => handleChange('method', value)}
          >
            <SelectTrigger id="method">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="GET">GET</SelectItem>
              <SelectItem value="POST">POST</SelectItem>
              <SelectItem value="PUT">PUT</SelectItem>
              <SelectItem value="PATCH">PATCH</SelectItem>
              <SelectItem value="DELETE">DELETE</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="col-span-2">
          <Label htmlFor="url">URL</Label>
          <Input
            id="url"
            value={data.url || ''}
            onChange={(e) => handleChange('url', e.target.value)}
            placeholder="https://api.example.com/endpoint"
          />
        </div>
      </div>

      <Tabs defaultValue="params" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="params">Params</TabsTrigger>
          <TabsTrigger value="headers">Headers</TabsTrigger>
          <TabsTrigger value="body">Body</TabsTrigger>
          <TabsTrigger value="auth">Auth</TabsTrigger>
        </TabsList>

        <TabsContent value="params" className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Query Parameters</Label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addQueryParam}
            >
              <Plus className="w-3 h-3 mr-1" />
              Add
            </Button>
          </div>
          
          <div className="space-y-2 max-h-[200px] overflow-y-auto">
            {queryParams.map((param, index) => (
              <div key={index} className="flex gap-2">
                <Input
                  placeholder="Key"
                  value={param.key}
                  onChange={(e) => handleQueryParamChange(index, 'key', e.target.value)}
                  className="flex-1"
                />
                <Input
                  placeholder="Value"
                  value={param.value}
                  onChange={(e) => handleQueryParamChange(index, 'value', e.target.value)}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeQueryParam(index)}
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="headers" className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Headers</Label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addHeader}
            >
              <Plus className="w-3 h-3 mr-1" />
              Add
            </Button>
          </div>
          
          <div className="space-y-2 max-h-[200px] overflow-y-auto">
            {headers.map((header, index) => (
              <div key={index} className="flex gap-2">
                <Input
                  placeholder="Key"
                  value={header.key}
                  onChange={(e) => handleHeaderChange(index, 'key', e.target.value)}
                  className="flex-1"
                />
                <Input
                  placeholder="Value"
                  value={header.value}
                  onChange={(e) => handleHeaderChange(index, 'value', e.target.value)}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeHeader(index)}
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="body" className="space-y-2">
          <div>
            <Label htmlFor="bodyType">Body Type</Label>
            <Select
              value={data.bodyType || 'json'}
              onValueChange={(value) => handleChange('bodyType', value)}
            >
              <SelectTrigger id="bodyType">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="form">Form Data</SelectItem>
                <SelectItem value="raw">Raw</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="body">Body</Label>
            <Textarea
              id="body"
              value={data.body || ''}
              onChange={(e) => handleChange('body', e.target.value)}
              placeholder={
                data.bodyType === 'json'
                  ? '{\n  "key": "value"\n}'
                  : 'Request body'
              }
              rows={8}
              className="font-mono text-xs"
            />
          </div>
        </TabsContent>

        <TabsContent value="auth" className="space-y-3">
          <div>
            <Label htmlFor="authType">Authentication Type</Label>
            <Select
              value={data.authType || 'none'}
              onValueChange={(value) => handleChange('authType', value)}
            >
              <SelectTrigger id="authType">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="bearer">Bearer Token</SelectItem>
                <SelectItem value="basic">Basic Auth</SelectItem>
                <SelectItem value="api_key">API Key</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {data.authType === 'bearer' && (
            <div>
              <Label htmlFor="token">Bearer Token</Label>
              <Input
                id="token"
                type="password"
                value={data.authConfig?.token || ''}
                onChange={(e) =>
                  handleChange('authConfig', {
                    ...data.authConfig,
                    token: e.target.value,
                  })
                }
                placeholder="Enter bearer token"
              />
            </div>
          )}

          {data.authType === 'basic' && (
            <>
              <div>
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={data.authConfig?.username || ''}
                  onChange={(e) =>
                    handleChange('authConfig', {
                      ...data.authConfig,
                      username: e.target.value,
                    })
                  }
                  placeholder="Enter username"
                />
              </div>
              <div>
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showAuthPassword ? 'text' : 'password'}
                    value={data.authConfig?.password || ''}
                    onChange={(e) =>
                      handleChange('authConfig', {
                        ...data.authConfig,
                        password: e.target.value,
                      })
                    }
                    placeholder="Enter password"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => setShowAuthPassword(!showAuthPassword)}
                  >
                    {showAuthPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
            </>
          )}

          {data.authType === 'api_key' && (
            <>
              <div>
                <Label htmlFor="keyName">Header Name</Label>
                <Input
                  id="keyName"
                  value={data.authConfig?.keyName || 'X-API-Key'}
                  onChange={(e) =>
                    handleChange('authConfig', {
                      ...data.authConfig,
                      keyName: e.target.value,
                    })
                  }
                  placeholder="X-API-Key"
                />
              </div>
              <div>
                <Label htmlFor="keyValue">API Key</Label>
                <Input
                  id="keyValue"
                  type="password"
                  value={data.authConfig?.keyValue || ''}
                  onChange={(e) =>
                    handleChange('authConfig', {
                      ...data.authConfig,
                      keyValue: e.target.value,
                    })
                  }
                  placeholder="Enter API key"
                />
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>

      <div className="space-y-3 pt-2 border-t">
        <div className="flex items-center justify-between">
          <Label htmlFor="followRedirects">Follow Redirects</Label>
          <Switch
            id="followRedirects"
            checked={data.followRedirects !== false}
            onCheckedChange={(checked) => handleChange('followRedirects', checked)}
          />
        </div>

        <div>
          <Label htmlFor="timeout">Timeout (seconds)</Label>
          <Input
            id="timeout"
            type="number"
            value={data.timeout || 30}
            onChange={(e) => handleChange('timeout', parseInt(e.target.value) || 30)}
            min={1}
            max={300}
          />
        </div>
      </div>

      {/* Retry Configuration */}
      <RetryConfig data={data} onChange={handleChange} />
    </div>
  );
}
