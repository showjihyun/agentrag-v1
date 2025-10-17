'use client';

import { useState, useEffect } from 'react';

const UPLOAD_HISTORY_KEY = 'agentic-rag-upload-history';
const MAX_HISTORY_ITEMS = 50;

export interface UploadHistoryItem {
  id: string;
  filename: string;
  fileSize: number;
  status: 'success' | 'failed' | 'cancelled' | 'processing';
  timestamp: number;
  errorMessage?: string;
  documentId?: string;
  processingStage?: 'uploading' | 'embedding' | 'indexing' | 'completed';
  progress?: number;
}

export function useUploadHistory() {
  const [history, setHistory] = useState<UploadHistoryItem[]>([]);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = () => {
    try {
      const stored = localStorage.getItem(UPLOAD_HISTORY_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setHistory(parsed);
      }
    } catch (error) {
      console.error('Failed to load upload history:', error);
    }
  };

  const addToHistory = (item: UploadHistoryItem) => {
    const updated = [item, ...history].slice(0, MAX_HISTORY_ITEMS);
    setHistory(updated);
    saveHistory(updated);
  };

  const updateHistoryItem = (id: string, updates: Partial<UploadHistoryItem>) => {
    const updated = history.map(item =>
      item.id === id ? { ...item, ...updates } : item
    );
    setHistory(updated);
    saveHistory(updated);
  };

  const removeFromHistory = (id: string) => {
    const updated = history.filter(item => item.id !== id);
    setHistory(updated);
    saveHistory(updated);
  };

  const clearHistory = () => {
    setHistory([]);
    try {
      localStorage.removeItem(UPLOAD_HISTORY_KEY);
    } catch (error) {
      console.error('Failed to clear upload history:', error);
    }
  };

  const saveHistory = (items: UploadHistoryItem[]) => {
    try {
      localStorage.setItem(UPLOAD_HISTORY_KEY, JSON.stringify(items));
    } catch (error) {
      console.error('Failed to save upload history:', error);
    }
  };

  const getStats = () => {
    const total = history.length;
    const successful = history.filter(h => h.status === 'success').length;
    const failed = history.filter(h => h.status === 'failed').length;
    const cancelled = history.filter(h => h.status === 'cancelled').length;
    const processing = history.filter(h => h.status === 'processing').length;

    return { total, successful, failed, cancelled, processing };
  };

  return {
    history,
    addToHistory,
    updateHistoryItem,
    removeFromHistory,
    clearHistory,
    getStats,
  };
}
