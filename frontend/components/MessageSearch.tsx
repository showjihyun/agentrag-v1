'use client';

/**
 * Message Search Component
 * 
 * Global search across all user's conversations with:
 * - Search input with debouncing
 * - Results list with highlighting
 * - Navigation to conversations
 * - Pagination support
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';

interface MessageResult {
  id: number;
  session_id: string;
  session_title?: string;
  role: string;
  content: string;
  created_at: string;
}

interface Props {
  onClose?: () => void;
  className?: string;
}

export default function MessageSearch({ onClose, className = '' }: Props) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MessageResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Debounced search
  useEffect(() => {
    if (query.trim().length < 3) {
      setResults([]);
      setTotal(0);
      return;
    }

    const timer = setTimeout(() => {
      performSearch();
    }, 500);

    return () => clearTimeout(timer);
  }, [query]);

  const performSearch = async () => {
    setIsSearching(true);
    setError(null);

    try {
      const response = await apiClient.searchMessages(query.trim(), 20, 0);
      setResults(response.messages || []);
      setTotal(response.total || 0);
    } catch (err: any) {
      console.error('Search failed:', err);
      setError(err.message || 'Search failed');
      setResults([]);
      setTotal(0);
    } finally {
      setIsSearching(false);
    }
  };

  const handleResultClick = (message: MessageResult) => {
    // Navigate to the conversation
    router.push(`/?session=${message.session_id}`);
    onClose?.();
  };

  const highlightMatch = (text: string, searchQuery: string): string => {
    if (!searchQuery) return text;
    
    const regex = new RegExp(`(${searchQuery})`, 'gi');
    return text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800">$1</mark>');
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) {
      return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 7) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Search Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            🔍 Search Messages
          </h2>
          {onClose && (
            <button
              onClick={onClose}
              className="ml-auto text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              aria-label="Close search"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Search Input */}
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search across all conversations..."
            className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            autoFocus
          />
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            {isSearching ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            ) : (
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            )}
          </div>
        </div>

        {/* Results Count */}
        {total > 0 && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            Found {total} result{total !== 1 ? 's' : ''}
          </p>
        )}
      </div>

      {/* Results List */}
      <div className="flex-1 overflow-y-auto p-4">
        {error && (
          <div className="text-center py-8">
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {!error && query.trim().length < 3 && (
          <div className="text-center py-8">
            <svg className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <p className="text-gray-500 dark:text-gray-400">
              Type at least 3 characters to search
            </p>
          </div>
        )}

        {!error && query.trim().length >= 3 && results.length === 0 && !isSearching && (
          <div className="text-center py-8">
            <svg className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-gray-500 dark:text-gray-400">
              No results found for "{query}"
            </p>
          </div>
        )}

        {results.length > 0 && (
          <div className="space-y-2">
            {results.map((message) => (
              <div
                key={message.id}
                onClick={() => handleResultClick(message)}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
              >
                {/* Header */}
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {message.session_title || 'Untitled Conversation'}
                    </span>
                    {message.role === 'user' && (
                      <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded">
                        You
                      </span>
                    )}
                    {message.role === 'assistant' && (
                      <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded">
                        AI
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {formatDate(message.created_at)}
                  </span>
                </div>

                {/* Content Preview */}
                <p 
                  className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2"
                  dangerouslySetInnerHTML={{ 
                    __html: highlightMatch(message.content, query) 
                  }}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
