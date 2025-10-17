/**
 * Global loading state
 * 
 * Displayed while pages are loading
 */

export default function Loading() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        {/* Spinner */}
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400 mb-4"></div>
        
        {/* Loading text */}
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Loading...
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Please wait while we load your content
        </p>
      </div>
    </div>
  );
}
