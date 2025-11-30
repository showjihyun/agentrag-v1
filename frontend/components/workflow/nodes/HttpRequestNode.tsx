'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Globe, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface HttpRequestNodeData {
  label?: string;
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  url?: string;
  headers?: Record<string, string>;
  queryParams?: Record<string, string>;
  body?: string;
  bodyType?: 'json' | 'form' | 'raw';
  authType?: 'none' | 'bearer' | 'basic' | 'api_key';
  authConfig?: Record<string, string>;
  timeout?: number;
  followRedirects?: boolean;
  error?: string;
}

const methodColors = {
  GET: 'bg-blue-500',
  POST: 'bg-green-500',
  PUT: 'bg-yellow-500',
  PATCH: 'bg-orange-500',
  DELETE: 'bg-red-500',
};

export function HttpRequestNode({ data, selected }: NodeProps<HttpRequestNodeData>) {
  const method = data.method || 'GET';
  const url = data.url || 'https://api.example.com';
  const hasError = !!data.error;

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 bg-card shadow-lg min-w-[280px] transition-all',
        selected ? 'border-primary ring-2 ring-primary/20' : 'border-border',
        hasError && 'border-red-500'
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        id="input"
        className="w-3 h-3 !bg-primary"
      />

      <div className="flex items-start gap-3">
        <div className={cn('p-2 rounded-md', methodColors[method])}>
          <Globe className="w-4 h-4 text-white" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn(
              'px-2 py-0.5 rounded text-[10px] font-bold text-white',
              methodColors[method]
            )}>
              {method}
            </span>
            <div className="font-semibold text-sm truncate">
              {data.label || 'HTTP Request'}
            </div>
          </div>

          <div className="text-xs text-muted-foreground truncate" title={url}>
            {url}
          </div>

          {hasError && (
            <div className="flex items-center gap-1 mt-2 text-xs text-red-500">
              <AlertCircle className="w-3 h-3" />
              <span className="truncate">{data.error}</span>
            </div>
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        id="output"
        className="w-3 h-3 !bg-primary"
      />
    </div>
  );
}
