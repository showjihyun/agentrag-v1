'use client';

import React from 'react';

// Simplified ChatInterface component for workflow platform
const ChatInterface = React.forwardRef<HTMLDivElement>((props, ref) => {
  return (
    <div ref={ref} className="flex items-center justify-center h-64 bg-gray-50 dark:bg-gray-900 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700">
      <div className="text-center">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
          Chat Interface
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          This component has been simplified for the workflow platform.
        </p>
      </div>
    </div>
  );
});

ChatInterface.displayName = 'ChatInterface';

export default ChatInterface;