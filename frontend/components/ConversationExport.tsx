'use client';

/**
 * Conversation Export Component
 * Allows users to export conversations in PDF or Markdown format
 */

import React, { useState } from 'react';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: Array<{
    title: string;
    content: string;
  }>;
}

interface ConversationExportProps {
  conversationId: string;
  conversationTitle: string;
  messages: Message[];
  onClose?: () => void;
}

type ExportFormat = 'pdf' | 'markdown' | 'json';

export default function ConversationExport({
  conversationId,
  conversationTitle,
  messages,
  onClose,
}: ConversationExportProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('pdf');
  const [includeSources, setIncludeSources] = useState(true);
  const [includeTimestamps, setIncludeTimestamps] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [shareLink, setShareLink] = useState<string | null>(null);

  const exportFormats = [
    {
      value: 'pdf' as ExportFormat,
      label: 'PDF',
      icon: '📄',
      description: 'Professional document format',
    },
    {
      value: 'markdown' as ExportFormat,
      label: 'Markdown',
      icon: '📝',
      description: 'Plain text with formatting',
    },
    {
      value: 'json' as ExportFormat,
      label: 'JSON',
      icon: '💾',
      description: 'Raw data format',
    },
  ];

  const generateMarkdown = (): string => {
    let markdown = `# ${conversationTitle}\n\n`;
    markdown += `**Conversation ID:** ${conversationId}\n`;
    markdown += `**Exported:** ${new Date().toLocaleString()}\n`;
    markdown += `**Total Messages:** ${messages.length}\n\n`;
    markdown += '---\n\n';

    messages.forEach((message, index) => {
      const role = message.role === 'user' ? '👤 User' : '🤖 Assistant';
      markdown += `## ${role}\n\n`;
      
      if (includeTimestamps) {
        markdown += `*${new Date(message.timestamp).toLocaleString()}*\n\n`;
      }
      
      markdown += `${message.content}\n\n`;
      
      if (includeSources && message.sources && message.sources.length > 0) {
        markdown += `### Sources\n\n`;
        message.sources.forEach((source, idx) => {
          markdown += `${idx + 1}. **${source.title}**\n`;
          markdown += `   ${source.content.substring(0, 200)}...\n\n`;
        });
      }
      
      markdown += '---\n\n';
    });

    return markdown;
  };

  const generateJSON = (): string => {
    const data = {
      conversationId,
      title: conversationTitle,
      exportedAt: new Date().toISOString(),
      messageCount: messages.length,
      messages: messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
        ...(includeSources && msg.sources ? { sources: msg.sources } : {}),
      })),
    };
    return JSON.stringify(data, null, 2);
  };

  const handleExport = async () => {
    setIsExporting(true);
    
    try {
      let content: string;
      let filename: string;
      let mimeType: string;

      switch (selectedFormat) {
        case 'markdown':
          content = generateMarkdown();
          filename = `${conversationTitle.replace(/[^a-z0-9]/gi, '_')}.md`;
          mimeType = 'text/markdown';
          break;
        
        case 'json':
          content = generateJSON();
          filename = `${conversationTitle.replace(/[^a-z0-9]/gi, '_')}.json`;
          mimeType = 'application/json';
          break;
        
        case 'pdf':
          // For PDF, we'll need to call a backend API
          const response = await fetch('/api/export/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              conversationId,
              title: conversationTitle,
              messages,
              includeSources,
              includeTimestamps,
            }),
          });
          
          if (!response.ok) throw new Error('PDF export failed');
          
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${conversationTitle.replace(/[^a-z0-9]/gi, '_')}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          setIsExporting(false);
          return;
      }

      // Download for Markdown and JSON
      const blob = new Blob([content], { type: mimeType });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const handleGenerateShareLink = async () => {
    try {
      const response = await fetch('/api/conversations/share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversationId }),
      });
      
      if (!response.ok) throw new Error('Failed to generate share link');
      
      const data = await response.json();
      setShareLink(data.shareUrl);
    } catch (error) {
      console.error('Failed to generate share link:', error);
      alert('Failed to generate share link. Please try again.');
    }
  };

  const handleCopyShareLink = () => {
    if (shareLink) {
      navigator.clipboard.writeText(shareLink);
      alert('Share link copied to clipboard!');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Export Conversation
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
          {/* Format Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Export Format
            </label>
            <div className="grid grid-cols-3 gap-3">
              {exportFormats.map((format) => (
                <button
                  key={format.value}
                  onClick={() => setSelectedFormat(format.value)}
                  className={cn(
                    'p-4 rounded-lg border-2 transition-all text-left',
                    selectedFormat === format.value
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  )}
                >
                  <div className="text-2xl mb-2">{format.icon}</div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">
                    {format.label}
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {format.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Options */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Export Options
            </label>
            
            <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer">
              <input
                type="checkbox"
                checked={includeSources}
                onChange={(e) => setIncludeSources(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Include Sources
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Add source citations and references
                </div>
              </div>
            </label>

            <label className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer">
              <input
                type="checkbox"
                checked={includeTimestamps}
                onChange={(e) => setIncludeTimestamps(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Include Timestamps
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Show message timestamps
                </div>
              </div>
            </label>
          </div>

          {/* Share Link */}
          <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Share Link
              </label>
              {!shareLink && (
                <button
                  onClick={handleGenerateShareLink}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Generate Link
                </button>
              )}
            </div>
            
            {shareLink ? (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={shareLink}
                  readOnly
                  className="flex-1 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg"
                />
                <button
                  onClick={handleCopyShareLink}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Copy
                </button>
              </div>
            ) : (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Generate a shareable link to this conversation
              </p>
            )}
          </div>

          {/* Preview */}
          <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
            <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Preview
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
              <div>📊 {messages.length} messages</div>
              <div>📅 {new Date().toLocaleDateString()}</div>
              <div>📦 Format: {selectedFormat.toUpperCase()}</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
          {onClose && (
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleExport}
            disabled={isExporting}
            className={cn(
              'flex-1 px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors',
              isExporting
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            )}
          >
            {isExporting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Exporting...
              </span>
            ) : (
              `Export as ${selectedFormat.toUpperCase()}`
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
