'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Database, TestTube, Plus, Trash } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function PostgresConfig({ data, onChange, onTest }: ToolConfigProps) {
  const [config, setConfig] = useState({
    operation: data.operation || 'query',
    connection_string: data.connection_string || '',
    host: data.host || 'localhost',
    port: data.port || 5432,
    database: data.database || '',
    username: data.username || '',
    password: data.password || '',
    use_connection_string: data.use_connection_string || false,
    query: data.query || '',
    table: data.table || '',
    columns: data.columns || '*',
    where_clause: data.where_clause || '',
    order_by: data.order_by || '',
    limit: data.limit || 100,
    parameters: data.parameters || [],
    return_type: data.return_type || 'rows',
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const addParameter = () => {
    updateConfig('parameters', [...config.parameters, { name: '', value: '' }]);
  };

  const updateParameter = (index: number, field: 'name' | 'value', value: string) => {
    const newParams = [...config.parameters];
    newParams[index][field] = value;
    updateConfig('parameters', newParams);
  };

  const removeParameter = (index: number) => {
    updateConfig('parameters', config.parameters.filter((_: any, i: number) => i !== index));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-950">
          <Database className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h3 className="font-semibold">PostgreSQL</h3>
          <p className="text-sm text-muted-foreground">Query PostgreSQL database</p>
        </div>
      </div>

      {/* Connection */}
      <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
        <div className="flex items-center justify-between">
          <Label>Use Connection String</Label>
          <Switch
            checked={config.use_connection_string}
            onCheckedChange={(checked) => updateConfig('use_connection_string', checked)}
          />
        </div>

        {config.use_connection_string ? (
          <div className="space-y-2">
            <Label>Connection String</Label>
            <Input
              type="password"
              placeholder="postgresql://user:password@host:port/database"
              value={config.connection_string}
              onChange={(e) => updateConfig('connection_string', e.target.value)}
            />
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Host</Label>
              <Input
                placeholder="localhost"
                value={config.host}
                onChange={(e) => updateConfig('host', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Port</Label>
              <Input
                type="number"
                placeholder="5432"
                value={config.port}
                onChange={(e) => updateConfig('port', parseInt(e.target.value) || 5432)}
              />
            </div>
            <div className="space-y-2">
              <Label>Database</Label>
              <Input
                placeholder="mydb"
                value={config.database}
                onChange={(e) => updateConfig('database', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Username</Label>
              <Input
                placeholder="postgres"
                value={config.username}
                onChange={(e) => updateConfig('username', e.target.value)}
              />
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Password</Label>
              <Input
                type="password"
                placeholder="••••••••"
                value={config.password}
                onChange={(e) => updateConfig('password', e.target.value)}
              />
            </div>
          </div>
        )}
      </div>

      {/* Operation */}
      <div className="space-y-2">
        <Label>Operation</Label>
        <Select value={config.operation} onValueChange={(v) => updateConfig('operation', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="query">Custom Query</SelectItem>
            <SelectItem value="select">SELECT</SelectItem>
            <SelectItem value="insert">INSERT</SelectItem>
            <SelectItem value="update">UPDATE</SelectItem>
            <SelectItem value="delete">DELETE</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Custom Query */}
      {config.operation === 'query' && (
        <div className="space-y-2">
          <Label>SQL Query</Label>
          <Textarea
            placeholder="SELECT * FROM users WHERE id = $1"
            value={config.query}
            onChange={(e) => updateConfig('query', e.target.value)}
            rows={5}
            className="font-mono text-sm"
          />
          <p className="text-xs text-muted-foreground">
            Use $1, $2, etc. for parameterized queries
          </p>
        </div>
      )}

      {/* SELECT Builder */}
      {config.operation === 'select' && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Table</Label>
            <Input
              placeholder="users"
              value={config.table}
              onChange={(e) => updateConfig('table', e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Columns</Label>
            <Input
              placeholder="* or id, name, email"
              value={config.columns}
              onChange={(e) => updateConfig('columns', e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>WHERE Clause</Label>
            <Input
              placeholder="status = 'active' AND created_at > '2024-01-01'"
              value={config.where_clause}
              onChange={(e) => updateConfig('where_clause', e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>ORDER BY</Label>
              <Input
                placeholder="created_at DESC"
                value={config.order_by}
                onChange={(e) => updateConfig('order_by', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>LIMIT</Label>
              <Input
                type="number"
                value={config.limit}
                onChange={(e) => updateConfig('limit', parseInt(e.target.value) || 100)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Query Parameters */}
      {(config.operation === 'query' || config.parameters.length > 0) && (
        <div className="space-y-3">
          <Label>Query Parameters</Label>
          {config.parameters.map((param: any, index: number) => (
            <div key={index} className="flex gap-2">
              <Input
                placeholder={`$${index + 1}`}
                value={param.name}
                onChange={(e) => updateParameter(index, 'name', e.target.value)}
                className="w-24"
                disabled
              />
              <Input
                placeholder="Value or {{variable}}"
                value={param.value}
                onChange={(e) => updateParameter(index, 'value', e.target.value)}
                className="flex-1"
              />
              <Button variant="ghost" size="icon" onClick={() => removeParameter(index)}>
                <Trash className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={addParameter} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            Add Parameter
          </Button>
        </div>
      )}

      {/* Return Type */}
      <div className="space-y-2">
        <Label>Return Type</Label>
        <Select value={config.return_type} onValueChange={(v) => updateConfig('return_type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="rows">All Rows</SelectItem>
            <SelectItem value="first">First Row Only</SelectItem>
            <SelectItem value="count">Row Count</SelectItem>
            <SelectItem value="affected">Affected Rows</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Test Button */}
      {onTest && (
        <Button onClick={onTest} variant="outline" className="w-full">
          <TestTube className="h-4 w-4 mr-2" />
          Test Query
        </Button>
      )}
    </div>
  );
}
