/**
 * User Cursor Component
 * 
 * 다른 사용자의 커서를 표시하는 컴포넌트
 */
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CollaborativeUser, CursorPosition } from '@/hooks/useCollaboration';

interface UserCursorProps {
  user: CollaborativeUser;
  position: CursorPosition;
  isVisible: boolean;
}

export const UserCursor: React.FC<UserCursorProps> = ({
  user,
  position,
  isVisible
}) => {
  if (!isVisible || !user.isOnline) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.8 }}
        transition={{ duration: 0.2 }}
        className="absolute pointer-events-none z-50"
        style={{
          left: position.x,
          top: position.y,
          transform: 'translate(-2px, -2px)'
        }}
      >
        {/* 커서 아이콘 */}
        <div className="relative">
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M2 2L18 8L8 12L2 18V2Z"
              fill={user.color}
              stroke="white"
              strokeWidth="1"
            />
          </svg>
          
          {/* 사용자 이름 라벨 */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute left-5 top-0 whitespace-nowrap"
          >
            <div
              className="px-2 py-1 rounded text-white text-xs font-medium shadow-lg"
              style={{ backgroundColor: user.color }}
            >
              {user.name}
            </div>
            
            {/* 말풍선 꼬리 */}
            <div
              className="absolute left-0 top-1/2 transform -translate-x-1 -translate-y-1/2"
              style={{
                width: 0,
                height: 0,
                borderTop: '4px solid transparent',
                borderBottom: '4px solid transparent',
                borderRight: `4px solid ${user.color}`
              }}
            />
          </motion.div>
        </div>

        {/* 현재 편집 중인 노드 표시 */}
        {position.nodeId && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-8 left-5"
          >
            <div
              className="px-2 py-1 rounded text-white text-xs"
              style={{ backgroundColor: user.color }}
            >
              편집 중
            </div>
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};