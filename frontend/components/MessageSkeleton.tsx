'use client';

import React from 'react';

/**
 * 메시지 로딩 스켈레톤 컴포넌트
 * 
 * 메시지 로딩 중 표시되는 스켈레톤으로
 * 레이아웃 시프트를 방지하고 체감 성능을 향상시킵니다.
 */
export const MessageSkeleton: React.FC = () => {
  return (
    <div className="flex justify-start animate-fadeIn">
      <div className="w-full max-w-3xl bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-md">
        <div className="animate-pulse">
          <div className="flex items-start gap-3">
            {/* 아바타 스켈레톤 */}
            <div className="flex-shrink-0 w-8 h-8 bg-gray-300 dark:bg-gray-700 rounded-full" />
            
            <div className="flex-1 space-y-3">
              {/* 이름 스켈레톤 */}
              <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-20" />
              
              {/* 텍스트 라인 스켈레톤 */}
              <div className="space-y-2">
                <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-full" />
                <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-5/6" />
                <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-4/6" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * 여러 메시지 스켈레톤을 표시하는 컴포넌트
 */
export const MessageSkeletonList: React.FC<{ count?: number }> = ({ count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <MessageSkeleton key={index} />
      ))}
    </>
  );
};

export default MessageSkeleton;
