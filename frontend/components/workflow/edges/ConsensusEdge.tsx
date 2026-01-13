'use client';

import React from 'react';
import {
  EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from 'reactflow';
import { Vote, CheckCircle2, Clock, Users, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConsensusEdgeData {
  consensusStatus: 'voting' | 'reached' | 'failed' | 'pending';
  votesFor?: number;
  votesAgainst?: number;
  totalVoters?: number;
  threshold?: number; // 합의 임계값 (0-1)
  consensusLevel?: number; // 현재 합의 수준 (0-1)
  votingDeadline?: string;
  lastVote?: {
    voter: string;
    decision: 'for' | 'against';
    timestamp: string;
  };
}

export const ConsensusEdge: React.FC<EdgeProps<ConsensusEdgeData>> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  data,
  markerEnd,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const consensusStatus = data?.consensusStatus || 'pending';
  const votesFor = data?.votesFor || 0;
  const votesAgainst = data?.votesAgainst || 0;
  const totalVoters = data?.totalVoters || 0;
  const threshold = data?.threshold || 0.7;
  const consensusLevel = data?.consensusLevel || 0;

  // 합의 상태별 스타일 정의
  const getEdgeStyle = () => {
    const baseStyle = {
      strokeWidth: 3,
    };

    switch (consensusStatus) {
      case 'voting':
        return {
          ...baseStyle,
          stroke: '#3B82F6',
          strokeDasharray: '12,8',
          opacity: 1,
        };
      case 'reached':
        return {
          ...baseStyle,
          stroke: '#10B981',
          strokeDasharray: '0',
          opacity: 0.9,
        };
      case 'failed':
        return {
          ...baseStyle,
          stroke: '#EF4444',
          strokeDasharray: '6,6',
          opacity: 0.7,
        };
      case 'pending':
        return {
          ...baseStyle,
          stroke: '#6B7280',
          strokeDasharray: '4,4',
          opacity: 0.5,
        };
      default:
        return baseStyle;
    }
  };

  // 합의 상태별 아이콘
  const getStatusIcon = () => {
    switch (consensusStatus) {
      case 'voting':
        return <Vote className="w-3 h-3 animate-pulse" />;
      case 'reached':
        return <CheckCircle2 className="w-3 h-3" />;
      case 'failed':
        return <Vote className="w-3 h-3 opacity-50" />;
      case 'pending':
        return <Clock className="w-3 h-3" />;
      default:
        return <Vote className="w-3 h-3" />;
    }
  };

  // 합의 상태별 라벨
  const getStatusLabel = () => {
    switch (consensusStatus) {
      case 'voting':
        return '투표 진행 중';
      case 'reached':
        return '합의 달성';
      case 'failed':
        return '합의 실패';
      case 'pending':
        return '투표 대기';
      default:
        return '합의';
    }
  };

  const edgeStyle = getEdgeStyle();
  const votingProgress = totalVoters > 0 ? ((votesFor + votesAgainst) / totalVoters) * 100 : 0;
  const supportRate = (votesFor + votesAgainst) > 0 ? (votesFor / (votesFor + votesAgainst)) * 100 : 0;

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          ...edgeStyle,
          filter: consensusStatus === 'voting' ? 'drop-shadow(0 0 6px currentColor)' : 'none',
        }}
      />
      
      {/* 투표 진행 시 애니메이션 효과 */}
      {consensusStatus === 'voting' && (
        <BaseEdge
          path={edgePath}
          style={{
            stroke: '#3B82F6',
            strokeWidth: 1,
            opacity: 0.3,
            strokeDasharray: '8,8',
            animation: 'consensus-flow 3s linear infinite',
          }}
        />
      )}

      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            fontSize: 12,
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        >
          <div
            className={cn(
              'flex flex-col items-center gap-2 px-3 py-2 rounded-lg text-white text-xs font-medium shadow-lg',
              'transition-all duration-200',
              consensusStatus === 'voting' && 'scale-110 shadow-xl'
            )}
            style={{
              backgroundColor: edgeStyle.stroke,
              opacity: consensusStatus === 'voting' ? 1 : 0.9,
            }}
          >
            {/* 상태 표시 */}
            <div className="flex items-center gap-1">
              {getStatusIcon()}
              <span>{getStatusLabel()}</span>
            </div>
            
            {/* 투표 현황 */}
            {consensusStatus === 'voting' && (
              <div className="flex flex-col items-center gap-1 w-full">
                {/* 투표 진행률 */}
                <div className="w-full bg-white/20 rounded-full h-1">
                  <div 
                    className="bg-white rounded-full h-1 transition-all duration-300"
                    style={{ width: `${votingProgress}%` }}
                  />
                </div>
                
                {/* 투표 결과 */}
                <div className="flex items-center gap-2 text-xs">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-green-400 rounded-full" />
                    <span>{votesFor}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-red-400 rounded-full" />
                    <span>{votesAgainst}</span>
                  </div>
                  <div className="flex items-center gap-1 opacity-80">
                    <Users className="w-2 h-2" />
                    <span>{totalVoters}</span>
                  </div>
                </div>
                
                {/* 지지율 */}
                <div className="flex items-center gap-1 text-xs opacity-90">
                  <TrendingUp className="w-2 h-2" />
                  <span>{supportRate.toFixed(0)}% 지지</span>
                </div>
              </div>
            )}
            
            {/* 합의 달성 시 결과 */}
            {consensusStatus === 'reached' && (
              <div className="flex items-center gap-1 text-xs opacity-90">
                <span>{(consensusLevel * 100).toFixed(0)}% 합의</span>
              </div>
            )}
          </div>
          
          {/* 최근 투표 툴팁 */}
          {data?.lastVote && consensusStatus === 'voting' && (
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
              <div className="font-medium mb-1">최근 투표:</div>
              <div className="opacity-90">
                {data.lastVote.voter} → {data.lastVote.decision === 'for' ? '찬성' : '반대'}
              </div>
            </div>
          )}
        </div>
      </EdgeLabelRenderer>

      <style jsx>{`
        @keyframes consensus-flow {
          0% {
            stroke-dashoffset: 0;
          }
          100% {
            stroke-dashoffset: -16;
          }
        }
      `}</style>
    </>
  );
};