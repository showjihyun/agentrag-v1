'use client';

import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ResponseFeedbackProps {
  messageId: string;
  onFeedback: (rating: 'positive' | 'negative', details?: string) => void;
  className?: string;
}

export default function ResponseFeedback({
  messageId,
  onFeedback,
  className
}: ResponseFeedbackProps) {
  const [rating, setRating] = useState<'positive' | 'negative' | null>(null);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handlePositiveFeedback = () => {
    setRating('positive');
    onFeedback('positive');
  };

  const handleNegativeFeedback = () => {
    setRating('negative');
    setShowFeedbackForm(true);
  };

  const handleSubmitFeedback = async () => {
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      await onFeedback('negative', feedbackText || undefined);
      setShowFeedbackForm(false);
      setFeedbackText('');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={cn('mt-3', className)}>
      {!rating && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Was this helpful?
          </span>
          <button
            onClick={handlePositiveFeedback}
            className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="Helpful"
            aria-label="Mark as helpful"
          >
            <ThumbsUp className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
          <button
            onClick={handleNegativeFeedback}
            className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="Not helpful"
            aria-label="Mark as not helpful"
          >
            <ThumbsDown className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      )}

      {rating === 'positive' && (
        <div className="flex items-center gap-2 text-xs text-green-600 dark:text-green-400">
          <ThumbsUp className="w-4 h-4" />
          <span>Thanks for your feedback!</span>
        </div>
      )}

      {rating === 'negative' && showFeedbackForm && (
        <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-start justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              What could be improved?
            </span>
            <button
              onClick={() => {
                setShowFeedbackForm(false);
                setRating(null);
              }}
              className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </div>
          
          <textarea
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Optional: Tell us what went wrong..."
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            rows={3}
          />
          
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleSubmitFeedback}
              disabled={isSubmitting}
              className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 rounded-md transition-colors"
            >
              {isSubmitting ? 'Submitting...' : 'Submit'}
            </button>
            <button
              onClick={() => {
                handleSubmitFeedback();
              }}
              disabled={isSubmitting}
              className="px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md transition-colors"
            >
              Skip
            </button>
          </div>
        </div>
      )}

      {rating === 'negative' && !showFeedbackForm && (
        <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
          <ThumbsDown className="w-4 h-4" />
          <span>Thanks for your feedback!</span>
        </div>
      )}
    </div>
  );
}
