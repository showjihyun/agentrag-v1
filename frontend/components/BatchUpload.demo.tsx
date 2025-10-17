/**
 * BatchUpload Component Demo
 * This file demonstrates the BatchUpload component in action.
 * 
 * To use this demo:
 * 1. Ensure you're logged in (component requires authentication)
 * 2. Import and render this component in a page
 * 3. Try uploading files via drag-and-drop or file picker
 */

'use client';

import React from 'react';
import BatchUpload from './BatchUpload';
import { useAuth } from '@/contexts/AuthContext';

export default function BatchUploadDemo() {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-3xl font-bold mb-2">Batch Upload Demo</h1>
          <p className="text-gray-600">
            Upload multiple documents at once with real-time progress tracking
          </p>
          
          {/* Auth Status */}
          <div className="mt-4 p-4 bg-gray-50 rounded">
            <p className="text-sm font-medium">
              Authentication Status: {' '}
              <span className={isAuthenticated ? 'text-green-600' : 'text-red-600'}>
                {isAuthenticated ? '✅ Authenticated' : '❌ Not Authenticated'}
              </span>
            </p>
            {user && (
              <p className="text-sm text-gray-600 mt-1">
                Logged in as: {user.email} ({user.username})
              </p>
            )}
          </div>
        </div>

        {/* Component Demo */}
        {isAuthenticated ? (
          <BatchUpload />
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <p className="text-yellow-800 font-medium mb-2">
              ⚠️ Authentication Required
            </p>
            <p className="text-yellow-700 text-sm">
              Please log in to use the batch upload feature.
            </p>
            <a
              href="/auth/login"
              className="inline-block mt-4 bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
            >
              Go to Login
            </a>
          </div>
        )}

        {/* Feature List */}
        <div className="mt-6 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4">Features</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex items-start">
              <span className="text-2xl mr-3">📁</span>
              <div>
                <h3 className="font-medium">Multiple File Selection</h3>
                <p className="text-sm text-gray-600">
                  Select up to 100 files at once
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <span className="text-2xl mr-3">🎯</span>
              <div>
                <h3 className="font-medium">Drag & Drop</h3>
                <p className="text-sm text-gray-600">
                  Drag files directly onto the upload zone
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <span className="text-2xl mr-3">✅</span>
              <div>
                <h3 className="font-medium">File Validation</h3>
                <p className="text-sm text-gray-600">
                  Automatic type and size validation
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <span className="text-2xl mr-3">📊</span>
              <div>
                <h3 className="font-medium">Real-time Progress</h3>
                <p className="text-sm text-gray-600">
                  Live updates via Server-Sent Events
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <span className="text-2xl mr-3">🔄</span>
              <div>
                <h3 className="font-medium">Error Handling</h3>
                <p className="text-sm text-gray-600">
                  Retry failed uploads individually
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <span className="text-2xl mr-3">🎨</span>
              <div>
                <h3 className="font-medium">Status Indicators</h3>
                <p className="text-sm text-gray-600">
                  Visual feedback for each file
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Supported Formats */}
        <div className="mt-6 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4">Supported Formats</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-red-50 rounded">
              <div className="text-3xl mb-2">📄</div>
              <div className="font-medium">PDF</div>
              <div className="text-xs text-gray-600">.pdf</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded">
              <div className="text-3xl mb-2">📝</div>
              <div className="font-medium">Text</div>
              <div className="text-xs text-gray-600">.txt</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded">
              <div className="text-3xl mb-2">📘</div>
              <div className="font-medium">Word</div>
              <div className="text-xs text-gray-600">.docx</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-3xl mb-2">📋</div>
              <div className="font-medium">Markdown</div>
              <div className="text-xs text-gray-600">.md</div>
            </div>
          </div>
        </div>

        {/* Limits */}
        <div className="mt-6 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4">Upload Limits</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="font-medium">Maximum Files</span>
              <span className="text-blue-600 font-bold">100 files</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="font-medium">Per File Size</span>
              <span className="text-blue-600 font-bold">10 MB</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <span className="font-medium">Total Batch Size</span>
              <span className="text-blue-600 font-bold">100 MB</span>
            </div>
          </div>
        </div>

        {/* Usage Tips */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4 text-blue-900">💡 Usage Tips</h2>
          <ul className="space-y-2 text-blue-800">
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Files are validated before upload - invalid files will be marked immediately</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>You can remove files from the list before uploading</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Failed uploads can be retried individually without re-uploading successful files</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Progress updates happen in real-time via Server-Sent Events</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>The upload continues in the background - you can navigate away and come back</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
