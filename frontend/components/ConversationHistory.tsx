'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { SessionResponse } from '@/lib/types';
import { apiClient } from '@/lib/api-client';
import { useAuth } from '@/contexts/AuthContext';
import SessionItem from './SessionItem';
import MessageSearch from './MessageSearch';
import { Button } from './Button';

interface ConversationHistoryProps {
  activeSessionId?: string;
  onSessionSelect?: (sessionId: string) => void;
}

const ConversationHistory: React.FC<ConversationHistoryProps> = React.memo(({
  activeSessionId,
  onSessionSelect,
}) => {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  
  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [hasMore, setHasMore] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [showMessageSearch, setShowMessageSearch] = useState(false);

  const LIMIT = 20;

  /**
   * Fetch sessions from API.
   */
  const fetchSessions = React.useCallback(async (offset: number = 0, append: boolean = false) => {
    try {
      if (!append) {
        setIsLoading(true);
      } else {
        setIsLoadingMore(true);
      }
      setError(null);

      const response = await apiClient.getSessions(LIMIT, offset);
      
      if (append) {
        setSessions((prev) => [...prev, ...response.sessions]);
      } else {
        setSessions(response.sessions);
      }
      
      // Check if there are more sessions to load
      setHasMore(offset + response.sessions.length < response.total);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
      setError(err instanceof Error ? err.message : 'Failed to load conversations');
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, []);

  /**
   * Load sessions on mount if authenticated.
   */
  useEffect(() => {
    if (isAuthenticated) {
      fetchSessions();
    } else {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  /**
   * Create a new conversation.
   */
  const handleNewConversation = React.useCallback(async () => {
    try {
      const newSession = await apiClient.createSession();
      
      // Add to the top of the list
      setSessions((prev) => [newSession, ...prev]);
      
      // Navigate to the new session
      if (onSessionSelect) {
        onSessionSelect(newSession.id);
      } else {
        router.push(`/?session=${newSession.id}`);
      }
      
      // Close mobile sidebar
      setIsMobileOpen(false);
    } catch (err) {
      console.error('Failed to create session:', err);
      setError(err instanceof Error ? err.message : 'Failed to create conversation');
    }
  }, [onSessionSelect, router]);

  /**
   * Handle session selection.
   */
  const handleSessionSelect = React.useCallback((sessionId: string) => {
    if (onSessionSelect) {
      onSessionSelect(sessionId);
    } else {
      router.push(`/?session=${sessionId}`);
    }
    
    // Close mobile sidebar
    setIsMobileOpen(false);
  }, [onSessionSelect, router]);

  /**
   * Handle session deletion.
   */
  const handleSessionDelete = React.useCallback(async (sessionId: string) => {
    try {
      await apiClient.deleteSession(sessionId);
      
      // Remove from list
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      
      // If deleted session was active, navigate to home
      if (sessionId === activeSessionId) {
        router.push('/');
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete conversation');
    }
  }, [activeSessionId, router]);

  /**
   * Handle session rename.
   */
  const handleSessionRename = React.useCallback(async (sessionId: string, newTitle: string) => {
    try {
      const updatedSession = await apiClient.updateSession(sessionId, newTitle);
      
      // Update in list
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? updatedSession : s))
      );
    } catch (err) {
      console.error('Failed to rename session:', err);
      setError(err instanceof Error ? err.message : 'Failed to rename conversation');
    }
  }, []);

  /**
   * Load more sessions (pagination).
   */
  const handleLoadMore = React.useCallback(() => {
    fetchSessions(sessions.length, true);
  }, [fetchSessions, sessions.length]);

  /**
   * Filter sessions by search query (local filter).
   */
  const filteredSessions = React.useMemo(() => 
    sessions.filter((session) =>
      session.title.toLowerCase().includes(searchQuery.toLowerCase())
    ),
    [sessions, searchQuery]
  );

  // Don't render if not authenticated
  if (!isAuthenticated) {
    return null;
  }

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        aria-label="Toggle conversation history"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6 text-gray-700 dark:text-gray-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>

      {/* Overlay for mobile */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          fixed lg:static inset-y-0 left-0 z-40
          w-80 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800
          flex flex-col
          transition-transform duration-300 ease-in-out
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Conversations
            </h2>
            
            {/* Close button for mobile */}
            <button
              onClick={() => setIsMobileOpen(false)}
              className="lg:hidden p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
              aria-label="Close sidebar"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5 text-gray-500 dark:text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            {/* New Conversation button */}
            <Button
              onClick={handleNewConversation}
              variant="primary"
              className="flex-1"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 4v16m8-8H4"
                />
              </svg>
              New
            </Button>

            {/* Global Search button */}
            <Button
              onClick={() => setShowMessageSearch(true)}
              variant="secondary"
              title="Search all messages"
              isIconOnly
            >
              <svg
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </Button>
          </div>

          {/* Search input */}
          <div className="mt-3 relative">
            <input
              type="text"
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 pl-9 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-gray-900 dark:text-gray-100"
            />
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {isLoading ? (
            // Loading skeleton
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="animate-pulse bg-gray-200 dark:bg-gray-800 rounded-lg h-16"
                />
              ))}
            </div>
          ) : error ? (
            // Error state
            <div className="text-center py-8">
              <p className="text-red-600 dark:text-red-400 text-sm mb-2">
                {error}
              </p>
              <button
                onClick={() => fetchSessions()}
                className="text-blue-600 dark:text-blue-400 hover:underline text-sm"
              >
                Try again
              </button>
            </div>
          ) : filteredSessions.length === 0 ? (
            // Empty state
            <div className="text-center py-12">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-600 mb-3"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
              <p className="text-gray-500 dark:text-gray-400 text-sm">
                {searchQuery
                  ? 'No conversations found'
                  : 'Start a new conversation'}
              </p>
              {!searchQuery && (
                <button
                  onClick={handleNewConversation}
                  className="mt-3 text-blue-600 dark:text-blue-400 hover:underline text-sm"
                >
                  Create your first conversation
                </button>
              )}
            </div>
          ) : (
            // Session list
            <>
              {filteredSessions.map((session) => (
                <SessionItem
                  key={session.id}
                  session={session}
                  isActive={session.id === activeSessionId}
                  onSelect={handleSessionSelect}
                  onDelete={handleSessionDelete}
                  onRename={handleSessionRename}
                />
              ))}

              {/* Load more button */}
              {hasMore && !searchQuery && (
                <button
                  onClick={handleLoadMore}
                  disabled={isLoadingMore}
                  className="w-full py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoadingMore ? 'Loading...' : 'Load more'}
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Message Search Modal */}
      {showMessageSearch && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-2xl h-[600px] shadow-2xl">
            <MessageSearch onClose={() => setShowMessageSearch(false)} />
          </div>
        </div>
      )}
    </>
  );
});

ConversationHistory.displayName = 'ConversationHistory';

export default ConversationHistory;
