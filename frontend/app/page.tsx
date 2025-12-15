'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  
  // Redirect to Agent Builder Dashboard immediately
  useEffect(() => {
    router.replace('/agent-builder');
  }, [router]);
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Redirecting to Agent Builder...
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Taking you to the workflow platform
        </p>
      </div>
    </div>
  );
}
