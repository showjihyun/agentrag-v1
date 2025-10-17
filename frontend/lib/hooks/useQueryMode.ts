'use client';

import { useState, useEffect } from 'react';
import { QueryMode } from '@/lib/types';

const STORAGE_KEY = 'query-mode-preference';
const DEFAULT_MODE: QueryMode = 'BALANCED';

/**
 * Custom hook for managing query mode with localStorage persistence.
 */
export function useQueryMode() {
  const [mode, setMode] = useState<QueryMode>(DEFAULT_MODE);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load mode from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && ['FAST', 'BALANCED', 'DEEP'].includes(stored)) {
        setMode(stored as QueryMode);
      }
    } catch (error) {
      console.error('Failed to load query mode from localStorage:', error);
    } finally {
      setIsLoaded(true);
    }
  }, []);

  // Save mode to localStorage when it changes
  const updateMode = (newMode: QueryMode) => {
    setMode(newMode);
    try {
      localStorage.setItem(STORAGE_KEY, newMode);
    } catch (error) {
      console.error('Failed to save query mode to localStorage:', error);
    }
  };

  return {
    mode,
    setMode: updateMode,
    isLoaded,
  };
}
