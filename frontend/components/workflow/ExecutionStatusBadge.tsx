'use client';

import React from 'react';
import { Loader2, CheckCircle2, XCircle, Clock, Minus } from 'lucide-react';

export type NodeStatus = 'idle' | 'pending' | 'running' | 'success' | 'error' | 'skipped';

interface ExecutionStatusBadgeProps {
  status: NodeStatus;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function ExecutionStatusBadge({ 
  status, 
  size = 'md',
  showLabel = false 
}: ExecutionStatusBadgeProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  const iconSize = {
    sm: 12,
    md: 16,
    lg: 20,
  };

  const getStatusConfig = () => {
    switch (status) {
      case 'pending':
        return {
          icon: <Clock size={iconSize[size]} />,
          bgColor: 'bg-yellow-400',
          textColor: 'text-yellow-900',
          label: 'Pending',
        };
      case 'running':
        return {
          icon: <Loader2 size={iconSize[size]} className="animate-spin" />,
          bgColor: 'bg-blue-500',
          textColor: 'text-white',
          label: 'Running',
        };
      case 'success':
        return {
          icon: <CheckCircle2 size={iconSize[size]} />,
          bgColor: 'bg-green-500',
          textColor: 'text-white',
          label: 'Success',
        };
      case 'error':
        return {
          icon: <XCircle size={iconSize[size]} />,
          bgColor: 'bg-red-500',
          textColor: 'text-white',
          label: 'Error',
        };
      case 'skipped':
        return {
          icon: <Minus size={iconSize[size]} />,
          bgColor: 'bg-gray-400',
          textColor: 'text-white',
          label: 'Skipped',
        };
      default:
        return null;
    }
  };

  const config = getStatusConfig();
  
  if (!config) return null;

  return (
    <div className="flex items-center gap-2">
      <div
        className={`
          ${sizeClasses[size]}
          ${config.bgColor}
          ${config.textColor}
          rounded-full
          flex items-center justify-center
          shadow-md
        `}
      >
        {config.icon}
      </div>
      {showLabel && (
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {config.label}
        </span>
      )}
    </div>
  );
}
