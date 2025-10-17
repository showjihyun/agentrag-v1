/**
 * Multimodal Search Component
 * 
 * 텍스트, 이미지, 오디오 쿼리를 지원하는 멀티모달 검색 UI
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
      
      // 쿼리 추가
      if (queryText) formData.append('query', queryText);
      if (queryImage) formData.append('query_image', queryImage);
      if (queryAudio) formData.append('query_audio', queryAudio);
      
      // 검색 옵션
      formData.append('search_images', searchImages.toString());
      formData.append('search_text', searchText.toString());
      formData.append('search_audio', searchAudio.toString());
      formData.append('top_k', '10');
      
      // 필터 추가
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
        <h2>멀티모달 검색</h2>
        
        {/* 텍스트 쿼리 */}
        <div className="query-section">
          <label>텍스트 쿼리</label>
          <input
            type="text"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder="검색어를 입력하세요..."
            className="text-input"
          />
        </div>

        {/* 이미지 쿼리 */}
        <div className="query-section">
          <label>이미지 쿼리 (선택)</label>
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

        {/* 오디오 쿼리 */}
        <div className="query-section">
          <label>오디오 쿼리 (선택)</label>
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

        {/* 검색 옵션 */}
        <div className="search-options">
          <label>검색 대상</label>
          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={searchText}
                onChange={(e) => setSearchText(e.target.checked)}
              />
              텍스트
            </label>
            <label>
              <input
                type="checkbox"
                checked={searchImages}
                onChange={(e) => setSearchImages(e.target.checked)}
              />
              이미지
            </label>
            <label>
              <input
                type="checkbox"
                checked={searchAudio}
                onChange={(e) => setSearchAudio(e.target.checked)}
              />
              오디오
            </label>
          </div>
        </div>

        {/* 필터 */}
        <div className="filters-section">
          <details>
            <summary>고급 필터</summary>
            
            <div className="filter-group">
              <label>날짜 범위</label>
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
              <label>화자/작성자</label>
              <input
                type="text"
                value={filters.speaker || ''}
                onChange={(e) => setFilters({ ...filters, speaker: e.target.value })}
                placeholder="화자 이름"
              />
            </div>

            <div className="filter-group">
              <label>언어</label>
              <select
                value={filters.language || ''}
                onChange={(e) => setFilters({ ...filters, language: e.target.value })}
              >
                <option value="">전체</option>
                <option value="ko">한국어</option>
                <option value="en">English</option>
                <option value="ja">日本語</option>
                <option value="zh">中文</option>
              </select>
            </div>
          </details>
        </div>

        {/* 검색 버튼 */}
        <div className="button-group">
          <button
            onClick={handleSearch}
            disabled={loading || (!queryText && !queryImage && !queryAudio)}
            className="search-button"
          >
            {loading ? '검색 중...' : '🔍 검색'}
          </button>
          <button onClick={clearQuery} className="clear-button">
            지우기
          </button>
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}
      </div>

      {/* 검색 결과 */}
      <div className="results-container">
        <h3>검색 결과 ({results.length})</h3>
        
        {results.length === 0 && !loading && (
          <div className="no-results">
            검색 결과가 없습니다.
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
