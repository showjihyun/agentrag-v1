'use client';

import React from 'react';

interface StreamingIndicatorProps {
  stage?: string;
  className?: string;
}

/**
 * 스트리밍 진행 상황 표시 컴포넌트
 * 
 * AI 응답 생성 중 현재 단계를 시각적으로 표시하여
 * 사용자에게 진행 상황을 알립니다.
 */
export const StreamingIndicator: React.FC<StreamingIndicatorProps> = ({
  stage = 'AI가 응답을 생성하고 있습니다...',
  className = ''
}) => {
  return (
    <div className={`flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400 ${className}`}>
      {/* 애니메이션 점들 */}
      <div className="flex gap-1">
        <span 
          className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
          style={{ animationDelay: '0ms', animationDuration: '1s' }}
        />
        <span 
          className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
          style={{ animationDelay: '150ms', animationDuration: '1s' }}
        />
        <span 
          className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
          style={{ animationDelay: '300ms', animationDuration: '1s' }}
        />
      </div>
      
      {/* 단계 텍스트 */}
      <span className="animate-pulse">{stage}</span>
    </div>
  );
};

/**
 * 상세 진행 상황 표시 컴포넌트 (진행률 포함)
 */
export const DetailedStreamingIndicator: React.FC<{
  stage: string;
  progress?: number;
  className?: string;
}> = ({ stage, progress, className = '' }) => {
  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between">
        <StreamingIndicator stage={stage} />
        {progress !== undefined && (
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {Math.round(progress)}%
          </span>
        )}
      </div>
      
      {progress !== undefined && (
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-full rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
};

/**
 * 단계별 스트리밍 표시 컴포넌트
 */
export const StageStreamingIndicator: React.FC<{
  currentStage: 'analyzing' | 'searching' | 'generating' | 'finalizing';
  className?: string;
}> = ({ currentStage, className = '' }) => {
  const stages = [
    { key: 'analyzing', label: '분석 중', icon: '🔍' },
    { key: 'searching', label: '검색 중', icon: '📚' },
    { key: 'generating', label: '생성 중', icon: '✨' },
    { key: 'finalizing', label: '완료 중', icon: '✅' }
  ];

  const currentIndex = stages.findIndex(s => s.key === currentStage);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {stages.map((stage, index) => (
        <div
          key={stage.key}
          className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-all ${
            index === currentIndex
              ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
              : index < currentIndex
              ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'
          }`}
        >
          <span>{stage.icon}</span>
          <span>{stage.label}</span>
          {index === currentIndex && (
            <div className="flex gap-0.5 ml-1">
              <span className="w-1 h-1 bg-current rounded-full animate-pulse" />
              <span className="w-1 h-1 bg-current rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
              <span className="w-1 h-1 bg-current rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default StreamingIndicator;
