'use client';

import React, { useState, useRef, useEffect } from 'react';
import { SessionResponse } from '@/lib/types';

interface SessionItemProps {
  session: SessionResponse;
  isActive: boolean;
  onSelect: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
  onRename: (sessionId: string, newTitle: string) => void;
}

/**
 * Format a date as a relative time string (e.g., "2 hours ago", "Yesterday")
 */
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return 'Just now';
  } else if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return `${diffDays} days ago`;
  } else {
    // Format as date for older items
    return date.toLocaleDateString();
  }
}

const SessionItem = React.memo(function SessionItem({
  session,
  isActive,
  onSelect,
  onDelete,
  onRename,
}: SessionItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(session.title);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleDoubleClick = () => {
    if (!isEditing) {
      setIsEditing(true);
      setEditedTitle(session.title);
    }
  };

  const handleSave = () => {
    const trimmedTitle = editedTitle.trim();
    if (trimmedTitle && trimmedTitle !== session.title) {
      onRename(session.id, trimmedTitle);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditedTitle(session.title);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    const confirmed = window.confirm(
      `Are you sure you want to delete "${session.title}"? This action cannot be undone.`
    );
    if (confirmed) {
      onDelete(session.id);
    }
  };

  const handleClick = () => {
    if (!isEditing) {
      onSelect(session.id);
    }
  };

  const relativeTime = formatRelativeTime(session.updated_at);

  return (
    <div
      className={`
        group relative px-3 py-2 rounded-lg cursor-pointer transition-all duration-200
        ${
          isActive
            ? 'bg-blue-100 dark:bg-blue-900/30 border-l-4 border-blue-500'
            : 'hover:bg-gray-100 dark:hover:bg-gray-800 border-l-4 border-transparent'
        }
      `}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      role="button"
      tabIndex={0}
      aria-label={`Session: ${session.title}`}
      aria-current={isActive ? 'page' : undefined}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {isEditing ? (
            <input
              ref={inputRef}
              type="text"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={handleSave}
              onClick={(e) => e.stopPropagation()}
              className="w-full px-2 py-1 text-sm font-medium bg-white dark:bg-gray-700 border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          ) : (
            <h3
              className={`
                text-sm font-medium truncate
                ${
                  isActive
                    ? 'text-blue-900 dark:text-blue-100'
                    : 'text-gray-900 dark:text-gray-100'
                }
              `}
              title={session.title}
            >
              {session.title}
            </h3>
          )}
          <div className="flex items-center gap-2 mt-1">
            <p
              className={`
                text-xs
                ${
                  isActive
                    ? 'text-blue-700 dark:text-blue-300'
                    : 'text-gray-500 dark:text-gray-400'
                }
              `}
            >
              {relativeTime}
            </p>
            {session.message_count > 0 && (
              <>
                <span
                  className={`
                    text-xs
                    ${
                      isActive
                        ? 'text-blue-700 dark:text-blue-300'
                        : 'text-gray-400 dark:text-gray-500'
                    }
                  `}
                >
                  •
                </span>
                <p
                  className={`
                    text-xs
                    ${
                      isActive
                        ? 'text-blue-700 dark:text-blue-300'
                        : 'text-gray-500 dark:text-gray-400'
                    }
                  `}
                >
                  {session.message_count} message{session.message_count !== 1 ? 's' : ''}
                </p>
              </>
            )}
          </div>
        </div>

        {/* Delete button - visible on hover or when active */}
        <button
          onClick={handleDeleteClick}
          className={`
            flex-shrink-0 p-1 rounded transition-all duration-200
            ${
              isActive
                ? 'text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30'
                : 'text-gray-400 dark:text-gray-500 opacity-0 group-hover:opacity-100 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
            }
          `}
          title="Delete conversation"
          aria-label="Delete conversation"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      </div>

      {/* Edit hint - shown on hover when not editing */}
      {!isEditing && (
        <div
          className={`
            absolute bottom-1 right-1 text-xs opacity-0 group-hover:opacity-100 transition-opacity duration-200
            ${
              isActive
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-gray-400 dark:text-gray-500'
            }
          `}
        >
          Double-click to edit
        </div>
      )}
    </div>
  );
});

export default SessionItem;
