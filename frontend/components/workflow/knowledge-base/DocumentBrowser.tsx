"use client";

import React, { useState, useEffect } from "react";
import { FileText, Search, Filter, ChevronDown, ChevronRight } from "lucide-react";

interface Document {
  document_id: string;
  document_name: string;
  file_type: string;
  chunk_count: number;
  author?: string;
  language?: string;
  upload_date?: number;
}

interface DocumentBrowserProps {
  onSelectDocument?: (documentId: string) => void;
}

export function DocumentBrowser({ onSelectDocument }: DocumentBrowserProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<string>("all");
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch("/api/knowledge-base/documents");

      if (!response.ok) {
        throw new Error("Failed to load documents");
      }

      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error("Failed to load documents:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const filteredDocuments = documents.filter((doc) => {
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      if (
        !doc.document_name.toLowerCase().includes(query) &&
        !doc.author?.toLowerCase().includes(query)
      ) {
        return false;
      }
    }

    // Type filter
    if (filterType !== "all" && doc.file_type !== filterType) {
      return false;
    }

    return true;
  });

  const fileTypes = Array.from(new Set(documents.map((d) => d.file_type)));

  const toggleExpand = (docId: string) => {
    setExpandedDoc(expandedDoc === docId ? null : docId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin h-8 w-8 border-4 border-gray-300 border-t-blue-600 rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-md">
        <div className="text-sm text-red-700">{error}</div>
        <button
          onClick={loadDocuments}
          className="mt-2 text-sm text-blue-600 hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search and Filter */}
      <div className="space-y-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            {fileTypes.map((type) => (
              <option key={type} value={type}>
                {type.toUpperCase()}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Document List */}
      <div className="space-y-2">
        <div className="text-sm text-gray-600">
          {filteredDocuments.length} document{filteredDocuments.length !== 1 ? "s" : ""}
        </div>

        {filteredDocuments.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No documents found
          </div>
        ) : (
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.document_id}
                className="border border-gray-200 rounded-md overflow-hidden"
              >
                {/* Document Header */}
                <div
                  className="flex items-center gap-2 p-3 hover:bg-gray-50 cursor-pointer"
                  onClick={() => toggleExpand(doc.document_id)}
                >
                  <button className="text-gray-400 hover:text-gray-600">
                    {expandedDoc === doc.document_id ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </button>

                  <FileText className="w-4 h-4 text-blue-600" />

                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {doc.document_name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {doc.chunk_count} chunks • {doc.file_type.toUpperCase()}
                    </div>
                  </div>

                  {onSelectDocument && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectDocument(doc.document_id);
                      }}
                      className="px-3 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded"
                    >
                      Select
                    </button>
                  )}
                </div>

                {/* Document Details (Expanded) */}
                {expandedDoc === doc.document_id && (
                  <div className="px-3 pb-3 pt-1 bg-gray-50 border-t border-gray-200 text-sm">
                    <div className="space-y-1">
                      {doc.author && (
                        <div className="flex items-center gap-2">
                          <span className="text-gray-500">Author:</span>
                          <span className="text-gray-900">{doc.author}</span>
                        </div>
                      )}
                      {doc.language && (
                        <div className="flex items-center gap-2">
                          <span className="text-gray-500">Language:</span>
                          <span className="text-gray-900">{doc.language}</span>
                        </div>
                      )}
                      {doc.upload_date && (
                        <div className="flex items-center gap-2">
                          <span className="text-gray-500">Uploaded:</span>
                          <span className="text-gray-900">
                            {new Date(doc.upload_date * 1000).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">ID:</span>
                        <code className="text-xs bg-gray-200 px-1 py-0.5 rounded">
                          {doc.document_id}
                        </code>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
