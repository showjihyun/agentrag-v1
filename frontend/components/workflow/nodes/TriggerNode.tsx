'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import { Zap, Clock, Webhook, Mail, Calendar, Database } from 'lucide-react';

export interface TriggerNodeData {
  triggerType: 'manual' | 'schedule' | 'webhook' | 'email' | 'event' | 'database';
  name: string;
  description?: string;
  config?: Record<string, any>;
  isValid?: boolean;
  validationErrors?: string[];
}

const triggerIcons = {
  manual: Zap,
  schedule: Clock,
  webhook: Webhook,
  email: Mail,
  event: Calendar,
  database: Database,
};

const triggerColors = {
  manual: 'from-yellow-400 to-orange-500',
  schedule: 'from-blue-400 to-cyan-500',
  webhook: 'from-purple-400 to-pink-500',
  email: 'from-green-400 to-emerald-500',
  event: 'from-red-400 to-rose-500',
  database: 'from-indigo-400 to-violet-500',
};

export const TriggerNode = memo(({ data, selected }: NodeProps<TriggerNodeData>) => {
  const Icon = triggerIcons[data.triggerType] || Zap;
  const colorClass = triggerColors[data.triggerType] || 'from-yellow-400 to-orange-500';
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 shadow-lg min-w-[200px] transition-all',
        `bg-gradient-to-r ${colorClass}`,
        selected ? 'ring-4 ring-yellow-500/30 scale-105' : '',
        hasErrors && 'border-destructive ring-2 ring-destructive/20'
      )}
    >
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

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-yellow-500"
        style={{ bottom: -6 }}
      />
    </div>
  );
});

TriggerNode.displayName = 'TriggerNode';
