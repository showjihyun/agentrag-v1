'use client';

import { useState, useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Check, X } from 'lucide-react';

interface InlineNodeEditorProps {
  nodeId: string;
  initialLabel: string;
  initialDescription?: string;
  position: { x: number; y: number };
  onSave: (label: string, description?: string) => void;
  onCancel: () => void;
}

export function InlineNodeEditor({
  nodeId,
  initialLabel,
  initialDescription,
  position,
  onSave,
  onCancel,
}: InlineNodeEditorProps) {
  const [label, setLabel] = useState(initialLabel);
  const [description, setDescription] = useState(initialDescription || '');
  const containerRef = useRef<HTMLDivElement>(null);
  const labelInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Focus label input on mount
    labelInputRef.current?.focus();
    labelInputRef.current?.select();

    // Handle click outside
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        handleSave();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSave = () => {
    if (label.trim()) {
      onSave(label.trim(), description.trim() || undefined);
    } else {
      onCancel();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    }
  };

  return (
    <div
      ref={containerRef}
      className="absolute z-50 bg-white dark:bg-gray-800 rounded-lg shadow-xl border-2 border-primary p-4 min-w-[300px]"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      <div className="space-y-3">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1 block">
            Label
          </label>
          <Input
            ref={labelInputRef}
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Node label"
            className="text-sm"
          />
        </div>

        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1 block">
            Description (optional)
          </label>
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Node description"
            className="text-sm resize-none"
            rows={2}
          />
        </div>

        <div className="flex gap-2 justify-end">
          <Button
            size="sm"
            variant="outline"
            onClick={onCancel}
          >
            <X className="h-3 w-3 mr-1" />
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={handleSave}
            disabled={!label.trim()}
          >
            <Check className="h-3 w-3 mr-1" />
            Save
          </Button>
        </div>
      </div>

      <div className="text-xs text-muted-foreground mt-2 pt-2 border-t">
        <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">Enter</kbd> to save
        {' • '}
        <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">Esc</kbd> to cancel
      </div>
    </div>
  );
}
