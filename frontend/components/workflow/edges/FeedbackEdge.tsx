'use client';

import React from 'react';
import {
  EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from 'reactflow';
import { ArrowLeft, Star, AlertTriangle, CheckCircle2, XCircle, MessageCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FeedbackEdgeData {
  feedbackType: 'positive' | 'negative' | 'neutral' | 'suggestion' | 'correction';
  rating?: number; // 1-5 stars
  message?: string;
  isRead?: boolean;
  timestamp?: string;
  severity?: 'low' | 'medium' | 'high';
  actionRequired?: boolean;
}

export const FeedbackEdge: React.FC<EdgeProps<FeedbackEdgeData>> = ({
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

  const feedbackType = data?.feedbackType || 'neutral';
  const rating = data?.rating || 0;
  const isRead = data?.isRead || false;
  const actionRequired = data?.actionRequired || false;

  // 피드백 타입별 스타일 정의
  const getEdgeStyle = () => {
    const baseStyle = {
      strokeWidth: isRead ? 2 : 3,
      opacity: isRead ? 0.6 : 1,
    };

    switch (feedbackType) {
      case 'positive':
        return {
          ...baseStyle,
          stroke: '#10B981',
          strokeDasharray: '8,3',
        };
      case 'negative':
        return {
          ...baseStyle,
          stroke: '#EF4444',
          strokeDasharray: '6,6',
        };
      case 'suggestion':
        return {
          ...baseStyle,
          stroke: '#3B82F6',
          strokeDasharray: '10,5',
        };
      case 'correction':
        return {
          ...baseStyle,
          stroke: '#F59E0B',
          strokeDasharray: '12,4,4,4',
        };
      case 'neutral':
      default:
        return {
          ...baseStyle,
          stroke: '#6B7280',
          strokeDasharray: '5,5',
        };
    }
  };

  // 피드백 타입별 아이콘
  const getIcon = () => {
    switch (feedbackType) {
      case 'positive':
        return <CheckCircle2 className="w-3 h-3" />;
      case 'negative':
        return <XCircle className="w-3 h-3" />;
      case 'suggestion':
        return <MessageCircle className="w-3 h-3" />;
      case 'correction':
        return <AlertTriangle className="w-3 h-3" />;
      case 'neutral':
      default:
        return <ArrowLeft className="w-3 h-3" />;
    }
  };

  // 피드백 타입별 라벨
  const getLabel = () => {
    switch (feedbackType) {
      case 'positive':
        return '긍정적 피드백';
      case 'negative':
        return '부정적 피드백';
      case 'suggestion':
        return '개선 제안';
      case 'correction':
        return '수정 요청';
      case 'neutral':
      default:
        return '피드백';
    }
  };

  // 별점 렌더링
  const renderStars = () => {
    if (rating === 0) return null;
    
    return (
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={cn(
              'w-2 h-2',
              star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
            )}
          />
        ))}
      </div>
    );
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
          filter: !isRead && actionRequired ? 'drop-shadow(0 0 6px currentColor)' : 'none',
        }}
      />
      
      {/* 읽지 않은 중요 피드백 애니메이션 */}
      {!isRead && actionRequired && (
        <BaseEdge
          path={edgePath}
          style={{
            stroke: edgeStyle.stroke,
            strokeWidth: 1,
            opacity: 0.4,
            strokeDasharray: '4,4',
            animation: 'feedback-pulse 2s ease-in-out infinite',
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
              !isRead && 'scale-110',
              isRead && 'opacity-75'
            )}
            style={{
              backgroundColor: edgeStyle.stroke,
              opacity: isRead ? 0.7 : 1,
            }}
          >
            {/* 상태 표시 */}
            <div className="flex items-center gap-1">
              {getIcon()}
              <span>{getLabel()}</span>
              {!isRead && (
                <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              )}
            </div>
            
            {/* 별점 표시 */}
            {rating > 0 && (
              <div className="flex items-center gap-1">
                {renderStars()}
                <span className="text-xs opacity-90">({rating}/5)</span>
              </div>
            )}
            
            {/* 액션 필요 표시 */}
            {actionRequired && !isRead && (
              <div className="flex items-center gap-1 text-xs bg-white/20 px-2 py-0.5 rounded">
                <AlertTriangle className="w-2 h-2" />
                <span>액션 필요</span>
              </div>
            )}
          </div>
          
          {/* 피드백 메시지 툴팁 */}
          {data?.message && (
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg max-w-64">
              <div className="font-medium mb-1">피드백 내용:</div>
              <div className="opacity-90">{data.message}</div>
              {data.timestamp && (
                <div className="text-xs opacity-60 mt-1">{data.timestamp}</div>
              )}
            </div>
          )}
        </div>
      </EdgeLabelRenderer>

      <style jsx>{`
        @keyframes feedback-pulse {
          0%, 100% {
            opacity: 0.4;
          }
          50% {
            opacity: 0.8;
          }
        }
      `}</style>
    </>
  );
};