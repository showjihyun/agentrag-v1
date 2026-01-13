'use client';

import React from 'react';
import {
  EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from 'reactflow';
import { MessageSquare, ArrowRight, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CommunicationEdgeData {
  communicationType: 'direct' | 'broadcast' | 'negotiation' | 'feedback' | 'consensus';
  messageCount?: number;
  isActive?: boolean;
  lastMessage?: string;
  timestamp?: string;
}

export const CommunicationEdge: React.FC<EdgeProps<CommunicationEdgeData>> = ({
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

  const communicationType = data?.communicationType || 'direct';
  const isActive = data?.isActive || false;
  const messageCount = data?.messageCount || 0;

  // 통신 타입별 스타일 정의
  const getEdgeStyle = () => {
    const baseStyle = {
      strokeWidth: isActive ? 3 : 2,
      opacity: isActive ? 1 : 0.7,
    };

    switch (communicationType) {
      case 'direct':
        return {
          ...baseStyle,
          stroke: '#3B82F6',
          strokeDasharray: isActive ? '0' : '5,5',
        };
      case 'broadcast':
        return {
          ...baseStyle,
          stroke: '#10B981',
          strokeDasharray: '10,5',
        };
      case 'negotiation':
        return {
          ...baseStyle,
          stroke: '#F59E0B',
          strokeDasharray: '15,5,5,5',
        };
      case 'feedback':
        return {
          ...baseStyle,
          stroke: '#8B5CF6',
          strokeDasharray: '8,3',
        };
      case 'consensus':
        return {
          ...baseStyle,
          stroke: '#EF4444',
          strokeDasharray: '12,8',
        };
      default:
        return baseStyle;
    }
  };

  // 통신 타입별 아이콘
  const getIcon = () => {
    switch (communicationType) {
      case 'direct':
        return <ArrowRight className="w-3 h-3" />;
      case 'broadcast':
        return <Zap className="w-3 h-3" />;
      case 'negotiation':
        return <MessageSquare className="w-3 h-3" />;
      case 'feedback':
        return <ArrowRight className="w-3 h-3 transform rotate-180" />;
      case 'consensus':
        return <MessageSquare className="w-3 h-3" />;
      default:
        return <MessageSquare className="w-3 h-3" />;
    }
  };

  // 통신 타입별 라벨
  const getLabel = () => {
    switch (communicationType) {
      case 'direct':
        return '직접 통신';
      case 'broadcast':
        return '브로드캐스트';
      case 'negotiation':
        return '협상';
      case 'feedback':
        return '피드백';
      case 'consensus':
        return '합의';
      default:
        return '통신';
    }
  };

  const edgeStyle = getEdgeStyle();

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          ...edgeStyle,
          filter: isActive ? 'drop-shadow(0 0 6px currentColor)' : 'none',
        }}
      />
      
      {/* 활성 상태일 때 애니메이션 효과 */}
      {isActive && (
        <BaseEdge
          path={edgePath}
          style={{
            stroke: edgeStyle.stroke,
            strokeWidth: 1,
            opacity: 0.6,
            strokeDasharray: '4,4',
            animation: 'dash 1s linear infinite',
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
              'flex items-center gap-1 px-2 py-1 rounded-full text-white text-xs font-medium shadow-sm',
              'transition-all duration-200',
              isActive && 'scale-110 shadow-md'
            )}
            style={{
              backgroundColor: edgeStyle.stroke,
              opacity: isActive ? 1 : 0.8,
            }}
          >
            {getIcon()}
            <span>{getLabel()}</span>
            {messageCount > 0 && (
              <span className="ml-1 px-1 py-0.5 bg-white/20 rounded text-xs">
                {messageCount}
              </span>
            )}
          </div>
          
          {/* 마지막 메시지 툴팁 */}
          {data?.lastMessage && isActive && (
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-1 px-2 py-1 bg-gray-900 text-white text-xs rounded shadow-lg max-w-48 truncate">
              {data.lastMessage}
            </div>
          )}
        </div>
      </EdgeLabelRenderer>

      <style jsx>{`
        @keyframes dash {
          to {
            stroke-dashoffset: -8;
          }
        }
      `}</style>
    </>
  );
};