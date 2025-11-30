/**
 * Exports API Client
 * 
 * Provides methods for exporting data to PDF:
 * - Chat history export
 * - Workflow reports
 * - Dashboard export
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

export interface ChatExportRequest {
  session_id: string;
  title?: string;
  include_metadata?: boolean;
}

export interface WorkflowExportRequest {
  workflow_id: string;
  include_details?: boolean;
  date_from?: string;
  date_to?: string;
}

// ============================================================================
// API Client
// ============================================================================

class ExportsAPI {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  // Export chat to PDF
  async exportChatToPDF(request: ChatExportRequest): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/api/exports/chat/pdf`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Export failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.blob();
  }

  // Export workflow report to PDF
  async exportWorkflowToPDF(request: WorkflowExportRequest): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/api/exports/workflow/pdf`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Export failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.blob();
  }

  // Export dashboard to PDF
  async exportDashboardToPDF(): Promise<Blob> {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('user_id') || 'default';
    
    const response = await fetch(`${API_BASE_URL}/api/exports/dashboard/pdf?user_id=${userId}`, {
      method: 'GET',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Export failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.blob();
  }

  // Helper to download blob as file
  downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }
}

export const exportsAPI = new ExportsAPI();
