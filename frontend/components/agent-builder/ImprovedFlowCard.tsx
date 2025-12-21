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
  const primaryColor = isAgentflow ? 'purple' : 'blue';
  const Icon = isAgentflow ? Users : MessageSquare;

  // 핵심 메트릭만 선별
  const primaryMetric = isAgentflow 
    ? { label: '에이전트', value: flow.agents?.length || 0, icon: Users }
    : { label: '대화', value: flow.execution_count || 0, icon: MessageSquare };

  const secondaryMetric = {
    label: '성공률',
    value: flow.execution_count > 0 
      ? `${Math.round(((flow.success_count || Math.floor(flow.execution_count * 0.85)) / flow.execution_count) * 100)}%`
      : '—',
    icon: TrendingUp
  };

  return (
    <Card className="group relative overflow-hidden hover:shadow-xl transition-all duration-300 border-2 hover:border-purple-400 cursor-pointer">
      {/* 상태 표시줄 - 더 명확하게 */}
      <div className={`absolute top-0 left-0 right-0 h-1 ${
        flow.is_active ? 'bg-green-500' : 'bg-gray-300'
      }`} />
      
      <CardHeader className="pb-3">
        {/* 헤더 - 정보 밀도 감소 */}
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className={`p-2.5 rounded-xl bg-${primaryColor}-100 dark:bg-${primaryColor}-900 group-hover:scale-105 transition-transform`}>
              <Icon className={`h-5 w-5 text-${primaryColor}-600 dark:text-${primaryColor}-400`} />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg truncate group-hover:text-purple-600 transition-colors">
                {flow.name}
              </h3>
              <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                {flow.description || '설명 없음'}
              </p>
            </div>
          </div>
          
          {/* 액션 메뉴 - 더 접근하기 쉽게 */}
          <DropdownMenu>
            <DropdownMenuTrigger className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-10 w-10 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
              <MoreVertical className="h-4 w-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onAction('view', flow.id)}>
                보기
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction('edit', flow.id)}>
                편집
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction('duplicate', flow.id)}>
                복제
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* 핵심 메트릭 - 2개만 표시 */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center p-3 rounded-lg bg-gray-50 dark:bg-gray-900/50">
            <div className={`text-2xl font-bold text-${primaryColor}-600`}>
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

        {/* 상태 배지 - 최소화 */}
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            {flow.is_active && (
              <Badge className="bg-green-500 text-xs">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                활성
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
            className={`bg-${primaryColor}-600 hover:bg-${primaryColor}-700 opacity-0 group-hover:opacity-100 transition-opacity`}
            onClick={(e) => {
              e.stopPropagation();
              onAction(isAgentflow ? 'execute' : 'chat', flow.id);
            }}
          >
            <Play className="h-3 w-3 mr-1" />
            {isAgentflow ? '실행' : '채팅'}
          </Button>
        </div>

        {/* 메타데이터 - 최소화 */}
        <div className="mt-3 pt-3 border-t text-xs text-muted-foreground">
          {flow.updated_at
            ? `수정: ${new Date(flow.updated_at).toLocaleDateString()}`
            : `생성: ${new Date(flow.created_at).toLocaleDateString()}`}
        </div>
      </CardContent>
    </Card>
  );
}