import { useEffect, useCallback } from 'react';

export interface KeyboardShortcutHandlers {
  onSave?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onExecute?: () => void;
  onStop?: () => void;
  onDelete?: () => void;
  onDuplicate?: () => void;
  onSelectAll?: () => void;
  onCopy?: () => void;
  onPaste?: () => void;
  onCut?: () => void;
  onFind?: () => void;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onZoomReset?: () => void;
  onFitView?: () => void;
}

/**
 * Check if an input element is currently focused
 */
function isInputFocused(): boolean {
  const activeElement = document.activeElement;
  return (
    activeElement instanceof HTMLInputElement ||
    activeElement instanceof HTMLTextAreaElement ||
    activeElement?.getAttribute('contenteditable') === 'true'
  );
}

/**
 * Enhanced keyboard shortcuts hook with comprehensive shortcuts
 */
export function useEnhancedKeyboardShortcuts(handlers: KeyboardShortcutHandlers) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modKey = isMac ? e.metaKey : e.ctrlKey;

      // Ctrl/Cmd + S: Save
      if (modKey && e.key === 's') {
        e.preventDefault();
        handlers.onSave?.();
        return;
      }

      // Ctrl/Cmd + Z: Undo
      if (modKey && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        handlers.onUndo?.();
        return;
      }

      // Ctrl/Cmd + Shift + Z or Ctrl/Cmd + Y: Redo
      if ((modKey && e.key === 'z' && e.shiftKey) || (modKey && e.key === 'y')) {
        e.preventDefault();
        handlers.onRedo?.();
        return;
      }

      // Ctrl/Cmd + Enter: Execute
      if (modKey && e.key === 'Enter') {
        e.preventDefault();
        handlers.onExecute?.();
        return;
      }

      // Escape: Stop/Cancel
      if (e.key === 'Escape') {
        handlers.onStop?.();
        return;
      }

      // Delete/Backspace: Delete selected (only if not in input)
      if ((e.key === 'Delete' || e.key === 'Backspace') && !isInputFocused()) {
        e.preventDefault();
        handlers.onDelete?.();
        return;
      }

      // Ctrl/Cmd + D: Duplicate
      if (modKey && e.key === 'd') {
        e.preventDefault();
        handlers.onDuplicate?.();
        return;
      }

      // Ctrl/Cmd + A: Select all (only if not in input)
      if (modKey && e.key === 'a' && !isInputFocused()) {
        e.preventDefault();
        handlers.onSelectAll?.();
        return;
      }

      // Ctrl/Cmd + C: Copy
      if (modKey && e.key === 'c' && !isInputFocused()) {
        e.preventDefault();
        handlers.onCopy?.();
        return;
      }

      // Ctrl/Cmd + V: Paste
      if (modKey && e.key === 'v' && !isInputFocused()) {
        e.preventDefault();
        handlers.onPaste?.();
        return;
      }

      // Ctrl/Cmd + X: Cut
      if (modKey && e.key === 'x' && !isInputFocused()) {
        e.preventDefault();
        handlers.onCut?.();
        return;
      }

      // Ctrl/Cmd + F: Find
      if (modKey && e.key === 'f') {
        e.preventDefault();
        handlers.onFind?.();
        return;
      }

      // Ctrl/Cmd + Plus/Equals: Zoom in
      if (modKey && (e.key === '+' || e.key === '=')) {
        e.preventDefault();
        handlers.onZoomIn?.();
        return;
      }

      // Ctrl/Cmd + Minus: Zoom out
      if (modKey && e.key === '-') {
        e.preventDefault();
        handlers.onZoomOut?.();
        return;
      }

      // Ctrl/Cmd + 0: Reset zoom
      if (modKey && e.key === '0') {
        e.preventDefault();
        handlers.onZoomReset?.();
        return;
      }

      // Ctrl/Cmd + Shift + F: Fit view
      if (modKey && e.shiftKey && e.key === 'F') {
        e.preventDefault();
        handlers.onFitView?.();
        return;
      }
    },
    [handlers]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

/**
 * Get keyboard shortcut display text based on platform
 */
export function getShortcutText(shortcut: string): string {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const modKey = isMac ? '⌘' : 'Ctrl';

  return shortcut
    .replace('Ctrl', modKey)
    .replace('Cmd', modKey)
    .replace('Shift', isMac ? '⇧' : 'Shift')
    .replace('Alt', isMac ? '⌥' : 'Alt')
    .replace('Enter', isMac ? '↵' : 'Enter');
}
