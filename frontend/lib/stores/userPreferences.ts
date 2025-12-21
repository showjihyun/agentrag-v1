import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UserPreferences {
  // View preferences
  defaultViewMode: 'grid' | 'list';
  cardDensity: 'compact' | 'comfortable' | 'spacious';
  
  // Sorting and filtering
  defaultSortBy: 'name' | 'created_at' | 'updated_at' | 'execution_count';
  defaultFilterStatus: 'all' | 'active' | 'inactive';
  
  // Display preferences
  showTemplatesByDefault: boolean;
  enableAnimations: boolean;
  enableSounds: boolean;
  
  // Workflow preferences
  favoriteTemplates: string[];
  recentlyUsedTemplates: string[];
  pinnedFlows: string[];
  
  // Performance preferences
  enableVirtualization: boolean;
  itemsPerPage: number;
  
  // Accessibility
  highContrast: boolean;
  reducedMotion: boolean;
  fontSize: 'small' | 'medium' | 'large';
}

interface UserPreferencesStore extends UserPreferences {
  // Actions
  setViewMode: (mode: 'grid' | 'list') => void;
  setCardDensity: (density: 'compact' | 'comfortable' | 'spacious') => void;
  setSortBy: (sortBy: 'name' | 'created_at' | 'updated_at' | 'execution_count') => void;
  setFilterStatus: (status: 'all' | 'active' | 'inactive') => void;
  
  toggleTemplatesByDefault: () => void;
  toggleAnimations: () => void;
  toggleSounds: () => void;
  
  addFavoriteTemplate: (templateId: string) => void;
  removeFavoriteTemplate: (templateId: string) => void;
  addRecentTemplate: (templateId: string) => void;
  
  pinFlow: (flowId: string) => void;
  unpinFlow: (flowId: string) => void;
  
  setVirtualization: (enabled: boolean) => void;
  setItemsPerPage: (count: number) => void;
  
  setHighContrast: (enabled: boolean) => void;
  setReducedMotion: (enabled: boolean) => void;
  setFontSize: (size: 'small' | 'medium' | 'large') => void;
  
  resetToDefaults: () => void;
}

const defaultPreferences: UserPreferences = {
  defaultViewMode: 'grid',
  cardDensity: 'comfortable',
  defaultSortBy: 'updated_at',
  defaultFilterStatus: 'all',
  showTemplatesByDefault: false,
  enableAnimations: true,
  enableSounds: false,
  favoriteTemplates: [],
  recentlyUsedTemplates: [],
  pinnedFlows: [],
  enableVirtualization: false,
  itemsPerPage: 12,
  highContrast: false,
  reducedMotion: false,
  fontSize: 'medium'
};

export const useUserPreferences = create<UserPreferencesStore>()(
  persist(
    (set, get) => ({
      ...defaultPreferences,
      
      setViewMode: (mode) => set({ defaultViewMode: mode }),
      setCardDensity: (density) => set({ cardDensity: density }),
      setSortBy: (sortBy) => set({ defaultSortBy: sortBy }),
      setFilterStatus: (status) => set({ defaultFilterStatus: status }),
      
      toggleTemplatesByDefault: () => set((state) => ({ 
        showTemplatesByDefault: !state.showTemplatesByDefault 
      })),
      toggleAnimations: () => set((state) => ({ 
        enableAnimations: !state.enableAnimations 
      })),
      toggleSounds: () => set((state) => ({ 
        enableSounds: !state.enableSounds 
      })),
      
      addFavoriteTemplate: (templateId) => set((state) => ({
        favoriteTemplates: [...new Set([...state.favoriteTemplates, templateId])]
      })),
      removeFavoriteTemplate: (templateId) => set((state) => ({
        favoriteTemplates: state.favoriteTemplates.filter(id => id !== templateId)
      })),
      addRecentTemplate: (templateId) => set((state) => {
        const recent = [templateId, ...state.recentlyUsedTemplates.filter(id => id !== templateId)];
        return { recentlyUsedTemplates: recent.slice(0, 10) }; // Keep only 10 recent
      }),
      
      pinFlow: (flowId) => set((state) => ({
        pinnedFlows: [...new Set([...state.pinnedFlows, flowId])]
      })),
      unpinFlow: (flowId) => set((state) => ({
        pinnedFlows: state.pinnedFlows.filter(id => id !== flowId)
      })),
      
      setVirtualization: (enabled) => set({ enableVirtualization: enabled }),
      setItemsPerPage: (count) => set({ itemsPerPage: count }),
      
      setHighContrast: (enabled) => set({ highContrast: enabled }),
      setReducedMotion: (enabled) => set({ reducedMotion: enabled }),
      setFontSize: (size) => set({ fontSize: size }),
      
      resetToDefaults: () => set(defaultPreferences)
    }),
    {
      name: 'user-preferences',
      version: 1
    }
  )
);