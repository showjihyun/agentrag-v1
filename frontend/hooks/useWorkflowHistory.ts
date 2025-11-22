import { useState, useCallback, useEffect } from 'react';
import { Node, Edge } from 'reactflow';

export interface HistoryState {
  nodes: Node[];
  edges: Edge[];
  timestamp: Date;
}

interface UseWorkflowHistoryOptions {
  maxSize?: number;
  persistToStorage?: boolean;
  storageKey?: string;
}

/**
 * Enhanced workflow history hook with localStorage persistence
 */
export function useWorkflowHistory(options: UseWorkflowHistoryOptions = {}) {
  const {
    maxSize = 50,
    persistToStorage = true,
    storageKey = 'workflow-history',
  } = options;

  // Initialize history from localStorage if available
  const [history, setHistory] = useState<HistoryState[]>(() => {
    if (persistToStorage && typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem(storageKey);
        if (saved) {
          const parsed = JSON.parse(saved);
          // Convert timestamp strings back to Date objects
          return parsed.map((item: any) => ({
            ...item,
            timestamp: new Date(item.timestamp),
          }));
        }
      } catch (error) {
        console.error('Failed to load history from localStorage:', error);
      }
    }
    return [];
  });

  const [currentIndex, setCurrentIndex] = useState(history.length - 1);

  // Save to localStorage whenever history changes
  useEffect(() => {
    if (persistToStorage && typeof window !== 'undefined') {
      try {
        localStorage.setItem(storageKey, JSON.stringify(history));
      } catch (error) {
        console.error('Failed to save history to localStorage:', error);
      }
    }
  }, [history, persistToStorage, storageKey]);

  const push = useCallback(
    (state: Omit<HistoryState, 'timestamp'>) => {
      setHistory((prev) => {
        // Remove any history after current index (when undoing then making new changes)
        const newHistory = prev.slice(0, currentIndex + 1);

        // Add new state with timestamp
        newHistory.push({
          ...state,
          timestamp: new Date(),
        });

        // Limit history size
        if (newHistory.length > maxSize) {
          newHistory.shift();
          setCurrentIndex((idx) => Math.max(0, idx - 1));
        } else {
          setCurrentIndex(newHistory.length - 1);
        }

        return newHistory;
      });
    },
    [currentIndex, maxSize]
  );

  const undo = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex((idx) => idx - 1);
      return history[currentIndex - 1];
    }
    return null;
  }, [currentIndex, history]);

  const redo = useCallback(() => {
    if (currentIndex < history.length - 1) {
      setCurrentIndex((idx) => idx + 1);
      return history[currentIndex + 1];
    }
    return null;
  }, [currentIndex, history]);

  const canUndo = useCallback(() => {
    return currentIndex > 0;
  }, [currentIndex]);

  const canRedo = useCallback(() => {
    return currentIndex < history.length - 1;
  }, [currentIndex, history.length]);

  const clear = useCallback(() => {
    setHistory([]);
    setCurrentIndex(-1);
    if (persistToStorage && typeof window !== 'undefined') {
      localStorage.removeItem(storageKey);
    }
  }, [persistToStorage, storageKey]);

  const getCurrentState = useCallback(() => {
    return history[currentIndex] || null;
  }, [history, currentIndex]);

  const getHistorySize = useCallback(() => {
    return history.length;
  }, [history.length]);

  const jumpTo = useCallback(
    (index: number) => {
      if (index >= 0 && index < history.length) {
        setCurrentIndex(index);
        return history[index];
      }
      return null;
    },
    [history]
  );

  return {
    history,
    currentIndex,
    push,
    undo,
    redo,
    canUndo,
    canRedo,
    clear,
    getCurrentState,
    getHistorySize,
    jumpTo,
  };
}
