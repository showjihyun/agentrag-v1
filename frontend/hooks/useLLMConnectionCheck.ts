/**
 * useLLMConnectionCheck Hook
 * 
 * Check LLM connection status (Ollama, OpenAI, Claude, etc.)
 */

import { useState, useEffect } from 'react';

interface ConnectionStatus {
  connected: boolean;
  checking: boolean;
  provider: string;
  model: string;
  message?: string;
  error?: string;
}

export function useLLMConnectionCheck(provider: string, model: string, apiKey?: string, enabled: boolean = true) {
  const [status, setStatus] = useState<ConnectionStatus>({
    connected: false,
    checking: true,
    provider,
    model,
  });

  useEffect(() => {
    if (!enabled || !provider || !model) {
      setStatus({
        connected: false,
        checking: false,
        provider,
        model,
      });
      return;
    }

    let cancelled = false;

    const checkConnection = async () => {
      setStatus(prev => ({ ...prev, checking: true }));

      try {
        console.log('🔍 Checking LLM connection:', { 
          provider, 
          model, 
          hasApiKey: !!apiKey,
          apiKeyLength: apiKey?.length,
          apiKeyPreview: apiKey ? `${apiKey.substring(0, 7)}...` : 'none'
        });

        const requestBody = { 
          provider, 
          model,
          api_key: apiKey  // Pass API key from node config
        };
        
        console.log('📤 Request body:', requestBody);

        const response = await fetch('/api/agent-builder/ai-agent-chat/check-connection', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        });

        if (cancelled) return;

        const data = await response.json();
        console.log('📊 Connection check result:', data);

        setStatus({
          connected: data.connected,
          checking: false,
          provider,
          model,
          message: data.message,
          error: data.error,
        });
      } catch (error) {
        if (cancelled) return;

        console.error('❌ Connection check failed:', error);
        setStatus({
          connected: false,
          checking: false,
          provider,
          model,
          error: error instanceof Error ? error.message : 'Connection check failed',
        });
      }
    };

    checkConnection();

    return () => {
      cancelled = true;
    };
  }, [provider, model, apiKey, enabled]);

  return status;
}
