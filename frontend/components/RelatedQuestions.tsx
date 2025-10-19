'use client';

import React, { useState, useEffect } from 'react';

interface RelatedQuestionsProps {
  currentQuery: string;
  answer: string;
  sources?: any[];
  onQuestionClick: (question: string) => void;
  isProcessing?: boolean;
}

const RelatedQuestions: React.FC<RelatedQuestionsProps> = ({
  currentQuery,
  answer,
  sources = [],
  onQuestionClick,
  isProcessing = false,
}) => {
  const [questions, setQuestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // Generate related questions when answer is complete
    if (answer && !isProcessing && questions.length === 0) {
      generateRelatedQuestions();
    }
  }, [answer, isProcessing]);

  const generateRelatedQuestions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/query/related-questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: currentQuery,
          answer: answer,
          sources: sources.map(s => s.document_name || '').filter(Boolean).slice(0, 3),
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setQuestions(data.questions || []);
      } else {
        // Fallback to client-side generation
        setQuestions(generateFallbackQuestions(currentQuery, answer));
      }
    } catch (error) {
      console.error('Failed to generate related questions:', error);
      // Fallback to client-side generation
      setQuestions(generateFallbackQuestions(currentQuery, answer));
    } finally {
      setIsLoading(false);
    }
  };

  const generateFallbackQuestions = (query: string, answer: string): string[] => {
    // Simple fallback logic for generating related questions
    const questions: string[] = [];

    // Extract key topics from answer (simple approach)
    const sentences = answer.split(/[.!?]+/).filter(s => s.trim().length > 20);

    if (sentences.length > 0) {
      // Generate "Tell me more about..." questions
      const firstSentence = sentences[0].trim();
      const words = firstSentence.split(' ');
      if (words.length > 3) {
        questions.push(`Tell me more about ${words.slice(0, 5).join(' ')}...`);
      }
    }

    // Generate comparison questions
    if (answer.toLowerCase().includes('difference') || answer.toLowerCase().includes('compare')) {
      questions.push('What are the key differences?');
    }

    // Generate example questions
    if (answer.toLowerCase().includes('example') || answer.toLowerCase().includes('such as')) {
      questions.push('Can you provide more examples?');
    }

    // Generate deeper dive questions
    questions.push('Can you explain this in more detail?');
    questions.push('What are the practical applications?');

    return questions.slice(0, 4);
  };

  if (isLoading) {
    return (
      <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span>Generating related questions...</span>
        </div>
      </div>
    );
  }

  if (questions.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden shadow-sm">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 flex items-center justify-between hover:from-purple-100 hover:to-blue-100 dark:hover:from-purple-900/30 dark:hover:to-blue-900/30 transition-all duration-200"
      >
        <div className="flex items-center gap-3">
          <svg
            className={`w-4 h-4 transition-transform duration-300 ${isExpanded ? 'transform rotate-90' : ''
              }`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
              clipRule="evenodd"
            />
          </svg>
          <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            💡 Related Questions
          </span>
          <span className="px-2 py-0.5 text-xs font-medium bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded-full">
            {questions.length}
          </span>
        </div>
        <span className="text-xs font-medium text-gray-600 dark:text-gray-400 px-2 py-1 rounded hover:bg-white/50 dark:hover:bg-black/20 transition-colors">
          {isExpanded ? '▼ Hide' : '▶ Show'}
        </span>
      </button>

      {isExpanded && (
        <div className="p-4 bg-gray-50/50 dark:bg-gray-900/50 space-y-2">
          {questions.map((question, index) => (
            <button
              key={index}
              onClick={() => onQuestionClick(question)}
              className="w-full text-left p-3 bg-white dark:bg-gray-800 hover:bg-purple-50 dark:hover:bg-purple-900/20 border border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-700 rounded-lg transition-all duration-200 group"
              style={{
                animation: `fadeInSlide 0.3s ease-out ${index * 0.1}s both`
              }}
            >
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-purple-500 dark:text-purple-400 flex-shrink-0 mt-0.5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
                <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-purple-700 dark:group-hover:text-purple-300 transition-colors">
                  {question}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      <style jsx>{`
        @keyframes fadeInSlide {
          from {
            opacity: 0;
            transform: translateX(-10px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      `}</style>
    </div>
  );
};

export default RelatedQuestions;
