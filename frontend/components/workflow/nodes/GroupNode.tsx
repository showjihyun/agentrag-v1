'use client';

import React, { useState } from 'react';
import { NodeProps, NodeResizer } from 'reactflow';
import { Folder, FolderOpen, Edit2, Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface GroupNodeData {
  label?: string;
  color?: string;
  collapsed?: boolean;
  onUpdate?: (data: Partial<GroupNodeData>) => void;
}

const GROUP_COLORS = [
  { name: 'Blue', bg: 'rgba(59, 130, 246, 0.05)', border: '#3b82f6' },
  { name: 'Green', bg: 'rgba(16, 185, 129, 0.05)', border: '#10b981' },
  { name: 'Purple', bg: 'rgba(168, 85, 247, 0.05)', border: '#a855f7' },
  { name: 'Orange', bg: 'rgba(249, 115, 22, 0.05)', border: '#f97316' },
  { name: 'Pink', bg: 'rgba(236, 72, 153, 0.05)', border: '#ec4899' },
  { name: 'Gray', bg: 'rgba(107, 114, 128, 0.05)', border: '#6b7280' },
];

export default function GroupNode({ data, selected }: NodeProps<GroupNodeData>) {
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [label, setLabel] = useState(data.label || 'Group');
  const [collapsed, setCollapsed] = useState(data.collapsed || false);

  const currentColor = GROUP_COLORS.find(c => c.name === data.color) || GROUP_COLORS[0];

  const handleLabelSave = () => {
    setIsEditingLabel(false);
    if (label !== data.label) {
      data.onUpdate?.({ label });
    }
  };

  const handleLabelCancel = () => {
    setIsEditingLabel(false);
    setLabel(data.label || 'Group');
  };

  const toggleCollapse = () => {
    const newCollapsed = !collapsed;
    setCollapsed(newCollapsed);
    data.onUpdate?.({ collapsed: newCollapsed });
  };

  return (
    <>
      <NodeResizer
        color={currentColor.border}
        isVisible={selected}
        minWidth={200}
        minHeight={150}
      />
      
      <div
        className={cn(
          'group-node relative rounded-xl transition-all',
          selected && 'ring-2 ring-offset-2',
          collapsed && 'opacity-50'
        )}
        style={{
          backgroundColor: currentColor.bg,
          borderColor: currentColor.border,
          borderWidth: '2px',
          borderStyle: 'dashed',
          width: '100%',
          height: '100%',
          minWidth: 200,
          minHeight: 150,
          ringColor: currentColor.border,
        }}
      >
        {/* Header */}
        <div
          className="absolute -top-8 left-0 right-0 flex items-center justify-between px-3 py-1 rounded-t-lg"
          style={{
            backgroundColor: currentColor.border,
            color: 'white',
          }}
        >
          <div className="flex items-center gap-2">
            <button
              onClick={toggleCollapse}
              className="p-1 rounded hover:bg-white/20 transition-colors"
              title={collapsed ? 'Expand group' : 'Collapse group'}
            >
              {collapsed ? (
                <Folder className="h-4 w-4" />
              ) : (
                <FolderOpen className="h-4 w-4" />
              )}
            </button>

            {isEditingLabel ? (
              <div className="flex items-center gap-1">
                <input
                  type="text"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleLabelSave();
                    if (e.key === 'Escape') handleLabelCancel();
                  }}
                  className="px-2 py-0.5 text-sm bg-white/20 border border-white/30 rounded outline-none"
                  autoFocus
                />
                <button
                  onClick={handleLabelSave}
                  className="p-1 rounded hover:bg-white/20"
                >
                  <Check className="h-3 w-3" />
                </button>
                <button
                  onClick={handleLabelCancel}
                  className="p-1 rounded hover:bg-white/20"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{label}</span>
                <button
                  onClick={() => setIsEditingLabel(true)}
                  className="p-1 rounded hover:bg-white/20 transition-colors opacity-0 group-hover:opacity-100"
                >
                  <Edit2 className="h-3 w-3" />
                </button>
              </div>
            )}
          </div>

          <div className="text-xs opacity-75">
            Group
          </div>
        </div>

        {/* Content area - child nodes will be rendered here */}
        {!collapsed && (
          <div className="absolute inset-0 pointer-events-none">
            {/* This is just a visual container, child nodes are positioned independently */}
          </div>
        )}

        {/* Collapsed indicator */}
        {collapsed && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-sm opacity-50">
              Group collapsed
            </div>
          </div>
        )}
      </div>
    </>
  );
}
