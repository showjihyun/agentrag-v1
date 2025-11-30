'use client';

import { useState, useEffect } from 'react';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Code, Play } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

const EXAMPLE_CODE = `# Available variables:
# - input: Input from previous node
# - context: Workflow context

def main(input, context):
    # Your code here
    result = input.upper()
    return {
        "output": result,
        "status": "success"
    }

# Return value will be passed to next node
return main(input, context)`;

export default function PythonCodeConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    code: data.code || EXAMPLE_CODE,
    timeout: data.timeout || 30,
    allow_imports: data.allow_imports !== false,
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-yellow-100 dark:bg-yellow-950">
          <Code className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
        </div>
        <div>
          <h3 className="font-semibold">Python Code</h3>
          <p className="text-sm text-muted-foreground">Execute custom Python code</p>
        </div>
        <Badge variant="secondary" className="ml-auto">Popular</Badge>
      </div>

      {/* Code Editor */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Code className="h-4 w-4" />
          Python Code *
        </Label>
        <Textarea
          value={config.code}
          onChange={(e) => updateConfig('code', e.target.value)}
          rows={16}
          className="font-mono text-sm"
          placeholder={EXAMPLE_CODE}
        />
        <p className="text-xs text-muted-foreground">
          Write Python code. Use <code className="px-1 py-0.5 bg-muted rounded">input</code> and <code className="px-1 py-0.5 bg-muted rounded">context</code> variables
        </p>
      </div>

      {/* Settings */}
      <div className="space-y-4 pt-4 border-t">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Allow Imports</Label>
            <p className="text-xs text-muted-foreground">
              Allow importing Python libraries
            </p>
          </div>
          <Switch
            checked={config.allow_imports}
            onCheckedChange={(v) => updateConfig('allow_imports', v)}
          />
        </div>
      </div>

      {/* Available Libraries */}
      <div className="p-3 bg-muted rounded-lg">
        <p className="text-xs font-medium mb-2">Available Libraries:</p>
        <div className="flex flex-wrap gap-1">
          {['json', 'datetime', 'math', 'random', 'requests', 'pandas', 'numpy'].map(lib => (
            <Badge key={lib} variant="outline" className="text-xs">
              {lib}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}
