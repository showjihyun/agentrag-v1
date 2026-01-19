'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { BlockTypeConfig, BlockSubBlock } from '@/lib/api/block-types';
import { Sparkles, Save, X, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AgenticBlockConfigPanelProps {
  block: BlockTypeConfig;
  initialConfig?: Record<string, any>;
  onSave?: (config: Record<string, any>) => void;
  onCancel?: () => void;
}

function renderSubBlock(
  subBlock: BlockSubBlock,
  value: any,
  onChange: (value: any) => void
) {
  const commonProps = {
    id: subBlock.id,
    required: subBlock.required,
  };

  switch (subBlock.type) {
    case 'text':
      return (
        <Input
          {...commonProps}
          type="text"
          placeholder={subBlock.placeholder}
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
        />
      );

    case 'textarea':
      return (
        <Textarea
          {...commonProps}
          placeholder={subBlock.placeholder}
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          rows={4}
        />
      );

    case 'number':
      return (
        <Input
          {...commonProps}
          type="number"
          min={subBlock.min}
          max={subBlock.max}
          step={subBlock.step}
          value={value || subBlock.default || 0}
          onChange={(e) => onChange(Number(e.target.value))}
        />
      );

    case 'dropdown':
      return (
        <Select value={value || subBlock.default} onValueChange={onChange}>
          <SelectTrigger>
            <SelectValue placeholder={`Select ${subBlock.title}`} />
          </SelectTrigger>
          <SelectContent>
            {subBlock.options?.map((option) => {
              const optionValue = typeof option === 'string' ? option : option.value;
              const optionLabel = typeof option === 'string' ? option : option.label;
              return (
                <SelectItem key={optionValue} value={optionValue}>
                  {optionLabel}
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
      );

    case 'toggle':
      return (
        <div className="flex items-center space-x-2">
          <Switch
            id={subBlock.id}
            checked={value ?? subBlock.default ?? false}
            onCheckedChange={onChange}
          />
          <Label htmlFor={subBlock.id} className="text-sm text-muted-foreground">
            {value ? 'Enabled' : 'Disabled'}
          </Label>
        </div>
      );

    case 'slider':
      return (
        <div className="space-y-2">
          <Slider
            value={[value ?? subBlock.default ?? 0]}
            onValueChange={([v]) => onChange(v)}
            min={subBlock.min ?? 0}
            max={subBlock.max ?? 1}
            step={subBlock.step ?? 0.1}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{subBlock.min ?? 0}</span>
            <span className="font-medium">{value ?? subBlock.default ?? 0}</span>
            <span>{subBlock.max ?? 1}</span>
          </div>
        </div>
      );

    case 'multi-select':
      // Simplified multi-select (would need a proper multi-select component)
      return (
        <div className="text-sm text-muted-foreground">
          Multi-select not yet implemented
        </div>
      );

    default:
      return (
        <div className="text-sm text-muted-foreground">
          Unknown field type: {subBlock.type}
        </div>
      );
  }
}

export function AgenticBlockConfigPanel({
  block,
  initialConfig = {},
  onSave,
  onCancel,
}: AgenticBlockConfigPanelProps) {
  const [config, setConfig] = useState<Record<string, any>>(initialConfig);

  const handleFieldChange = (fieldId: string, value: any) => {
    setConfig((prev) => ({
      ...prev,
      [fieldId]: value,
    }));
  };

  const handleSave = () => {
    onSave?.(config);
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className="p-2 rounded-lg"
              style={{ backgroundColor: `${block.bg_color}20` }}
            >
              <Sparkles className="h-5 w-5" style={{ color: block.bg_color }} />
            </div>
            <div>
              <CardTitle>{block.name} Configuration</CardTitle>
              <CardDescription>{block.description}</CardDescription>
            </div>
          </div>
          <Badge variant="outline" className="bg-purple-500/10 text-purple-700">
            Agentic
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Configuration Fields */}
        {block.sub_blocks.map((subBlock, index) => (
          <div key={subBlock.id} className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor={subBlock.id} className="text-sm font-medium">
                {subBlock.title}
                {subBlock.required && (
                  <span className="text-destructive ml-1">*</span>
                )}
              </Label>
              {subBlock.required && (
                <Badge variant="secondary" className="text-xs">
                  Required
                </Badge>
              )}
            </div>
            {renderSubBlock(
              subBlock,
              config[subBlock.id],
              (value) => handleFieldChange(subBlock.id, value)
            )}
            {index < block.sub_blocks.length - 1 && (
              <Separator className="mt-4" />
            )}
          </div>
        ))}

        {/* Input/Output Schema Info */}
        <Card className="bg-muted/50">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-sm">Block Schema</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div>
              <span className="font-medium">Inputs:</span>{' '}
              {Object.keys(block.inputs).join(', ')}
            </div>
            <div>
              <span className="font-medium">Outputs:</span>{' '}
              {Object.keys(block.outputs).join(', ')}
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex items-center gap-2 pt-4">
          <Button onClick={handleSave} className="flex-1">
            <Save className="h-4 w-4 mr-2" />
            Save Configuration
          </Button>
          {onCancel && (
            <Button variant="outline" onClick={onCancel}>
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          )}
        </div>

        {/* Documentation Link */}
        {block.docs_link && (
          <div className="text-center">
            <a
              href={block.docs_link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline"
            >
              View Documentation →
            </a>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default AgenticBlockConfigPanel;
