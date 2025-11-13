'use client';

import React, { memo, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import { Zap, Clock, Webhook, Mail, Calendar, Database, Play, Copy, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface TriggerNodeData {
  triggerType: 'manual' | 'schedule' | 'webhook' | 'email' | 'event' | 'database' | 'file' | 'api' | 'chat' | 'form';
  name: string;
  description?: string;
  config?: Record<string, any>;
  isValid?: boolean;
  validationErrors?: string[];
  isExecuting?: boolean;
  executionStatus?: 'success' | 'error' | 'running';
  onTrigger?: () => void;
  onConfigure?: () => void;
  onCopyWebhook?: () => void;
}

const triggerIcons = {
  manual: Zap,
  schedule: Clock,
  webhook: Webhook,
  email: Mail,
  event: Calendar,
  database: Database,
  file: Mail, // Using Mail as placeholder, will show emoji
  api: Zap,
  chat: Mail,
  form: Mail,
};

const triggerColors = {
  manual: 'from-yellow-400 to-orange-500',
  schedule: 'from-blue-400 to-cyan-500',
  webhook: 'from-purple-400 to-pink-500',
  email: 'from-green-400 to-emerald-500',
  event: 'from-red-400 to-rose-500',
  database: 'from-indigo-400 to-violet-500',
  file: 'from-orange-400 to-amber-500',
  api: 'from-violet-400 to-purple-500',
  chat: 'from-cyan-400 to-blue-500',
  form: 'from-emerald-400 to-green-500',
};

export const TriggerNode = memo(({ data, selected }: NodeProps<TriggerNodeData>) => {
  const Icon = triggerIcons[data.triggerType] || Zap;
  const colorClass = triggerColors[data.triggerType] || 'from-yellow-400 to-orange-500';
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;
  const isExecuting = data.isExecuting || false;
  const executionStatus = data.executionStatus;

  // Handle button clicks - prevent event propagation to ReactFlow
  const handleTrigger = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (data.onTrigger) {
      data.onTrigger();
    }
  }, [data]);

  const handleConfigure = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (data.onConfigure) {
      data.onConfigure();
    }
  }, [data]);

  const handleCopyWebhook = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (data.onCopyWebhook) {
      data.onCopyWebhook();
    }
  }, [data]);

  return (
    <div
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 shadow-lg min-w-[240px] transition-all',
        `bg-gradient-to-r ${colorClass}`,
        selected ? 'ring-4 ring-yellow-500/30 scale-105' : '',
        hasErrors && 'border-destructive ring-2 ring-destructive/20',
        isExecuting && 'ring-4 ring-blue-500/50 animate-pulse'
      )}
    >
      {/* Execution Status Indicator */}
      {(isExecuting || executionStatus) && (
        <div className="absolute -top-2 -right-2 z-10">
          {isExecuting && (
            <div className="w-5 h-5 bg-blue-500 rounded-full animate-pulse flex items-center justify-center">
              <div className="w-3 h-3 bg-white rounded-full animate-ping"></div>
            </div>
          )}
          {executionStatus === 'success' && (
            <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center text-white text-xs">
              ✓
            </div>
          )}
          {executionStatus === 'error' && (
            <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs">
              ✕
            </div>
          )}
        </div>
      )}
      {/* Node Content */}
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center text-white flex-shrink-0">
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <div className="font-semibold text-sm text-white truncate" title={data.name}>
              {data.name}
            </div>
          </div>
          {data.description && (
            <div className="text-xs text-white/80 mt-1 line-clamp-2">
              {data.description}
            </div>
          )}
          <div className="text-xs text-white/90 mt-1 font-medium capitalize">
            {data.triggerType} Trigger
          </div>
        </div>
      </div>

      {/* Validation Errors */}
      {hasErrors && (
        <div className="mt-2 text-xs text-white bg-red-500/50 rounded px-2 py-1">
          {data.validationErrors![0]}
        </div>
      )}

      {/* Action Buttons */}
      <div className="mt-3 flex gap-2" onMouseDown={(e) => e.stopPropagation()}>
        {/* Manual Trigger Button */}
        {data.triggerType === 'manual' && (
          <Button
            size="sm"
            variant="secondary"
            className="flex-1 h-7 text-xs bg-white/90 hover:bg-white text-gray-900 font-medium"
            onClick={handleTrigger}
            disabled={isExecuting}
          >
            <Play className="h-3 w-3 mr-1" />
            {isExecuting ? 'Running...' : 'Trigger'}
          </Button>
        )}

        {/* Webhook Copy Button */}
        {data.triggerType === 'webhook' && (
          <Button
            size="sm"
            variant="secondary"
            className="flex-1 h-7 text-xs bg-white/90 hover:bg-white text-gray-900 font-medium"
            onClick={handleCopyWebhook}
          >
            <Copy className="h-3 w-3 mr-1" />
            Copy URL
          </Button>
        )}

        {/* Configure Button (for all types) */}
        <Button
          size="sm"
          variant="secondary"
          className="h-7 w-7 p-0 bg-white/90 hover:bg-white text-gray-900"
          onClick={handleConfigure}
          title="Configure trigger"
        >
          <Settings className="h-3 w-3" />
        </Button>
      </div>

      {/* Output Handle - Trigger nodes only have output, no input */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="output"
        isConnectable={true}
        className="!w-8 !h-8 !bg-yellow-500 !border-4 !border-white hover:!w-10 hover:!h-10 hover:!border-yellow-300 transition-all cursor-pointer shadow-lg"
        style={{ 
          bottom: -16,
          left: '50%',
          transform: 'translateX(-50%)'
        }}
      />
    </div>
  );
});

TriggerNode.displayName = 'TriggerNode';
