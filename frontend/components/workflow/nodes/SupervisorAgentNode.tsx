'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { 
  Brain,
  Crown,
  Settings,
  MessageSquare,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Zap,
  Users,
  Clock,
} from 'lucide-react';

export interface SupervisorAgentNodeData {
  name: string;
  description?: string;
  llmProvider: string;
  llmModel: string;
  decisionStrategy: 'llm_based' | 'consensus' | 'weighted_voting' | 'expert_system';
  maxIterations: number;
  
  // 실시간 상태
  supervisorStatus?: 'idle' | 'analyzing' | 'deciding' | 'coordinating' | 'monitoring';
  currentDecision?: string;
  managedAgents?: number;
  activeDecisions?: number;
  
  // 성능 메트릭
  decisionsCount?: number;
  averageDecisionTime?: number;
  successfulCoordinations?: number;
  
  // 실행 상태
  isExecuting?: boolean;
  executionStatus?: 'success' | 'error' | 'running';
  
  // 검증
  isValid?: boolean;
  validationErrors?: string[];
}

const getStatusColor = (status?: string) => {
  switch (status) {
    case 'idle':
      return 'text-gray-500 bg-gray-50';
    case 'analyzing':
      return 'text-blue-600 bg-blue-50';
    case 'deciding':
      return 'text-purple-600 bg-purple-50';
    case 'coordinating':
      return 'text-green-600 bg-green-50';
    case 'monitoring':
      return 'text-yellow-600 bg-yellow-50';
    default:
      return 'text-gray-500 bg-gray-50';
  }
};

const getStatusIcon = (status?: string) => {
  switch (status) {
    case 'analyzing':
      return Brain;
    case 'deciding':
      return Settings;
    case 'coordinating':
      return Users;
    case 'monitoring':
      return TrendingUp;
    default:
      return Crown;
  }
};

const getDecisionStrategyLabel = (strategy: string) => {
  switch (strategy) {
    case 'llm_based':
      return 'LLM 기반';
    case 'consensus':
      return '합의 기반';
    case 'weighted_voting':
      return '가중 투표';
    case 'expert_system':
      return '전문가 시스템';
    default:
      return strategy;
  }
};

export const SupervisorAgentNode = memo(({ data, selected }: NodeProps<SupervisorAgentNodeData>) => {
  const StatusIcon = getStatusIcon(data.supervisorStatus);
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;
  const isExecuting = data.isExecuting || data.supervisorStatus === 'deciding' || data.supervisorStatus === 'coordinating';

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 shadow-lg min-w-[250px] transition-all relative',
        'bg-gradient-to-br from-purple-50 to-blue-50',
        selected ? 'border-purple-500 ring-2 ring-purple-500/20' : 'border-purple-300',
        hasErrors && 'border-red-500 ring-2 ring-red-500/20',
        isExecuting && 'ring-2 ring-purple-500/50'
      )}
    >
      {/* 입력 핸들 (다중) */}
      <Handle
        type="target"
        position={Position.Top}
        id="input-1"
        style={{ left: '25%' }}
        className="w-3 h-3 border-2 border-purple-400 bg-white"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="input-2"
        style={{ left: '50%' }}
        className="w-3 h-3 border-2 border-purple-400 bg-white"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="input-3"
        style={{ left: '75%' }}
        className="w-3 h-3 border-2 border-purple-400 bg-white"
      />

      {/* Supervisor 배지 */}
      <div className="absolute -top-2 -left-2 z-10">
        <Badge className="bg-purple-600 text-white text-xs px-2 py-1">
          <Crown className="w-3 h-3 mr-1" />
          Supervisor
        </Badge>
      </div>

      {/* 실행 상태 표시기 */}
      {(isExecuting || data.executionStatus) && (
        <div className="absolute -top-2 -right-2 z-10">
          {isExecuting && (
            <div className="w-5 h-5 bg-purple-500 rounded-full animate-pulse flex items-center justify-center">
              <div className="w-3 h-3 bg-white rounded-full animate-ping"></div>
            </div>
          )}
          {data.executionStatus === 'success' && (
            <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center text-white text-xs">
              ✓
            </div>
          )}
          {data.executionStatus === 'error' && (
            <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs">
              ✕
            </div>
          )}
        </div>
      )}

      {/* 헤더 */}
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 rounded-lg bg-purple-100 text-purple-600">
          <Brain className="w-6 h-6" />
        </div>
        <div className="flex-1">
          <div className="font-semibold text-lg">{data.name}</div>
          <div className="text-xs text-gray-600">AI Supervisor</div>
        </div>
      </div>

      {/* LLM 정보 */}
      <div className="mb-3 p-2 bg-white/50 rounded border">
        <div className="text-xs text-gray-600 mb-1">LLM 설정</div>
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">{data.llmProvider}</span>
          <Badge variant="outline" className="text-xs">
            {data.llmModel}
          </Badge>
        </div>
      </div>

      {/* 의사결정 전략 */}
      <div className="mb-3">
        <div className="text-xs text-gray-600 mb-1">의사결정 전략</div>
        <Badge variant="secondary" className="text-xs">
          <Settings className="w-3 h-3 mr-1" />
          {getDecisionStrategyLabel(data.decisionStrategy)}
        </Badge>
      </div>

      {/* Supervisor 상태 */}
      {data.supervisorStatus && (
        <div className="mb-3">
          <Badge
            variant="outline"
            className={cn('text-xs', getStatusColor(data.supervisorStatus))}
          >
            <StatusIcon className={cn(
              'w-3 h-3 mr-1',
              (data.supervisorStatus === 'analyzing' || data.supervisorStatus === 'deciding') && 'animate-spin'
            )} />
            {data.supervisorStatus === 'idle' && '대기'}
            {data.supervisorStatus === 'analyzing' && '분석 중'}
            {data.supervisorStatus === 'deciding' && '결정 중'}
            {data.supervisorStatus === 'coordinating' && '조정 중'}
            {data.supervisorStatus === 'monitoring' && '모니터링'}
          </Badge>
        </div>
      )}

      {/* 현재 결정 */}
      {data.currentDecision && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 mb-1">현재 결정:</div>
          <div className="text-xs bg-purple-50 p-2 rounded border border-purple-200">
            {data.currentDecision}
          </div>
        </div>
      )}

      {/* 관리 현황 */}
      {(data.managedAgents || data.activeDecisions) && (
        <div className="mb-3 grid grid-cols-2 gap-2 text-xs">
          {data.managedAgents && (
            <div className="bg-white/50 p-2 rounded text-center">
              <div className="text-gray-500">관리 Agent</div>
              <div className="font-semibold text-purple-600">{data.managedAgents}</div>
            </div>
          )}
          {data.activeDecisions && (
            <div className="bg-white/50 p-2 rounded text-center">
              <div className="text-gray-500">활성 결정</div>
              <div className="font-semibold text-blue-600">{data.activeDecisions}</div>
            </div>
          )}
        </div>
      )}

      {/* 성능 메트릭 */}
      {(data.decisionsCount || data.averageDecisionTime || data.successfulCoordinations) && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 mb-1">성능 메트릭:</div>
          <div className="grid grid-cols-2 gap-1 text-xs">
            {data.decisionsCount && (
              <div className="bg-white/50 p-1 rounded text-center">
                <div className="text-gray-500">총 결정</div>
                <div className="font-medium">{data.decisionsCount}</div>
              </div>
            )}
            {data.averageDecisionTime && (
              <div className="bg-white/50 p-1 rounded text-center">
                <div className="text-gray-500">평균 시간</div>
                <div className="font-medium">{data.averageDecisionTime}ms</div>
              </div>
            )}
            {data.successfulCoordinations && (
              <div className="bg-white/50 p-1 rounded text-center col-span-2">
                <div className="text-gray-500">성공한 조정</div>
                <div className="font-medium">{data.successfulCoordinations}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 설정 정보 */}
      <div className="mb-3 flex items-center justify-between text-xs text-gray-600">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>최대 {data.maxIterations}회 반복</span>
        </div>
      </div>

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

      {/* 출력 핸들 (다중) */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="output-1"
        style={{ left: '25%' }}
        className="w-3 h-3 border-2 border-purple-400 bg-white"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="output-2"
        style={{ left: '50%' }}
        className="w-3 h-3 border-2 border-purple-400 bg-white"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="output-3"
        style={{ left: '75%' }}
        className="w-3 h-3 border-2 border-purple-400 bg-white"
      />
    </div>
  );
});