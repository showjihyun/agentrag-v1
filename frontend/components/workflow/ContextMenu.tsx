'use client';

import React, { useEffect, useRef } from 'react';
import { Copy, Files, Trash2, Group, AlignCenter, AlignLeft, AlignRight, StickyNote } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ContextMenuItem {
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  action: () => void;
  disabled?: boolean;
  separator?: boolean;
  danger?: boolean;
}

interface ContextMenuProps {
  x: number;
  y: number;
  items: ContextMenuItem[];
  onClose: () => void;
}

export function ContextMenu({ x, y, items, onClose }: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  // Adjust position if menu would go off screen
  useEffect(() => {
    if (menuRef.current) {
      const rect = menuRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      let adjustedX = x;
      let adjustedY = y;

      if (rect.right > viewportWidth) {
        adjustedX = viewportWidth - rect.width - 10;
      }

      if (rect.bottom > viewportHeight) {
        adjustedY = viewportHeight - rect.height - 10;
      }

      menuRef.current.style.left = `${adjustedX}px`;
      menuRef.current.style.top = `${adjustedY}px`;
    }
  }, [x, y]);

  return (
    <div
      ref={menuRef}
      className="fixed z-50 min-w-[200px] rounded-md border bg-white shadow-lg dark:bg-gray-800 dark:border-gray-700"
      style={{ left: x, top: y }}
    >
      <div className="py-1">
        {items.map((item, index) => {
          if (item.separator) {
            return (
              <div
                key={`separator-${index}`}
                className="my-1 h-px bg-gray-200 dark:bg-gray-700"
              />
            );
          }

          const Icon = item.icon;

          return (
            <button
              key={index}
              onClick={() => {
                if (!item.disabled) {
                  item.action();
                  onClose();
                }
              }}
              disabled={item.disabled}
              className={cn(
                'flex w-full items-center gap-2 px-3 py-2 text-sm transition-colors',
                'hover:bg-gray-100 dark:hover:bg-gray-700',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                item.danger && 'text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20'
              )}
            >
              {Icon && <Icon className="h-4 w-4" />}
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// Node context menu items
export const getNodeContextMenuItems = (
  selectedNodes: any[],
  handlers: {
    onCopy: () => void;
    onDuplicate: () => void;
    onDelete: () => void;
    onGroup: () => void;
    onAlignHorizontal: () => void;
    onAlignVertical: () => void;
    onAddNote: () => void;
  }
): ContextMenuItem[] => {
  const multipleSelected = selectedNodes.length > 1;

  return [
    {
      label: 'Copy',
      icon: Copy,
      action: handlers.onCopy,
    },
    {
      label: 'Duplicate',
      icon: Files,
      action: handlers.onDuplicate,
    },
    {
      separator: true,
    },
    {
      label: 'Add Note',
      icon: StickyNote,
      action: handlers.onAddNote,
      disabled: multipleSelected,
    },
    {
      separator: true,
    },
    {
      label: 'Align Horizontal',
      icon: AlignCenter,
      action: handlers.onAlignHorizontal,
      disabled: !multipleSelected,
    },
    {
      label: 'Align Vertical',
      icon: AlignLeft,
      action: handlers.onAlignVertical,
      disabled: !multipleSelected,
    },
    {
      label: 'Group Nodes',
      icon: Group,
      action: handlers.onGroup,
      disabled: !multipleSelected,
    },
    {
      separator: true,
    },
    {
      label: 'Delete',
      icon: Trash2,
      action: handlers.onDelete,
      danger: true,
    },
  ];
};

// Canvas context menu items
export const getCanvasContextMenuItems = (
  handlers: {
    onPaste: () => void;
    onSelectAll: () => void;
    onFitView: () => void;
  },
  hasClipboard: boolean
): ContextMenuItem[] => {
  return [
    {
      label: 'Paste',
      icon: Copy,
      action: handlers.onPaste,
      disabled: !hasClipboard,
    },
    {
      separator: true,
    },
    {
      label: 'Select All',
      action: handlers.onSelectAll,
    },
    {
      label: 'Fit View',
      icon: Maximize,
      action: handlers.onFitView,
    },
  ];
};
