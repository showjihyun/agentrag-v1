/**
 * AI Agent Streaming Hook
 * 
 * Handles Server-Sent Events (SSE) streaming for AI Agent responses
 */

import { useState, useCallback } from 'react';

interface StreamingOptions {
  provider: string;
  model: string;
  systemPrompt?: string;
  sessionId?: string;
  temperature?: number;
  maxTokens?: number;
}

interface StreamingMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export function useAIAgentStreaming() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const streamMessage = useCallback(
    async (
      userMessage: string,
      options: StreamingOptions,
      onChunk: (chunk: string) => void,
      onComplete: () => void,
      onError: (error: string) => void
    ) => {
      setIsStreaming(true);
      setError(null);

      try {
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('Authentication required');
        }

        const response = await fetch('/api/agent-builder/ai-agent/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            provider: options.provider,
            model: options.model,
            user_message: userMessage,
            system_prompt: options.systemPrompt,
            session_id: options.sessionId,
            temperature: options.temperature || 0.7,
            max_tokens: options.maxTokens || 1000,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        if (!response.body) {
          throw new Error('Response body is null');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);

              if (data === '[DONE]') {
                onComplete();
                setIsStreaming(false);
                return;
              }

              try {
                const parsed = JSON.parse(data);

                if (parsed.type === 'content') {
                  onChunk(parsed.content);
                } else if (parsed.type === 'error') {
                  throw new Error(parsed.error);
                } else if (parsed.type === 'done') {
                  onComplete();
                  setIsStreaming(false);
                  return;
                }
              } catch (parseError: unknown) {
                console.error('Failed to parse SSE data:', parseError instanceof Error ? parseError.message : parseError);
              }
            }
          }
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Streaming failed';
        setError(errorMessage);
        onError(errorMessage);
        setIsStreaming(false);
      }
    },
    []
  );

  return {
    streamMessage,
    isStreaming,
    error,
  };
}
