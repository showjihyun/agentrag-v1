'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { FileText, TestTube } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function CSVParserConfig({ data, onChange, onTest }: ToolConfigProps) {
  const [config, setConfig] = useState({
    input_source: data.input_source || 'file',
    file_path: data.file_path || '',
    csv_content: data.csv_content || '',
    delimiter: data.delimiter || ',',
    quote_char: data.quote_char || '"',
    has_header: data.has_header !== false,
    skip_rows: data.skip_rows || 0,
    encoding: data.encoding || 'utf-8',
    output_format: data.output_format || 'array',
    columns: data.columns || '',
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-green-100 dark:bg-green-950">
          <FileText className="h-5 w-5 text-green-600 dark:text-green-400" />
        </div>
        <div>
          <h3 className="font-semibold">CSV Parser</h3>
          <p className="text-sm text-muted-foreground">Parse CSV files and data</p>
        </div>
      </div>

      {/* Input Source */}
      <div className="space-y-2">
        <Label>Input Source</Label>
        <Select value={config.input_source} onValueChange={(v) => updateConfig('input_source', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="file">File Path</SelectItem>
            <SelectItem value="content">Raw CSV Content</SelectItem>
            <SelectItem value="variable">From Variable</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {config.input_source === 'file' && (
        <div className="space-y-2">
          <Label>File Path</Label>
          <Input
            placeholder="/path/to/file.csv or {{input.file_path}}"
            value={config.file_path}
            onChange={(e) => updateConfig('file_path', e.target.value)}
          />
        </div>
      )}

      {config.input_source === 'content' && (
        <div className="space-y-2">
          <Label>CSV Content</Label>
          <Input
            placeholder="{{input.csv_data}}"
            value={config.csv_content}
            onChange={(e) => updateConfig('csv_content', e.target.value)}
          />
        </div>
      )}

      {/* Delimiter */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Delimiter</Label>
          <Select value={config.delimiter} onValueChange={(v) => updateConfig('delimiter', v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value=",">Comma (,)</SelectItem>
              <SelectItem value=";">Semicolon (;)</SelectItem>
              <SelectItem value="\t">Tab</SelectItem>
              <SelectItem value="|">Pipe (|)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Quote Character</Label>
          <Select value={config.quote_char} onValueChange={(v) => updateConfig('quote_char', v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value='"'>Double Quote (")</SelectItem>
              <SelectItem value="'">Single Quote (')</SelectItem>
              <SelectItem value="">None</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Options */}
      <div className="flex items-center justify-between py-2">
        <div>
          <Label>Has Header Row</Label>
          <p className="text-xs text-muted-foreground">First row contains column names</p>
        </div>
        <Switch
          checked={config.has_header}
          onCheckedChange={(checked) => updateConfig('has_header', checked)}
        />
      </div>

      <div className="space-y-2">
        <Label>Skip Rows</Label>
        <Input
          type="number"
          min="0"
          value={config.skip_rows}
          onChange={(e) => updateConfig('skip_rows', parseInt(e.target.value) || 0)}
        />
        <p className="text-xs text-muted-foreground">Number of rows to skip at the beginning</p>
      </div>

      {/* Encoding */}
      <div className="space-y-2">
        <Label>Encoding</Label>
        <Select value={config.encoding} onValueChange={(v) => updateConfig('encoding', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="utf-8">UTF-8</SelectItem>
            <SelectItem value="utf-16">UTF-16</SelectItem>
            <SelectItem value="ascii">ASCII</SelectItem>
            <SelectItem value="euc-kr">EUC-KR (Korean)</SelectItem>
            <SelectItem value="iso-8859-1">ISO-8859-1</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Output Format */}
      <div className="space-y-2">
        <Label>Output Format</Label>
        <Select value={config.output_format} onValueChange={(v) => updateConfig('output_format', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="array">Array of Objects</SelectItem>
            <SelectItem value="dict">Dictionary (by column)</SelectItem>
            <SelectItem value="raw">Raw 2D Array</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Specific Columns */}
      <div className="space-y-2">
        <Label>Select Columns (optional)</Label>
        <Input
          placeholder="col1, col2, col3 (leave empty for all)"
          value={config.columns}
          onChange={(e) => updateConfig('columns', e.target.value)}
        />
      </div>

      {/* Test Button */}
      {onTest && (
        <Button onClick={onTest} variant="outline" className="w-full">
          <TestTube className="h-4 w-4 mr-2" />
          Test Parser
        </Button>
      )}
    </div>
  );
}
