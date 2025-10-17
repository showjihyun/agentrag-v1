'use client';

import { useState } from 'react';
import { ThumbsUp, ThumbsDown } from 'lucide-react';

interface FeedbackButtonProps {
  messageId: string;
  onFeedbackSubmitted?: () => void;
}

export default function FeedbackButton({ messageId, onFeedbackSubmitted }: FeedbackButtonProps) {
  const [rating, setRating] = useState<number | null>(null);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleRating = async (newRating: number) => {
    setRating(newRating);
    
    if (newRating > 0) {
      // Positive feedback - submit immediately
      await submitFeedback(newRating, '');
    } else {
      // Negative feedback - show comment box
      setShowComment(true);
    }
  };

  const submitFeedback = async (feedbackRating: number, feedbackComment: string) => {
    setSubmitting(true);
    
    try {
      const response = await fetch('/api/feedback/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message_id: messageId,
          rating: feedbackRating,
          comment: feedbackComment || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit feedback');
      }

      onFeedbackSubmitted?.();
      
      // Reset after 2 seconds
      setTimeout(() => {
        setShowComment(false);
        setComment('');
      }, 2000);
      
    } catch (error) {
      console.error('Error submitting feedback:', error);
      setRating(null);
      setShowComment(false);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCommentSubmit = async () => {
    if (rating !== null) {
      await submitFeedback(rating, comment);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => handleRating(1)}
        disabled={rating !== null || submitting}
        className={`p-2 rounded-lg transition-colors ${
          rating === 1
            ? 'bg-green-100 text-green-600'
            : 'hover:bg-gray-100 text-gray-600'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
        title="Good answer"
      >
        <ThumbsUp size={18} />
      </button>
      
      <button
        onClick={() => handleRating(-1)}
        disabled={rating !== null || submitting}
        className={`p-2 rounded-lg transition-colors ${
          rating === -1
            ? 'bg-red-100 text-red-600'
            : 'hover:bg-gray-100 text-gray-600'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
        title="Poor answer"
      >
        <ThumbsDown size={18} />
      </button>

      {showComment && (
        <div className="flex items-center gap-2 ml-2">
          <input
            type="text"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="What went wrong? (optional)"
            className="px-3 py-1 border rounded-lg text-sm w-64"
            disabled={submitting}
          />
          <button
            onClick={handleCommentSubmit}
            disabled={submitting}
            className="px-3 py-1 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 disabled:opacity-50"
          >
            {submitting ? 'Sending...' : 'Send'}
          </button>
        </div>
      )}

      {rating !== null && !showComment && (
        <span className="text-sm text-gray-500 ml-2">
          Thanks for your feedback!
        </span>
      )}
    </div>
  );
}
