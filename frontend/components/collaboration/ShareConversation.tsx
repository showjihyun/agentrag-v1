'use client';

/**
 * Share Conversation Component
 * Allows users to share conversations with team members
 */

import React, { useState } from 'react';
import { cn } from '@/lib/utils';

interface ShareConversationProps {
  conversationId: string;
  conversationTitle: string;
  onClose?: () => void;
}

interface SharedUser {
  id: string;
  email: string;
  name: string;
  role: 'viewer' | 'editor' | 'admin';
  avatar?: string;
}

export default function ShareConversation({
  conversationId,
  conversationTitle,
  onClose,
}: ShareConversationProps) {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'viewer' | 'editor'>('viewer');
  const [sharedUsers, setSharedUsers] = useState<SharedUser[]>([]);
  const [isPublic, setIsPublic] = useState(false);
  const [publicLink, setPublicLink] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleShare = async () => {
    if (!email) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`/api/conversations/${conversationId}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, role }),
      });
      
      if (!response.ok) throw new Error('Failed to share');
      
      const data = await response.json();
      setSharedUsers([...sharedUsers, data.user]);
      setEmail('');
    } catch (error) {
      console.error('Failed to share:', error);
      alert('Failed to share conversation');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveUser = async (userId: string) => {
    try {
      const response = await fetch(
        `/api/conversations/${conversationId}/share/${userId}`,
        { method: 'DELETE' }
      );
      
      if (!response.ok) throw new Error('Failed to remove user');
      
      setSharedUsers(sharedUsers.filter(u => u.id !== userId));
    } catch (error) {
      console.error('Failed to remove user:', error);
      alert('Failed to remove user');
    }
  };

  const handleUpdateRole = async (userId: string, newRole: 'viewer' | 'editor') => {
    try {
      const response = await fetch(
        `/api/conversations/${conversationId}/share/${userId}`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role: newRole }),
        }
      );
      
      if (!response.ok) throw new Error('Failed to update role');
      
      setSharedUsers(
        sharedUsers.map(u => u.id === userId ? { ...u, role: newRole } : u)
      );
    } catch (error) {
      console.error('Failed to update role:', error);
      alert('Failed to update role');
    }
  };

  const handleTogglePublic = async () => {
    try {
      const response = await fetch(
        `/api/conversations/${conversationId}/public`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ isPublic: !isPublic }),
        }
      );
      
      if (!response.ok) throw new Error('Failed to toggle public');
      
      const data = await response.json();
      setIsPublic(!isPublic);
      if (data.publicLink) setPublicLink(data.publicLink);
    } catch (error) {
      console.error('Failed to toggle public:', error);
      alert('Failed to toggle public access');
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(publicLink);
    alert('Link copied to clipboard!');
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Share Conversation
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {conversationTitle}
            </p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Share with specific users */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Share with people
            </label>
            
            <div className="flex gap-2">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter email address"
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                onKeyPress={(e) => e.key === 'Enter' && handleShare()}
              />
              
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as 'viewer' | 'editor')}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="viewer">Viewer</option>
                <option value="editor">Editor</option>
              </select>
              
              <button
                onClick={handleShare}
                disabled={isLoading || !email}
                className={cn(
                  'px-6 py-2 rounded-lg font-medium transition-colors',
                  isLoading || !email
                    ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                )}
              >
                Share
              </button>
            </div>
          </div>

          {/* Shared users list */}
          {sharedUsers.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                People with access
              </h3>
              <div className="space-y-2">
                {sharedUsers.map((user) => (
                  <div
                    key={user.id}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                        {user.avatar ? (
                          <img src={user.avatar} alt={user.name} className="w-10 h-10 rounded-full" />
                        ) : (
                          <span className="text-blue-600 dark:text-blue-400 font-medium">
                            {user.name.charAt(0).toUpperCase()}
                          </span>
                        )}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {user.name}
                        </p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          {user.email}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <select
                        value={user.role}
                        onChange={(e) => handleUpdateRole(user.id, e.target.value as 'viewer' | 'editor')}
                        className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      >
                        <option value="viewer">Viewer</option>
                        <option value="editor">Editor</option>
                      </select>
                      
                      <button
                        onClick={() => handleRemoveUser(user.id)}
                        className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Public link */}
          <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Public Link
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  Anyone with the link can view
                </p>
              </div>
              
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={isPublic}
                  onChange={handleTogglePublic}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
            
            {isPublic && publicLink && (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={publicLink}
                  readOnly
                  className="flex-1 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg"
                />
                <button
                  onClick={handleCopyLink}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Copy
                </button>
              </div>
            )}
          </div>

          {/* Permissions info */}
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 dark:text-blue-300 mb-2">
              Permission Levels
            </h4>
            <ul className="text-xs text-blue-800 dark:text-blue-400 space-y-1">
              <li>• <strong>Viewer:</strong> Can view conversation and messages</li>
              <li>• <strong>Editor:</strong> Can view and add messages</li>
              <li>• <strong>Admin:</strong> Can manage sharing and permissions</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
            >
              Done
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
