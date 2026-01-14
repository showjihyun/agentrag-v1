/**
 * Zustand Store for Agent Plugin
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface AgentPlugin {
  agent_id: string;
  agent_name: string;
  agent_type: string;
  description: string;
  status: 'active' | 'inactive' | 'error';
  version: string;
  created_at: string;
  last_used: string;
  execution_count: number;
  success_rate: number;
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'error';
  active_plugins: number;
  total_executions: number;
  average_response_time: number;
  error_rate: number;
}

export interface PluginExecutionResult {
  success: boolean;
  result?: any;
  error?: string;
  duration?: number;
  timestamp: string;
}

interface PluginState {
  // Data
  plugins: AgentPlugin[];
  customAgents: AgentPlugin[];
  systemHealth: SystemHealth | null;
  executionHistory: Record<string, PluginExecutionResult[]>;
  
  // UI State
  loading: boolean;
  searchTerm: string;
  filterStatus: string;
  selectedPlugin: string | null;
  isInstallDialogOpen: boolean;
  
  // Error State
  error: string | null;
  
  // Actions
  setPlugins: (plugins: AgentPlugin[]) => void;
  setCustomAgents: (agents: AgentPlugin[]) => void;
  setSystemHealth: (health: SystemHealth) => void;
  setLoading: (loading: boolean) => void;
  setSearchTerm: (term: string) => void;
  setFilterStatus: (status: string) => void;
  setSelectedPlugin: (pluginId: string | null) => void;
  setInstallDialogOpen: (open: boolean) => void;
  setError: (error: string | null) => void;
  
  // Business Logic
  addExecutionResult: (pluginId: string, result: PluginExecutionResult) => void;
  updatePluginStatus: (pluginId: string, status: AgentPlugin['status']) => void;
  getFilteredPlugins: () => AgentPlugin[];
  getFilteredCustomAgents: () => AgentPlugin[];
  getPluginById: (pluginId: string) => AgentPlugin | undefined;
  
  // API Actions
  loadPlugins: () => Promise<void>;
  loadCustomAgents: () => Promise<void>;
  loadSystemHealth: () => Promise<void>;
  registerAsPlugin: (agentId: string) => Promise<void>;
  unregisterPlugin: (agentId: string) => Promise<void>;
  refreshPlugin: (agentId: string) => Promise<void>;
  executePlugin: (pluginId: string, input: any) => Promise<PluginExecutionResult>;
}

export const usePluginStore = create<PluginState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial State
        plugins: [],
        customAgents: [],
        systemHealth: null,
        executionHistory: {},
        loading: false,
        searchTerm: '',
        filterStatus: 'all',
        selectedPlugin: null,
        isInstallDialogOpen: false,
        error: null,

        // Basic Actions
        setPlugins: (plugins) => set({ plugins }),
        setCustomAgents: (customAgents) => set({ customAgents }),
        setSystemHealth: (systemHealth) => set({ systemHealth }),
        setLoading: (loading) => set({ loading }),
        setSearchTerm: (searchTerm) => set({ searchTerm }),
        setFilterStatus: (filterStatus) => set({ filterStatus }),
        setSelectedPlugin: (selectedPlugin) => set({ selectedPlugin }),
        setInstallDialogOpen: (isInstallDialogOpen) => set({ isInstallDialogOpen }),
        setError: (error) => set({ error }),

        // Business Logic
        addExecutionResult: (pluginId, result) => {
          const { executionHistory } = get();
          const history = executionHistory[pluginId] || [];
          const updatedHistory = [...history, result].slice(-50); // Keep only recent 50 entries
          
          set({
            executionHistory: {
              ...executionHistory,
              [pluginId]: updatedHistory
            }
          });
        },

        updatePluginStatus: (pluginId, status) => {
          const { plugins, customAgents } = get();
          
          const updatedPlugins = plugins.map(plugin =>
            plugin.agent_id === pluginId ? { ...plugin, status } : plugin
          );
          
          const updatedCustomAgents = customAgents.map(agent =>
            agent.agent_id === pluginId ? { ...agent, status } : agent
          );
          
          set({ plugins: updatedPlugins, customAgents: updatedCustomAgents });
        },

        getFilteredPlugins: () => {
          const { plugins, searchTerm, filterStatus } = get();
          return plugins.filter(plugin => {
            const matchesSearch = plugin.agent_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                 plugin.description.toLowerCase().includes(searchTerm.toLowerCase());
            const matchesFilter = filterStatus === 'all' || plugin.status === filterStatus;
            return matchesSearch && matchesFilter;
          });
        },

        getFilteredCustomAgents: () => {
          const { customAgents, searchTerm, filterStatus } = get();
          return customAgents.filter(agent => {
            const matchesSearch = agent.agent_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                                 agent.description.toLowerCase().includes(searchTerm.toLowerCase());
            const matchesFilter = filterStatus === 'all' || agent.status === filterStatus;
            return matchesSearch && matchesFilter;
          });
        },

        getPluginById: (pluginId) => {
          const { plugins, customAgents } = get();
          return [...plugins, ...customAgents].find(p => p.agent_id === pluginId);
        },

        // API Actions
        loadPlugins: async () => {
          try {
            set({ loading: true, error: null });
            const response = await fetch('/api/v1/agent-plugins/agents');
            if (!response.ok) throw new Error('Failed to load plugins');
            
            const data = await response.json();
            set({ plugins: data.agents || [] });
          } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Unknown error' });
          } finally {
            set({ loading: false });
          }
        },

        loadCustomAgents: async () => {
          try {
            set({ loading: true, error: null });
            const response = await fetch('/api/v1/agent-plugins/custom-agents');
            if (!response.ok) throw new Error('Failed to load custom agents');
            
            const data = await response.json();
            set({ customAgents: data.custom_agents || [] });
          } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Unknown error' });
          } finally {
            set({ loading: false });
          }
        },

        loadSystemHealth: async () => {
          try {
            const response = await fetch('/api/v1/agent-plugins/system/health');
            if (!response.ok) throw new Error('Failed to load system health');
            
            const data = await response.json();
            set({ systemHealth: data });
          } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Unknown error' });
          }
        },

        registerAsPlugin: async (agentId) => {
          try {
            set({ loading: true, error: null });
            const response = await fetch(`/api/v1/agent-plugins/custom-agents/${agentId}/register`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({}),
            });

            if (!response.ok) throw new Error('Failed to register plugin');
            
            // Update state
            get().updatePluginStatus(agentId, 'active');
            
            // Refresh list
            await get().loadCustomAgents();
          } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Unknown error' });
            throw error;
          } finally {
            set({ loading: false });
          }
        },

        unregisterPlugin: async (agentId) => {
          try {
            set({ loading: true, error: null });
            const response = await fetch(`/api/v1/agent-plugins/custom-agents/${agentId}/unregister`, {
              method: 'DELETE',
            });

            if (!response.ok) throw new Error('Failed to unregister plugin');
            
            // Update state
            get().updatePluginStatus(agentId, 'inactive');
            
            // Refresh list
            await get().loadCustomAgents();
          } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Unknown error' });
            throw error;
          } finally {
            set({ loading: false });
          }
        },

        refreshPlugin: async (agentId) => {
          try {
            set({ loading: true, error: null });
            const response = await fetch(`/api/v1/agent-plugins/custom-agents/${agentId}/refresh`, {
              method: 'POST',
            });

            if (!response.ok) throw new Error('Failed to refresh plugin');
            
            // Refresh list
            await get().loadCustomAgents();
          } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Unknown error' });
            throw error;
          } finally {
            set({ loading: false });
          }
        },

        executePlugin: async (pluginId, input) => {
          const startTime = Date.now();
          
          try {
            const response = await fetch('/api/v1/agent-plugins/execute', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                agent_type: pluginId,
                input_data: input,
              }),
            });

            const duration = Date.now() - startTime;
            
            if (!response.ok) {
              const errorData = await response.json();
              const result: PluginExecutionResult = {
                success: false,
                error: errorData.detail || 'Execution failed',
                duration,
                timestamp: new Date().toISOString(),
              };
              
              get().addExecutionResult(pluginId, result);
              return result;
            }

            const data = await response.json();
            const result: PluginExecutionResult = {
              success: true,
              result: data,
              duration,
              timestamp: new Date().toISOString(),
            };
            
            get().addExecutionResult(pluginId, result);
            return result;
            
          } catch (error) {
            const duration = Date.now() - startTime;
            const result: PluginExecutionResult = {
              success: false,
              error: error instanceof Error ? error.message : 'Unknown error',
              duration,
              timestamp: new Date().toISOString(),
            };
            
            get().addExecutionResult(pluginId, result);
            return result;
          }
        },
      }),
      {
        name: 'plugin-store',
        partialize: (state) => ({
          // Select only persistent state
          searchTerm: state.searchTerm,
          filterStatus: state.filterStatus,
          executionHistory: state.executionHistory,
        }),
      }
    ),
    { name: 'plugin-store' }
  )
);