'use client';

import { useEffect, useCallback } from 'react';
import { Node, Edge } from 'reactflow';
import { toast } from 'sonner';

interface KeyboardShortcutsProps {
  nodes: Node[];
  edges: Edge[];
  selectedNodes: Node[];
  onSave: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
  onSelectAll: () => void;
  onCopy: () => void;
  onPaste: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitView: () => void;
}

export function KeyboardShortcuts({
  nodes,
  edges,
  selectedNodes,
  onSave,
  onUndo,
  onRedo,
  onDelete,
  onDuplicate,
  onSelectAll,
  onCopy,
  onPaste,
  onZoomIn,
  onZoomOut,
  onFitView,
}: KeyboardShortcutsProps) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      const isCtrl = event.ctrlKey || event.metaKey;
      const isShift = event.shiftKey;

      // Ignore if typing in input/textarea
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      // Ctrl+S - Save
      if (isCtrl && event.key === 's') {
        event.preventDefault();
        onSave();
        toast.success('Workflow saved');
      }

      // Ctrl+Z - Undo
      else if (isCtrl && !isShift && event.key === 'z') {
        event.preventDefault();
        onUndo();
        toast.info('Undo');
      }

      // Ctrl+Shift+Z or Ctrl+Y - Redo
      else if ((isCtrl && isShift && event.key === 'z') || (isCtrl && event.key === 'y')) {
        event.preventDefault();
        onRedo();
        toast.info('Redo');
      }

      // Delete or Backspace - Delete selected nodes
      else if ((event.key === 'Delete' || event.key === 'Backspace') && selectedNodes.length > 0) {
        event.preventDefault();
        onDelete();
        toast.success(`Deleted ${selectedNodes.length} node(s)`);
      }

      // Ctrl+D - Duplicate
      else if (isCtrl && event.key === 'd' && selectedNodes.length > 0) {
        event.preventDefault();
        onDuplicate();
        toast.success(`Duplicated ${selectedNodes.length} node(s)`);
      }

      // Ctrl+A - Select all
      else if (isCtrl && event.key === 'a') {
        event.preventDefault();
        onSelectAll();
        toast.info(`Selected ${nodes.length} nodes`);
      }

      // Ctrl+C - Copy
      else if (isCtrl && event.key === 'c' && selectedNodes.length > 0) {
        event.preventDefault();
        onCopy();
        toast.success(`Copied ${selectedNodes.length} node(s)`);
      }

      // Ctrl+V - Paste
      else if (isCtrl && event.key === 'v') {
        event.preventDefault();
        onPaste();
      }

      // Ctrl++ or Ctrl+= - Zoom in
      else if (isCtrl && (event.key === '+' || event.key === '=')) {
        event.preventDefault();
        onZoomIn();
      }

      // Ctrl+- - Zoom out
      else if (isCtrl && event.key === '-') {
        event.preventDefault();
        onZoomOut();
      }

      // Ctrl+0 - Fit view
      else if (isCtrl && event.key === '0') {
        event.preventDefault();
        onFitView();
        toast.info('Fit to view');
      }

      // ? - Show shortcuts help
      else if (event.key === '?' && !isCtrl && !isShift) {
        event.preventDefault();
        showShortcutsHelp();
      }
    },
    [
      nodes,
      selectedNodes,
      onSave,
      onUndo,
      onRedo,
      onDelete,
      onDuplicate,
      onSelectAll,
      onCopy,
      onPaste,
      onZoomIn,
      onZoomOut,
      onFitView,
    ]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return null;
}

function showShortcutsHelp() {
  const shortcuts = [
    { keys: 'Ctrl+S', action: 'Save workflow' },
    { keys: 'Ctrl+Z', action: 'Undo' },
    { keys: 'Ctrl+Shift+Z', action: 'Redo' },
    { keys: 'Delete', action: 'Delete selected nodes' },
    { keys: 'Ctrl+D', action: 'Duplicate selected nodes' },
    { keys: 'Ctrl+A', action: 'Select all nodes' },
    { keys: 'Ctrl+C', action: 'Copy selected nodes' },
    { keys: 'Ctrl+V', action: 'Paste nodes' },
    { keys: 'Ctrl++', action: 'Zoom in' },
    { keys: 'Ctrl+-', action: 'Zoom out' },
    { keys: 'Ctrl+0', action: 'Fit to view' },
    { keys: '?', action: 'Show this help' },
  ];

  const message = shortcuts
    .map((s) => `${s.keys}: ${s.action}`)
    .join('\n');

  toast.info('Keyboard Shortcuts', {
    description: (
      <div className="space-y-1 text-xs font-mono">
        {shortcuts.map((s, i) => (
          <div key={i} className="flex justify-between gap-4">
            <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded">
              {s.keys}
            </kbd>
            <span className="text-muted-foreground">{s.action}</span>
          </div>
        ))}
      </div>
    ),
    duration: 10000,
  });
}
