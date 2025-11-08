'use client';

import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { Trash2, Database, AlertTriangle, RefreshCw } from 'lucide-react';

export default function AdminActions() {
  const [isOpen, setIsOpen] = useState(false);
  const [showConfirm, setShowConfirm] = useState<'milvus' | 'files' | 'all' | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleResetMilvus = async () => {
    setIsLoading(true);
    setMessage(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/admin/reset-milvus', {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessage({ type: 'success', text: data.message });
        setTimeout(() => setMessage(null), 5000);
      } else {
        throw new Error('Failed to reset Milvus');
      }
    } catch (error) {
      console.error('Error resetting Milvus:', error);
      setMessage({ type: 'error', text: 'Failed to reset Milvus database' });
    } finally {
      setIsLoading(false);
      setShowConfirm(null);
    }
  };

  const handleDeleteFiles = async () => {
    setIsLoading(true);
    setMessage(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/admin/delete-all-files', {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessage({ type: 'success', text: data.message });
        setTimeout(() => setMessage(null), 5000);
      } else {
        throw new Error('Failed to delete files');
      }
    } catch (error) {
      console.error('Error deleting files:', error);
      setMessage({ type: 'error', text: 'Failed to delete uploaded files' });
    } finally {
      setIsLoading(false);
      setShowConfirm(null);
    }
  };

  const handleResetAll = async () => {
    setIsLoading(true);
    setMessage(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/admin/reset-all', {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        setMessage({ type: 'success', text: data.message });
        setTimeout(() => setMessage(null), 5000);
      } else {
        throw new Error('Failed to reset system');
      }
    } catch (error) {
      console.error('Error resetting system:', error);
      setMessage({ type: 'error', text: 'Failed to reset system' });
    } finally {
      setIsLoading(false);
      setShowConfirm(null);
    }
  };

  const confirmAction = () => {
    switch (showConfirm) {
      case 'milvus':
        handleResetMilvus();
        break;
      case 'files':
        handleDeleteFiles();
        break;
      case 'all':
        handleResetAll();
        break;
    }
  };

  return (
    <>
      {/* Main Button */}
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors shadow-md hover:shadow-lg"
          title="Admin Actions"
        >
          <Database className="w-4 h-4" />
          <span className="text-sm font-medium hidden sm:inline">Admin</span>
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-xl z-50">
            <div className="p-2">
              <div className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                Danger Zone
              </div>
              
              <button
                onClick={() => {
                  setShowConfirm('milvus');
                  setIsOpen(false);
                }}
                disabled={isLoading}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                <Database className="w-4 h-4 text-red-500" />
                <span>Reset Milvus DB</span>
              </button>
              
              <button
                onClick={() => {
                  setShowConfirm('files');
                  setIsOpen(false);
                }}
                disabled={isLoading}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4 text-red-500" />
                <span>Delete All Files</span>
              </button>
              
              <div className="my-2 border-t border-gray-200 dark:border-gray-700" />
              
              <button
                onClick={() => {
                  setShowConfirm('all');
                  setIsOpen(false);
                }}
                disabled={isLoading}
                className="w-full px-3 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded flex items-center gap-2 font-semibold transition-colors disabled:opacity-50"
              >
                <AlertTriangle className="w-4 h-4" />
                <span>Reset Everything</span>
              </button>
            </div>
          </div>
        )}

        {/* Backdrop */}
        {isOpen && (
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
        )}
      </div>

      {/* Confirmation Modal */}
      {showConfirm && typeof window !== 'undefined' && createPortal(
        <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => !isLoading && setShowConfirm(null)}
          />
          
          {/* Modal */}
          <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-md w-full p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  {showConfirm === 'milvus' && 'Reset Milvus Database?'}
                  {showConfirm === 'files' && 'Delete All Files?'}
                  {showConfirm === 'all' && 'Reset Everything?'}
                </h3>
                
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {showConfirm === 'milvus' && 'This will delete all vector embeddings from Milvus. You will need to re-upload and re-process all documents.'}
                  {showConfirm === 'files' && 'This will permanently delete all uploaded files from the server. This action cannot be undone.'}
                  {showConfirm === 'all' && 'This will delete ALL data including Milvus vectors and uploaded files. This action cannot be undone!'}
                </p>
                
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowConfirm(null)}
                    disabled={isLoading}
                    className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  
                  <button
                    onClick={confirmAction}
                    disabled={isLoading}
                    className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Processing...</span>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-4 h-4" />
                        <span>Confirm</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Success/Error Message */}
      {message && typeof window !== 'undefined' && createPortal(
        <div className="fixed top-4 right-4 z-[10001] animate-slide-in">
          <div className={`px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 ${
            message.type === 'success' 
              ? 'bg-green-500 text-white' 
              : 'bg-red-500 text-white'
          }`}>
            {message.type === 'success' ? (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            ) : (
              <AlertTriangle className="w-5 h-5" />
            )}
            <span className="text-sm font-medium">{message.text}</span>
            <button
              onClick={() => setMessage(null)}
              className="ml-2 hover:opacity-80"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>,
        document.body
      )}

      <style jsx>{`
        @keyframes slide-in {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }
      `}</style>
    </>
  );
}
