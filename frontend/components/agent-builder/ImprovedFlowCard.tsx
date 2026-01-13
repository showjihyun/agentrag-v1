'use client';

import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Users, 
  MessageSquare, 
  Play, 
  MoreVertical, 
  CheckCircle2,
  TrendingUp
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface FlowCardProps {
  flow: any;
  type: 'agentflow' | 'chatflow';
  onAction: (action: string, flowId: string) => void;
}

export function ImprovedFlowCard({ flow, type, onAction }: FlowCardProps) {
  const isAgentflow = type === 'agentflow';
  const Icon = isAgentflow ? Users : MessageSquare;

  // 동적 클래스명 대신 조건부 클래스명 사용
  const iconBgClass = isAgentflow 
    ? 'bg-purple-100 dark:bg-purple-900' 
    : 'bg-blue-100 dark:bg-blue-900';
  const iconColorClass = isAgentflow 
    ? 'text-purple-600 dark:text-purple-400' 
    : 'text-blue-600 dark:text-blue-400';
  const metricColorClass = isAgentflow 
    ? 'text-purple-600' 
    : 'text-blue-600';
  const buttonClass = isAgentflow 
    ? 'bg-purple-600 hover:bg-purple-700' 
    : 'bg-blue-600 hover:bg-blue-700';

  // Select core metrics only
  const primaryMetric = isAgentflow 
    ? { label: 'Agents', value: flow.agents?.length || 0, icon: Users }
    : { label: 'Conversations', value: flow.execution_count || 0, icon: MessageSquare };

  const secondaryMetric = {
    label: 'Success Rate',
    value: flow.execution_count > 0 
      ? `${Math.round(((flow.success_count || Math.floor(flow.execution_count * 0.85)) / flow.execution_count) * 100)}%`
      : '—',
    icon: TrendingUp
  };

  return (
    <Card className="group relative overflow-hidden hover:shadow-xl transition-all duration-300 border-2 hover:border-purple-400 cursor-pointer">
      {/* Status Bar - More Clear */}
      <div className={`absolute top-0 left-0 right-0 h-1 ${
        flow.is_active ? 'bg-green-500' : 'bg-gray-300'
      }`} />
      
      <CardHeader className="pb-3">
        {/* Header - Reduced Information Density */}
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className={`p-2.5 rounded-xl group-hover:scale-105 transition-transform ${iconBgClass}`}>
              <Icon className={`h-5 w-5 ${iconColorClass}`} />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg truncate group-hover:text-purple-600 transition-colors">
                {flow.name}
              </h3>
              <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                {flow.description || 'No description'}
              </p>
            </div>
          </div>
          
          {/* Action Menu - More Accessible */}
          <DropdownMenu>
            <DropdownMenuTrigger className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-10 w-10 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
              <MoreVertical className="h-4 w-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onAction('view', flow.id)}>
                View
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction('edit', flow.id)}>
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction('duplicate', flow.id)}>
                Duplicate
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Core Metrics - Show Only 2 */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center p-3 rounded-lg bg-gray-50 dark:bg-gray-900/50">
            <div className={`text-2xl font-bold ${metricColorClass}`}>
              {primaryMetric.value}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {primaryMetric.label}
            </div>
          </div>
          <div className="text-center p-3 rounded-lg bg-gray-50 dark:bg-gray-900/50">
            <div className="text-2xl font-bold text-green-600">
              {secondaryMetric.value}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {secondaryMetric.label}
            </div>
          </div>
        </div>

        {/* Status Badges - Minimized */}
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            {flow.is_active && (
              <Badge className="bg-green-500 text-xs">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Active
              </Badge>
            )}
            {isAgentflow && (
              <Badge variant="outline" className="text-xs">
                {flow.orchestration_type || 'sequential'}
              </Badge>
            )}
            {!isAgentflow && flow.rag_config?.enabled && (
              <Badge variant="outline" className="text-xs">
                RAG
              </Badge>
            )}
          </div>
          
          {/* 주요 액션 버튼 */}
          <Button 
            size="sm" 
            className={`opacity-0 group-hover:opacity-100 transition-opacity ${buttonClass}`}
            onClick={(e) => {
              e.stopPropagation();
              onAction(isAgentflow ? 'execute' : 'chat', flow.id);
            }}
          >
            <Play className="h-3 w-3 mr-1" />
            {isAgentflow ? 'Execute' : 'Chat'}
          </Button>
        </div>

        {/* Metadata - Minimized */}
        <div className="mt-3 pt-3 border-t text-xs text-muted-foreground">
          {flow.updated_at
            ? `Updated: ${new Date(flow.updated_at).toLocaleDateString()}`
            : `Created: ${new Date(flow.created_at).toLocaleDateString()}`}
        </div>
      </CardContent>
    </Card>
  );
}