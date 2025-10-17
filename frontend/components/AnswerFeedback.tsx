'use client';

/**
 * AnswerFeedback Component
 * Allows users to provide feedback on answer quality.
 */

import React, { useState } from 'react';
import { apiClient } from '@/lib/api-client';

interface AnswerFeedbackProps {
  messageId?: string;
  sessionId?: string;
  onFeedbackSubmitted?: (rating: number) => void;
}

export function AnswerFeedback({
  messageId,
  sessionId,
  onFeedbackSubmitted
}: AnswerFeedbackProps) {
  const [feedback, setFeedback] = useState<'good' | 'bad' | null>(null);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleFeedback = async (type: 'good' | 'bad') => {
    if (isSubmitted) return;

    setFeedback(type);
    
    // Show comment box for negative feedback
    if (type === 'bad') {
      setShowComment(true);
      return;
    }

    // Submit positive feedback immediately
    await submitFeedback(type, '');
  };

  const submitFeedback = async (type: 'good' | 'bad', userComment: string) => {
    setIsSubmitting(true);

    try {
      const rating = type === 'good' ? 1 : -1;

      await apiClient.submitFeedback({
        message_id: messageId,
        session_id: sessionId,
        rating,
        comment: userComment || undefined
      });

      setIsSubmitted(true);
      onFeedbackSubmitted?.(rating);

      // Hide comment box after submission
      setTimeout(() => {
        setShowComment(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('Failed to submit feedback. Please try again.');
      setFeedback(null);
      setShowComment(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCommentSubmit = () => {
    if (feedback) {
      submitFeedback(feedback, comment);
    }
  };

  if (isSubmitted) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <span>✓ Thank you for your feedback!</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Was this helpful?</span>
        
        <button
          onClick={() => handleFeedback('good')}
          disabled={isSubmitting || feedback !== null}
          className={`p-2 rounded-lg transition-colors ${
            feedback === 'good'
              ? 'bg-green-100 text-green-700'
              : 'hover:bg-gray-100 text-gray-600'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          title="This answer was helpful"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
          </svg>
        </button>

        <button
          onClick={() => handleFeedback('bad')}
          disabled={isSubmitting || feedback !== null}
          className={`p-2 rounded-lg transition-colors ${
            feedback === 'bad'
              ? 'bg-red-100 text-red-700'
              : 'hover:bg-gray-100 text-gray-600'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          title="This answer was not helpful"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
          </svg>
        </button>
      </div>

      {showComment && (
        <div className="flex flex-col gap-2 mt-2 p-3 bg-gray-50 rounded-lg">
          <label className="text-sm font-medium text-gray-700">
            What went wrong? (optional)
          </label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Tell us how we can improve..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={3}
            disabled={isSubmitting}
          />
          <div className="flex gap-2">
            <button
              onClick={handleCommentSubmit}
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
            </button>
            <button
              onClick={() => {
                setShowComment(false);
                setFeedback(null);
                setComment('');
              }}
              disabled={isSubmitting}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
