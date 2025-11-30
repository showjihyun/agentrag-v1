/**
 * useDashboard Hook
 * 
 * Provides dashboard layout management:
 * - Load/save layouts
 * - Widget CRUD operations
 * - Drag and drop support
 */

import { useState, useEffect, useCallback } from 'react';
import { dashboardAPI, DashboardLayout, DashboardWidget, AddWidgetRequest, UpdateWidgetRequest } from '@/lib/api/dashboard';

interface UseDashboardReturn {
  layout: DashboardLayout | null;
  widgets: DashboardWidget[];
  loading: boolean;
  error: string | null;
  isDirty: boolean;
  refreshLayout: () => Promise<void>;
  saveLayout: () => Promise<void>;
  resetLayout: () => Promise<void>;
  addWidget: (request: AddWidgetRequest) => Promise<void>;
  updateWidget: (widgetId: string, updates: UpdateWidgetRequest) => Promise<void>;
  removeWidget: (widgetId: string) => Promise<void>;
  moveWidget: (widgetId: string, x: number, y: number) => void;
  resizeWidget: (widgetId: string, width: number, height: number) => void;
}

export function useDashboard(): UseDashboardReturn {
  const [layout, setLayout] = useState<DashboardLayout | null>(null);
  const [widgets, setWidgets] = useState<DashboardWidget[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState(false);

  const refreshLayout = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dashboardAPI.getLayout();
      setLayout(data);
      setWidgets(data.widgets);
      setIsDirty(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  const saveLayout = useCallback(async () => {
    if (!layout) return;
    try {
      setLoading(true);
      await dashboardAPI.saveLayout({ ...layout, widgets });
      setIsDirty(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save dashboard');
    } finally {
      setLoading(false);
    }
  }, [layout, widgets]);

  const resetLayout = useCallback(async () => {
    try {
      setLoading(true);
      const data = await dashboardAPI.resetLayout();
      setLayout(data);
      setWidgets(data.widgets);
      setIsDirty(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  const addWidget = useCallback(async (request: AddWidgetRequest) => {
    try {
      const widget = await dashboardAPI.addWidget(request);
      setWidgets(prev => [...prev, widget]);
      setIsDirty(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add widget');
    }
  }, []);

  const updateWidget = useCallback(async (widgetId: string, updates: UpdateWidgetRequest) => {
    try {
      const updated = await dashboardAPI.updateWidget(widgetId, updates);
      setWidgets(prev => prev.map(w => w.id === widgetId ? updated : w));
      setIsDirty(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update widget');
    }
  }, []);

  const removeWidget = useCallback(async (widgetId: string) => {
    try {
      await dashboardAPI.removeWidget(widgetId);
      setWidgets(prev => prev.filter(w => w.id !== widgetId));
      setIsDirty(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove widget');
    }
  }, []);

  const moveWidget = useCallback((widgetId: string, x: number, y: number) => {
    setWidgets(prev => prev.map(w => w.id === widgetId ? { ...w, x, y } : w));
    setIsDirty(true);
  }, []);

  const resizeWidget = useCallback((widgetId: string, width: number, height: number) => {
    setWidgets(prev => prev.map(w => w.id === widgetId ? { ...w, width, height } : w));
    setIsDirty(true);
  }, []);

  useEffect(() => {
    refreshLayout();
  }, [refreshLayout]);

  return {
    layout,
    widgets,
    loading,
    error,
    isDirty,
    refreshLayout,
    saveLayout,
    resetLayout,
    addWidget,
    updateWidget,
    removeWidget,
    moveWidget,
    resizeWidget,
  };
}
