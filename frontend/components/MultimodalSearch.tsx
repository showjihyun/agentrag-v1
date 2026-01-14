/**
 * Multimodal Search Component
 * 
 * Multimodal search UI supporting text, image, and audio queries
 */

import React, { useState, useRef } from 'react';

interface SearchFilters {
  dateRange?: { start: string; end: string };
  contentTypes?: string[];
  speaker?: string;
  author?: string;
  language?: string;
}

interface SearchResult {
  id: string;
  content: string;
  score: number;
  modality: 'text' | 'image' | 'audio';
  metadata?: any;
}

export function MultimodalSearch() {
  const [queryText, setQueryText] = useState('');
  const [queryImage, setQueryImage] = useState<File | null>(null);
  const [queryAudio, setQueryAudio] = useState<File | null>(null);
  const [searchImages, setSearchImages] = useState(true);
  const [searchText, setSearchText] = useState(true);
  const [searchAudio, setSearchAudio] = useState(true);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const imageInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setQueryImage(file);
    }
  };

  const handleAudioSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setQueryAudio(file);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      
      // Add query
      if (queryText) formData.append('query', queryText);
      if (queryImage) formData.append('query_image', queryImage);
      if (queryAudio) formData.append('query_audio', queryAudio);
      
      // Search options
      formData.append('search_images', searchImages.toString());
      formData.append('search_text', searchText.toString());
      formData.append('search_audio', searchAudio.toString());
      formData.append('top_k', '10');
      
      // Add filters
      if (filters.dateRange) {
        formData.append('date_range_start', filters.dateRange.start);
        formData.append('date_range_end', filters.dateRange.end);
      }
      if (filters.contentTypes && filters.contentTypes.length > 0) {
        formData.append('content_types', JSON.stringify(filters.contentTypes));
      }
      if (filters.speaker) formData.append('speaker', filters.speaker);
      if (filters.author) formData.append('author', filters.author);
      if (filters.language) formData.append('language', filters.language);

      const response = await fetch('/api/documents/search/multimodal', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data.combined || []);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const clearQuery = () => {
    setQueryText('');
    setQueryImage(null);
    setQueryAudio(null);
    if (imageInputRef.current) imageInputRef.current.value = '';
    if (audioInputRef.current) audioInputRef.current.value = '';
  };

  return (
    <div className="multimodal-search">
      <div className="search-container">
        <h2>Multimodal Search</h2>
        
        {/* Text query */}
        <div className="query-section">
          <label>Text Query</label>
          <input
            type="text"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder="Enter search term..."
            className="text-input"
          />
        </div>

        {/* Image query */}
        <div className="query-section">
          <label>Image Query (Optional)</label>
          <input
            ref={imageInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageSelect}
            className="file-input"
          />
          {queryImage && (
            <div className="file-preview">
              <span>📷 {queryImage.name}</span>
              <button onClick={() => setQueryImage(null)}>✕</button>
            </div>
          )}
        </div>

        {/* Audio query */}
        <div className="query-section">
          <label>Audio Query (Optional)</label>
          <input
            ref={audioInputRef}
            type="file"
            accept="audio/*"
            onChange={handleAudioSelect}
            className="file-input"
          />
          {queryAudio && (
            <div className="file-preview">
              <span>🎵 {queryAudio.name}</span>
              <button onClick={() => setQueryAudio(null)}>✕</button>
            </div>
          )}
        </div>

        {/* Search options */}
        <div className="search-options">
          <label>Search Target</label>
          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={searchText}
                onChange={(e) => setSearchText(e.target.checked)}
              />
              Text
            </label>
            <label>
              <input
                type="checkbox"
                checked={searchImages}
                onChange={(e) => setSearchImages(e.target.checked)}
              />
              Images
            </label>
            <label>
              <input
                type="checkbox"
                checked={searchAudio}
                onChange={(e) => setSearchAudio(e.target.checked)}
              />
              Audio
            </label>
          </div>
        </div>

        {/* Filters */}
        <div className="filters-section">
          <details>
            <summary>Advanced Filters</summary>
            
            <div className="filter-group">
              <label>Date Range</label>
              <div className="date-range">
                <input
                  type="date"
                  value={filters.dateRange?.start || ''}
                  onChange={(e) => setFilters({
                    ...filters,
                    dateRange: { ...filters.dateRange, start: e.target.value, end: filters.dateRange?.end || '' }
                  })}
                />
                <span>~</span>
                <input
                  type="date"
                  value={filters.dateRange?.end || ''}
                  onChange={(e) => setFilters({
                    ...filters,
                    dateRange: { start: filters.dateRange?.start || '', end: e.target.value }
                  })}
                />
              </div>
            </div>

            <div className="filter-group">
              <label>Speaker/Author</label>
              <input
                type="text"
                value={filters.speaker || ''}
                onChange={(e) => setFilters({ ...filters, speaker: e.target.value })}
                placeholder="Speaker name"
              />
            </div>

            <div className="filter-group">
              <label>Language</label>
              <select
                value={filters.language || ''}
                onChange={(e) => setFilters({ ...filters, language: e.target.value })}
              >
                <option value="">All</option>
                <option value="ko">Korean</option>
                <option value="en">English</option>
                <option value="ja">Japanese</option>
                <option value="zh">Chinese</option>
              </select>
            </div>
          </details>
        </div>

        {/* Search button */}
        <div className="button-group">
          <button
            onClick={handleSearch}
            disabled={loading || (!queryText && !queryImage && !queryAudio)}
            className="search-button"
          >
            {loading ? 'Searching...' : '🔍 Search'}
          </button>
          <button onClick={clearQuery} className="clear-button">
            Clear
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* Search results */}
      <div className="results-container">
        <h3>Search Results ({results.length})</h3>
        
        {results.length === 0 && !loading && (
          <div className="no-results">
            No results found.
          </div>
        )}

        <div className="results-list">
          {results.map((result) => (
            <div key={result.id} className="result-item">
              <div className="result-header">
                <span className={`modality-badge ${result.modality}`}>
                  {result.modality === 'text' && '📄'}
                  {result.modality === 'image' && '🖼️'}
                  {result.modality === 'audio' && '🎵'}
                  {result.modality}
                </span>
                <span className="score">
                  {(result.score * 100).toFixed(1)}%
                </span>
              </div>
              
              <div className="result-content">
                {result.modality === 'image' && result.metadata?.image_path && (
                  <img
                    src={result.metadata.image_path}
                    alt="Result"
                    className="result-image"
                  />
                )}
                <p>{result.content}</p>
              </div>

              {result.metadata && (
                <div className="result-metadata">
                  {result.metadata.document_id && (
                    <span>📄 {result.metadata.document_id}</span>
                  )}
                  {result.metadata.created_at && (
                    <span>📅 {new Date(result.metadata.created_at).toLocaleDateString()}</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <style jsx>{`
        .multimodal-search {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
        }

        .search-container {
          background: white;
          border-radius: 8px;
          padding: 24px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          margin-bottom: 24px;
        }

        h2 {
          margin: 0 0 24px 0;
          font-size: 24px;
          font-weight: 600;
        }

        .query-section {
          margin-bottom: 20px;
        }

        label {
          display: block;
          margin-bottom: 8px;
          font-weight: 500;
          color: #333;
        }

        .text-input {
          width: 100%;
          padding: 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 16px;
        }

        .file-input {
          width: 100%;
          padding: 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .file-preview {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-top: 8px;
          padding: 8px 12px;
          background: #f5f5f5;
          border-radius: 4px;
        }

        .file-preview button {
          background: none;
          border: none;
          cursor: pointer;
          font-size: 18px;
          color: #999;
        }

        .search-options {
          margin-bottom: 20px;
        }

        .checkbox-group {
          display: flex;
          gap: 16px;
        }

        .checkbox-group label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-weight: normal;
        }

        .filters-section {
          margin-bottom: 20px;
        }

        details {
          border: 1px solid #ddd;
          border-radius: 4px;
          padding: 12px;
        }

        summary {
          cursor: pointer;
          font-weight: 500;
          user-select: none;
        }

        .filter-group {
          margin-top: 16px;
        }

        .date-range {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .date-range input {
          flex: 1;
          padding: 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .filter-group input,
        .filter-group select {
          width: 100%;
          padding: 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .button-group {
          display: flex;
          gap: 12px;
        }

        .search-button,
        .clear-button {
          padding: 12px 24px;
          border: none;
          border-radius: 4px;
          font-size: 16px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .search-button {
          flex: 1;
          background: #007bff;
          color: white;
        }

        .search-button:hover:not(:disabled) {
          background: #0056b3;
        }

        .search-button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .clear-button {
          background: #f5f5f5;
          color: #333;
        }

        .clear-button:hover {
          background: #e0e0e0;
        }

        .error-message {
          margin-top: 16px;
          padding: 12px;
          background: #fee;
          border: 1px solid #fcc;
          border-radius: 4px;
          color: #c00;
        }

        .results-container {
          background: white;
          border-radius: 8px;
          padding: 24px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        h3 {
          margin: 0 0 20px 0;
          font-size: 20px;
          font-weight: 600;
        }

        .no-results {
          text-align: center;
          padding: 40px;
          color: #999;
        }

        .results-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .result-item {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 16px;
          transition: box-shadow 0.2s;
        }

        .result-item:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .modality-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 14px;
          font-weight: 500;
        }

        .modality-badge.text {
          background: #e3f2fd;
          color: #1976d2;
        }

        .modality-badge.image {
          background: #f3e5f5;
          color: #7b1fa2;
        }

        .modality-badge.audio {
          background: #e8f5e9;
          color: #388e3c;
        }

        .score {
          font-weight: 600;
          color: #666;
        }

        .result-content {
          margin-bottom: 12px;
        }

        .result-image {
          max-width: 200px;
          max-height: 150px;
          border-radius: 4px;
          margin-bottom: 8px;
        }

        .result-content p {
          margin: 0;
          line-height: 1.6;
          color: #333;
        }

        .result-metadata {
          display: flex;
          gap: 16px;
          font-size: 14px;
          color: #666;
        }
      `}</style>
    </div>
  );
}
