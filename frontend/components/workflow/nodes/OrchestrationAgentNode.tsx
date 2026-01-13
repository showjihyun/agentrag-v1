'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { 
  Crown, 
  Wrench, 
  Eye, 
  Merge, 
  Users, 
  Star,
  MessageSquare,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Loader2,
} from 'lucide-react';
import { AGENT_ROLES, type AgentRole } from '@/lib/constants/orchestration';

export interface OrchestrationAgentNodeData {
  agentId: string;
  name: string;
  description?: string;
  role: AgentRole;
  priority: number;
  maxRetries: number;
  timeoutSeconds: number;
  dependencies: string[];
  capabilities?: string[];
  
  // 오케스트레이션 상태
  orchestrationStatus?: 'idle' | 'waiting' | 'negotiating' | 'executing' | 'completed' | 'failed';
  currentTask?: string;
  collaborationPartners?: string[];
  
  // 실행 상태
  isExecuting?: boolean;
  executionStatus?: 'success' | 'error' | 'running';
  executionProgress?: number;
  
  // 통신 상태
  activeConnections?: number;
  messageCount?: number;
  lastCommunication?: string;
  
  // 성능 메트릭
  tokenUsage?: number;
  responseTime?: number;
  successRate?: number;
  
  // 검증
  isValid?: boolean;
  validationErrors?: string[];
}

const getIconComponent = (role: AgentRole) => {
  const iconMap: Record<AgentRole, React.ComponentType<any>> = {
    manager: Crown,
    worker: Wrench,
    critic: Eye,
    synthesizer: Merge,
    coordinator: Users,
    specialist: Star,
  };
  return iconMap[role] || Users;
};

const getOrchestrationStatusColor = (status?: string) => {
  switch (status) {
    case 'idle':
      return 'text-gray-500 bg-gray-50';
    case 'waiting':
      return 'text-yellow-600 bg-yellow-50';
    case 'negotiating':
      return 'text-blue-600 bg-blue-50';
    case 'executing':
      return 'text-green-600 bg-green-50';
    case 'completed':
      return 'text-green-700 bg-green-100';
    case 'failed':
      return 'text-red-600 bg-red-50';
    default:
      return 'text-gray-500 bg-gray-50';
  }
};

const getOrchestrationStatusIcon = (status?: string) => {
  switch (status) {
    case 'waiting':
      return Clock;
    case 'negotiating':
      return MessageSquare;
    case 'executing':
      return Loader2;
    case 'completed':
      return CheckCircle2;
    case 'failed':
      return AlertTriangle;
    default:
      return Clock;
  }
};

export const OrchestrationAgentNode = memo(({ data, selected }: NodeProps<OrchestrationAgentNodeData>) => {
  const roleInfo = AGENT_ROLES[data.role];
  const IconComponent = getIconComponent(data.role);
  const StatusIcon = getOrchestrationStatusIcon(data.orchestrationStatus);
  
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;
  const isExecuting = data.isExecuting || data.orchestrationStatus === 'executing';
  const executionStatus = data.executionStatus;

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 shadow-md min-w-[220px] transition-all bg-white relative',
        selected ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-gray-300',
        hasErrors && 'border-red-500 ring-2 ring-red-500/20',
        isExecuting && 'ring-2 ring-green-500/50',
        data.orchestrationStatus === 'negotiating' && 'ring-2 ring-blue-500/50 animate-pulse'
      )}
    >
      {/* 입력 핸들 */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 border-2 border-gray-400 bg-white"
      />

      {/* 우선순위 배지 */}
      {data.priority > 0 && (
        <div className="absolute -top-2 -left-2 z-10">
          <Badge variant="secondary" className="text-xs px-1 py-0">
            P{data.priority}
          </Badge>
        </div>
      )}

      {/* 실행 상태 표시기 */}
      {(isExecuting || executionStatus) && (
        <div className="absolute -top-2 -right-2 z-10">
          {isExecuting && (
            <div className="w-5 h-5 bg-green-500 rounded-full animate-pulse flex items-center justify-center">
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

      {/* 헤더 */}
      <div className="flex items-center gap-3 mb-3">
        <div
          className="p-2 rounded-lg"
          style={{ backgroundColor: `${roleInfo.color}20`, color: roleInfo.color }}
        >
          <IconComponent className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-semibold text-sm">{data.name}</div>
          <div className="text-xs text-gray-500">{roleInfo.name}</div>
        </div>
      </div>

      {/* 오케스트레이션 상태 */}
      {data.orchestrationStatus && (
        <div className="mb-3">
          <Badge
            variant="outline"
            className={cn('text-xs', getOrchestrationStatusColor(data.orchestrationStatus))}
          >
            <StatusIcon className={cn(
              'w-3 h-3 mr-1',
              data.orchestrationStatus === 'executing' && 'animate-spin'
            )} />
            {data.orchestrationStatus === 'idle' && '대기'}
            {data.orchestrationStatus === 'waiting' && '대기 중'}
            {data.orchestrationStatus === 'negotiating' && '협상 중'}
            {data.orchestrationStatus === 'executing' && '실행 중'}
            {data.orchestrationStatus === 'completed' && '완료'}
            {data.orchestrationStatus === 'failed' && '실패'}
          </Badge>
        </div>
      )}

      {/* 현재 작업 */}
      {data.currentTask && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 mb-1">현재 작업:</div>
          <div className="text-xs bg-gray-50 p-2 rounded border">
            {data.currentTask}
          </div>
        </div>
      )}

      {/* 실행 진행률 */}
      {data.executionProgress !== undefined && data.executionProgress > 0 && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>진행률</span>
            <span>{Math.round(data.executionProgress * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div
              className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${data.executionProgress * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* 통신 상태 */}
      {(data.activeConnections || data.messageCount) && (
        <div className="mb-3 flex items-center gap-3 text-xs text-gray-600">
          {data.activeConnections && (
            <div className="flex items-center gap-1">
              <Users className="w-3 h-3" />
              <span>{data.activeConnections} 연결</span>
            </div>
          )}
          {data.messageCount && (
            <div className="flex items-center gap-1">
              <MessageSquare className="w-3 h-3" />
              <span>{data.messageCount} 메시지</span>
            </div>
          )}
        </div>
      )}

      {/* 성능 메트릭 */}
      {(data.tokenUsage || data.responseTime || data.successRate) && (
        <div className="mb-3 space-y-1">
          <div className="text-xs text-gray-600 mb-1">성능 메트릭:</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {data.tokenUsage && (
              <div className="bg-gray-50 p-1 rounded text-center">
                <div className="text-gray-500">토큰</div>
                <div className="font-medium">{data.tokenUsage.toLocaleString()}</div>
              </div>
            )}
            {data.responseTime && (
              <div className="bg-gray-50 p-1 rounded text-center">
                <div className="text-gray-500">응답시간</div>
                <div className="font-medium">{data.responseTime}ms</div>
              </div>
            )}
            {data.successRate && (
              <div className="bg-gray-50 p-1 rounded text-center col-span-2">
                <div className="text-gray-500">성공률</div>
                <div className="font-medium">{Math.round(data.successRate * 100)}%</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 의존성 표시 */}
      {data.dependencies && data.dependencies.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 mb-1">의존성:</div>
          <div className="flex flex-wrap gap-1">
            {data.dependencies.slice(0, 2).map((dep, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {dep}
              </Badge>
            ))}
            {data.dependencies.length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{data.dependencies.length - 2}
              </Badge>
            )}
          </div>
        </div>
      )}

      {/* 에러 표시 */}
      {hasErrors && (
        <div className="mb-3">
          <div className="text-xs text-red-600 mb-1">오류:</div>
          <div className="text-xs text-red-600 bg-red-50 p-2 rounded border border-red-200">
            {data.validationErrors?.[0]}
            {data.validationErrors && data.validationErrors.length > 1 && (
              <div className="mt-1">+{data.validationErrors.length - 1}개 더</div>
            )}
          </div>
        </div>
      )}

      {/* 설명 */}
      {data.description && (
        <div className="text-xs text-gray-600 line-clamp-2">
          {data.description}
        </div>
      )}

      {/* 출력 핸들 */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 border-2 border-gray-400 bg-white"
      />
    </div>
  );
});