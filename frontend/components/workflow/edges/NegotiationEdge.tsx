'use client';

import React from 'react';
import {
  EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from 'reactflow';
import { MessageSquare, Users, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NegotiationEdgeData {
  negotiationStatus: 'active' | 'completed' | 'failed' | 'pending';
  currentRound?: number;
  maxRounds?: number;
  participants?: string[];
  lastProposal?: string;
  agreementReached?: boolean;
  timestamp?: string;
}

export const NegotiationEdge: React.FC<EdgeProps<NegotiationEdgeData>> = ({
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

  const negotiationStatus = data?.negotiationStatus || 'pending';
  const currentRound = data?.currentRound || 0;
  const maxRounds = data?.maxRounds || 3;
  const agreementReached = data?.agreementReached || false;

  // 협상 상태별 스타일 정의
  const getEdgeStyle = () => {
    const baseStyle = {
      strokeWidth: 3,
    };

    switch (negotiationStatus) {
      case 'active':
        return {
          ...baseStyle,
          stroke: '#F59E0B',
          strokeDasharray: '15,5,5,5',
          opacity: 1,
        };
      case 'completed':
        return {
          ...baseStyle,
          stroke: agreementReached ? '#10B981' : '#EF4444',
          strokeDasharray: '0',
          opacity: 0.8,
        };
      case 'failed':
        return {
          ...baseStyle,
          stroke: '#EF4444',
          strokeDasharray: '8,8',
          opacity: 0.7,
        };
      case 'pending':
        return {
          ...baseStyle,
          stroke: '#6B7280',
          strokeDasharray: '5,5',
          opacity: 0.5,
        };
      default:
        return baseStyle;
    }
  };

  // 협상 상태별 아이콘
  const getStatusIcon = () => {
    switch (negotiationStatus) {
      case 'active':
        return <MessageSquare className="w-3 h-3 animate-pulse" />;
      case 'completed':
        return agreementReached ? 
          <CheckCircle2 className="w-3 h-3" /> : 
          <XCircle className="w-3 h-3" />;
      case 'failed':
        return <XCircle className="w-3 h-3" />;
      case 'pending':
        return <Clock className="w-3 h-3" />;
      default:
        return <MessageSquare className="w-3 h-3" />;
    }
  };

  // 협상 상태별 라벨
  const getStatusLabel = () => {
    switch (negotiationStatus) {
      case 'active':
        return `협상 중 (${currentRound}/${maxRounds})`;
      case 'completed':
        return agreementReached ? '합의 완료' : '합의 실패';
      case 'failed':
        return '협상 실패';
      case 'pending':
        return '협상 대기';
      default:
        return '협상';
    }
  };

  const edgeStyle = getEdgeStyle();
  const progress = maxRounds > 0 ? (currentRound / maxRounds) * 100 : 0;

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          ...edgeStyle,
          filter: negotiationStatus === 'active' ? 'drop-shadow(0 0 8px currentColor)' : 'none',
        }}
      />
      
      {/* 활성 협상 시 애니메이션 효과 */}
      {negotiationStatus === 'active' && (
        <BaseEdge
          path={edgePath}
          style={{
            stroke: '#F59E0B',
            strokeWidth: 1,
            opacity: 0.4,
            strokeDasharray: '6,6',
            animation: 'negotiation-pulse 2s ease-in-out infinite',
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
              'flex flex-col items-center gap-1 px-3 py-2 rounded-lg text-white text-xs font-medium shadow-lg',
              'transition-all duration-200',
              negotiationStatus === 'active' && 'scale-110 shadow-xl'
            )}
            style={{
              backgroundColor: edgeStyle.stroke,
              opacity: negotiationStatus === 'active' ? 1 : 0.9,
            }}
          >
            {/* 상태 표시 */}
            <div className="flex items-center gap-1">
              {getStatusIcon()}
              <span>{getStatusLabel()}</span>
            </div>
            
            {/* 진행률 바 (활성 협상 시) */}
            {negotiationStatus === 'active' && maxRounds > 0 && (
              <div className="w-full bg-white/20 rounded-full h-1">
                <div 
                  className="bg-white rounded-full h-1 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            )}
            
            {/* 참가자 수 */}
            {data?.participants && data.participants.length > 0 && (
              <div className="flex items-center gap-1 text-xs opacity-80">
                <Users className="w-2 h-2" />
                <span>{data.participants.length}명</span>
              </div>
            )}
          </div>
          
          {/* 마지막 제안 툴팁 */}
          {data?.lastProposal && negotiationStatus === 'active' && (
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg max-w-64">
              <div className="font-medium mb-1">최근 제안:</div>
              <div className="opacity-90">{data.lastProposal}</div>
            </div>
          )}
        </div>
      </EdgeLabelRenderer>

      <style jsx>{`
        @keyframes negotiation-pulse {
          0%, 100% {
            opacity: 0.4;
            stroke-width: 1;
          }
          50% {
            opacity: 0.8;
            stroke-width: 2;
          }
        }
      `}</style>
    </>
  );
};