/**
 * useExport Hook
 * 
 * Provides PDF export functionality:
 * - Chat export
 * - Workflow report export
 * - Dashboard export
 */

import { useState, useCallback } from 'react';
import { exportsAPI, ChatExportRequest, WorkflowExportRequest } from '@/lib/api/exports';

interface UseExportReturn {
  exporting: boolean;
  error: string | null;
  exportChatToPDF: (sessionId: string, title?: string) => Promise<void>;
  exportWorkflowToPDF: (workflowId: string, includeDetails?: boolean) => Promise<void>;
  exportDashboardToPDF: () => Promise<void>;
}

export function useExport(): UseExportReturn {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exportChatToPDF = useCallback(async (sessionId: string, title?: string) => {
    try {
      setExporting(true);
      setError(null);
      
      const request: ChatExportRequest = {
        session_id: sessionId,
        title,
        include_metadata: true,
      };
      
      const blob = await exportsAPI.exportChatToPDF(request);
      const filename = `chat_export_${new Date().toISOString().slice(0, 10)}.pdf`;
      exportsAPI.downloadBlob(blob, filename);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed';
      setError(message);
      throw err;
    } finally {
      setExporting(false);
    }
  }, []);

  const exportWorkflowToPDF = useCallback(async (workflowId: string, includeDetails = true) => {
    try {
      setExporting(true);
      setError(null);
      
      const request: WorkflowExportRequest = {
        workflow_id: workflowId,
        include_details: includeDetails,
      };
      
      const blob = await exportsAPI.exportWorkflowToPDF(request);
      const filename = `workflow_report_${new Date().toISOString().slice(0, 10)}.pdf`;
      exportsAPI.downloadBlob(blob, filename);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed';
      setError(message);
      throw err;
    } finally {
      setExporting(false);
    }
  }, []);

  const exportDashboardToPDF = useCallback(async () => {
    try {
      setExporting(true);
      setError(null);
      
      const blob = await exportsAPI.exportDashboardToPDF();
      const filename = `dashboard_${new Date().toISOString().slice(0, 10)}.pdf`;
      exportsAPI.downloadBlob(blob, filename);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed';
      setError(message);
      throw err;
    } finally {
      setExporting(false);
    }
  }, []);

  return {
    exporting,
    error,
    exportChatToPDF,
    exportWorkflowToPDF,
    exportDashboardToPDF,
  };
}
