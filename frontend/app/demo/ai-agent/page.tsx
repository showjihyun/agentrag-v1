/**
 * AI Agent Demo Page
 * Demonstrates AI Agent capabilities
 */

'use client';

import { useState } from 'react';
import { Header } from '@/components/Header';

export default function AIAgentDemoPage() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setResponse('');

    try {
      // Simulate AI agent response
      await new Promise(resolve => setTimeout(resolve, 1500));
      setResponse(`AI Agent Response for: "${query}"\n\nThis is a demo response showing how the AI agent processes queries and returns intelligent responses.`);
    } catch (error) {
      setResponse('Error processing query');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">AI Agent Demo</h1>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Enter your query
              </label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-600 dark:bg-gray-700 dark:border-gray-600"
                rows={4}
                placeholder="Ask the AI agent anything..."
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50"
            >
              {isLoading ? 'Processing...' : 'Submit Query'}
            </button>
          </form>

          {response && (
            <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
              <h3 className="font-medium mb-2">Response:</h3>
              <pre className="whitespace-pre-wrap text-sm">{response}</pre>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
