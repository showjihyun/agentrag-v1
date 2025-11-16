'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { StickyNote, Trash2, Palette } from 'lucide-react';
import { cn } from '@/lib/utils';

const COLORS = [
  { name: 'Yellow', bg: '#fef3c7', border: '#fbbf24', text: '#78350f' },
  { name: 'Pink', bg: '#fce7f3', border: '#ec4899', text: '#831843' },
  { name: 'Blue', bg: '#dbeafe', border: '#3b82f6', text: '#1e3a8a' },
  { name: 'Green', bg: '#d1fae5', border: '#10b981', text: '#064e3b' },
  { name: 'Purple', bg: '#e9d5ff', border: '#a855f7', text: '#581c87' },
  { name: 'Orange', bg: '#fed7aa', border: '#f97316', text: '#7c2d12' },
];

export interface CommentNodeData {
  text?: string;
  color?: string;
  width?: number;
  height?: number;
  onUpdate?: (data: Partial<CommentNodeData>) => void;
  onDelete?: () => void;
}

export default function CommentNode({ data, selected }: NodeProps<CommentNodeData>) {
  const [isEditing, setIsEditing] = useState(false);
  const [text, setText] = useState(data.text || '');
  const [showColorPicker, setShowColorPicker] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const nodeRef = useRef<HTMLDivElement>(null);

  const currentColor = COLORS.find(c => c.name === data.color) || COLORS[0];

  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.select();
    }
  }, [isEditing]);

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
  };

  const handleBlur = () => {
    setIsEditing(false);
    if (text !== data.text) {
      data.onUpdate?.({ text });
    }
  };

  const handleColorChange = (colorName: string) => {
    data.onUpdate?.({ color: colorName });
    setShowColorPicker(false);
  };

  const handleDelete = () => {
    data.onDelete?.();
  };

  return (
    <div
      ref={nodeRef}
      className={cn(
        'comment-node relative rounded-lg shadow-md transition-all',
        selected && 'ring-2 ring-blue-500 ring-offset-2'
      )}
      style={{
        backgroundColor: currentColor.bg,
        borderColor: currentColor.border,
        borderWidth: '2px',
        borderStyle: 'solid',
        width: data.width || 250,
        minHeight: data.height || 150,
        color: currentColor.text,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b" style={{ borderColor: currentColor.border }}>
        <div className="flex items-center gap-2">
          <StickyNote className="h-4 w-4" />
          <span className="text-xs font-medium">Note</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowColorPicker(!showColorPicker)}
            className="p-1 rounded hover:bg-black/10 transition-colors"
            title="Change color"
          >
            <Palette className="h-3 w-3" />
          </button>
          <button
            onClick={handleDelete}
            className="p-1 rounded hover:bg-red-500/20 transition-colors"
            title="Delete note"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
      </div>

      {/* Color Picker */}
      {showColorPicker && (
        <div
          className="absolute top-10 right-2 z-10 bg-white rounded-lg shadow-lg p-2 border"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="grid grid-cols-3 gap-2">
            {COLORS.map((color) => (
              <button
                key={color.name}
                onClick={() => handleColorChange(color.name)}
                className={cn(
                  'w-8 h-8 rounded border-2 transition-transform hover:scale-110',
                  color.name === data.color && 'ring-2 ring-blue-500 ring-offset-2'
                )}
                style={{
                  backgroundColor: color.bg,
                  borderColor: color.border,
                }}
                title={color.name}
              />
            ))}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-3">
        {isEditing ? (
          <textarea
            ref={textareaRef}
            value={text}
            onChange={handleTextChange}
            onBlur={handleBlur}
            className="w-full h-full min-h-[100px] bg-transparent border-none outline-none resize-none text-sm"
            style={{ color: currentColor.text }}
            placeholder="Add your note here..."
          />
        ) : (
          <div
            onClick={() => setIsEditing(true)}
            className="min-h-[100px] text-sm whitespace-pre-wrap cursor-text"
            style={{ color: currentColor.text }}
          >
            {text || (
              <span className="opacity-50">Click to add note...</span>
            )}
          </div>
        )}
      </div>

      {/* Resize handle */}
      <div
        className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize opacity-50 hover:opacity-100"
        style={{ borderRight: `2px solid ${currentColor.border}`, borderBottom: `2px solid ${currentColor.border}` }}
      />
    </div>
  );
}
