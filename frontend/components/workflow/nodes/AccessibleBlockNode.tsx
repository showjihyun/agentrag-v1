'use client';

/**
 * Accessible Block Node Component
 * 
 * WCAG 2.1 AA compliant workflow node with:
 * - Keyboard navigation support
 * - Screen reader announcements
 * - Focus indicators
 * - High contrast mode support
 * - Reduced motion support
 */

import React, { memo, useCallback, useRef, useEffect } from 'react';
import { Handle, Position, NodeProps, useReactFlow } from 'reactflow';
import { cn } from '@/lib/utils';
import { 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  AlertTriangle,
  GripVertical,
  Settings,
  Trash2,
  Copy
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

export interface AccessibleBlockNodeData {
  type: string;
  name: string;
  description?: string;
  category: string;
  bg_color?: string;
  icon?: string | React.ReactNode;
  label?: string;
  config?: Record<string, any>;
  isValid?: boolean;
  validationErrors?: string[];
  isExecuting?: boolean;
  executionStatus?: 'success' | 'error' | 'running' | 'pending' | 'skipped';
  disabled?: boolean;
  // Callbacks
  onConfigure?: () => void;
  onDelete?: () => void;
  onDuplicate?: () => void;
}

// Status configuration for accessibility
const statusConfig = {
  success: {
    icon: CheckCircle2,
    label: 'Completed successfully',
    className: 'bg-green-500 text-white',
    ringColor: 'ring-green-500/30',
  },
  error: {
    icon: XCircle,
    label: 'Failed with error',
    className: 'bg-red-500 text-white',
    ringColor: 'ring-red-500/30',
  },
  running: {
    icon: Loader2,
    label: 'Currently executing',
    className: 'bg-blue-500 text-white animate-pulse',
    ringColor: 'ring-blue-500/30',
  },
  pending: {
    icon: null,
    label: 'Waiting to execute',
    className: 'bg-gray-400 text-white',
    ringColor: 'ring-gray-400/30',
  },
  skipped: {
    icon: null,
    label: 'Skipped',
    className: 'bg-gray-300 text-gray-600',
    ringColor: 'ring-gray-300/30',
  },
};

export const AccessibleBlockNode = memo(({ 
  id,
  data, 
  selected,
  dragging,
}: NodeProps<AccessibleBlockNodeData>) => {
  const nodeRef = useRef<HTMLDivElement>(null);
  const { deleteElements, getNode } = useReactFlow();
  
  const bgColor = data.bg_color || '#6366f1';
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;
  const isExecuting = data.isExecuting || data.executionStatus === 'running';
  const executionStatus = data.executionStatus;
  const isDisabled = data.disabled;
  
  const statusInfo = executionStatus ? statusConfig[executionStatus] : null;
  const StatusIcon = statusInfo?.icon;
  
  // Announce status changes to screen readers
  useEffect(() => {
    if (executionStatus && statusInfo) {
      const announcement = `${data.label || data.name}: ${statusInfo.label}`;
      // Create live region announcement
      const liveRegion = document.getElementById('workflow-live-region');
      if (liveRegion) {
        liveRegion.textContent = announcement;
      }
    }
  }, [executionStatus, statusInfo, data.label, data.name]);
  
  // Keyboard handlers
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Delete':
      case 'Backspace':
        if (e.target === nodeRef.current) {
          e.preventDefault();
          data.onDelete?.();
        }
        break;
      case 'Enter':
      case ' ':
        if (e.target === nodeRef.current) {
          e.preventDefault();
          data.onConfigure?.();
        }
        break;
      case 'd':
        if ((e.ctrlKey || e.metaKey) && e.target === nodeRef.current) {
          e.preventDefault();
          data.onDuplicate?.();
        }
        break;
    }
  }, [data]);
  
  // Generate accessible description
  const getAccessibleDescription = () => {
    const parts = [
      data.label || data.name,
      data.category && `Category: ${data.category}`,
      data.description,
      isDisabled && 'Disabled',
      hasErrors && `Has ${data.validationErrors!.length} validation error${data.validationErrors!.length > 1 ? 's' : ''}`,
      statusInfo && statusInfo.label,
    ].filter(Boolean);
    
    return parts.join('. ');
  };

  return (
    <TooltipProvider>
      <div
        ref={nodeRef}
        role="button"
        tabIndex={0}
        aria-label={getAccessibleDescription()}
        aria-selected={selected}
        aria-disabled={isDisabled}
        aria-describedby={hasErrors ? `${id}-errors` : undefined}
        onKeyDown={handleKeyDown}
        className={cn(
          'group relative px-4 py-3 rounded-lg border-2 shadow-md min-w-[200px] max-w-[280px]',
          'transition-all duration-200',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary',
          // Selection state
          selected ? 'border-primary ring-2 ring-primary/20' : 'border-border',
          // Error state
          hasErrors && 'border-destructive ring-2 ring-destructive/20',
          // Executing state
          isExecuting && 'ring-2 ring-blue-500/50',
          // Disabled state
          isDisabled && 'opacity-50 grayscale',
          // Dragging state
          dragging && 'cursor-grabbing shadow-xl scale-105',
          // Execution status ring
          statusInfo && statusInfo.ringColor && `ring-2 ${statusInfo.ringColor}`,
          // Reduced motion preference
          'motion-reduce:transition-none motion-reduce:animate-none'
        )}
        style={{
          backgroundColor: `${bgColor}15`,
          borderColor: selected ? bgColor : hasErrors ? 'rgb(239 68 68)' : undefined,
        }}
      >
        {/* Skip link for keyboard users */}
        <a
          href={`#node-${id}-output`}
          className="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:z-50 focus:p-2 focus:bg-background focus:text-foreground"
        >
          Skip to output connection
        </a>
        
        {/* Execution Status Indicator */}
        {statusInfo && (
          <div 
            className="absolute -top-2 -right-2 z-10"
            role="status"
            aria-label={statusInfo.label}
          >
            <div className={cn(
              'w-6 h-6 rounded-full flex items-center justify-center shadow-md',
              statusInfo.className
            )}>
              {StatusIcon && (
                <StatusIcon 
                  className={cn('h-4 w-4', isExecuting && 'animate-spin')} 
                  aria-hidden="true"
                />
              )}
            </div>
          </div>
        )}
        
        {/* Disabled Badge */}
        {isDisabled && (
          <div 
            className="absolute -top-2 -left-2 z-10"
            role="status"
            aria-label="Node is disabled"
          >
            <div className="px-2 py-0.5 rounded-full bg-gray-500 text-white text-xs font-medium shadow-md">
              Disabled
            </div>
          </div>
        )}
        
        {/* Input Handle */}
        <Handle
          type="target"
          position={Position.Top}
          id="input"
          isConnectable={!isDisabled}
          aria-label="Input connection point"
          className={cn(
            '!w-4 !h-4 !bg-primary !border-2 !border-background',
            'hover:!w-5 hover:!h-5 hover:!border-primary/50',
            'focus:!ring-2 focus:!ring-primary focus:!ring-offset-2',
            'transition-all cursor-pointer shadow-md',
            isDisabled && '!bg-gray-400 cursor-not-allowed'
          )}
          style={{ top: -8 }}
        />

        {/* Node Content */}
        <div className="flex items-start gap-3">
          {/* Drag Handle (visible on hover) */}
          <div 
            className={cn(
              'absolute left-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100',
              'transition-opacity cursor-grab active:cursor-grabbing',
              'motion-reduce:transition-none'
            )}
            aria-hidden="true"
          >
            <GripVertical className="h-4 w-4 text-muted-foreground" />
          </div>
          
          {/* Icon */}
          {data.icon && (
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-sm font-bold flex-shrink-0 shadow-sm"
              style={{ backgroundColor: bgColor }}
              aria-hidden="true"
            >
              {typeof data.icon === 'string' ? data.icon : data.icon}
            </div>
          )}
          
          {/* Text Content */}
          <div className="flex-1 min-w-0 pr-2">
            <div 
              className="font-semibold text-sm truncate" 
              title={data.label || data.name}
            >
              {data.label || data.name}
            </div>
            
            {data.description && (
              <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {data.description}
              </div>
            )}
            
            {data.category && (
              <div className="inline-flex items-center mt-2">
                <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground capitalize">
                  {data.category}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Validation Errors */}
        {hasErrors && (
          <div 
            id={`${id}-errors`}
            className="mt-3 p-2 rounded-md bg-destructive/10 border border-destructive/20"
            role="alert"
          >
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-destructive flex-shrink-0 mt-0.5" aria-hidden="true" />
              <div className="text-xs text-destructive">
                {data.validationErrors!.map((error, i) => (
                  <p key={i}>{error}</p>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {/* Quick Actions (visible on hover/focus) */}
        <div 
          className={cn(
            'absolute -bottom-10 left-1/2 -translate-x-1/2',
            'flex items-center gap-1 p-1 rounded-lg bg-background border shadow-lg',
            'opacity-0 group-hover:opacity-100 group-focus-within:opacity-100',
            'transition-opacity duration-200',
            'motion-reduce:transition-none'
          )}
          role="toolbar"
          aria-label="Node actions"
        >
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0"
                onClick={(e) => {
                  e.stopPropagation();
                  data.onConfigure?.();
                }}
                aria-label="Configure node"
              >
                <Settings className="h-3.5 w-3.5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Configure (Enter)</TooltipContent>
          </Tooltip>
          
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0"
                onClick={(e) => {
                  e.stopPropagation();
                  data.onDuplicate?.();
                }}
                aria-label="Duplicate node"
              >
                <Copy className="h-3.5 w-3.5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Duplicate (Ctrl+D)</TooltipContent>
          </Tooltip>
          
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                onClick={(e) => {
                  e.stopPropagation();
                  data.onDelete?.();
                }}
                aria-label="Delete node"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Delete (Del)</TooltipContent>
          </Tooltip>
        </div>

        {/* Output Handle */}
        <Handle
          type="source"
          position={Position.Bottom}
          id="output"
          isConnectable={!isDisabled}
          aria-label="Output connection point"
          className={cn(
            '!w-4 !h-4 !bg-primary !border-2 !border-background',
            'hover:!w-5 hover:!h-5 hover:!border-primary/50',
            'focus:!ring-2 focus:!ring-primary focus:!ring-offset-2',
            'transition-all cursor-pointer shadow-md',
            isDisabled && '!bg-gray-400 cursor-not-allowed'
          )}
          style={{ bottom: -8 }}
        />
      </div>
    </TooltipProvider>
  );
});

AccessibleBlockNode.displayName = 'AccessibleBlockNode';

// Live region component for screen reader announcements
export function WorkflowLiveRegion() {
  return (
    <div
      id="workflow-live-region"
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="sr-only"
    />
  );
}
