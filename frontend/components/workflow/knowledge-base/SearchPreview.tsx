"use client";

import React, { useState } from "react";
import { Search, Loader2 } from "lucide-react";

interface SearchResult {
  id: string;
  text: string;
  score: number;
  document_name: string;
  chunk_index: number;
  metadata?: {
    author?: string;
    keywords?: string;
    language?: string;
  };
}

interface SearchPreviewProps {
  query: string;
  topK?: number;
  filters?: string; // JSON string
}

export function SearchPreview({ query, topK = 5, filters }: SearchPreviewProps) {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const performSearch = async () => {
    if (!query.trim()) {
      setError("Please enter a search query");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSearched(true);

      // Parse filters
      let parsedFilters = null;
      if (filters) {
        try {
          parsedFilters = JSON.parse(filters);
        } catch {
          setError("Invalid filter JSON");
          return;
        }
      }

      const response = await fetch("/api/knowledge-base/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          top_k: topK,
          filters: parsedFilters,
        }),
      });

      if (!response.ok) {
        throw new Error("Search failed");
      }

      const data = await response.json();
      setResults(data.results || []);
    } catch (err) {
      console.error("Search error:", err);
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <button
          onClick={performSearch}
          disabled={loading || !query.trim()}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Preview Search
            </>
          )}
        </button>

        {searched && !loading && (
          <span className="text-sm text-gray-600">
            {results.length} result{results.length !== 1 ? "s" : ""} found
          </span>
        )}
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}

      {searched && !loading && results.length === 0 && !error && (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-md text-center text-gray-600">
          No results found. Try adjusting your query or filters.
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          <div className="text-sm font-medium text-gray-700">
            Search Results:
          </div>

          {results.map((result, index) => (
            <div
              key={result.id}
              className="p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-gray-500">
                      #{index + 1}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {result.document_name}
                    </span>
                    <span className="text-xs text-gray-500">
                      (Chunk {result.chunk_index})
                    </span>
                  </div>

                  {result.metadata && (
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                      {result.metadata.author && (
                        <span>Author: {result.metadata.author}</span>
                      )}
                      {result.metadata.language && (
                        <span>Lang: {result.metadata.language}</span>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-1">
                  <span className="text-xs text-gray-500">Score:</span>
                  <span className="text-sm font-semibold text-blue-600">
                    {(result.score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Text content */}
              <div className="text-sm text-gray-700 line-clamp-3">
                {result.text}
              </div>

              {/* Keywords */}
              {result.metadata?.keywords && (
                <div className="mt-2 flex items-center gap-2 flex-wrap">
                  {result.metadata.keywords.split(",").map((keyword, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded"
                    >
                      {keyword.trim()}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
