/**
 * Chat Style Store
 * Shared chat interface styling configuration
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface ChatStyleConfig {
  theme: 'light' | 'dark' | 'auto';
  primaryColor: string;
  buttonSize: number;
  windowWidth: number;
  windowHeight: number;
  welcomeMessage: string;
  placeholder: string;
  showBranding: boolean;
  allowFullscreen: boolean;
  borderRadius: number;
  fontSize: number;
}

export const DEFAULT_CHAT_STYLE: ChatStyleConfig = {
  theme: 'auto',
  primaryColor: '#6366f1',
  buttonSize: 60,
  windowWidth: 400,
  windowHeight: 600,
  welcomeMessage: '안녕하세요! 무엇을 도와드릴까요?',
  placeholder: '메시지를 입력하세요...',
  showBranding: true,
  allowFullscreen: true,
  borderRadius: 12,
  fontSize: 14,
};

interface ChatStyleStore {
  config: ChatStyleConfig;
  updateConfig: (updates: Partial<ChatStyleConfig>) => void;
  resetConfig: () => void;
}

export const useChatStyleStore = create<ChatStyleStore>()(
  persist(
    (set) => ({
      config: DEFAULT_CHAT_STYLE,
      updateConfig: (updates) =>
        set((state) => ({
          config: { ...state.config, ...updates },
        })),
      resetConfig: () => set({ config: DEFAULT_CHAT_STYLE }),
    }),
    {
      name: 'chat-style-storage',
    }
  )
);
