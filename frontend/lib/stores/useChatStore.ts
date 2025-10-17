/**
 * Chat Store using Zustand
 * 
 * Manages chat messages and conversation state.
 */

import { create } from 'zustand';
import { Message } from '@/components/MessageList';

interface ChatStore {
  // State
  messages: Message[];
  isProcessing: boolean;
  currentSessionId: string | null;
  
  // Actions
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  removeMessage: (id: string) => void;
  setMessages: (messages: Message[]) => void;
  clearMessages: () => void;
  setProcessing: (isProcessing: boolean) => void;
  setSessionId: (sessionId: string) => void;
  reset: () => void;
}

const initialState = {
  messages: [],
  isProcessing: false,
  currentSessionId: null,
};

export const useChatStore = create<ChatStore>()((set) => ({
  ...initialState,
  
  addMessage: (message) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },
  
  updateMessage: (id, updates) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    }));
  },
  
  removeMessage: (id) => {
    set((state) => ({
      messages: state.messages.filter((msg) => msg.id !== id),
    }));
  },
  
  setMessages: (messages) => {
    set({ messages });
  },
  
  clearMessages: () => {
    set({ messages: [] });
  },
  
  setProcessing: (isProcessing) => {
    set({ isProcessing });
  },
  
  setSessionId: (sessionId) => {
    set({ currentSessionId: sessionId });
  },
  
  reset: () => {
    set(initialState);
  },
}));

// Selectors
export const useMessages = () => useChatStore((state) => state.messages);
export const useIsProcessing = () => useChatStore((state) => state.isProcessing);
export const useCurrentSessionId = () => useChatStore((state) => state.currentSessionId);
