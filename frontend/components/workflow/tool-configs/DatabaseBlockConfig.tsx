'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Database, Plus, Trash } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function DatabaseBlockConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    database_type: data.database_type || 'postgres',
    connection_string: data.connection_string || '',
    operation: data.operation || 'query',
    query: data.query || '',
    table: data.table || '',
    columns: data.columns || '*',
    where: data.where || '',
    order_by: data.order_by || '',
    limit: data.limit || 100,
    parameters: data.parameters || [],
    return_type: data.return_type || 'rows',
    use_transaction: data.use_transaction || false,
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

  const updateParameter = (index: number, field: string, value: string) => {
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
          <h3 className="font-semibold">Database Query</h3>
          <p className="text-sm text-muted-foreground">Query any database</p>
        </div>
      </div>

      {/* Database Type */}
      <div className="space-y-2">
        <Label>Database Type</Label>
        <Select value={config.database_type} onValueChange={(v) => updateConfig('database_type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="postgres">PostgreSQL</SelectItem>
            <SelectItem value="mysql">MySQL</SelectItem>
            <SelectItem value="sqlite">SQLite</SelectItem>
            <SelectItem value="mongodb">MongoDB</SelectItem>
            <SelectItem value="redis">Redis</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Connection String */}
      <div className="space-y-2">
        <Label>Connection String</Label>
        <Input
          type="password"
          placeholder="postgresql://user:pass@host:5432/db"
          value={config.connection_string}
          onChange={(e) => updateConfig('connection_string', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Or use {'{{env.DATABASE_URL}}'}
        </p>
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
            <SelectItem value="upsert">UPSERT</SelectItem>
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
        </div>
      )}

      {/* Query Builder */}
      {config.operation !== 'query' && (
        <>
          <div className="space-y-2">
            <Label>Table</Label>
            <Input
              placeholder="users"
              value={config.table}
              onChange={(e) => updateConfig('table', e.target.value)}
            />
          </div>

          {config.operation === 'select' && (
            <>
              <div className="space-y-2">
                <Label>Columns</Label>
                <Input
                  placeholder="* or id, name, email"
                  value={config.columns}
                  onChange={(e) => updateConfig('columns', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>WHERE</Label>
                <Input
                  placeholder="status = 'active'"
                  value={config.where}
                  onChange={(e) => updateConfig('where', e.target.value)}
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
            </>
          )}
        </>
      )}

      {/* Parameters */}
      <div className="space-y-3">
        <Label>Query Parameters</Label>
        {config.parameters.map((param: any, index: number) => (
          <div key={index} className="flex gap-2">
            <Input
              placeholder={`$${index + 1}`}
              value={`$${index + 1}`}
              disabled
              className="w-16"
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

      {/* Options */}
      <div className="flex items-center justify-between">
        <div>
          <Label>Use Transaction</Label>
          <p className="text-xs text-muted-foreground">Wrap in transaction</p>
        </div>
        <Switch
          checked={config.use_transaction}
          onCheckedChange={(checked) => updateConfig('use_transaction', checked)}
        />
      </div>

      {/* Return Type */}
      <div className="space-y-2">
        <Label>Return Type</Label>
        <Select value={config.return_type} onValueChange={(v) => updateConfig('return_type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="rows">All Rows</SelectItem>
            <SelectItem value="first">First Row</SelectItem>
            <SelectItem value="count">Row Count</SelectItem>
            <SelectItem value="affected">Affected Rows</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
