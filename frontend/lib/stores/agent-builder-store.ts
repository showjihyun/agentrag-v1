import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { Agent, Block, Workflow } from '@/lib/api/agent-builder';

interface AgentBuilderState {
  // UI State
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;

  // Selected Resources
  selectedAgent: Agent | null;
  setSelectedAgent: (agent: Agent | null) => void;

  selectedBlock: Block | null;
  setSelectedBlock: (block: Block | null) => void;

  selectedWorkflow: Workflow | null;
  setSelectedWorkflow: (workflow: Workflow | null) => void;

  // Recent Items (persisted)
  recentAgents: Agent[];
  addRecentAgent: (agent: Agent) => void;
  clearRecentAgents: () => void;

  recentBlocks: Block[];
  addRecentBlock: (block: Block) => void;
  clearRecentBlocks: () => void;

  // Favorites (persisted)
  favoriteAgentIds: string[];
  toggleFavoriteAgent: (agentId: string) => void;
  isFavoriteAgent: (agentId: string) => boolean;

  favoriteBlockIds: string[];
  toggleFavoriteBlock: (blockId: string) => void;
  isFavoriteBlock: (blockId: string) => boolean;

  // Preferences (persisted)
  preferences: {
    defaultLLMProvider: string;
    defaultLLMModel: string;
    autoSave: boolean;
    showHints: boolean;
  };
  updatePreferences: (preferences: Partial<AgentBuilderState['preferences']>) => void;

  // Reset
  reset: () => void;
}

const initialState = {
  sidebarOpen: false,
  selectedAgent: null,
  selectedBlock: null,
  selectedWorkflow: null,
  recentAgents: [],
  recentBlocks: [],
  favoriteAgentIds: [],
  favoriteBlockIds: [],
  preferences: {
    defaultLLMProvider: 'ollama',
    defaultLLMModel: 'llama3.1',
    autoSave: true,
    showHints: true,
  },
};

export const useAgentBuilderStore = create<AgentBuilderState>()(
  persist(
    (set, get) => ({
      ...initialState,

      // UI State
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      // Selected Resources
      setSelectedAgent: (agent) => set({ selectedAgent: agent }),
      setSelectedBlock: (block) => set({ selectedBlock: block }),
      setSelectedWorkflow: (workflow) => set({ selectedWorkflow: workflow }),

      // Recent Agents
      addRecentAgent: (agent) =>
        set((state) => {
          const filtered = state.recentAgents.filter((a) => a.id !== agent.id);
          return {
            recentAgents: [agent, ...filtered].slice(0, 10), // Keep last 10
          };
        }),
      clearRecentAgents: () => set({ recentAgents: [] }),

      // Recent Blocks
      addRecentBlock: (block) =>
        set((state) => {
          const filtered = state.recentBlocks.filter((b) => b.id !== block.id);
          return {
            recentBlocks: [block, ...filtered].slice(0, 10), // Keep last 10
          };
        }),
      clearRecentBlocks: () => set({ recentBlocks: [] }),

      // Favorite Agents
      toggleFavoriteAgent: (agentId) =>
        set((state) => {
          const isFavorite = state.favoriteAgentIds.includes(agentId);
          return {
            favoriteAgentIds: isFavorite
              ? state.favoriteAgentIds.filter((id) => id !== agentId)
              : [...state.favoriteAgentIds, agentId],
          };
        }),
      isFavoriteAgent: (agentId) => get().favoriteAgentIds.includes(agentId),

      // Favorite Blocks
      toggleFavoriteBlock: (blockId) =>
        set((state) => {
          const isFavorite = state.favoriteBlockIds.includes(blockId);
          return {
            favoriteBlockIds: isFavorite
              ? state.favoriteBlockIds.filter((id) => id !== blockId)
              : [...state.favoriteBlockIds, blockId],
          };
        }),
      isFavoriteBlock: (blockId) => get().favoriteBlockIds.includes(blockId),

      // Preferences
      updatePreferences: (preferences) =>
        set((state) => ({
          preferences: { ...state.preferences, ...preferences },
        })),

      // Reset
      reset: () => set(initialState),
    }),
    {
      name: 'agent-builder-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Only persist these fields
        recentAgents: state.recentAgents,
        recentBlocks: state.recentBlocks,
        favoriteAgentIds: state.favoriteAgentIds,
        favoriteBlockIds: state.favoriteBlockIds,
        preferences: state.preferences,
      }),
    }
  )
);

// Selectors for better performance
export const useAgentBuilderSelectors = () => {
  const store = useAgentBuilderStore();

  return {
    // UI
    sidebarOpen: store.sidebarOpen,
    setSidebarOpen: store.setSidebarOpen,
    toggleSidebar: store.toggleSidebar,

    // Recent
    recentAgents: store.recentAgents,
    recentBlocks: store.recentBlocks,

    // Favorites
    favoriteAgentIds: store.favoriteAgentIds,
    favoriteBlockIds: store.favoriteBlockIds,
    isFavoriteAgent: store.isFavoriteAgent,
    isFavoriteBlock: store.isFavoriteBlock,

    // Preferences
    preferences: store.preferences,
  };
};
