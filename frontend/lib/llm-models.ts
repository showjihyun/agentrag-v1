/**
 * LLM Models Configuration
 * Centralized model definitions for consistency across the application
 */

export interface LLMProvider {
  id: string;
  name: string;
  description: string;
  requiresApiKey: boolean;
  models: LLMModel[];
  icon: string;
  type: 'cloud' | 'local';
}

export interface LLMModel {
  id: string;
  name: string;
  description?: string;
}

/**
 * Offline/Local LLM Models (Ollama)
 */
export const OFFLINE_MODELS: LLMModel[] = [
  { id: 'llama3.3:70b', name: 'Llama 3.3 70B', description: 'Latest Llama model' },
  { id: 'llama3.1:70b', name: 'Llama 3.1 70B', description: 'Powerful reasoning' },
  { id: 'qwen2.5:72b', name: 'Qwen 2.5 72B', description: 'Multilingual excellence' },
  { id: 'deepseek-r1:70b', name: 'DeepSeek R1 70B', description: 'Advanced reasoning' },
  { id: 'mixtral:8x7b', name: 'Mixtral 8x7B', description: 'Mixture of experts' },
];

/**
 * OpenAI Models
 */
export const OPENAI_MODELS: LLMModel[] = [
  { id: 'gpt-5', name: 'GPT-5', description: 'Latest flagship model' },
  { id: 'o3', name: 'GPT-o3', description: 'Advanced reasoning' },
  { id: 'o3-mini', name: 'GPT-o3 Mini', description: 'Fast reasoning' },
  { id: 'gpt-4o', name: 'GPT-4o', description: 'Multimodal powerhouse' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', description: 'Fast and efficient' },
];

/**
 * Anthropic Claude Models
 */
export const CLAUDE_MODELS: LLMModel[] = [
  { id: 'claude-4.5-sonnet', name: 'Claude 4.5 Sonnet', description: 'Latest Claude' },
  { id: 'claude-4-sonnet', name: 'Claude 4 Sonnet', description: 'Powerful reasoning' },
  { id: 'claude-3.7-sonnet', name: 'Claude 3.7 Sonnet', description: 'Enhanced capabilities' },
  { id: 'claude-3.5-sonnet', name: 'Claude 3.5 Sonnet', description: 'Balanced performance' },
  { id: 'claude-3-opus', name: 'Claude 3 Opus', description: 'Maximum intelligence' },
];

/**
 * Google Gemini Models
 */
export const GEMINI_MODELS: LLMModel[] = [
  { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', description: 'Ultra-fast responses' },
  { id: 'gemini-2.0-pro', name: 'Gemini 2.0 Pro', description: 'Advanced capabilities' },
  { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', description: 'Long context' },
  { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash', description: 'Fast and efficient' },
  { id: 'gemini-ultra', name: 'Gemini Ultra', description: 'Maximum performance' },
];

/**
 * xAI Grok Models
 */
export const GROK_MODELS: LLMModel[] = [
  { id: 'grok-3', name: 'Grok 3', description: 'Latest Grok model' },
  { id: 'grok-2.5', name: 'Grok 2.5', description: 'Enhanced reasoning' },
  { id: 'grok-2', name: 'Grok 2', description: 'Powerful AI' },
  { id: 'grok-2-mini', name: 'Grok 2 Mini', description: 'Fast responses' },
  { id: 'grok-vision', name: 'Grok Vision', description: 'Multimodal AI' },
];

/**
 * All LLM Providers
 */
export const LLM_PROVIDERS: LLMProvider[] = [
  {
    id: 'ollama',
    name: 'Ollama',
    description: 'Local LLM runtime',
    requiresApiKey: false,
    models: OFFLINE_MODELS,
    icon: '🦙',
    type: 'local',
  },
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT models',
    requiresApiKey: true,
    models: OPENAI_MODELS,
    icon: '🤖',
    type: 'cloud',
  },
  {
    id: 'claude',
    name: 'Claude',
    description: 'Anthropic AI',
    requiresApiKey: true,
    models: CLAUDE_MODELS,
    icon: '🧠',
    type: 'cloud',
  },
  {
    id: 'gemini',
    name: 'Gemini',
    description: 'Google AI',
    requiresApiKey: true,
    models: GEMINI_MODELS,
    icon: '✨',
    type: 'cloud',
  },
  {
    id: 'grok',
    name: 'Grok',
    description: 'xAI models',
    requiresApiKey: true,
    models: GROK_MODELS,
    icon: '⚡',
    type: 'cloud',
  },
];

/**
 * Get provider by ID
 */
export function getProvider(providerId: string): LLMProvider | undefined {
  return LLM_PROVIDERS.find((p) => p.id === providerId);
}

/**
 * Get model by provider and model ID
 */
export function getModel(providerId: string, modelId: string): LLMModel | undefined {
  const provider = getProvider(providerId);
  return provider?.models.find((m) => m.id === modelId);
}

/**
 * Get all models for a provider
 * For Settings-configured providers, loads from localStorage (set by LLM settings page)
 * For Ollama, tries to load from localStorage first (set by LLM settings page)
 */
export function getModelsForProvider(providerId: string): LLMModel[] {
  // First, try to get models from Settings configuration
  try {
    const savedConfig = localStorage.getItem('llm_config');
    if (savedConfig) {
      const config = JSON.parse(savedConfig);
      
      // For Ollama, use the models fetched from Ollama API and saved in Settings
      if (providerId === 'ollama') {
        const ollamaModels = localStorage.getItem('ollama_models');
        if (ollamaModels) {
          const models = JSON.parse(ollamaModels) as string[];
          if (models.length > 0) {
            return models.map(modelName => ({
              id: modelName,
              name: modelName,
              description: 'Local model',
            }));
          }
        }
        // Fallback to default Ollama models if none found
        return OFFLINE_MODELS;
      }
      
      // For cloud providers, use the models defined in Settings
      const settingsProviderModels: Record<string, string[]> = {
        openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
        anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
        claude: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'], // alias for anthropic
        gemini: ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
        google: ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'], // alias for gemini
      };
      
      const models = settingsProviderModels[providerId];
      if (models) {
        return models.map(modelId => ({
          id: modelId,
          name: modelId,
          description: `${providerId} model`,
        }));
      }
    }
  } catch (error) {
    console.warn('Failed to load models from Settings configuration:', error);
  }
  
  // Fallback to hardcoded models if Settings config not available
  const provider = getProvider(providerId);
  return provider?.models || [];
}

/**
 * Save Ollama models to localStorage
 * Called by LLM settings page after fetching from Ollama API
 */
export function saveOllamaModels(models: string[]): void {
  try {
    localStorage.setItem('ollama_models', JSON.stringify(models));
  } catch (error) {
    console.error('Failed to save Ollama models to localStorage:', error);
  }
}

/**
 * Get available providers based on Settings configuration
 * Only returns providers that are properly configured in Settings
 */
export function getAvailableProviders(): LLMProvider[] {
  try {
    const savedConfig = localStorage.getItem('llm_config');
    if (!savedConfig) {
      // If no config, return all providers (fallback)
      return LLM_PROVIDERS;
    }
    
    const config = JSON.parse(savedConfig);
    const availableProviders: LLMProvider[] = [];
    
    // Check each provider's configuration
    for (const provider of LLM_PROVIDERS) {
      let isAvailable = false;
      
      if (provider.id === 'ollama') {
        // Ollama is available if enabled in settings
        isAvailable = config.ollama?.enabled === true;
      } else {
        // Cloud providers are available if they have API keys
        const apiKey = config.apiKeys?.[provider.id];
        isAvailable = apiKey && apiKey.trim().length > 0;
      }
      
      if (isAvailable) {
        availableProviders.push(provider);
      }
    }
    
    return availableProviders.length > 0 ? availableProviders : LLM_PROVIDERS;
  } catch (error) {
    console.warn('Failed to load provider configuration:', error);
    return LLM_PROVIDERS;
  }
}

/**
 * Check if a specific provider is available based on Settings configuration
 */
export function isProviderAvailable(providerId: string): boolean {
  const availableProviders = getAvailableProviders();
  return availableProviders.some(p => p.id === providerId);
}
