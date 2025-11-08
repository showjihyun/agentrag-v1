/**
 * UI Store using Zustand
 * 
 * Manages global UI state like modals, sidebars, themes, etc.
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

// Types
interface UIState {
  // Theme
  theme: 'light' | 'dark' | 'system';
  
  // Sidebar
  isSidebarOpen: boolean;
  sidebarWidth: number;
  
  // Modals
  activeModal: string | null;
  modalData: Record<string, unknown> | null;
  
  // Mobile
  isMobileMenuOpen: boolean;
  
  // Document viewer
  isDocViewerOpen: boolean;
  
  // Loading
  globalLoading: boolean;
  loadingMessage: string | null;
  
  // Toast
  toasts: Array<{
    id: string;
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
    duration?: number;
  }>;
}

interface UIActions {
  // Theme actions
  setTheme: (theme: UIState['theme']) => void;
  toggleTheme: () => void;
  
  // Sidebar actions
  toggleSidebar: () => void;
  setSidebarOpen: (isOpen: boolean) => void;
  setSidebarWidth: (width: number) => void;
  
  // Modal actions
  openModal: (modalId: string, data?: Record<string, unknown>) => void;
  closeModal: () => void;
  
  // Mobile actions
  toggleMobileMenu: () => void;
  setMobileMenuOpen: (isOpen: boolean) => void;
  
  // Document viewer actions
  toggleDocViewer: () => void;
  setDocViewerOpen: (isOpen: boolean) => void;
  
  // Loading actions
  setGlobalLoading: (isLoading: boolean, message?: string) => void;
  
  // Toast actions
  addToast: (toast: Omit<UIState['toasts'][0], 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
  
  // Utility
  reset: () => void;
}

type UIStore = UIState & UIActions;

// Initial state
const initialState: UIState = {
  theme: 'system',
  isSidebarOpen: true,
  sidebarWidth: 280,
  activeModal: null,
  modalData: null,
  isMobileMenuOpen: false,
  isDocViewerOpen: true,
  globalLoading: false,
  loadingMessage: null,
  toasts: [],
};

// Create store
export const useUIStore = create<UIStore>()(
  devtools(
    persist(
      immer((set, get) => ({
        ...initialState,
        
        // Theme actions
        setTheme: (theme) => {
          set((state) => {
            state.theme = theme;
          });
        },
        
        toggleTheme: () => {
          set((state) => {
            state.theme = state.theme === 'light' ? 'dark' : 'light';
          });
        },
        
        // Sidebar actions
        toggleSidebar: () => {
          set((state) => {
            state.isSidebarOpen = !state.isSidebarOpen;
          });
        },
        
        setSidebarOpen: (isOpen) => {
          set((state) => {
            state.isSidebarOpen = isOpen;
          });
        },
        
        setSidebarWidth: (width) => {
          set((state) => {
            state.sidebarWidth = Math.max(200, Math.min(400, width));
          });
        },
        
        // Modal actions
        openModal: (modalId, data) => {
          set((state) => {
            state.activeModal = modalId;
            state.modalData = data || null;
          });
        },
        
        closeModal: () => {
          set((state) => {
            state.activeModal = null;
            state.modalData = null;
          });
        },
        
        // Mobile actions
        toggleMobileMenu: () => {
          set((state) => {
            state.isMobileMenuOpen = !state.isMobileMenuOpen;
          });
        },
        
        setMobileMenuOpen: (isOpen) => {
          set((state) => {
            state.isMobileMenuOpen = isOpen;
          });
        },
        
        // Document viewer actions
        toggleDocViewer: () => {
          set((state) => {
            state.isDocViewerOpen = !state.isDocViewerOpen;
          });
        },
        
        setDocViewerOpen: (isOpen) => {
          set((state) => {
            state.isDocViewerOpen = isOpen;
          });
        },
        
        // Loading actions
        setGlobalLoading: (isLoading, message) => {
          set((state) => {
            state.globalLoading = isLoading;
            state.loadingMessage = message || null;
          });
        },
        
        // Toast actions
        addToast: (toast) => {
          const id = `toast-${Date.now()}-${Math.random()}`;
          set((state) => {
            state.toasts.push({ ...toast, id });
          });
          
          // Auto remove after duration
          const duration = toast.duration || 5000;
          setTimeout(() => {
            get().removeToast(id);
          }, duration);
        },
        
        removeToast: (id) => {
          set((state) => {
            state.toasts = state.toasts.filter((t) => t.id !== id);
          });
        },
        
        clearToasts: () => {
          set((state) => {
            state.toasts = [];
          });
        },
        
        // Utility
        reset: () => {
          set(initialState);
        },
      })),
      {
        name: 'ui-storage',
        partialize: (state) => ({
          theme: state.theme,
          isSidebarOpen: state.isSidebarOpen,
          sidebarWidth: state.sidebarWidth,
          isDocViewerOpen: state.isDocViewerOpen,
        }),
      }
    ),
    { name: 'UIStore' }
  )
);

// Selectors
export const useTheme = () => useUIStore((state) => state.theme);
export const useIsSidebarOpen = () => useUIStore((state) => state.isSidebarOpen);
export const useSidebarWidth = () => useUIStore((state) => state.sidebarWidth);
export const useActiveModal = () => useUIStore((state) => state.activeModal);
export const useModalData = () => useUIStore((state) => state.modalData);
export const useIsMobileMenuOpen = () => useUIStore((state) => state.isMobileMenuOpen);
export const useIsDocViewerOpen = () => useUIStore((state) => state.isDocViewerOpen);
export const useGlobalLoading = () => useUIStore((state) => state.globalLoading);
export const useLoadingMessage = () => useUIStore((state) => state.loadingMessage);
export const useToasts = () => useUIStore((state) => state.toasts);

// Action selectors
export const useUIActions = () => useUIStore((state) => ({
  setTheme: state.setTheme,
  toggleTheme: state.toggleTheme,
  toggleSidebar: state.toggleSidebar,
  setSidebarOpen: state.setSidebarOpen,
  openModal: state.openModal,
  closeModal: state.closeModal,
  toggleDocViewer: state.toggleDocViewer,
  setDocViewerOpen: state.setDocViewerOpen,
  addToast: state.addToast,
  removeToast: state.removeToast,
}));
