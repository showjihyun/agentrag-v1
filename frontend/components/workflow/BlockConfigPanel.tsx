'use client';

import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { SubBlockRenderer, SubBlockConfig } from './subblocks/SubBlockRenderer';
import { cn } from '@/lib/utils';

export interface BlockConfigPanelProps {
  block: {
    id: string;
    type: string;
    name: string;
    description?: string;
    category: string;
    bg_color?: string;
    icon?: string;
    sub_blocks?: SubBlockConfig[];
    config?: Record<string, any>;
  } | null;
  onClose: () => void;
  onSave: (blockId: string, config: Record<string, any>) => void;
  className?: string;
}

export function BlockConfigPanel({
  block,
  onClose,
  onSave,
  className,
}: BlockConfigPanelProps) {
  const [values, setValues] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize values from block config
  useEffect(() => {
    if (block?.config) {
      setValues(block.config);
      setHasChanges(false);
    } else if (block?.sub_blocks) {
      // Initialize with default values
      const defaultValues: Record<string, any> = {};
      block.sub_blocks.forEach((subBlock) => {
        if (subBlock.defaultValue !== undefined) {
          defaultValues[subBlock.id] = subBlock.defaultValue;
        }
      });
      setValues(defaultValues);
      setHasChanges(false);
    }
  }, [block]);

  // Handle value change
  const handleChange = (id: string, value: any) => {
    setValues((prev) => ({ ...prev, [id]: value }));
    setHasChanges(true);
    
    // Clear error for this field
    if (errors[id]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[id];
        return newErrors;
      });
    }
  };

  // Validate form
  const validate = (): boolean => {
    if (!block?.sub_blocks) return true;

    const newErrors: Record<string, string> = {};

    block.sub_blocks.forEach((subBlock) => {
      if (subBlock.required && !values[subBlock.id]) {
        newErrors[subBlock.id] = `${subBlock.title} is required`;
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle save
  const handleSave = () => {
    if (!block) return;

    if (validate()) {
      onSave(block.id, values);
      setHasChanges(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    if (hasChanges) {
      const confirmed = window.confirm('You have unsaved changes. Are you sure you want to close?');
      if (!confirmed) return;
    }
    onClose();
  };

  if (!block) {
    return null;
  }

  const hasErrors = Object.keys(errors).length > 0;

  return (
    <div className={cn('flex flex-col h-full bg-card border-l', className)}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start gap-3 flex-1">
            {block.icon && (
              <div
                className="w-10 h-10 rounded flex items-center justify-center text-white font-bold flex-shrink-0"
                style={{ backgroundColor: block.bg_color || '#6366f1' }}
              >
                {block.icon}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg truncate">{block.name}</h3>
              {block.description && (
                <p className="text-sm text-muted-foreground mt-1">{block.description}</p>
              )}
              <p className="text-xs text-muted-foreground mt-1 capitalize">{block.category}</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={handleCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {hasChanges && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              You have unsaved changes
            </AlertDescription>
          </Alert>
        )}
      </div>

      {/* Configuration Form */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {block.sub_blocks && block.sub_blocks.length > 0 ? (
            <SubBlockRenderer
              subBlocks={block.sub_blocks}
              values={values}
              errors={errors}
              onChange={handleChange}
            />
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p className="text-sm">No configuration options available</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-4 border-t">
        {hasErrors && (
          <Alert variant="destructive" className="mb-3">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              Please fix the errors above before saving
            </AlertDescription>
          </Alert>
        )}
        
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleCancel} className="flex-1">
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!hasChanges || hasErrors}
            className="flex-1 gap-2"
          >
            <Save className="h-4 w-4" />
            Save
          </Button>
        </div>
      </div>
    </div>
  );
}
