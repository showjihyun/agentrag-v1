'use client';

/**
 * ExportButton Component
 * 
 * Provides PDF export functionality with loading state.
 */

import React from 'react';
import { Download, FileText, Loader2 } from 'lucide-react';
import { useExport } from '@/hooks/useExport';
import { cn } from '@/lib/utils';

type ExportType = 'chat' | 'workflow' | 'dashboard';

interface ExportButtonProps {
  type: ExportType;
  id?: string;
  title?: string;
  className?: string;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function ExportButton({
  type,
  id,
  title,
  className,
  variant = 'default',
  size = 'md',
  showLabel = true,
}: ExportButtonProps) {
  const { exporting, error, exportChatToPDF, exportWorkflowToPDF, exportDashboardToPDF } = useExport();

  const handleExport = async () => {
    try {
      switch (type) {
        case 'chat':
          if (!id) throw new Error('Session ID required');
          await exportChatToPDF(id, title);
          break;
        case 'workflow':
          if (!id) throw new Error('Workflow ID required');
          await exportWorkflowToPDF(id);
          break;
        case 'dashboard':
          await exportDashboardToPDF();
          break;
      }
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-2.5 text-base',
  };

  const variantClasses = {
    default: 'bg-blue-600 text-white hover:bg-blue-700',
    outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300',
    ghost: 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800',
  };

  const labels = {
    chat: 'Export Chat',
    workflow: 'Export Report',
    dashboard: 'Export Dashboard',
  };

  return (
    <button
      onClick={handleExport}
      disabled={exporting}
      className={cn(
        'inline-flex items-center gap-2 rounded-lg font-medium transition-colors disabled:opacity-50',
        sizeClasses[size],
        variantClasses[variant],
        className
      )}
      title={error || labels[type]}
    >
      {exporting ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Download className="w-4 h-4" />
      )}
      {showLabel && <span>{exporting ? 'Exporting...' : labels[type]}</span>}
    </button>
  );
}

// Quick export menu for multiple options
interface ExportMenuProps {
  chatSessionId?: string;
  workflowId?: string;
  className?: string;
}

export function ExportMenu({ chatSessionId, workflowId, className }: ExportMenuProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const { exporting, exportChatToPDF, exportWorkflowToPDF, exportDashboardToPDF } = useExport();

  const menuRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={cn('relative', className)} ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600"
      >
        <FileText className="w-4 h-4" />
        Export PDF
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
          {chatSessionId && (
            <button
              onClick={async () => {
                await exportChatToPDF(chatSessionId);
                setIsOpen(false);
              }}
              disabled={exporting}
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export Chat
            </button>
          )}
          {workflowId && (
            <button
              onClick={async () => {
                await exportWorkflowToPDF(workflowId);
                setIsOpen(false);
              }}
              disabled={exporting}
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export Workflow
            </button>
          )}
          <button
            onClick={async () => {
              await exportDashboardToPDF();
              setIsOpen(false);
            }}
            disabled={exporting}
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export Dashboard
          </button>
        </div>
      )}
    </div>
  );
}

export default ExportButton;
