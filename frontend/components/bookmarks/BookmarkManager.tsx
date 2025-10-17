'use client';

/**
 * Bookmark Manager Component
 * Manage bookmarks and favorites for conversations and documents
 */

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface Bookmark {
  id: string;
  type: 'conversation' | 'document';
  itemId: string;
  title: string;
  description?: string;
  tags: string[];
  createdAt: string;
  isFavorite: boolean;
}

interface BookmarkManagerProps {
  userId?: string;
  className?: string;
}

export default function BookmarkManager({ userId, className }: BookmarkManagerProps) {
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [filter, setFilter] = useState<'all' | 'conversation' | 'document'>('all');
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchBookmarks();
  }, [userId]);

  const fetchBookmarks = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        ...(userId && { userId }),
      });
      
      const response = await fetch(`/api/bookmarks?${params}`);
      if (!response.ok) throw new Error('Failed to fetch bookmarks');
      
      const data = await response.json();
      setBookmarks(data.bookmarks);
    } catch (error) {
      console.error('Failed to fetch bookmarks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleFavorite = async (bookmarkId: string) => {
    try {
      const bookmark = bookmarks.find(b => b.id === bookmarkId);
      if (!bookmark) return;

      const response = await fetch(`/api/bookmarks/${bookmarkId}/favorite`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isFavorite: !bookmark.isFavorite }),
      });
      
      if (!response.ok) throw new Error('Failed to toggle favorite');
      
      setBookmarks(
        bookmarks.map(b =>
          b.id === bookmarkId ? { ...b, isFavorite: !b.isFavorite } : b
        )
      );
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  const handleRemoveBookmark = async (bookmarkId: string) => {
    try {
      const response = await fetch(`/api/bookmarks/${bookmarkId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) throw new Error('Failed to remove bookmark');
      
      setBookmarks(bookmarks.filter(b => b.id !== bookmarkId));
    } catch (error) {
      console.error('Failed to remove bookmark:', error);
    }
  };

  const handleToggleTag = (tag: string) => {
    setSelectedTags(
      selectedTags.includes(tag)
        ? selectedTags.filter(t => t !== tag)
        : [...selectedTags, tag]
    );
  };

  const filteredBookmarks = bookmarks.filter(bookmark => {
    // Filter by type
    if (filter !== 'all' && bookmark.type !== filter) return false;
    
    // Filter by favorites
    if (showFavoritesOnly && !bookmark.isFavorite) return false;
    
    // Filter by search query
    if (searchQuery && !bookmark.title.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    
    // Filter by tags
    if (selectedTags.length > 0) {
      const hasAllTags = selectedTags.every(tag => bookmark.tags.includes(tag));
      if (!hasAllTags) return false;
    }
    
    return true;
  });

  const allTags = Array.from(new Set(bookmarks.flatMap(b => b.tags)));

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Bookmarks & Favorites
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {filteredBookmarks.length} items
          </p>
        </div>

        <button
          onClick={fetchBookmarks}
          className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700 space-y-4">
        {/* Search */}
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search bookmarks..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <svg className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        {/* Type filter */}
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('all')}
            className={cn(
              'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            )}
          >
            All
          </button>
          <button
            onClick={() => setFilter('conversation')}
            className={cn(
              'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
              filter === 'conversation'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            )}
          >
            💬 Conversations
          </button>
          <button
            onClick={() => setFilter('document')}
            className={cn(
              'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
              filter === 'document'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            )}
          >
            📄 Documents
          </button>
        </div>

        {/* Favorites toggle */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showFavoritesOnly}
            onChange={(e) => setShowFavoritesOnly(e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">
            ⭐ Show favorites only
          </span>
        </label>

        {/* Tags */}
        {allTags.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Filter by tags
            </label>
            <div className="flex flex-wrap gap-2">
              {allTags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => handleToggleTag(tag)}
                  className={cn(
                    'px-3 py-1 text-sm rounded-lg transition-colors',
                    selectedTags.includes(tag)
                      ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-2 border-purple-500'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-200 dark:hover:bg-gray-600'
                  )}
                >
                  #{tag}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Bookmarks list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading bookmarks...</p>
          </div>
        </div>
      ) : filteredBookmarks.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
          <p className="text-gray-600 dark:text-gray-400">No bookmarks found</p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
            Start bookmarking conversations and documents
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredBookmarks.map((bookmark) => (
            <div
              key={bookmark.id}
              className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">
                    {bookmark.type === 'conversation' ? '💬' : '📄'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                      {bookmark.title}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(bookmark.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => handleToggleFavorite(bookmark.id)}
                  className="text-2xl hover:scale-110 transition-transform"
                >
                  {bookmark.isFavorite ? '⭐' : '☆'}
                </button>
              </div>

              {/* Description */}
              {bookmark.description && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                  {bookmark.description}
                </p>
              )}

              {/* Tags */}
              {bookmark.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {bookmark.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={() => window.location.href = `/${bookmark.type}s/${bookmark.itemId}`}
                  className="flex-1 px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Open
                </button>
                <button
                  onClick={() => handleRemoveBookmark(bookmark.id)}
                  className="px-3 py-1.5 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
