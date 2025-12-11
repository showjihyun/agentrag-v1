/**
 * ToolConfigHeader - Common header component for Tool Configurations
 * 
 * Provides consistent header styling across all tool configs
 */

'use client';

import { memo, ReactNode } from 'react';
import { Badge } from '@/components/ui/badge';
import { LucideIcon } from 'lucide-react';

export interface ToolConfigHeaderProps {
  /** Tool icon component */
  icon: LucideIcon;
  /** Icon background color class (e.g., 'bg-blue-100 dark:bg-blue-950') */
  iconBgColor: string;
  /** Icon color class (e.g., 'text-blue-600 dark:text-blue-400') */
  iconColor: string;
  /** Tool title */
  title: string;
  /** Tool description */
  description: string;
  /** Optional badge text (e.g., 'Popular', 'New', 'Beta') */
  badge?: string;
  /** Optional badge variant */
  badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline';
  /** Optional additional content on the right */
  rightContent?: ReactNode;
}

export const ToolConfigHeader = memo(function ToolConfigHeader({
  icon: Icon,
  iconBgColor,
  iconColor,
  title,
  description,
  badge,
  badgeVariant = 'secondary',
  rightContent,
}: ToolConfigHeaderProps) {
  return (
    <div className="flex items-center gap-3 pb-4 border-b">
      <div className={`p-2 rounded-lg ${iconBgColor}`}>
        <Icon className={`h-5 w-5 ${iconColor}`} />
      </div>
      <div className="flex-1">
        <h3 className="font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {badge && (
        <Badge variant={badgeVariant} className="ml-auto">
          {badge}
        </Badge>
      )}
      {rightContent}
    </div>
  );
});

// ============================================
// Preset Header Configurations
// ============================================

export const TOOL_HEADER_PRESETS = {
  http: {
    iconBgColor: 'bg-blue-100 dark:bg-blue-950',
    iconColor: 'text-blue-600 dark:text-blue-400',
  },
  slack: {
    iconBgColor: 'bg-purple-100 dark:bg-purple-950',
    iconColor: 'text-purple-600 dark:text-purple-400',
  },
  email: {
    iconBgColor: 'bg-red-100 dark:bg-red-950',
    iconColor: 'text-red-600 dark:text-red-400',
  },
  database: {
    iconBgColor: 'bg-green-100 dark:bg-green-950',
    iconColor: 'text-green-600 dark:text-green-400',
  },
  ai: {
    iconBgColor: 'bg-violet-100 dark:bg-violet-950',
    iconColor: 'text-violet-600 dark:text-violet-400',
  },
  code: {
    iconBgColor: 'bg-orange-100 dark:bg-orange-950',
    iconColor: 'text-orange-600 dark:text-orange-400',
  },
  control: {
    iconBgColor: 'bg-cyan-100 dark:bg-cyan-950',
    iconColor: 'text-cyan-600 dark:text-cyan-400',
  },
  trigger: {
    iconBgColor: 'bg-yellow-100 dark:bg-yellow-950',
    iconColor: 'text-yellow-600 dark:text-yellow-400',
  },
  storage: {
    iconBgColor: 'bg-teal-100 dark:bg-teal-950',
    iconColor: 'text-teal-600 dark:text-teal-400',
  },
} as const;

export type ToolHeaderPreset = keyof typeof TOOL_HEADER_PRESETS;
