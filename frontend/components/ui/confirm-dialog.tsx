'use client';

/**
 * Confirm Dialog Component
 * 
 * Accessible confirmation dialog with:
 * - Undo support
 * - Keyboard navigation
 * - Screen reader announcements
 * - Customizable actions
 */

import * as React from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { AlertTriangle, Trash2, Info, CheckCircle, XCircle, Undo2 } from 'lucide-react';

type DialogVariant = 'default' | 'destructive' | 'warning' | 'info' | 'success';

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: DialogVariant;
  icon?: React.ReactNode;
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
  // Undo support
  undoable?: boolean;
  undoDuration?: number; // in seconds
  onUndo?: () => void;
  // Loading state
  loading?: boolean;
  // Additional content
  children?: React.ReactNode;
}

const variantConfig: Record<DialogVariant, {
  icon: React.ReactNode;
  iconBg: string;
  iconColor: string;
  confirmVariant: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
}> = {
  default: {
    icon: <Info className="h-6 w-6" />,
    iconBg: 'bg-primary/10',
    iconColor: 'text-primary',
    confirmVariant: 'default',
  },
  destructive: {
    icon: <Trash2 className="h-6 w-6" />,
    iconBg: 'bg-destructive/10',
    iconColor: 'text-destructive',
    confirmVariant: 'destructive',
  },
  warning: {
    icon: <AlertTriangle className="h-6 w-6" />,
    iconBg: 'bg-amber-500/10',
    iconColor: 'text-amber-500',
    confirmVariant: 'default',
  },
  info: {
    icon: <Info className="h-6 w-6" />,
    iconBg: 'bg-blue-500/10',
    iconColor: 'text-blue-500',
    confirmVariant: 'default',
  },
  success: {
    icon: <CheckCircle className="h-6 w-6" />,
    iconBg: 'bg-green-500/10',
    iconColor: 'text-green-500',
    confirmVariant: 'default',
  },
};

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'default',
  icon,
  onConfirm,
  onCancel,
  undoable = false,
  undoDuration = 5,
  onUndo,
  loading = false,
  children,
}: ConfirmDialogProps) {
  const [isConfirming, setIsConfirming] = React.useState(false);
  const [showUndo, setShowUndo] = React.useState(false);
  const [undoCountdown, setUndoCountdown] = React.useState(undoDuration);
  const undoTimerRef = React.useRef<NodeJS.Timeout | null>(null);
  const countdownRef = React.useRef<NodeJS.Timeout | null>(null);
  
  const config = variantConfig[variant];
  const displayIcon = icon || config.icon;
  
  // Cleanup timers on unmount
  React.useEffect(() => {
    return () => {
      if (undoTimerRef.current) clearTimeout(undoTimerRef.current);
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, []);
  
  const handleConfirm = async () => {
    setIsConfirming(true);
    
    try {
      if (undoable) {
        // Show undo toast instead of immediate action
        onOpenChange(false);
        setShowUndo(true);
        setUndoCountdown(undoDuration);
        
        // Start countdown
        countdownRef.current = setInterval(() => {
          setUndoCountdown(prev => {
            if (prev <= 1) {
              if (countdownRef.current) clearInterval(countdownRef.current);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
        
        // Execute after delay
        undoTimerRef.current = setTimeout(async () => {
          setShowUndo(false);
          await onConfirm();
        }, undoDuration * 1000);
      } else {
        await onConfirm();
        onOpenChange(false);
      }
    } finally {
      setIsConfirming(false);
    }
  };
  
  const handleUndo = () => {
    if (undoTimerRef.current) clearTimeout(undoTimerRef.current);
    if (countdownRef.current) clearInterval(countdownRef.current);
    setShowUndo(false);
    onUndo?.();
  };
  
  const handleCancel = () => {
    onCancel?.();
    onOpenChange(false);
  };
  
  return (
    <>
      <AlertDialog open={open} onOpenChange={onOpenChange}>
        <AlertDialogContent className="sm:max-w-[425px]">
          <AlertDialogHeader>
            <div className="flex items-start gap-4">
              {/* Icon */}
              <div className={cn(
                'flex h-12 w-12 shrink-0 items-center justify-center rounded-full',
                config.iconBg
              )}>
                <span className={config.iconColor}>{displayIcon}</span>
              </div>
              
              <div className="flex-1 space-y-2">
                <AlertDialogTitle className="text-lg">
                  {title}
                </AlertDialogTitle>
                {description && (
                  <AlertDialogDescription>
                    {description}
                  </AlertDialogDescription>
                )}
              </div>
            </div>
            
            {/* Additional content */}
            {children && (
              <div className="mt-4 pl-16">
                {children}
              </div>
            )}
          </AlertDialogHeader>
          
          <AlertDialogFooter className="mt-4">
            <AlertDialogCancel onClick={handleCancel} disabled={loading || isConfirming}>
              {cancelText}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirm}
              disabled={loading || isConfirming}
              className={cn(
                config.confirmVariant === 'destructive' && 'bg-destructive text-destructive-foreground hover:bg-destructive/90'
              )}
            >
              {(loading || isConfirming) ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Processing...
                </span>
              ) : (
                confirmText
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      
      {/* Undo Toast */}
      {showUndo && (
        <div
          role="alert"
          aria-live="assertive"
          className={cn(
            'fixed bottom-4 left-1/2 -translate-x-1/2 z-[100]',
            'flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg',
            'bg-foreground text-background',
            'animate-in slide-in-from-bottom-4 fade-in duration-300'
          )}
        >
          <span className="text-sm font-medium">
            Action will complete in {undoCountdown}s
          </span>
          <Button
            size="sm"
            variant="secondary"
            onClick={handleUndo}
            className="h-7 gap-1.5"
          >
            <Undo2 className="h-3.5 w-3.5" />
            Undo
          </Button>
        </div>
      )}
    </>
  );
}

// Hook for easier usage
interface UseConfirmDialogOptions {
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: DialogVariant;
  undoable?: boolean;
  undoDuration?: number;
}

export function useConfirmDialog() {
  const [dialogState, setDialogState] = React.useState<{
    open: boolean;
    options: UseConfirmDialogOptions;
    onConfirm: () => void | Promise<void>;
    onUndo?: () => void;
  }>({
    open: false,
    options: { title: '' },
    onConfirm: () => {},
  });
  
  const confirm = React.useCallback((
    options: UseConfirmDialogOptions,
    onConfirm: () => void | Promise<void>,
    onUndo?: () => void
  ) => {
    setDialogState({
      open: true,
      options,
      onConfirm,
      onUndo,
    });
  }, []);
  
  const DialogComponent = React.useCallback(() => (
    <ConfirmDialog
      open={dialogState.open}
      onOpenChange={(open) => setDialogState(prev => ({ ...prev, open }))}
      title={dialogState.options.title}
      description={dialogState.options.description}
      confirmText={dialogState.options.confirmText}
      cancelText={dialogState.options.cancelText}
      variant={dialogState.options.variant}
      undoable={dialogState.options.undoable}
      undoDuration={dialogState.options.undoDuration}
      onConfirm={dialogState.onConfirm}
      onUndo={dialogState.onUndo}
    />
  ), [dialogState]);
  
  return { confirm, ConfirmDialog: DialogComponent };
}

export type { DialogVariant, ConfirmDialogProps };
