'use client';

import { useState, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

interface InlineEditableNodeProps {
  value: string;
  onUpdate: (value: string) => void;
  className?: string;
  placeholder?: string;
}

export const InlineEditableNode = ({
  value,
  onUpdate,
  className,
  placeholder = 'Enter name...',
}: InlineEditableNodeProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [localValue, setLocalValue] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleSave = () => {
    if (localValue.trim() && localValue !== value) {
      onUpdate(localValue.trim());
    } else {
      setLocalValue(value);
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      setLocalValue(value);
      setIsEditing(false);
    }
  };

  if (isEditing) {
    return (
      <Input
        ref={inputRef}
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        onBlur={handleSave}
        onKeyDown={handleKeyDown}
        className={cn('h-6 text-sm', className)}
        placeholder={placeholder}
      />
    );
  }

  return (
    <div
      className={cn(
        'cursor-pointer hover:bg-muted/50 px-2 py-1 rounded transition-colors',
        className
      )}
      onDoubleClick={() => setIsEditing(true)}
      title="Double-click to edit"
    >
      {value || placeholder}
    </div>
  );
};
