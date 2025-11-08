/**
 * Chat Store using Zustand with Best Practices
 * 
 * Features:
 * - Immer middleware for immutable updates
 * - Persist middleware for localStorage
 * - DevTools integration
 * - Optimized selectors
 * - Type-safe actions
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { Message } from '@/components/MessageList';

// Types
interface ChatState {
  messages: Message[];
  isProcessing: boolean;
  currentSessionId: string | null;
  error: string | null;
  lastMessageTimestamp: number | null;
}

interface ChatActions {
  // Message actions
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  removeMessage: (id: string) => void;
  setMessages: (messages: Message[]) => void;
  clearMessages: () => void;
  
  // Processing actions
  setProcessing: (isProcessing: boolean) => void;
  
  // Session actions
  setSessionId: (sessionId: string | null) => void;
  
  // Error actions
  setError: (error: string | null) => void;
  
  // Utility actions
  reset: () => void;
  
  // Computed actions
  getMessageById: (id: string) => Message | undefined;
  getLastMessage: () => Message | undefined;
  getMessageCount: () => number;
}

type ChatStore = ChatState & ChatActions;

// Initial state
const initialState: ChatState = {
  messages: [],
  isProcessing: false,
  currentSessionId: null,
  error: null,
  lastMessageTimestamp: null,
};

// Create store with middleware
export const useChatStore = create<ChatStore>()(
  devtools(
    persist(
      immer((set, get) => ({
        ...initialState,
        
        // Message actions
        addMessage: (message) => {
          set((state) => {
            state.messages.push(message);
            state.lastMessageTimestamp = Date.now();
          });
        },
        
        updateMessage: (id, updates) => {
          set((state) => {
            const index = state.messages.findIndex((msg) => msg.id === id);
            if (index !== -1) {
              state.messages[index] = { ...state.messages[index], ...updates };
            }
          });
        },
        
        removeMessage: (id) => {
          set((state) => {
            state.messages = state.messages.filter((msg) => msg.id !== id);
          });
        },
        
        setMessages: (messages) => {
          set((state) => {
            state.messages = messages;
            state.lastMessageTimestamp = messages.length > 0 ? Date.now() : null;
          });
        },
        
        clearMessages: () => {
          set((state) => {
            state.messages = [];
            state.lastMessageTimestamp = null;
          });
        },
        
        // Processing actions
        setProcessing: (isProcessing) => {
          set((state) => {
            state.isProcessing = isProcessing;
            if (!isProcessing) {
              state.error = null;
            }
          });
        },
        
        // Session actions
        setSessionId: (sessionId) => {
          set((state) => {
            state.currentSessionId = sessionId;
          });
        },
        
        // Error actions
        setError: (error) => {
          set((state) => {
            state.error = error;
            if (error) {
              state.isProcessing = false;
            }
          });
        },
        
        // Utility actions
        reset: () => {
          set(initialState);
        },
        
        // Computed actions
        getMessageById: (id) => {
          return get().messages.find((msg) => msg.id === id);
        },
        
        getLastMessage: () => {
          const messages = get().messages;
          return messages[messages.length - 1];
        },
        
        getMessageCount: () => {
          return get().messages.length;
        },
      })),
      {
        name: 'chat-storage',
        partialize: (state) => ({
          currentSessionId: state.currentSessionId,
          // Don't persist messages - they should be loaded from server
        }),
      }
    ),
    { name: 'ChatStore' }
  )
);

// Optimized Selectors
export const useMessages = () => useChatStore((state) => state.messages);
export const useIsProcessing = () => useChatStore((state) => state.isProcessing);
export const useCurrentSessionId = () => useChatStore((state) => state.currentSessionId);
export const useChatError = () => useChatStore((state) => state.error);
export const useLastMessageTimestamp = () => useChatStore((state) => state.lastMessageTimestamp);

// Computed selectors
export const useMessageCount = () => useChatStore((state) => state.messages.length);
export const useHasMessages = () => useChatStore((state) => state.messages.length > 0);
export const useLastMessage = () => useChatStore((state) => {
  const messages = state.messages;
  return messages[messages.length - 1];
});

// Action selectors
export const useChatActions = () => useChatStore((state) => ({
  addMessage: state.addMessage,
  updateMessage: state.updateMessage,
  removeMessage: state.removeMessage,
  setMessages: state.setMessages,
  clearMessages: state.clearMessages,
  setProcessing: state.setProcessing,
  setSessionId: state.setSessionId,
  setError: state.setError,
  reset: state.reset,
}));
