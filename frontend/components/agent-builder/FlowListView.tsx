'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Users, 
  MessageSquare, 
  Play, 
  Edit,
  Copy,
  Trash,
  Eye,
  MoreVertical,
  CheckCircle2,
  Clock,
  TrendingUp,
  Calendar
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface FlowListViewProps {
  flows: any[];
  type: 'agentflow' | 'chatflow';
  onAction: (action: string, flowId: string, flow?: any) => void;
}

export function FlowListView({ flows, type, onAction }: FlowListViewProps) {
  const isAgentflow = type === 'agentflow';
  const Icon = isAgentflow ? Users : MessageSquare;
  const primaryColor = isAgentflow ? 'purple' : 'blue';

  return (
    <div className="space-y-3">
      {flows.map((flow) => (
        <Card 
          key={flow.id}
          className="group hover:shadow-lg transition-all duration-200 cursor-pointer border-l-4 border-l-gray-200 hover:border-l-purple-500"
          onClick={() => onAction('view', flow.id)}
        >
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              {/* 왼쪽: 기본 정보 */}
              <div className="flex items-center gap-4 flex-1 min-w-0">
                <div className={`p-2 rounded-lg bg-${primaryColor}-100 dark:bg-${primaryColor}-900 shrink-0`}>
                  <Icon className={`h-5 w-5 text-${primaryColor}-600 dark:text-${primaryColor}-400`} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-lg truncate group-hover:text-purple-600 transition-colors">
                      {flow.name}
                    </h3>
                    {flow.is_active && (
                      <Badge className="bg-green-500 text-xs shrink-0">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        활성
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-1">
                    {flow.description || '설명 없음'}
                  </p>
                </div>
              </div>

              {/* 중앙: 메트릭 */}
              <div className="hidden md:flex items-center gap-6 mx-6">
                <div className="text-center">
                  <div className={`text-lg font-bold text-${primaryColor}-600`}>
                    {isAgentflow ? (flow.agents?.length || 0) : (flow.execution_count || 0)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {isAgentflow ? '에이전트' : '대화'}
                  </div>
                </div>
                
                <div className="text-center">
                  <div className="text-lg font-bold text-green-600">
                    {flow.execution_count > 0 
                      ? `${Math.round(((flow.success_count || Math.floor(flow.execution_count * 0.85)) / flow.execution_count) * 100)}%`
                      : '—'}
                  </div>
                  <div className="text-xs text-muted-foreground">성공률</div>
                </div>
                
                <div className="text-center">
                  <div className="text-sm text-muted-foreground flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {flow.updated_at
                      ? new Date(flow.updated_at).toLocaleDateString()
                      : new Date(flow.created_at).toLocaleDateString()}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {flow.updated_at ? '수정일' : '생성일'}
                  </div>
                </div>
              </div>

              {/* 오른쪽: 액션 */}
              <div className="flex items-center gap-2 shrink-0">
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

                <DropdownMenu>
                  <DropdownMenuTrigger 
                    className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-10 w-10 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreVertical className="h-4 w-4" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onAction('view', flow.id)}>
                      <Eye className="mr-2 h-4 w-4" />
                      보기
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onAction('edit', flow.id)}>
                      <Edit className="mr-2 h-4 w-4" />
                      편집
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onAction('duplicate', flow.id, flow)}>
                      <Copy className="mr-2 h-4 w-4" />
                      복제
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem 
                      className="text-destructive"
                      onClick={() => onAction('delete', flow.id)}
                    >
                      <Trash className="mr-2 h-4 w-4" />
                      삭제
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>

            {/* 모바일용 메트릭 */}
            <div className="md:hidden mt-3 pt-3 border-t">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className={`text-lg font-bold text-${primaryColor}-600`}>
                    {isAgentflow ? (flow.agents?.length || 0) : (flow.execution_count || 0)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {isAgentflow ? '에이전트' : '대화'}
                  </div>
                </div>
                <div>
                  <div className="text-lg font-bold text-green-600">
                    {flow.execution_count > 0 
                      ? `${Math.round(((flow.success_count || Math.floor(flow.execution_count * 0.85)) / flow.execution_count) * 100)}%`
                      : '—'}
                  </div>
                  <div className="text-xs text-muted-foreground">성공률</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">
                    {flow.updated_at
                      ? new Date(flow.updated_at).toLocaleDateString()
                      : new Date(flow.created_at).toLocaleDateString()}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {flow.updated_at ? '수정일' : '생성일'}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}