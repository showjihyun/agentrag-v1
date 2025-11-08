'use client';

import React from 'react';
import { CollaborationUser } from '@/lib/websocket/collaboration-client';

interface CursorOverlayProps {
  users: CollaborationUser[];
}

export function CursorOverlay({ users }: CursorOverlayProps) {
  return (
    <div className="absolute inset-0 pointer-events-none z-10">
      {users.map((user) => {
        if (!user.cursor) return null;

        return (
          <div
            key={user.id}
            className="absolute transition-all duration-100"
            style={{
              left: user.cursor.x,
              top: user.cursor.y,
            }}
          >
            {/* Cursor */}
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="drop-shadow-md"
            >
              <path
                d="M2 2L18 10L10 12L8 18L2 2Z"
                fill={user.color}
                stroke="white"
                strokeWidth="1"
              />
            </svg>

            {/* User label */}
            <div
              className="absolute top-5 left-5 px-2 py-1 rounded text-xs font-medium text-white whitespace-nowrap shadow-lg"
              style={{ backgroundColor: user.color }}
            >
              {user.name}
            </div>

            {/* Selection highlight */}
            {user.selection && (
              <div
                className="absolute opacity-30"
                style={{
                  backgroundColor: user.color,
                  // Position based on selection - this would need more complex calculation
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
