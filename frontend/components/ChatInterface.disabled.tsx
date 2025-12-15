// ChatInterface component - Disabled for workflow-focused platform
// This component was part of the RAG chat functionality
// Moved to .disabled.tsx to preserve code while removing from active use

export default function ChatInterfaceDisabled() {
  return (
    <div className="flex items-center justify-center h-64 bg-gray-50 dark:bg-gray-900 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700">
      <div className="text-center">
        <div className="text-gray-400 dark:text-gray-600 mb-2">
          <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
          Chat Interface Disabled
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          This platform now focuses on workflow automation.
        </p>
        <button
          onClick={() => window.location.href = '/agent-builder'}
          className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
        >
          Go to Workflow Builder
        </button>
      </div>
    </div>
  );
}