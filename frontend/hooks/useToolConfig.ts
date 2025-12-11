/**
 * useToolConfig - Common hook for Tool Configuration components
 * 
 * Provides:
 * - Type-safe config state management
 * - Automatic onChange synchronization
 * - updateConfig helper with proper memoization
 * - Prevents infinite loops with proper dependency handling
 */

import { useState, useCallback, useRef, useEffect } from 'react';

export interface UseToolConfigOptions<T> {
  /** Initial data from parent */
  initialData: Partial<T>;
  /** Default values for the config */
  defaults: T;
  /** Callback when config changes */
  onChange: (config: T) => void;
  /** Optional: debounce delay in ms (default: 0) */
  debounceMs?: number;
}

export interface UseToolConfigReturn<T> {
  /** Current config state */
  config: T;
  /** Update a single field */
  updateField: <K extends keyof T>(key: K, value: T[K]) => void;
  /** Update multiple fields at once */
  updateFields: (updates: Partial<T>) => void;
  /** Reset to defaults */
  resetToDefaults: () => void;
  /** Check if config has been modified from initial */
  isDirty: boolean;
}

export function useToolConfig<T extends object>({
  initialData,
  defaults,
  onChange,
  debounceMs = 0,
}: UseToolConfigOptions<T>): UseToolConfigReturn<T> {
  // Merge defaults with initial data
  const [config, setConfig] = useState<T>(() => ({
    ...defaults,
    ...initialData,
  }));

  // Track initial config for dirty checking
  const initialConfigRef = useRef<T>({ ...defaults, ...initialData });
  
  // Track if this is the first render
  const isFirstRender = useRef(true);
  
  // Debounce timer ref
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Sync config changes to parent (skip first render)
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    if (debounceMs > 0) {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      debounceTimerRef.current = setTimeout(() => {
        onChange(config);
      }, debounceMs);
    } else {
      onChange(config);
    }

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [config, onChange, debounceMs]);

  // Update a single field
  const updateField = useCallback(<K extends keyof T>(key: K, value: T[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  }, []);

  // Update multiple fields at once
  const updateFields = useCallback((updates: Partial<T>) => {
    setConfig((prev) => ({ ...prev, ...updates }));
  }, []);

  // Reset to defaults
  const resetToDefaults = useCallback(() => {
    setConfig(defaults);
  }, [defaults]);

  // Check if config has been modified
  const isDirty = JSON.stringify(config) !== JSON.stringify(initialConfigRef.current);

  return {
    config,
    updateField,
    updateFields,
    resetToDefaults,
    isDirty,
  };
}

// ============================================
// Array Field Helpers
// ============================================

export interface ArrayFieldHelpers<T> {
  items: T[];
  addItem: (item: T) => void;
  updateItem: (index: number, updates: Partial<T>) => void;
  removeItem: (index: number) => void;
  moveItem: (fromIndex: number, toIndex: number) => void;
}

export function useArrayField<T>(
  items: T[],
  setItems: (items: T[]) => void
): ArrayFieldHelpers<T> {
  const addItem = useCallback((item: T) => {
    setItems([...items, item]);
  }, [items, setItems]);

  const updateItem = useCallback((index: number, updates: Partial<T>) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], ...updates };
    setItems(newItems);
  }, [items, setItems]);

  const removeItem = useCallback((index: number) => {
    setItems(items.filter((_, i) => i !== index));
  }, [items, setItems]);

  const moveItem = useCallback((fromIndex: number, toIndex: number) => {
    const newItems = [...items];
    const [removed] = newItems.splice(fromIndex, 1);
    newItems.splice(toIndex, 0, removed);
    setItems(newItems);
  }, [items, setItems]);

  return { items, addItem, updateItem, removeItem, moveItem };
}
