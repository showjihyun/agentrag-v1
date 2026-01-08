/**
 * LLM Settings API Client
 */

import { apiClient } from '../api-client';

export interface LLMProvider {
  name: string;
  display_name: string;
  models: string[];
  requires_api_key: boolean;
  is_available: boolean;
}

export interface LLMConfiguration {
  provider: string;
  model: string;
  providers: LLMProvider[];
}

export interface LLMTestRequest {
  provider: string;
  model: string;
  apiKey?: string;
  ollamaUrl?: string;
}

export interface LLMTestResponse {
  success: boolean;
  message: string;
  latency?: number;
}

export interface ChatflowLLMConfig {
  provider: string;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt?: string;
}

export interface ChatflowLLMConfigResponse {
  success: boolean;
  config?: ChatflowLLMConfig;
  message: string;
}

export const llmSettingsAPI = {
  /**
   * Get current LLM configuration and available providers
   */
  async getConfiguration(): Promise<LLMConfiguration> {
    return apiClient.request('/api/llm/configuration');
  },

  /**
   * Test LLM provider connection
   */
  async testConnection(request: LLMTestRequest): Promise<LLMTestResponse> {
    return apiClient.request('/api/llm/test', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Get LLM configuration for a specific chatflow
   */
  async getChatflowConfig(chatflowId: string): Promise<ChatflowLLMConfigResponse> {
    return apiClient.request(`/api/llm/chatflow/${chatflowId}/config`);
  },

  /**
   * Update LLM configuration for a specific chatflow
   */
  async updateChatflowConfig(chatflowId: string, config: ChatflowLLMConfig): Promise<ChatflowLLMConfigResponse> {
    return apiClient.request(`/api/llm/chatflow/${chatflowId}/config`, {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  },
};