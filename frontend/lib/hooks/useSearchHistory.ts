'use client';

import { useState, useEffect } from 'react';

const SEARCH_HISTORY_KEY = 'agentic-rag-search-history';
const MAX_HISTORY_ITEMS = 10;

export interface SearchHistoryItem {
  query: string;
  timestamp: number;
}

export function useSearchHistory() {
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = () => {
    try {
      const stored = localStorage.getItem(SEARCH_HISTORY_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setHistory(parsed);
      }
    } catch (error) {
      console.error('Failed to load search history:', error);
    }
  };

  const addToHistory = (query: string) => {
    if (!query.trim()) return;

    const newItem: SearchHistoryItem = {
      query: query.trim(),
      timestamp: Date.now(),
    };

    // Remove duplicates and add to front
    const filtered = history.filter(item => 
      item.query.toLowerCase() !== query.toLowerCase()
    );
    
    const updated = [newItem, ...filtered].slice(0, MAX_HISTORY_ITEMS);
    
    setHistory(updated);
    
    try {
      localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(updated));
    } catch (error) {
      console.error('Failed to save search history:', error);
    }
  };

  const removeFromHistory = (query: string) => {
    const updated = history.filter(item => item.query !== query);
    setHistory(updated);
    
    try {
      localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(updated));
    } catch (error) {
      console.error('Failed to update search history:', error);
    }
  };

  const clearHistory = () => {
    setHistory([]);
    try {
      localStorage.removeItem(SEARCH_HISTORY_KEY);
    } catch (error) {
      console.error('Failed to clear search history:', error);
    }
  };

  return {
    history,
    addToHistory,
    removeFromHistory,
    clearHistory,
  };
}
