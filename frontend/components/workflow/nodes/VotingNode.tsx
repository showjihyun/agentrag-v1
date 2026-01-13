'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { 
  Vote,
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  AlertCircle,
  Loader2,
} from 'lucide-react';

export interface VotingNodeData {
  name: string;
  description?: string;
  votingMethod: 'majority' | 'unanimous' | 'weighted' | 'threshold';
  threshold?: number; // threshold 방식일 때 필요한 최소 득표율
  timeoutSeconds: number;
  
  // 실시간 투표 상태
  votingStatus?: 'waiting' | 'voting' | 'counting' | 'completed' | 'timeout';
  totalVoters?: number;
  votesReceived?: number;
  currentResult?: 'pending' | 'approved' | 'rejected';
  
  // 투표 결과
  approvalVotes?: number;
  rejectionVotes?: number;
  abstentionVotes?: number;
  
  // 가중 투표 정보
  weightedScores?: Record<string, number>;
  
  // 실행 상태
  isExecuting?: boolean;
  executionStatus?: 'success' | 'error' | 'running';
  
  // 검증
  isValid?: boolean;
  validationErrors?: string[];
}

const getVotingMethodLabel = (method: string) => {
  switch (method) {
    case 'majority':
      return '과반수';
    case 'unanimous':
      return '만장일치';
    case 'weighted':
      return '가중 투표';
    case 'threshold':
      return '임계값';
    default:
      return method;
  }
};

const getStatusColor = (status?: string) => {
  switch (status) {
    case 'waiting':
      return 'text-gray-500 bg-gray-50';
    case 'voting':
      return 'text-blue-600 bg-blue-50';
    case 'counting':
      return 'text-yellow-600 bg-yellow-50';
    case 'completed':
      return 'text-green-600 bg-green-50';
    case 'timeout':
      return 'text-red-600 bg-red-50';
    default:
      return 'text-gray-500 bg-gray-50';
  }
};

const getStatusIcon = (status?: string) => {
  switch (status) {
    case 'waiting':
      return Clock;
    case 'voting':
      return Vote;
    case 'counting':
      return Loader2;
    case 'completed':
      return CheckCircle2;
    case 'timeout':
      return XCircle;
    default:
      return Vote;
  }
};

const getResultColor = (result?: string) => {
  switch (result) {
    case 'approved':
      return 'text-green-600 bg-green-50 border-green-200';
    case 'rejected':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'pending':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

export const VotingNode = memo(({ data, selected }: NodeProps<VotingNodeData>) => {
  const StatusIcon = getStatusIcon(data.votingStatus);
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;
  const isExecuting = data.isExecuting || data.votingStatus === 'voting' || data.votingStatus === 'counting';

  const votingProgress = data.totalVoters && data.votesReceived 
    ? (data.votesReceived / data.totalVoters) * 100 
    : 0;

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 shadow-md min-w-[200px] transition-all relative',
        'bg-gradient-to-br from-blue-50 to-indigo-50',
        selected ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-blue-300',
        hasErrors && 'border-red-500 ring-2 ring-red-500/20',
        isExecuting && 'ring-2 ring-blue-500/50'
      )}
    >
      {/* 입력 핸들 (다중) */}
      <Handle
        type="target"
        position={Position.Top}
        id="input-1"
        style={{ left: '20%' }}
        className="w-3 h-3 border-2 border-blue-400 bg-white"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="input-2"
        style={{ left: '40%' }}
        className="w-3 h-3 border-2 border-blue-400 bg-white"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="input-3"
        style={{ left: '60%' }}
        className="w-3 h-3 border-2 border-blue-400 bg-white"
      />
      <Handle
        type="target"
        position={Position.Top}
        id="input-4"
        style={{ left: '80%' }}
        className="w-3 h-3 border-2 border-blue-400 bg-white"
      />

      {/* 투표 배지 */}
      <div className="absolute -top-2 -left-2 z-10">
        <Badge className="bg-blue-600 text-white text-xs px-2 py-1">
          <Vote className="w-3 h-3 mr-1" />
          투표
        </Badge>
      </div>

      {/* 실행 상태 표시기 */}
      {(isExecuting || data.executionStatus) && (
        <div className="absolute -top-2 -right-2 z-10">
          {isExecuting && (
            <div className="w-5 h-5 bg-blue-500 rounded-full animate-pulse flex items-center justify-center">
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
        <div className="p-2 rounded-lg bg-blue-100 text-blue-600">
          <Vote className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="font-semibold text-sm">{data.name}</div>
          <div className="text-xs text-gray-600">투표 노드</div>
        </div>
      </div>

      {/* 투표 방식 */}
      <div className="mb-3">
        <div className="text-xs text-gray-600 mb-1">투표 방식</div>
        <Badge variant="secondary" className="text-xs">
          {getVotingMethodLabel(data.votingMethod)}
          {data.votingMethod === 'threshold' && data.threshold && (
            <span className="ml-1">({Math.round(data.threshold * 100)}%)</span>
          )}
        </Badge>
      </div>

      {/* 투표 상태 */}
      {data.votingStatus && (
        <div className="mb-3">
          <Badge
            variant="outline"
            className={cn('text-xs', getStatusColor(data.votingStatus))}
          >
            <StatusIcon className={cn(
              'w-3 h-3 mr-1',
              data.votingStatus === 'counting' && 'animate-spin'
            )} />
            {data.votingStatus === 'waiting' && '대기 중'}
            {data.votingStatus === 'voting' && '투표 중'}
            {data.votingStatus === 'counting' && '집계 중'}
            {data.votingStatus === 'completed' && '완료'}
            {data.votingStatus === 'timeout' && '시간 초과'}
          </Badge>
        </div>
      )}

      {/* 투표 진행률 */}
      {data.totalVoters && data.votesReceived !== undefined && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>투표 진행률</span>
            <span>{data.votesReceived}/{data.totalVoters} ({Math.round(votingProgress)}%)</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div
              className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${votingProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* 현재 결과 */}
      {data.currentResult && data.currentResult !== 'pending' && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 mb-1">현재 결과:</div>
          <div className={cn(
            'text-xs p-2 rounded border text-center font-medium',
            getResultColor(data.currentResult)
          )}>
            {data.currentResult === 'approved' && '승인'}
            {data.currentResult === 'rejected' && '거부'}
          </div>
        </div>
      )}

      {/* 투표 결과 상세 */}
      {(data.approvalVotes || data.rejectionVotes || data.abstentionVotes) && (
        <div className="mb-3">
          <div className="text-xs text-gray-600 mb-1">투표 결과:</div>
          <div className="grid grid-cols-3 gap-1 text-xs">
            {data.approvalVotes !== undefined && (
              <div className="bg-green-50 p-1 rounded text-center">
                <div className="text-green-600 font-medium">{data.approvalVotes}</div>
                <div className="text-gray-500">찬성</div>
              </div>
            )}
            {data.rejectionVotes !== undefined && (
              <div className="bg-red-50 p-1 rounded text-center">
                <div className="text-red-600 font-medium">{data.rejectionVotes}</div>
                <div className="text-gray-500">반대</div>
              </div>
            )}
            {data.abstentionVotes !== undefined && (
              <div className="bg-gray-50 p-1 rounded text-center">
                <div className="text-gray-600 font-medium">{data.abstentionVotes}</div>
                <div className="text-gray-500">기권</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 타임아웃 정보 */}
      <div className="mb-3 flex items-center gap-1 text-xs text-gray-600">
        <Clock className="w-3 h-3" />
        <span>타임아웃: {data.timeoutSeconds}초</span>
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

      {/* 출력 핸들 */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="approved"
        style={{ left: '30%' }}
        className="w-3 h-3 border-2 border-green-400 bg-white"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="rejected"
        style={{ left: '70%' }}
        className="w-3 h-3 border-2 border-red-400 bg-white"
      />
    </div>
  );
});