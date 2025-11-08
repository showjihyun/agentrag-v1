'use client';

import React, { useState, useEffect } from 'react';
import { SearchResult } from '@/lib/types';

interface DocumentViewerProps {
  sources: SearchResult[];
  selectedChunkId?: string;
  onChunkSelect?: (chunkId: string) => void;
}

interface DocumentFile {
  id: string;
  name: string;
  type: string;
  url: string;
  uploadDate: string;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({
  sources,
  selectedChunkId,
  onChunkSelect,
}) => {
  const [documents, setDocuments] = useState<DocumentFile[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentFile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'preview' | 'list' | 'tree'>('preview');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [showAIPanel, setShowAIPanel] = useState(false);
  const [documentSummary, setDocumentSummary] = useState<string>('');
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([]);
  const [documentInsights, setDocumentInsights] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<number[]>([]);
  const [currentSearchIndex, setCurrentSearchIndex] = useState(0);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [bookmarkedPages, setBookmarkedPages] = useState<Set<number>>(new Set());
  const [showTools, setShowTools] = useState(false);

  // Extract unique documents from sources
  useEffect(() => {
    const uniqueDocs = new Map<string, DocumentFile>();
    
    sources.forEach((source) => {
      // Use document_id from source (not from metadata)
      const docId = source.document_id;
      if (docId && !uniqueDocs.has(docId)) {
        uniqueDocs.set(docId, {
          id: docId,
          name: source.document_name || 'Unknown Document',
          type: source.metadata?.file_type || 'unknown',
          url: `/api/document-preview/${docId}/preview`,
          uploadDate: source.metadata?.upload_date || new Date().toISOString(),
        });
      }
    });

    const docList = Array.from(uniqueDocs.values());
    setDocuments(docList);
    
    // Auto-select first document
    if (docList.length > 0 && !selectedDoc) {
      setSelectedDoc(docList[0]);
    }
  }, [sources]);

  const getFileIcon = (type: string) => {
    const iconMap: Record<string, string> = {
      pdf: '📄',
      docx: '📝',
      doc: '📝',
      txt: '📃',
      md: '📋',
      png: '🖼️',
      jpg: '🖼️',
      jpeg: '🖼️',
      gif: '🖼️',
      xlsx: '📊',
      xls: '📊',
      csv: '📊',
      pptx: '📊',
      ppt: '📊',
    };
    return iconMap[type.toLowerCase()] || '📄';
  };

  const getFileTypeLabel = (type: string) => {
    const labelMap: Record<string, string> = {
      pdf: 'PDF Documents',
      docx: 'Word Documents',
      doc: 'Word Documents',
      txt: 'Text Files',
      md: 'Markdown Files',
      png: 'Images',
      jpg: 'Images',
      jpeg: 'Images',
      gif: 'Images',
      xlsx: 'Spreadsheets',
      xls: 'Spreadsheets',
      csv: 'CSV Files',
      pptx: 'Presentations',
      ppt: 'Presentations',
    };
    return labelMap[type.toLowerCase()] || 'Other Files';
  };

  const groupDocumentsByType = () => {
    const grouped = new Map<string, DocumentFile[]>();
    
    documents.forEach((doc) => {
      const label = getFileTypeLabel(doc.type);
      if (!grouped.has(label)) {
        grouped.set(label, []);
      }
      grouped.get(label)!.push(doc);
    });

    return Array.from(grouped.entries()).map(([label, docs]) => ({
      label,
      type: docs[0].type,
      count: docs.length,
      documents: docs,
    }));
  };

  const toggleGroup = (label: string) => {
    setExpandedGroups((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(label)) {
        newSet.delete(label);
      } else {
        newSet.add(label);
      }
      return newSet;
    });
  };

  // Generate AI insights when document is selected
  useEffect(() => {
    if (selectedDoc && showAIPanel) {
      generateDocumentInsights();
    }
  }, [selectedDoc, showAIPanel]);

  // Search functionality
  const handleSearch = () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    const results: number[] = [];
    const docChunks = sources.filter(
      (s) => (s.metadata?.document_id || s.document_name) === selectedDoc?.id
    );

    docChunks.forEach((chunk, index) => {
      if (chunk.text.toLowerCase().includes(searchQuery.toLowerCase())) {
        results.push(index);
      }
    });

    setSearchResults(results);
    setCurrentSearchIndex(0);
  };

  const navigateSearch = (direction: 'next' | 'prev') => {
    if (searchResults.length === 0) return;

    if (direction === 'next') {
      setCurrentSearchIndex((prev) => (prev + 1) % searchResults.length);
    } else {
      setCurrentSearchIndex((prev) => (prev - 1 + searchResults.length) % searchResults.length);
    }
  };

  // Zoom functionality
  const handleZoom = (action: 'in' | 'out' | 'reset') => {
    if (action === 'in') {
      setZoomLevel((prev) => Math.min(prev + 25, 200));
    } else if (action === 'out') {
      setZoomLevel((prev) => Math.max(prev - 25, 50));
    } else {
      setZoomLevel(100);
    }
  };

  // Bookmark functionality
  const toggleBookmark = (page: number) => {
    setBookmarkedPages((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(page)) {
        newSet.delete(page);
      } else {
        newSet.add(page);
      }
      return newSet;
    });
  };

  // Download document
  const handleDownload = () => {
    if (!selectedDoc) return;
    
    const link = document.createElement('a');
    link.href = selectedDoc.url;
    link.download = selectedDoc.name;
    link.click();
  };

  const generateDocumentInsights = async () => {
    if (!selectedDoc) return;

    // Get relevant chunks for this document
    const docChunks = sources.filter(
      (s) => (s.metadata?.document_id || s.document_name) === selectedDoc.id
    );

    if (docChunks.length === 0) return;

    // Generate summary (first 3 chunks)
    const summaryText = docChunks
      .slice(0, 3)
      .map((c) => c.text)
      .join(' ')
      .substring(0, 500);
    
    setDocumentSummary(summaryText + '...');

    // Generate suggested questions
    const questions = [
      `What are the main points in ${selectedDoc.name}?`,
      `Can you explain the key concepts from this document?`,
      `What are the important details I should know?`,
      `Summarize the findings in this document`,
    ];
    setSuggestedQuestions(questions);

    // Extract keywords (simple implementation)
    const allText = docChunks.map((c) => c.text).join(' ');
    const words = allText.toLowerCase().split(/\s+/);
    const wordFreq = new Map<string, number>();
    
    words.forEach((word) => {
      if (word.length > 4) {
        wordFreq.set(word, (wordFreq.get(word) || 0) + 1);
      }
    });

    const topKeywords = Array.from(wordFreq.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([word]) => word);

    setDocumentInsights({
      totalChunks: docChunks.length,
      keywords: topKeywords,
      avgScore: docChunks.reduce((sum, c) => sum + c.score, 0) / docChunks.length,
    });
  };

  const highlightChunk = (chunkId: string) => {
    // Highlight the chunk in the document viewer
    const element = document.getElementById(`chunk-${chunkId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      element.classList.add('highlight-pulse');
      setTimeout(() => {
        element.classList.remove('highlight-pulse');
      }, 2000);
    }
  };

  useEffect(() => {
    if (selectedChunkId) {
      highlightChunk(selectedChunkId);
    }
  }, [selectedChunkId]);

  const [ocrData, setOcrData] = useState<any>(null);
  const [showOcrOverlay, setShowOcrOverlay] = useState(false);

  // Fetch document info when document is selected
  useEffect(() => {
    if (selectedDoc) {
      setCurrentPage(1);
      setIsLoading(true);
      
      // Fetch document info
      fetch(`/api/document-preview/${selectedDoc.id}/info`)
        .then(res => res.json())
        .then(data => {
          setTotalPages(data.total_pages || 1);
          setIsLoading(false);
        })
        .catch(err => {
          console.error('Failed to fetch document info:', err);
          setIsLoading(false);
        });
    }
  }, [selectedDoc]);

  // Fetch OCR data when document or page changes
  useEffect(() => {
    if (selectedDoc) {
      const isImage = ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(selectedDoc.type.toLowerCase());
      
      if (isImage) {
        // Fetch OCR data
        fetch(`/api/document-preview/${selectedDoc.id}/preview?include_ocr=true&include_layout=true&page=${currentPage}`)
          .then(res => res.json())
          .then(data => {
            setOcrData(data);
          })
          .catch(err => {
            console.error('Failed to fetch OCR data:', err);
          });
      }
    }
  }, [selectedDoc, currentPage]);

  const renderDocumentPreview = () => {
    if (!selectedDoc) {
      return (
        <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
          <div className="text-center">
            <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
            </svg>
            <p className="text-sm">No document selected</p>
          </div>
        </div>
      );
    }

    const isImage = ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(selectedDoc.type.toLowerCase());

    // For images, use the image endpoint; for PDFs and other documents, use the page endpoint
    const imageUrl = isImage 
      ? `/api/document-preview/${selectedDoc.id}/image`
      : `/api/document-preview/${selectedDoc.id}/page/${currentPage}`;

    return (
      <div className="relative h-full flex flex-col bg-gray-100 dark:bg-gray-900">
        {/* Page Navigation */}
        {totalPages > 1 && (
          <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-3 flex items-center justify-between">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 rounded-lg bg-blue-500 text-white disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              Prev
            </button>
            
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Page
              </span>
              <input
                type="number"
                min="1"
                max={totalPages}
                value={currentPage}
                onChange={(e) => {
                  const page = parseInt(e.target.value);
                  if (page >= 1 && page <= totalPages) {
                    setCurrentPage(page);
                  }
                }}
                className="w-16 px-2 py-1 text-center border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <span className="text-sm text-gray-500 dark:text-gray-400">
                / {totalPages}
              </span>
            </div>
            
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 rounded-lg bg-blue-500 text-white disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors flex items-center gap-1"
            >
              Next
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        )}
        
        {/* Document Display */}
        <div className="flex-1 overflow-auto p-4">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-full space-y-4">
              <div className="relative">
                <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-200 dark:border-gray-700"></div>
                <div className="animate-spin rounded-full h-16 w-16 border-4 border-transparent border-t-blue-500 border-r-purple-500 absolute top-0 left-0"></div>
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Loading document...
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Page {currentPage} of {totalPages}
                </p>
              </div>
            </div>
          ) : (
            <div className="relative inline-block max-w-full">
              <img
                src={imageUrl}
                alt={`${selectedDoc.name} - Page ${currentPage}`}
                className="max-w-full h-auto mx-auto rounded-lg shadow-lg transition-transform duration-200"
                style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
                onError={(e) => {
                  console.error('Failed to load image');
                  e.currentTarget.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1000"><rect fill="%23f0f0f0" width="800" height="1000"/><text x="50%" y="50%" text-anchor="middle" fill="%23666">Failed to load page</text></svg>';
                }}
              />
              
              {/* Bookmark indicator */}
              {bookmarkedPages.has(currentPage) && (
                <div className="absolute top-2 right-2 bg-yellow-400 text-yellow-900 px-2 py-1 rounded-full text-xs font-bold shadow-lg animate-bounce-in">
                  ⭐ Bookmarked
                </div>
              )}
              
              {/* OCR Overlay for images */}
              {isImage && showOcrOverlay && ocrData && ocrData.text_boxes && (
                <svg
                  className="absolute top-0 left-0 w-full h-full pointer-events-none"
                  viewBox={`0 0 ${ocrData.width || 1000} ${ocrData.height || 1000}`}
                  preserveAspectRatio="none"
                >
                  {ocrData.text_boxes.map((box: any, idx: number) => {
                    const [topLeft, topRight, bottomRight, bottomLeft] = box.box;
                    const points = `${topLeft[0]},${topLeft[1]} ${topRight[0]},${topRight[1]} ${bottomRight[0]},${bottomRight[1]} ${bottomLeft[0]},${bottomLeft[1]}`;
                    
                    return (
                      <g key={idx}>
                        <polygon
                          points={points}
                          fill="rgba(255, 255, 0, 0.2)"
                          stroke="rgba(255, 255, 0, 0.8)"
                          strokeWidth="2"
                        />
                        <text
                          x={topLeft[0]}
                          y={topLeft[1] - 5}
                          fill="yellow"
                          fontSize="12"
                          fontWeight="bold"
                        >
                          {box.text}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              )}
            </div>
          )}
        </div>
        
        {/* OCR Toggle Button for images */}
        {isImage && ocrData && ocrData.text_boxes && (
          <button
            onClick={() => setShowOcrOverlay(!showOcrOverlay)}
            className="absolute top-20 left-4 px-4 py-2 rounded-lg bg-white dark:bg-gray-800 shadow-lg hover:shadow-xl transition-all duration-200 flex items-center gap-2 z-10"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
              <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
            </svg>
            <span className="text-sm font-medium">
              {showOcrOverlay ? 'Hide' : 'Show'} OCR
            </span>
          </button>
        )}
      </div>
    );

    // For PDFs and other documents, show chunks with highlights
    const filteredSources = sources.filter(
      (s) => (s.metadata?.document_id || s.document_name) === selectedDoc!.id
    );

    return (
      <div className="h-full overflow-auto bg-white dark:bg-gray-900 p-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {filteredSources.map((source, idx) => {
            const isSelected = selectedChunkId === source.chunk_id;
            
            // Render text with highlighting
            const renderHighlightedText = () => {
              const text = source.text || '';
              
              if (!isSelected) {
                return <span className="whitespace-pre-wrap">{text}</span>;
              }

              // Split text into sentences for highlighting
              const sentences = text.split(/([.!?]\s+)/);
              
              return (
                <span className="whitespace-pre-wrap">
                  {sentences.map((sentence, sIdx) => {
                    // Highlight every sentence when selected
                    if (sentence.trim().length > 0 && !/^[.!?]\s*$/.test(sentence)) {
                      return (
                        <mark
                          key={sIdx}
                          className="bg-gradient-to-r from-yellow-200 via-yellow-300 to-yellow-200 dark:from-yellow-800/70 dark:via-yellow-700/80 dark:to-yellow-800/70 px-1 py-0.5 rounded-md font-medium shadow-sm border-b-2 border-yellow-400 dark:border-yellow-600 animate-highlight-pulse"
                        >
                          {sentence}
                        </mark>
                      );
                    }
                    return <span key={sIdx}>{sentence}</span>;
                  })}
                </span>
              );
            };

            return (
              <div
                key={source.chunk_id}
                id={`chunk-${source.chunk_id}`}
                className={`p-4 rounded-lg border-2 transition-all duration-300 cursor-pointer relative ${
                  isSelected
                    ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20 shadow-xl scale-[1.02] ring-4 ring-yellow-300/50 dark:ring-yellow-600/50'
                    : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-md'
                }`}
                onClick={() => onChunkSelect?.(source.chunk_id)}
              >
                {/* Animated border for selected chunk */}
                {isSelected && (
                  <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-yellow-400/20 via-amber-400/20 to-yellow-400/20 animate-pulse pointer-events-none"></div>
                )}
                
                <div className="flex items-start gap-3 relative z-10">
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm transition-all duration-300 ${
                    isSelected
                      ? 'bg-gradient-to-br from-yellow-500 to-amber-600 shadow-lg scale-110'
                      : 'bg-gradient-to-br from-blue-500 to-purple-600'
                  }`}>
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">
                        Chunk {source.metadata?.chunk_index || idx + 1}
                      </span>
                      <span className={`text-xs px-2.5 py-1 rounded-full font-semibold shadow-sm transition-all duration-300 ${
                        isSelected
                          ? 'bg-gradient-to-r from-yellow-400 to-amber-500 text-white scale-110'
                          : 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                      }`}>
                        🎯 {(source.score * 100).toFixed(0)}% match
                      </span>
                      {isSelected && (
                        <span className="text-xs px-2.5 py-1 rounded-full bg-gradient-to-r from-yellow-200 to-amber-300 dark:from-yellow-800/50 dark:to-amber-700/50 text-yellow-900 dark:text-yellow-200 font-bold shadow-md animate-pulse">
                          ✨ Selected
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                      {renderHighlightedText()}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (!selectedDoc) return;

      // Ctrl/Cmd + F: Focus search
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        setShowTools(true);
        setTimeout(() => {
          document.querySelector<HTMLInputElement>('input[placeholder*="Search"]')?.focus();
        }, 100);
      }

      // Arrow keys for page navigation
      if (e.key === 'ArrowLeft' && currentPage > 1) {
        setCurrentPage(currentPage - 1);
      } else if (e.key === 'ArrowRight' && currentPage < totalPages) {
        setCurrentPage(currentPage + 1);
      }

      // Ctrl/Cmd + +/-: Zoom
      if ((e.ctrlKey || e.metaKey) && e.key === '+') {
        e.preventDefault();
        handleZoom('in');
      } else if ((e.ctrlKey || e.metaKey) && e.key === '-') {
        e.preventDefault();
        handleZoom('out');
      } else if ((e.ctrlKey || e.metaKey) && e.key === '0') {
        e.preventDefault();
        handleZoom('reset');
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedDoc, currentPage, totalPages]);

  if (documents.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="text-center space-y-4 max-w-md">
          <svg className="w-20 h-20 mx-auto text-gray-300 dark:text-gray-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
          </svg>
          <div>
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
              No Documents Yet
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Upload documents or ask questions to see relevant sources here.
            </p>
          </div>
          <div className="flex items-center justify-center gap-2 text-xs text-gray-400 dark:text-gray-500">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <span>Documents appear when you get search results</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800 overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500 rounded-lg">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                Document Viewer
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {documents.length} {documents.length === 1 ? 'document' : 'documents'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Tools Toggle */}
            <button
              onClick={() => setShowTools(!showTools)}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-2 ${
                showTools
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
              title="Tools"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
              </svg>
              <span>Tools</span>
            </button>

            {/* AI Assistant Toggle */}
            <button
              onClick={() => setShowAIPanel(!showAIPanel)}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-2 ${
                showAIPanel
                  ? 'bg-purple-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
              title="AI Assistant"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z" />
              </svg>
              <span>AI</span>
            </button>
            
            {/* View Mode Buttons */}
            <div className="flex gap-1 ml-2">
              <button
                onClick={() => setViewMode('preview')}
                className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 ${
                  viewMode === 'preview'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title="Preview"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                  <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                </svg>
              </button>
              <button
                onClick={() => setViewMode('tree')}
                className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 ${
                  viewMode === 'tree'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title="Tree View"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                </svg>
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-1 ${
                  viewMode === 'list'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title="List View"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Document Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
          {documents.map((doc) => (
            <button
              key={doc.id}
              onClick={() => setSelectedDoc(doc)}
              className={`flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
                selectedDoc?.id === doc.id
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <span className="text-lg">{getFileIcon(doc.type)}</span>
              <div className="flex flex-col items-start">
                <span className="truncate max-w-[150px]">{doc.name}</span>
                <span className={`text-xs ${selectedDoc?.id === doc.id ? 'text-white/80' : 'text-gray-500 dark:text-gray-400'}`}>
                  {doc.type.toUpperCase()}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Tools Panel */}
      {showTools && selectedDoc && (
        <div className="flex-shrink-0 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-3">
          <div className="grid grid-cols-2 gap-2">
            {/* Search */}
            <div className="col-span-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Search in document..."
                  className="flex-1 px-3 py-1.5 text-xs border border-blue-300 dark:border-blue-700 rounded-lg bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={handleSearch}
                  className="px-3 py-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-xs font-medium"
                >
                  🔍
                </button>
              </div>
              {searchResults.length > 0 && (
                <div className="flex items-center justify-between mt-2 text-xs text-gray-600 dark:text-gray-400">
                  <span>{searchResults.length} results</span>
                  <div className="flex gap-1">
                    <button
                      onClick={() => navigateSearch('prev')}
                      className="px-2 py-1 bg-white dark:bg-gray-800 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      ←
                    </button>
                    <button
                      onClick={() => navigateSearch('next')}
                      className="px-2 py-1 bg-white dark:bg-gray-800 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      →
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Zoom Controls */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-2 border border-gray-200 dark:border-gray-700">
              <div className="text-xs font-semibold text-blue-900 dark:text-blue-300 mb-1">Zoom</div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => handleZoom('out')}
                  className="px-2 py-1 bg-blue-100 dark:bg-blue-900/50 rounded hover:bg-blue-200 dark:hover:bg-blue-800 text-xs"
                  disabled={zoomLevel <= 50}
                >
                  −
                </button>
                <span className="text-xs font-medium px-2">{zoomLevel}%</span>
                <button
                  onClick={() => handleZoom('in')}
                  className="px-2 py-1 bg-blue-100 dark:bg-blue-900/50 rounded hover:bg-blue-200 dark:hover:bg-blue-800 text-xs"
                  disabled={zoomLevel >= 200}
                >
                  +
                </button>
                <button
                  onClick={() => handleZoom('reset')}
                  className="px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-xs ml-1"
                >
                  Reset
                </button>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-2 border border-gray-200 dark:border-gray-700">
              <div className="text-xs font-semibold text-cyan-900 dark:text-cyan-300 mb-1">Actions</div>
              <div className="flex gap-1">
                <button
                  onClick={() => toggleBookmark(currentPage)}
                  className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                    bookmarkedPages.has(currentPage)
                      ? 'bg-yellow-400 text-yellow-900'
                      : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                  title="Bookmark"
                >
                  ⭐
                </button>
                <button
                  onClick={handleDownload}
                  className="flex-1 px-2 py-1 bg-cyan-100 dark:bg-cyan-900/50 rounded hover:bg-cyan-200 dark:hover:bg-cyan-800 text-xs font-medium"
                  title="Download"
                >
                  📥
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Assistant Panel */}
      {showAIPanel && selectedDoc && (
        <div className="flex-shrink-0 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-4">
          <div className="space-y-3">
            {/* Document Summary */}
            {documentSummary && (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                    <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                  </svg>
                  <h4 className="text-xs font-semibold text-gray-900 dark:text-gray-100">AI Summary</h4>
                </div>
                <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
                  {documentSummary}
                </p>
              </div>
            )}

            {/* Suggested Questions */}
            {suggestedQuestions.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  <h4 className="text-xs font-semibold text-gray-900 dark:text-gray-100">Ask AI</h4>
                </div>
                <div className="space-y-1">
                  {suggestedQuestions.slice(0, 3).map((question, idx) => (
                    <button
                      key={idx}
                      className="w-full text-left px-2 py-1.5 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors flex items-start gap-2"
                      onClick={() => {
                        // TODO: Send question to chat
                        console.log('Ask:', question);
                      }}
                    >
                      <span className="text-blue-500">→</span>
                      <span className="flex-1">{question}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Document Insights */}
            {documentInsights && (
              <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-2">
                  <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                  </svg>
                  <h4 className="text-xs font-semibold text-gray-900 dark:text-gray-100">Insights</h4>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-gray-100 dark:bg-gray-700 rounded p-2">
                    <div className="text-gray-600 dark:text-gray-400 font-medium">Chunks</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-gray-100">{documentInsights.totalChunks}</div>
                  </div>
                  <div className="bg-gray-100 dark:bg-gray-700 rounded p-2">
                    <div className="text-gray-600 dark:text-gray-400 font-medium">Relevance</div>
                    <div className="text-lg font-bold text-gray-900 dark:text-gray-100">{(documentInsights.avgScore * 100).toFixed(0)}%</div>
                  </div>
                </div>
                {documentInsights.keywords.length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Top Keywords:</div>
                    <div className="flex flex-wrap gap-1">
                      {documentInsights.keywords.slice(0, 5).map((keyword: string, idx: number) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-200 rounded-full font-medium"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'preview' ? (
          renderDocumentPreview()
        ) : viewMode === 'tree' ? (
          <div className="h-full overflow-auto p-4">
            <div className="space-y-2">
              {groupDocumentsByType().map((group) => (
                <div key={group.label} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  {/* Group Header */}
                  <button
                    onClick={() => toggleGroup(group.label)}
                    className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors flex items-center justify-between group"
                  >
                    <div className="flex items-center gap-3">
                      <svg
                        className={`w-4 h-4 transition-transform duration-200 ${
                          expandedGroups.has(group.label) ? 'transform rotate-90' : ''
                        }`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      </svg>
                      <span className="text-2xl">{getFileIcon(group.type)}</span>
                      <div className="text-left">
                        <h4 className="font-semibold text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                          {group.label}
                        </h4>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {group.count} {group.count === 1 ? 'file' : 'files'}
                        </p>
                      </div>
                    </div>
                    <span className="px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">
                      {group.count}
                    </span>
                  </button>

                  {/* Group Items */}
                  {expandedGroups.has(group.label) && (
                    <div className="bg-white dark:bg-gray-900">
                      {group.documents.map((doc, idx) => (
                        <div
                          key={doc.id}
                          onClick={() => {
                            setSelectedDoc(doc);
                            setViewMode('preview');
                          }}
                          className={`px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer group flex items-center gap-3 ${
                            idx !== group.documents.length - 1 ? 'border-b border-gray-100 dark:border-gray-800' : ''
                          }`}
                        >
                          <div className="w-6 flex justify-center">
                            <div className="w-px h-6 bg-gray-300 dark:bg-gray-600"></div>
                          </div>
                          <span className="text-xl">{getFileIcon(doc.type)}</span>
                          <div className="flex-1 min-w-0">
                            <h5 className="font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 text-sm">
                              {doc.name}
                            </h5>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {new Date(doc.uploadDate).toLocaleDateString()}
                            </p>
                          </div>
                          <svg className="w-4 h-4 text-gray-400 group-hover:text-blue-500 transition-colors flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="h-full overflow-auto p-4">
            <div className="space-y-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => {
                    setSelectedDoc(doc);
                    setViewMode('preview');
                  }}
                  className="p-4 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-lg transition-all duration-200 cursor-pointer group"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{getFileIcon(doc.type)}</span>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400">
                        {doc.name}
                      </h4>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(doc.uploadDate).toLocaleDateString()}
                      </p>
                    </div>
                    <svg className="w-5 h-5 text-gray-400 group-hover:text-blue-500 transition-colors" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes highlight-pulse {
          0%, 100% {
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(234, 179, 8, 0.7);
          }
          50% {
            transform: scale(1.02);
            box-shadow: 0 0 0 10px rgba(234, 179, 8, 0);
          }
        }

        @keyframes animate-highlight-pulse {
          0%, 100% {
            opacity: 1;
            background-size: 200% 100%;
          }
          50% {
            opacity: 0.9;
            background-size: 220% 100%;
          }
        }

        :global(.highlight-pulse) {
          animation: highlight-pulse 1s ease-in-out 2;
        }

        :global(.animate-highlight-pulse) {
          animation: animate-highlight-pulse 2s ease-in-out infinite;
        }

        .scrollbar-thin::-webkit-scrollbar {
          height: 4px;
        }

        .scrollbar-thin::-webkit-scrollbar-track {
          background: rgba(0, 0, 0, 0.05);
          border-radius: 2px;
        }

        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 2px;
        }

        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
          background: rgba(0, 0, 0, 0.3);
        }
      `}</style>
    </div>
  );
};

export default DocumentViewer;
