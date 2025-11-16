import { useEffect, useRef, useCallback } from 'react';

interface AutoSaveOptions<T> {
  data: T;
  onSave: (data: T) => Promise<void>;
  delay?: number; // milliseconds
  enabled?: boolean;
  storageKey?: string; // for localStorage backup
}

export function useAutoSave<T>({
  data,
  onSave,
  delay = 5000,
  enabled = true,
  storageKey,
}: AutoSaveOptions<T>) {
  const timeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const lastSavedRef = useRef<string | undefined>(undefined);
  const isSavingRef = useRef(false);

  // Save to localStorage as backup
  const saveToLocalStorage = useCallback(() => {
    if (storageKey) {
      try {
        localStorage.setItem(storageKey, JSON.stringify({
          data,
          timestamp: Date.now(),
        }));
        if (process.env.NODE_ENV === 'development') {
          console.log('💾 Auto-saved to localStorage:', storageKey);
        }
      } catch (error) {
        console.error('Failed to save to localStorage:', error);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storageKey]);

  // Restore from localStorage
  const restoreFromLocalStorage = useCallback((): T | null => {
    if (!storageKey) return null;

    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const { data: savedData, timestamp } = JSON.parse(saved);
        const age = Date.now() - timestamp;
        
        // Only restore if less than 1 hour old
        if (age < 60 * 60 * 1000) {
          if (process.env.NODE_ENV === 'development') {
            console.log('📂 Restored from localStorage:', storageKey);
          }
          return savedData;
        } else {
          localStorage.removeItem(storageKey);
        }
      }
    } catch (error) {
      console.error('Failed to restore from localStorage:', error);
    }

    return null;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Clear localStorage backup
  const clearLocalStorage = useCallback(() => {
    if (storageKey) {
      localStorage.removeItem(storageKey);
      if (process.env.NODE_ENV === 'development') {
        console.log('🗑️ Cleared localStorage:', storageKey);
      }
    }
  }, [storageKey]);

  // Auto-save effect
  useEffect(() => {
    if (!enabled) return;

    const dataString = JSON.stringify(data);
    
    // Skip if data hasn't changed
    if (dataString === lastSavedRef.current) return;

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Save to localStorage immediately
    saveToLocalStorage();

    // Schedule server save
    timeoutRef.current = setTimeout(async () => {
      if (isSavingRef.current) return;

      try {
        isSavingRef.current = true;
        await onSave(data);
        lastSavedRef.current = dataString;
        if (process.env.NODE_ENV === 'development') {
          console.log('✅ Auto-saved to server');
        }
        
        // Clear localStorage backup after successful server save
        clearLocalStorage();
      } catch (error) {
        console.error('❌ Auto-save failed:', error);
        // Keep localStorage backup on failure
      } finally {
        isSavingRef.current = false;
      }
    }, delay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [data, enabled, delay, onSave, saveToLocalStorage, clearLocalStorage]);

  return {
    restoreFromLocalStorage,
    clearLocalStorage,
  };
}
