/**
 * Global Application State Management with Zustand
 * 
 * Replaces Context API for better performance and developer experience
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { MessageResponse } from '@/lib/types';
import { Locale } from '@/lib/i18n/config';

interface AppState {
  // Session state
  activeSessionId: string | null;
  setActiveSessionId: (id: string | null) => void;
  
  // UI state
  showSidebar: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  
  // Messages state (cached by session)
  messagesCache: Map<string, MessageResponse[]>;
  addMessage: (sessionId: string, message: MessageResponse) => void;
  setMessages: (sessionId: string, messages: MessageResponse[]) => void;
  clearMessages: (sessionId: string) => void;
  
  // Loading state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  
  // Query mode
  selectedMode: 'fast' | 'balanced' | 'deep' | 'auto' | 'web_search';
  setSelectedMode: (mode: 'fast' | 'balanced' | 'deep' | 'auto' | 'web_search') => void;
  
  // Theme
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  
  // Onboarding
  hasCompletedOnboarding: boolean;
  setHasCompletedOnboarding: (completed: boolean) => void;
  
  // Internationalization
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // Session state
        activeSessionId: null,
        setActiveSessionId: (id) => set({ activeSessionId: id }),
        
        // UI state
        showSidebar: false,
        toggleSidebar: () => set((state) => ({ showSidebar: !state.showSidebar })),
        setSidebarOpen: (open) => set({ showSidebar: open }),
        
        // Messages state
        messagesCache: new Map(),
        addMessage: (sessionId, message) => set((state) => {
          const newCache = new Map(state.messagesCache);
          const sessionMessages = newCache.get(sessionId) || [];
          newCache.set(sessionId, [...sessionMessages, message]);
          return { messagesCache: newCache };
        }),
        setMessages: (sessionId, messages) => set((state) => {
          const newCache = new Map(state.messagesCache);
          newCache.set(sessionId, messages);
          return { messagesCache: newCache };
        }),
        clearMessages: (sessionId) => set((state) => {
          const newCache = new Map(state.messagesCache);
          newCache.delete(sessionId);
          return { messagesCache: newCache };
        }),
        
        // Loading state
        isLoading: false,
        setIsLoading: (loading) => set({ isLoading: loading }),
        
        // Query mode
        selectedMode: 'auto',
        setSelectedMode: (mode) => set({ selectedMode: mode }),
        
        // Theme
        theme: 'system',
        setTheme: (theme) => set({ theme: theme }),
        
        // Onboarding
        hasCompletedOnboarding: false,
        setHasCompletedOnboarding: (completed) => set({ hasCompletedOnboarding: completed }),
        
        // Internationalization
        locale: 'en' as Locale,
        setLocale: (locale) => set({ locale }),
      }),
      {
        name: 'app-storage',
        // Only persist certain fields
        partialize: (state) => ({
          selectedMode: state.selectedMode,
          theme: state.theme,
          hasCompletedOnboarding: state.hasCompletedOnboarding,
          locale: state.locale,
        }),
      }
    ),
    { name: 'AppStore' }
  )
);

// Selectors for optimized re-renders
export const useActiveSessionId = () => useAppStore((state) => state.activeSessionId);
export const useShowSidebar = () => useAppStore((state) => state.showSidebar);
export const useIsLoading = () => useAppStore((state) => state.isLoading);
export const useSelectedMode = () => useAppStore((state) => state.selectedMode);
export const useTheme = () => useAppStore((state) => state.theme);
export const useHasCompletedOnboarding = () => useAppStore((state) => state.hasCompletedOnboarding);
export const useLocale = () => useAppStore((state) => state.locale);

// Individual action hooks (stable references, no re-renders)
export const useSetActiveSessionId = () => useAppStore((state) => state.setActiveSessionId);
export const useToggleSidebar = () => useAppStore((state) => state.toggleSidebar);
export const useSetSidebarOpen = () => useAppStore((state) => state.setSidebarOpen);
export const useSetIsLoading = () => useAppStore((state) => state.setIsLoading);
export const useSetSelectedMode = () => useAppStore((state) => state.setSelectedMode);
export const useSetTheme = () => useAppStore((state) => state.setTheme);
export const useSetHasCompletedOnboarding = () => useAppStore((state) => state.setHasCompletedOnboarding);
export const useSetLocale = () => useAppStore((state) => state.setLocale);

// Combined actions hook (use sparingly, prefer individual hooks)
// This creates a stable reference by selecting only the actions
const actionsSelector = (state: AppState) => ({
  setActiveSessionId: state.setActiveSessionId,
  toggleSidebar: state.toggleSidebar,
  setSidebarOpen: state.setSidebarOpen,
  addMessage: state.addMessage,
  setMessages: state.setMessages,
  clearMessages: state.clearMessages,
  setIsLoading: state.setIsLoading,
  setSelectedMode: state.setSelectedMode,
  setTheme: state.setTheme,
  setHasCompletedOnboarding: state.setHasCompletedOnboarding,
  setLocale: state.setLocale,
});

export const useAppActions = () => useAppStore(actionsSelector);
