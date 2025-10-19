'use client';

import { useState, useEffect } from 'react';
import { QueryMode } from '@/lib/types';

const AUTO_MODE_KEY = 'smart-mode-enabled';
const MODE_PREFERENCE_KEY = 'query-mode-preference';
const FIRST_VISIT_KEY = 'first-visit-completed';

/**
 * Smart Mode Hook
 * 
 * Manages intelligent mode selection with:
 * - Auto mode (AI selects best mode)
 * - Manual mode (user selects)
 * - First-time user onboarding
 * - Preference persistence
 */
export function useSmartMode() {
  const [autoMode, setAutoMode] = useState(true);
  const [mode, setMode] = useState<QueryMode>('BALANCED');
  const [isFirstVisit, setIsFirstVisit] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load preferences on mount
  useEffect(() => {
    try {
      // Check if first visit
      const hasVisited = localStorage.getItem(FIRST_VISIT_KEY);
      if (!hasVisited) {
        setIsFirstVisit(true);
        localStorage.setItem(FIRST_VISIT_KEY, 'true');
      }

      // Load auto mode preference (default: true)
      const storedAutoMode = localStorage.getItem(AUTO_MODE_KEY);
      if (storedAutoMode !== null) {
        setAutoMode(storedAutoMode === 'true');
      }

      // Load mode preference
      const storedMode = localStorage.getItem(MODE_PREFERENCE_KEY);
      if (storedMode && ['FAST', 'BALANCED', 'DEEP', 'WEB_SEARCH'].includes(storedMode)) {
        setMode(storedMode as QueryMode);
      }
    } catch (error) {
      console.error('Failed to load smart mode preferences:', error);
    } finally {
      setIsLoaded(true);
    }
  }, []);

  // Update auto mode
  const updateAutoMode = (enabled: boolean) => {
    setAutoMode(enabled);
    try {
      localStorage.setItem(AUTO_MODE_KEY, enabled.toString());
    } catch (error) {
      console.error('Failed to save auto mode preference:', error);
    }
  };

  // Update mode
  const updateMode = (newMode: QueryMode) => {
    setMode(newMode);
    try {
      localStorage.setItem(MODE_PREFERENCE_KEY, newMode);
    } catch (error) {
      console.error('Failed to save mode preference:', error);
    }
  };

  // Complete first visit
  const completeFirstVisit = () => {
    setIsFirstVisit(false);
  };

  return {
    autoMode,
    setAutoMode: updateAutoMode,
    mode,
    setMode: updateMode,
    isFirstVisit,
    completeFirstVisit,
    isLoaded,
  };
}
