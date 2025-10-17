/**
 * 404 Not Found page
 * 
 * Displayed when a route doesn't exist
 */

import Link from 'next/link';
import { Button } from '@/components/Button';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* 404 illustration */}
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-gray-300 dark:text-gray-700">
            404
          </h1>
        </div>

        {/* Message */}
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Page Not Found
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Sorry, we couldn't find the page you're looking for.
          It might have been moved or deleted.
        </p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link href="/">
            <Button variant="primary" aria-label="Go to homepage">
              Go Home
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button variant="secondary" aria-label="Go to dashboard">
              Dashboard
            </Button>
          </Link>
        </div>

        {/* Search suggestion */}
        <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-500 mb-4">
            Looking for something specific?
          </p>
          <div className="flex gap-2 text-sm">
            <Link
              href="/"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Home
            </Link>
            <span className="text-gray-400">•</span>
            <Link
              href="/dashboard"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Dashboard
            </Link>
            <span className="text-gray-400">•</span>
            <Link
              href="/auth/login"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
