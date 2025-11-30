'use client';

/**
 * Enhanced Toast System
 * 
 * Unified notification system with:
 * - Multiple variants (success, error, warning, info)
 * - Action buttons
 * - Progress indicator
 * - Stacking support
 * - Accessibility
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@/lib/utils';
import { X, CheckCircle2, XCircle, AlertTriangle, Info, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';

type ToastVariant = 'default' | 'success' | 'error' | 'warning' | 'info' | 'loading';

interface ToastAction {
  label: string;
  onClick: () => void;
  variant?: 'default' | 'outline' | 'ghost';
}

interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
  action?: ToastAction;
  dismissible?: boolean;
  progress?: boolean;
  icon?: React.ReactNode;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => string;
  removeToast: (id: string) => void;
  updateToast: (id: string, updates: Partial<Toast>) => void;
  clearAll: () => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

// Variant configurations
const variantConfig: Record<ToastVariant, { icon: React.ReactNode; className: string }> = {
  default: {
    icon: null,
    className: 'bg-background border-border',
  },
  success: {
    icon: <CheckCircle2 className="h-5 w-5 text-green-500" />,
    className: 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800',
  },
  error: {
    icon: <XCircle className="h-5 w-5 text-red-500" />,
    className: 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800',
  },
  warning: {
    icon: <AlertTriangle className="h-5 w-5 text-amber-500" />,
    className: 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800',
  },
  info: {
    icon: <Info className="h-5 w-5 text-blue-500" />,
    className: 'bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800',
  },
  loading: {
    icon: <Loader2 className="h-5 w-5 text-primary animate-spin" />,
    className: 'bg-background border-border',
  },
};

// Individual toast component
function ToastItem({ 
  toast, 
  onRemove 
}: { 
  toast: Toast; 
  onRemove: () => void;
}) {
  const [progress, setProgress] = useState(100);
  const [isExiting, setIsExiting] = useState(false);
  const config = variantConfig[toast.variant || 'default'];
  const duration = toast.duration ?? 5000;

  // Auto-dismiss with progress
  useEffect(() => {
    if (duration === 0 || toast.variant === 'loading') return;

    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);

      if (remaining === 0) {
        handleDismiss();
      }
    }, 50);

    return () => clearInterval(interval);
  }, [duration, toast.variant]);

  const handleDismiss = useCallback(() => {
    setIsExiting(true);
    setTimeout(onRemove, 200);
  }, [onRemove]);

  return (
    <div
      role="alert"
      aria-live="polite"
      className={cn(
        'relative flex items-start gap-3 p-4 rounded-lg border shadow-lg',
        'w-[380px] max-w-[calc(100vw-2rem)]',
        'transition-all duration-200',
        isExiting ? 'opacity-0 translate-x-full' : 'opacity-100 translate-x-0',
        'animate-in slide-in-from-right-full',
        config.className
      )}
    >
      {/* Icon */}
      {(toast.icon || config.icon) && (
        <div className="flex-shrink-0 mt-0.5">
          {toast.icon || config.icon}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm">{toast.title}</p>
        {toast.description && (
          <p className="text-sm text-muted-foreground mt-1">{toast.description}</p>
        )}
        {toast.action && (
          <Button
            size="sm"
            variant={toast.action.variant || 'outline'}
            className="mt-2 h-7 text-xs"
            onClick={() => {
              toast.action?.onClick();
              handleDismiss();
            }}
          >
            {toast.action.label}
          </Button>
        )}
      </div>

      {/* Dismiss button */}
      {toast.dismissible !== false && (
        <button
          onClick={handleDismiss}
          className="flex-shrink-0 p-1 rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
          aria-label="Dismiss"
        >
          <X className="h-4 w-4 text-muted-foreground" />
        </button>
      )}

      {/* Progress bar */}
      {toast.progress !== false && duration > 0 && toast.variant !== 'loading' && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/5 dark:bg-white/5 rounded-b-lg overflow-hidden">
          <div
            className="h-full bg-current opacity-20 transition-all duration-100"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
}

// Toast container
function ToastContainer({ toasts, removeToast }: { toasts: Toast[]; removeToast: (id: string) => void }) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) return null;

  return createPortal(
    <div
      className="fixed top-4 right-4 z-[10000] flex flex-col gap-2"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onRemove={() => removeToast(toast.id)}
        />
      ))}
    </div>,
    document.body
  );
}

// Provider component
export function EnhancedToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setToasts((prev) => [...prev, { ...toast, id }]);
    return id;
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const updateToast = useCallback((id: string, updates: Partial<Toast>) => {
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, ...updates } : t))
    );
  }, []);

  const clearAll = useCallback(() => {
    setToasts([]);
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, updateToast, clearAll }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
}

// Hook for using toasts
export function useEnhancedToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useEnhancedToast must be used within EnhancedToastProvider');
  }

  const { addToast, removeToast, updateToast, clearAll } = context;

  // Convenience methods
  const toast = useCallback((options: Omit<Toast, 'id'>) => addToast(options), [addToast]);

  const success = useCallback((title: string, description?: string) => 
    addToast({ title, description, variant: 'success' }), [addToast]);

  const error = useCallback((title: string, description?: string) => 
    addToast({ title, description, variant: 'error', duration: 8000 }), [addToast]);

  const warning = useCallback((title: string, description?: string) => 
    addToast({ title, description, variant: 'warning' }), [addToast]);

  const info = useCallback((title: string, description?: string) => 
    addToast({ title, description, variant: 'info' }), [addToast]);

  const loading = useCallback((title: string, description?: string) => 
    addToast({ title, description, variant: 'loading', duration: 0, dismissible: false }), [addToast]);

  const promise = useCallback(async <T,>(
    promise: Promise<T>,
    options: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((err: Error) => string);
    }
  ): Promise<T> => {
    const id = addToast({ title: options.loading, variant: 'loading', duration: 0, dismissible: false });
    
    try {
      const result = await promise;
      updateToast(id, {
        title: typeof options.success === 'function' ? options.success(result) : options.success,
        variant: 'success',
        duration: 5000,
        dismissible: true,
      });
      return result;
    } catch (err) {
      updateToast(id, {
        title: typeof options.error === 'function' ? options.error(err as Error) : options.error,
        variant: 'error',
        duration: 8000,
        dismissible: true,
      });
      throw err;
    }
  }, [addToast, updateToast]);

  return {
    toast,
    success,
    error,
    warning,
    info,
    loading,
    promise,
    dismiss: removeToast,
    update: updateToast,
    clearAll,
  };
}

export type { Toast, ToastVariant, ToastAction };
