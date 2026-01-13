'use client';

import React from 'react';
import {
  EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from 'reactflow';
import { Radio, Users, Zap, Clock, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BroadcastEdgeData {
  broadcastStatus: 'sending' | 'delivered' | 'failed' | 'pending';
  totalRecipients?: number;
  deliveredCount?: number;
  failedCount?: number;
  messageType?: 'announcement' | 'alert' | 'update' | 'command';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  timestamp?: string;
  deliveryRate?: number; // 0-1
}

export const BroadcastEdge: React.FC<EdgeProps<BroadcastEdgeData>> = ({
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

  const broadcastStatus = data?.broadcastStatus || 'pending';
  const totalRecipients = data?.totalRecipients || 0;
  const deliveredCount = data?.deliveredCount || 0;
  const failedCount = data?.failedCount || 0;
  const messageType = data?.messageType || 'announcement';
  const priority = data?.priority || 'medium';

  // 브로드캐스트 상태별 스타일 정의
  const getEdgeStyle = () => {
    const baseStyle = {
      strokeWidth: priority === 'urgent' ? 4 : priority === 'high' ? 3 : 2,
    };

    switch (broadcastStatus) {
      case 'sending':
        return {
          ...baseStyle,
          stroke: '#3B82F6',
          strokeDasharray: '10,5',
          opacity: 1,
        };
      case 'delivered':
        return {
          ...baseStyle,
          stroke: '#10B981',
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
          strokeDasharray: '4,4',
          opacity: 0.5,
        };
      default:
        return baseStyle;
    }
  };

  // 우선순위별 색상
  const getPriorityColor = () => {
    switch (priority) {
      case 'urgent':
        return '#DC2626';
      case 'high':
        return '#F59E0B';
      case 'medium':
        return '#3B82F6';
      case 'low':
        return '#6B7280';
      default:
        return '#3B82F6';
    }
  };

  // 메시지 타입별 아이콘
  const getMessageIcon = () => {
    switch (messageType) {
      case 'announcement':
        return <Radio className="w-3 h-3" />;
      case 'alert':
        return <Zap className="w-3 h-3" />;
      case 'update':
        return <CheckCircle2 className="w-3 h-3" />;
      case 'command':
        return <Users className="w-3 h-3" />;
      default:
        return <Radio className="w-3 h-3" />;
    }
  };

  // 상태별 아이콘
  const getStatusIcon = () => {
    switch (broadcastStatus) {
      case 'sending':
        return <Radio className="w-3 h-3 animate-pulse" />;
      case 'delivered':
        return <CheckCircle2 className="w-3 h-3" />;
      case 'failed':
        return <Zap className="w-3 h-3" />;
      case 'pending':
        return <Clock className="w-3 h-3" />;
      default:
        return <Radio className="w-3 h-3" />;
    }
  };

  // 상태별 라벨
  const getStatusLabel = () => {
    switch (broadcastStatus) {
      case 'sending':
        return '전송 중';
      case 'delivered':
        return '전송 완료';
      case 'failed':
        return '전송 실패';
      case 'pending':
        return '전송 대기';
      default:
        return '브로드캐스트';
    }
  };

  const edgeStyle = getEdgeStyle();
  const deliveryProgress = totalRecipients > 0 ? ((deliveredCount + failedCount) / totalRecipients) * 100 : 0;
  const successRate = (deliveredCount + failedCount) > 0 ? (deliveredCount / (deliveredCount + failedCount)) * 100 : 0;

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          ...edgeStyle,
          filter: broadcastStatus === 'sending' ? 'drop-shadow(0 0 8px currentColor)' : 'none',
        }}
      />
      
      {/* 전송 중 애니메이션 효과 */}
      {broadcastStatus === 'sending' && (
        <>
          <BaseEdge
            path={edgePath}
            style={{
              stroke: '#3B82F6',
              strokeWidth: 1,
              opacity: 0.3,
              strokeDasharray: '6,6',
              animation: 'broadcast-wave 1.5s ease-in-out infinite',
            }}
          />
          <BaseEdge
            path={edgePath}
            style={{
              stroke: '#3B82F6',
              strokeWidth: 1,
              opacity: 0.2,
              strokeDasharray: '12,12',
              animation: 'broadcast-wave 1.5s ease-in-out infinite 0.5s',
            }}
          />
        </>
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
              broadcastStatus === 'sending' && 'scale-110 shadow-xl'
            )}
            style={{
              backgroundColor: edgeStyle.stroke,
              opacity: broadcastStatus === 'sending' ? 1 : 0.9,
            }}
          >
            {/* 상태 및 우선순위 표시 */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1">
                {getStatusIcon()}
                <span>{getStatusLabel()}</span>
              </div>
              
              {/* 우선순위 표시 */}
              {priority !== 'medium' && (
                <div 
                  className="px-1.5 py-0.5 rounded text-xs font-bold"
                  style={{ backgroundColor: getPriorityColor() }}
                >
                  {priority === 'urgent' ? '긴급' : 
                   priority === 'high' ? '높음' : 
                   priority === 'low' ? '낮음' : '보통'}
                </div>
              )}
            </div>
            
            {/* 전송 진행률 (전송 중일 때) */}
            {broadcastStatus === 'sending' && totalRecipients > 0 && (
              <div className="flex flex-col items-center gap-1 w-full">
                <div className="w-full bg-white/20 rounded-full h-1.5">
                  <div 
                    className="bg-white rounded-full h-1.5 transition-all duration-300"
                    style={{ width: `${deliveryProgress}%` }}
                  />
                </div>
                
                <div className="flex items-center gap-2 text-xs">
                  <div className="flex items-center gap-1">
                    <CheckCircle2 className="w-2 h-2 text-green-300" />
                    <span>{deliveredCount}</span>
                  </div>
                  {failedCount > 0 && (
                    <div className="flex items-center gap-1">
                      <Zap className="w-2 h-2 text-red-300" />
                      <span>{failedCount}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1 opacity-80">
                    <Users className="w-2 h-2" />
                    <span>{totalRecipients}</span>
                  </div>
                </div>
              </div>
            )}
            
            {/* 완료된 전송 결과 */}
            {broadcastStatus === 'delivered' && totalRecipients > 0 && (
              <div className="flex items-center gap-2 text-xs opacity-90">
                <span>{deliveredCount}/{totalRecipients}</span>
                <span>({successRate.toFixed(0)}% 성공)</span>
              </div>
            )}
            
            {/* 메시지 타입 */}
            <div className="flex items-center gap-1 text-xs opacity-80">
              {getMessageIcon()}
              <span>
                {messageType === 'announcement' ? '공지' :
                 messageType === 'alert' ? '알림' :
                 messageType === 'update' ? '업데이트' :
                 messageType === 'command' ? '명령' : '메시지'}
              </span>
            </div>
          </div>
        </div>
      </EdgeLabelRenderer>

      <style jsx>{`
        @keyframes broadcast-wave {
          0% {
            stroke-dashoffset: 0;
            opacity: 0.3;
          }
          50% {
            opacity: 0.1;
          }
          100% {
            stroke-dashoffset: -18;
            opacity: 0.3;
          }
        }
      `}</style>
    </>
  );
};