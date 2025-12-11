'use client';

/**
 * PostgresConfig - PostgreSQL Database Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Database, TestTube, Plus, Trash } from 'lucide-react';
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
  InfoBox,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const OPERATIONS = [
  { value: 'query', label: 'Custom Query' },
  { value: 'select', label: 'SELECT' },
  { value: 'insert', label: 'INSERT' },
  { value: 'update', label: 'UPDATE' },
  { value: 'delete', label: 'DELETE' },
] as const;

const RETURN_TYPES = [
  { value: 'rows', label: 'All Rows' },
  { value: 'first', label: 'First Row Only' },
  { value: 'count', label: 'Row Count' },
  { value: 'affected', label: 'Affected Rows' },
] as const;

// ============================================
// Types
// ============================================

interface QueryParameter {
  name: string;
  value: string;
}

interface PostgresConfigData {
  operation: string;
  connection_string: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  use_connection_string: boolean;
  query: string;
  table: string;
  columns: string;
  where_clause: string;
  order_by: string;
  limit: number;
  parameters: QueryParameter[];
  return_type: string;
}

const DEFAULTS: PostgresConfigData = {
  operation: 'query',
  connection_string: '',
  host: 'localhost',
  port: 5432,
  database: '',
  username: '',
  password: '',
  use_connection_string: false,
  query: '',
  table: '',
  columns: '*',
  where_clause: '',
  order_by: '',
  limit: 100,
  parameters: [],
  return_type: 'rows',
};

// ============================================
// Component
// ============================================

export default function PostgresConfig({ data, onChange, onTest }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<PostgresConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  // Parameter handlers
  const addParameter = useCallback(() => {
    const newParams = [...config.parameters, { name: `$${config.parameters.length + 1}`, value: '' }];
    updateField('parameters', newParams);
  }, [config.parameters, updateField]);

  const updateParameter = useCallback((index: number, field: 'name' | 'value', value: string) => {
    const newParams = [...config.parameters];
    newParams[index] = { ...newParams[index], [field]: value };
    updateField('parameters', newParams);
  }, [config.parameters, updateField]);

  const removeParameter = useCallback((index: number) => {
    updateField('parameters', config.parameters.filter((_, i) => i !== index));
  }, [config.parameters, updateField]);

  const isCustomQuery = config.operation === 'query';
  const isSelect = config.operation === 'select';

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Database}
          {...TOOL_HEADER_PRESETS.database}
          title="PostgreSQL"
          description="Query PostgreSQL database"
        />

        {/* Connection Section */}
        <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
          <SwitchField
            label="Use Connection String"
            checked={config.use_connection_string}
            onChange={(v) => updateField('use_connection_string', v)}
            tooltip="연결 문자열을 직접 입력하거나 개별 필드로 설정할 수 있습니다."
          />

          {config.use_connection_string ? (
            <TextField
              label="Connection String"
              value={config.connection_string}
              onChange={(v) => updateField('connection_string', v)}
              type="password"
              placeholder="postgresql://user:password@host:port/database"
            />
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <TextField
                label="Host"
                value={config.host}
                onChange={(v) => updateField('host', v)}
                placeholder="localhost"
              />
              <NumberField
                label="Port"
                value={config.port}
                onChange={(v) => updateField('port', v)}
                min={1}
                max={65535}
              />
              <TextField
                label="Database"
                value={config.database}
                onChange={(v) => updateField('database', v)}
                placeholder="mydb"
              />
              <TextField
                label="Username"
                value={config.username}
                onChange={(v) => updateField('username', v)}
                placeholder="postgres"
              />
              <div className="col-span-2">
                <TextField
                  label="Password"
                  value={config.password}
                  onChange={(v) => updateField('password', v)}
                  type="password"
                  placeholder="••••••••"
                />
              </div>
            </div>
          )}
        </div>

        {/* Operation */}
        <SelectField
          label="Operation"
          value={config.operation}
          onChange={(v) => updateField('operation', v)}
          options={OPERATIONS.map(o => ({ value: o.value, label: o.label }))}
        />

        {/* Custom Query */}
        {isCustomQuery && (
          <TextareaField
            label="SQL Query"
            value={config.query}
            onChange={(v) => updateField('query', v)}
            placeholder="SELECT * FROM users WHERE id = $1"
            rows={5}
            mono
            hint="Use $1, $2, etc. for parameterized queries"
          />
        )}

        {/* SELECT Builder */}
        {isSelect && (
          <div className="space-y-4">
            <TextField
              label="Table"
              value={config.table}
              onChange={(v) => updateField('table', v)}
              placeholder="users"
            />
            <TextField
              label="Columns"
              value={config.columns}
              onChange={(v) => updateField('columns', v)}
              placeholder="* or id, name, email"
            />
            <TextField
              label="WHERE Clause"
              value={config.where_clause}
              onChange={(v) => updateField('where_clause', v)}
              placeholder="status = 'active' AND created_at > '2024-01-01'"
            />
            <div className="grid grid-cols-2 gap-4">
              <TextField
                label="ORDER BY"
                value={config.order_by}
                onChange={(v) => updateField('order_by', v)}
                placeholder="created_at DESC"
              />
              <NumberField
                label="LIMIT"
                value={config.limit}
                onChange={(v) => updateField('limit', v)}
                min={1}
              />
            </div>
          </div>
        )}

        {/* Query Parameters */}
        {(isCustomQuery || config.parameters.length > 0) && (
          <div className="space-y-3">
            <Label>Query Parameters ({config.parameters.length})</Label>
            {config.parameters.map((param, index) => (
              <div key={index} className="flex gap-2">
                <Input
                  value={`$${index + 1}`}
                  className="w-16 text-center"
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
        <SelectField
          label="Return Type"
          value={config.return_type}
          onChange={(v) => updateField('return_type', v)}
          options={RETURN_TYPES.map(r => ({ value: r.value, label: r.label }))}
        />

        {/* Info */}
        <InfoBox title="Security Note:" variant="warning">
          Always use parameterized queries ($1, $2) to prevent SQL injection.
        </InfoBox>

        {/* Test Button */}
        {onTest && (
          <Button onClick={onTest} variant="outline" className="w-full">
            <TestTube className="h-4 w-4 mr-2" />
            Test Query
          </Button>
        )}
      </div>
    </TooltipProvider>
  );
}
