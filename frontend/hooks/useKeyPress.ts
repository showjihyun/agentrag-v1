/**
 * Custom hook to detect key press
 * 
 * @param targetKey - Key to detect
 * @param handler - Handler function to call on key press
 * @param options - Options for event listener
 * 
 * @example
 * useKeyPress('Escape', () => closeModal());
 * useKeyPress('Enter', handleSubmit, { ctrlKey: true });
 */

import { useEffect } from 'react';

interface UseKeyPressOptions {
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
}

export function useKeyPress(
  targetKey: string,
  handler: () => void,
  options: UseKeyPressOptions = {}
): void {
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      const { ctrlKey = false, shiftKey = false, altKey = false, metaKey = false } = options;

      const modifiersMatch =
        event.ctrlKey === ctrlKey &&
        event.shiftKey === shiftKey &&
        event.altKey === altKey &&
        event.metaKey === metaKey;

      if (event.key === targetKey && modifiersMatch) {
        event.preventDefault();
        handler();
      }
    };

    window.addEventListener('keydown', handleKeyPress);

    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [targetKey, handler, options]);
}
