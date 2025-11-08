"use client";

import React, { useState, useEffect } from "react";

interface KnowledgeBaseSelectorProps {
  value?: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

interface CollectionInfo {
  name: string;
  num_entities: number;
  loaded: boolean;
}

export function KnowledgeBaseSelector({
  value,
  onChange,
  disabled = false,
}: KnowledgeBaseSelectorProps) {
  const [collections, setCollections] = useState<CollectionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch("/api/knowledge-base/collections");

      if (!response.ok) {
        throw new Error("Failed to load collections");
      }

      const data = await response.json();
      setCollections(data.collections || []);
    } catch (err) {
      console.error("Failed to load collections:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <div className="animate-spin h-4 w-4 border-2 border-gray-300 border-t-blue-600 rounded-full" />
        Loading collections...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-red-600">
        Error: {error}
        <button
          onClick={loadCollections}
          className="ml-2 text-blue-600 hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <select
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        <option value="">Select a collection...</option>
        {collections.map((collection) => (
          <option key={collection.name} value={collection.name}>
            {collection.name} ({collection.num_entities.toLocaleString()}{" "}
            documents)
          </option>
        ))}
      </select>

      {value && (
        <div className="text-xs text-gray-500">
          {collections.find((c) => c.name === value)?.num_entities.toLocaleString() || 0}{" "}
          documents available
        </div>
      )}
    </div>
  );
}
