'use client';

/**
 * Workflow Context Menu
 * 
 * Right-click context menu with:
 * - Node actions (copy, paste, delete, duplicate)
 * - Canvas actions (add node, auto-layout, fit view)
 * - Keyboard shortcuts display
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@/lib/utils';
import {
  Copy,
  Clipboard,
  Trash2,
  Copy as Duplicate,
  Settings,
  Eye,
  EyeOff,
  Play,
  Plus,
  LayoutGrid,
  Maximize,
  ZoomIn,
  ZoomOut,
  Undo,
  Redo,
  AlignHorizontalJustifyCenter,
  AlignVerticalJustifyCenter,
} from 'lucide-react';

interface MenuItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  shortcut?: string;
  disabled?: boolean;
  danger?: boolean;
  separator?: boolean;
  onClick?: () => void;
}

interface ContextMenuProps {
  x: number;
  y: number;
  type: 'node' | 'canvas' | 'edge';
  targetId?: string;
  onClose: () => void;
  // Node actions
  onCopyNode?: (nodeId: string) => void;
  onPasteNode?: (x: number, y: number) => void;
  onDeleteNode?: (nodeId: string) => void;
  onDuplicateNode?: (nodeId: string) => void;
  onConfigureNode?: (nodeId: string) => void;
  onToggleNodeEnabled?: (nodeId: string) => void;
  onRunFromNode?: (nodeId: string) => void;
  // Canvas actions
  onAddNode?: (x: number, y: number) => void;
  onAutoLayout?: () => void;
  onFitView?: () => void;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onAlignHorizontal?: () => void;
  onAlignVertical?: () => void;
  // Edge actions
  onDeleteEdge?: (edgeId: string) => void;
  // State
  canPaste?: boolean;
  canUndo?: boolean;
  canRedo?: boolean;
  isNodeEnabled?: boolean;
  hasSelection?: boolean;
}

export function WorkflowContextMenu({
  x,
  y,
  type,
  targetId,
  onClose,
  onCopyNode,
  onPasteNode,
  onDeleteNode,
  onDuplicateNode,
  onConfigureNode,
  onToggleNodeEnabled,
  onRunFromNode,
  onAddNode,
  onAutoLayout,
  onFitView,
  onZoomIn,
  onZoomOut,
  onUndo,
  onRedo,
  onAlignHorizontal,
  onAlignVertical,
  onDeleteEdge,
  canPaste = false,
  canUndo = false,
  canRedo = false,
  isNodeEnabled = true,
  hasSelection = false,
}: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ x, y });
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Adjust position to keep menu in viewport
  useEffect(() => {
    if (!menuRef.current) return;

    const rect = menuRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let newX = x;
    let newY = y;

    if (x + rect.width > viewportWidth - 10) {
      newX = viewportWidth - rect.width - 10;
    }
    if (y + rect.height > viewportHeight - 10) {
      newY = viewportHeight - rect.height - 10;
    }

    setPosition({ x: newX, y: newY });
  }, [x, y]);

  // Close on click outside or escape
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  const handleItemClick = useCallback((item: MenuItem) => {
    if (item.disabled) return;
    item.onClick?.();
    onClose();
  }, [onClose]);

  // Build menu items based on context type
  const getMenuItems = (): MenuItem[] => {
    if (type === 'node' && targetId) {
      return [
        {
          id: 'configure',
          label: 'Configure',
          icon: <Settings className="h-4 w-4" />,
          shortcut: 'Enter',
          onClick: () => onConfigureNode?.(targetId),
        },
        {
          id: 'toggle-enabled',
          label: isNodeEnabled ? 'Disable Node' : 'Enable Node',
          icon: isNodeEnabled ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />,
          onClick: () => onToggleNodeEnabled?.(targetId),
        },
        { id: 'sep1', label: '', separator: true },
        {
          id: 'run-from',
          label: 'Run from here',
          icon: <Play className="h-4 w-4" />,
          onClick: () => onRunFromNode?.(targetId),
        },
        { id: 'sep2', label: '', separator: true },
        {
          id: 'copy',
          label: 'Copy',
          icon: <Copy className="h-4 w-4" />,
          shortcut: 'Ctrl+C',
          onClick: () => onCopyNode?.(targetId),
        },
        {
          id: 'duplicate',
          label: 'Duplicate',
          icon: <Duplicate className="h-4 w-4" />,
          shortcut: 'Ctrl+D',
          onClick: () => onDuplicateNode?.(targetId),
        },
        { id: 'sep3', label: '', separator: true },
        {
          id: 'delete',
          label: 'Delete',
          icon: <Trash2 className="h-4 w-4" />,
          shortcut: 'Del',
          danger: true,
          onClick: () => onDeleteNode?.(targetId),
        },
      ];
    }

    if (type === 'edge' && targetId) {
      return [
        {
          id: 'delete-edge',
          label: 'Delete Connection',
          icon: <Trash2 className="h-4 w-4" />,
          danger: true,
          onClick: () => onDeleteEdge?.(targetId),
        },
      ];
    }

    // Canvas context menu
    return [
      {
        id: 'add-node',
        label: 'Add Node',
        icon: <Plus className="h-4 w-4" />,
        onClick: () => onAddNode?.(x, y),
      },
      {
        id: 'paste',
        label: 'Paste',
        icon: <Clipboard className="h-4 w-4" />,
        shortcut: 'Ctrl+V',
        disabled: !canPaste,
        onClick: () => onPasteNode?.(x, y),
      },
      { id: 'sep1', label: '', separator: true },
      {
        id: 'undo',
        label: 'Undo',
        icon: <Undo className="h-4 w-4" />,
        shortcut: 'Ctrl+Z',
        disabled: !canUndo,
        onClick: onUndo,
      },
      {
        id: 'redo',
        label: 'Redo',
        icon: <Redo className="h-4 w-4" />,
        shortcut: 'Ctrl+Y',
        disabled: !canRedo,
        onClick: onRedo,
      },
      { id: 'sep2', label: '', separator: true },
      {
        id: 'align-h',
        label: 'Align Horizontal',
        icon: <AlignHorizontalJustifyCenter className="h-4 w-4" />,
        disabled: !hasSelection,
        onClick: onAlignHorizontal,
      },
      {
        id: 'align-v',
        label: 'Align Vertical',
        icon: <AlignVerticalJustifyCenter className="h-4 w-4" />,
        disabled: !hasSelection,
        onClick: onAlignVertical,
      },
      {
        id: 'auto-layout',
        label: 'Auto Layout',
        icon: <LayoutGrid className="h-4 w-4" />,
        onClick: onAutoLayout,
      },
      { id: 'sep3', label: '', separator: true },
      {
        id: 'fit-view',
        label: 'Fit to View',
        icon: <Maximize className="h-4 w-4" />,
        onClick: onFitView,
      },
      {
        id: 'zoom-in',
        label: 'Zoom In',
        icon: <ZoomIn className="h-4 w-4" />,
        shortcut: 'Ctrl++',
        onClick: onZoomIn,
      },
      {
        id: 'zoom-out',
        label: 'Zoom Out',
        icon: <ZoomOut className="h-4 w-4" />,
        shortcut: 'Ctrl+-',
        onClick: onZoomOut,
      },
    ];
  };

  const menuItems = getMenuItems();

  if (!isMounted) return null;

  return createPortal(
    <div
      ref={menuRef}
      className={cn(
        'fixed z-[10000] min-w-[200px] py-1',
        'bg-popover border rounded-lg shadow-lg',
        'animate-in fade-in zoom-in-95 duration-100'
      )}
      style={{ left: position.x, top: position.y }}
      role="menu"
      aria-label="Context menu"
    >
      {menuItems.map((item) => {
        if (item.separator) {
          return <div key={item.id} className="my-1 h-px bg-border" role="separator" />;
        }

        return (
          <button
            key={item.id}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 text-sm',
              'hover:bg-accent transition-colors',
              'focus:outline-none focus:bg-accent',
              item.disabled && 'opacity-50 cursor-not-allowed',
              item.danger && 'text-destructive hover:bg-destructive/10'
            )}
            onClick={() => handleItemClick(item)}
            disabled={item.disabled}
            role="menuitem"
          >
            {item.icon && (
              <span className={cn('flex-shrink-0', item.danger ? 'text-destructive' : 'text-muted-foreground')}>
                {item.icon}
              </span>
            )}
            <span className="flex-1 text-left">{item.label}</span>
            {item.shortcut && (
              <kbd className="ml-auto text-xs text-muted-foreground font-mono">
                {item.shortcut}
              </kbd>
            )}
          </button>
        );
      })}
    </div>,
    document.body
  );
}

// Hook for managing context menu state
export function useContextMenu() {
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    type: 'node' | 'canvas' | 'edge';
    targetId?: string;
  } | null>(null);

  const showContextMenu = useCallback((
    e: React.MouseEvent,
    type: 'node' | 'canvas' | 'edge',
    targetId?: string
  ) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({ x: e.clientX, y: e.clientY, type, targetId });
  }, []);

  const hideContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  return { contextMenu, showContextMenu, hideContextMenu };
}
