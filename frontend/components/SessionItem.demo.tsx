'use client';

/**
 * Demo page for SessionItem component
 * This file demonstrates the SessionItem component with sample data
 * 
 * To use: Create a page at app/demo/session-item/page.tsx and import this component
 */

import React, { useState } from 'react';
import SessionItem from './SessionItem';
import { SessionResponse } from '@/lib/types';

// Sample session data
const sampleSessions: SessionResponse[] = [
  {
    id: '1',
    user_id: 'user-1',
    title: 'Machine Learning Research',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    message_count: 12,
  },
  {
    id: '2',
    user_id: 'user-1',
    title: 'Project Planning Discussion',
    created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), // 5 hours ago
    updated_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    message_count: 8,
  },
  {
    id: '3',
    user_id: 'user-1',
    title: 'Code Review Notes',
    created_at: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(), // Yesterday
    updated_at: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(),
    message_count: 15,
  },
  {
    id: '4',
    user_id: 'user-1',
    title: 'API Documentation Questions',
    created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
    updated_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    message_count: 6,
  },
  {
    id: '5',
    user_id: 'user-1',
    title: 'Database Schema Design',
    created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
    updated_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    message_count: 20,
  },
  {
    id: '6',
    user_id: 'user-1',
    title: 'Quick Question',
    created_at: new Date(Date.now() - 30 * 1000).toISOString(), // 30 seconds ago
    updated_at: new Date(Date.now() - 30 * 1000).toISOString(),
    message_count: 2,
  },
];

export default function SessionItemDemo() {
  const [sessions, setSessions] = useState<SessionResponse[]>(sampleSessions);
  const [activeSessionId, setActiveSessionId] = useState<string | null>('1');
  const [log, setLog] = useState<string[]>([]);

  const addLog = (message: string) => {
    setLog((prev) => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const handleSelect = (sessionId: string) => {
    setActiveSessionId(sessionId);
    addLog(`Selected session: ${sessionId}`);
  };

  const handleDelete = (sessionId: string) => {
    setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    if (activeSessionId === sessionId) {
      setActiveSessionId(null);
    }
    addLog(`Deleted session: ${sessionId}`);
  };

  const handleRename = (sessionId: string, newTitle: string) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === sessionId ? { ...s, title: newTitle } : s))
    );
    addLog(`Renamed session ${sessionId} to: "${newTitle}"`);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-2 text-gray-900 dark:text-gray-100">
          SessionItem Component Demo
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Interactive demonstration of the SessionItem component with all features
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Component Demo */}
          <div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
                Session List
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Try these interactions:
              </p>
              <ul className="text-sm text-gray-600 dark:text-gray-400 mb-6 space-y-1">
                <li>• Click to select a session</li>
                <li>• Double-click to edit the title</li>
                <li>• Hover to see the delete button</li>
                <li>• Press Enter to save, Escape to cancel</li>
              </ul>

              <div className="space-y-2">
                {sessions.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No sessions. All deleted!
                  </div>
                ) : (
                  sessions.map((session) => (
                    <SessionItem
                      key={session.id}
                      session={session}
                      isActive={session.id === activeSessionId}
                      onSelect={handleSelect}
                      onDelete={handleDelete}
                      onRename={handleRename}
                    />
                  ))
                )}
              </div>

              {sessions.length > 0 && (
                <button
                  onClick={() => setSessions(sampleSessions)}
                  className="mt-4 w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                >
                  Reset Sessions
                </button>
              )}
            </div>
          </div>

          {/* Right Column - Event Log and Info */}
          <div className="space-y-6">
            {/* Event Log */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
                Event Log
              </h2>
              <div className="bg-gray-50 dark:bg-gray-900 rounded p-4 h-64 overflow-y-auto font-mono text-xs">
                {log.length === 0 ? (
                  <div className="text-gray-500 dark:text-gray-400">
                    No events yet. Interact with the sessions to see events.
                  </div>
                ) : (
                  log.map((entry, index) => (
                    <div
                      key={index}
                      className="text-gray-700 dark:text-gray-300 mb-1"
                    >
                      {entry}
                    </div>
                  ))
                )}
              </div>
              <button
                onClick={() => setLog([])}
                className="mt-2 text-sm text-blue-500 hover:text-blue-600"
              >
                Clear Log
              </button>
            </div>

            {/* Component Info */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
                Component Features
              </h2>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Relative time formatting (Just now, Yesterday, etc.)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Active session highlighting with blue border</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Inline title editing (double-click)</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Delete with confirmation dialog</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Message count display</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Hover effects and transitions</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Dark mode support</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Keyboard navigation (Enter/Escape)</span>
                </li>
              </ul>
            </div>

            {/* Active Session Info */}
            {activeSessionId && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
                  Active Session
                </h2>
                {(() => {
                  const activeSession = sessions.find((s) => s.id === activeSessionId);
                  if (!activeSession) return null;
                  return (
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">ID:</span>{' '}
                        <span className="text-gray-900 dark:text-gray-100">
                          {activeSession.id}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Title:</span>{' '}
                        <span className="text-gray-900 dark:text-gray-100">
                          {activeSession.title}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Messages:</span>{' '}
                        <span className="text-gray-900 dark:text-gray-100">
                          {activeSession.message_count}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Updated:</span>{' '}
                        <span className="text-gray-900 dark:text-gray-100">
                          {new Date(activeSession.updated_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
