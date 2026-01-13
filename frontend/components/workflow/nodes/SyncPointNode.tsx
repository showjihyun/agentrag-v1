'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { 
  RefreshCw,
  Clock,
  Users,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Pause,
  Play,
} from 'lucide-react';

export interface SyncPointNodeData {
  name: string;
  description?: string;
  syncType: 'barrier' | 'timeout' | 'condition' | 'manual';
  timeoutSeconds?: number;
  condition?: string;
  
  // 실시간 동기화 상태
  syncStatus?: 'waiting' | 'syncing' | 'completed' | 'timeout' | 'failed';
  expectedAgents?: number;
  arrivedAgents?: number;
  waitingAgents?: string[];
  
  // 조건 기반 동기화
  conditionMet?: boolean;
  conditionProgress?: number;
  
  // 수동 동기화
  manualTrigger?: boolean;
  
  // 실행 상태
  isExecuting?: boolean;
  executionStatus?: 'success' | 'error' | 'running';
  
  // 검증
  isValid?: boolean;
  validationErrors?: string[];
}

const getSyncTypeLabel = (type: string) => {
  switch (type) {
    case 'barrier':
      return '배리어';
    case 'timeout':
      return '타임아웃';
    case 'condition':
      return '조건';
    case 'manual':
      return '수동';
    default:
      return type;
  }
};

const getStatusColor = (status?: string) => {
  switch (status) {
    case 'waiting':
      return 'text-yellow-600 bg-yellow-50';
    case 'syncing':
      return 'text-blue-600 bg-blue-50';
    case 'completed':
      return 'text-green-600 bg-green-50';
    case 'timeout':
      return 'text-red-600 bg-red-50';
    case 'failed':
      return 'text-red-600 bg-red-50';
    default:
      return 'text-gray-500 bg-gray-50';
  }
};

const getStatusIcon = (status?: string) => {
  switch (status) {
    case 'waiting':
      return Pause;
    case 'syncing':
      return Loader2;
    case 'completed':
      return CheckCircle2;
    case 'timeout':
      return Clock;
    case 'failed':
      return AlertCircle;
    default:
      return RefreshCw;
  }
};

export const SyncPointNode = memo(({ data, selected }: NodeProps<SyncPointNodeData>) => {
  const StatusIcon = getStatusIcon(data.syncStatus);
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;
  const isExecuting = data.isExecuting || data.syncStatus === 'syncing';

  const syncProgress = data.expectedAgents && data.arrivedAgents 
    ? (data.arrivedAgents / data.expectedAgents) * 100 
    : 0;

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 shadow-md min-w-[180px] transition-all relative',
        'bg-gradient-to-br from-yellow-50 to-orange-50',
        selected ? 'border-yellow-500 ring-2 ring-yellow-500/20' : 'border-yellow-300',
        hasErrors && 'border-red-500 ring-2 ring-red-500/20',
        isExecuting && 'ring-2 ring-yellow-500/50'
      )}
    >
      {/* 입력 핸들 (다중) */}
      <Handle
        type="target"
        position={Position.Top}
        id="input-1"
        style={{ left: '20%' }}
        className="w-3 h-3 border-2 border-yellow-400 bg-white"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="input-2"
        style={{ left: '40%' }}
        className="w-3 h-3 border-2 border-yellow-400 bg-white"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="input-3"
        style={{ left: '60%' }}
        className="w-3 h-3 border-2 border-yellow-400 bg-white"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="input-4"
        style={{ left: '80%' }}
        className="w-3 h-3 border-2 border-yellow-400 bg-white"
      />

      {/* 동기화 배지 */}
      <div className="absolute -top-2 -left-2 z-10">
        <Badge className="bg-yellow-600 text-white text-xs px-2 py-1">
          <RefreshCw className="w-3 h-3 mr-1" />
          동기화
        </Badge>
      </div>

      {/* 실행 상태 표시기 */}
      {(isExecuting || data.executionStatus) && (
        <div className="absolute -top-2 -right-2 z-10">
          {isExecuting && (
            <div className="w-5 h-5 bg-yellow-500 rounded-full animate-pulse flex items-center justify-center">
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
        <div className="p-2 rounded-lg bg-yellow-100 text-yellow-600">
          <RefreshCw className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-semibold text-sm">{data.name}</div>
          <div className="text-xs text-gray-600">동기화 포인트</div>
        </div>
      </div>

      {/* 동기화 타입 */}
      <div className="mb-3">
        <div className="text-xs text-gray-600 mb-1">동기화 타입</div>
        <Badge variant="secondary" className="text-xs">
          {getSyncTypeLabel(data.syncType)}
        </Badge>
      </div>

      {/* 동기화 상태 */}
      {data.syncStatus && (
        <div className="mb-3">
          <Badge
            variant="outline"
            className={cn('text-xs', getStatusColor(data.syncStatus))}
          >
            <StatusIcon className={cn(
              'w-3 h-3 mr-1',
              data.syncStatus === 'syncing' && 'animate-spin'
            )} />
            {data.syncStatus === 'waiting' && '대기 중'}
            {data.syncStatus === 'syncing' && '동기화 중'}
            {data.syncStatus === 'completed' && '완료'}
            {data.syncStatus === 'timeout' && '시간 초과'}
            {data.syncStatus === 'failed' && '실패'}
          </Badge>
        </div>
      )}

      {/* Agent 도착 진행률 */}
      {data.expectedAgents && data.arrivedAgents !== undefined && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>Agent 도착</span>
            <span>{data.arrivedAgents}/{data.expectedAgents} ({Math.round(syncProgress)}%)</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div
              className="bg-yellow-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${syncProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* 대기 중인 Agent들 */}
      {data.waitingAgents && data.waitingAgents.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 mb-1">대기 중:</div>
          <div className="flex flex-wrap gap-1">
            {data.waitingAgents.slice(0, 3).map((agent, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {agent}
              </Badge>
            ))}
            {data.waitingAgents.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{data.waitingAgents.length - 3}
              </Badge>
            )}
          </div>
        </div>
      )}

      {/* 조건 기반 동기화 */}
      {data.syncType === 'condition' && data.condition && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 mb-1">조건:</div>
          <div className="text-xs bg-white/50 p-2 rounded border">
            {data.condition}
          </div>
          {data.conditionProgress !== undefined && (
            <div className="mt-2">
              <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                <span>조건 진행률</span>
                <span>{Math.round(data.conditionProgress * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className={cn(
                    'h-1.5 rounded-full transition-all duration-300',
                    data.conditionMet ? 'bg-green-500' : 'bg-yellow-500'
                  )}
                  style={{ width: `${data.conditionProgress * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* 수동 트리거 */}
      {data.syncType === 'manual' && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 mb-1">수동 제어:</div>
          <div className="flex items-center gap-2">
            <div className={cn(
              'w-3 h-3 rounded-full',
              data.manualTrigger ? 'bg-green-500' : 'bg-gray-300'
            )} />
            <span className="text-xs">
              {data.manualTrigger ? '트리거됨' : '대기 중'}
            </span>
          </div>
        </div>
      )}

      {/* 타임아웃 정보 */}
      {data.timeoutSeconds && (
        <div className="mb-3 flex items-center gap-1 text-xs text-gray-600">
          <Clock className="w-3 h-3" />
          <span>타임아웃: {data.timeoutSeconds}초</span>
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
        className="w-3 h-3 border-2 border-yellow-400 bg-white"
      />
    </div>
  );
});