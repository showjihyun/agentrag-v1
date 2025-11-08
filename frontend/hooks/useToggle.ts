/**
 * Custom hook for managing boolean toggle state
 * 
 * @param initialState - Initial state (default: false)
 * @returns Object with state and toggle functions
 * 
 * @example
 * const { isOpen, open, close, toggle } = useToggle();
 */

import { useState, useCallback } from 'react';

interface UseToggleReturn {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  setIsOpen: (value: boolean) => void;
}

export function useToggle(initialState = false): UseToggleReturn {
  const [isOpen, setIsOpen] = useState<boolean>(initialState);

  const open = useCallback(() => {
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
  }, []);

  const toggle = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  return {
    isOpen,
    open,
    close,
    toggle,
    setIsOpen,
  };
}
