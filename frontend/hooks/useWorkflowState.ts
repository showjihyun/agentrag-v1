import { useReducer, useCallback } from 'react';
import { Node, Edge } from 'reactflow';
import { WorkflowTabValue } from '@/types/workflow';

// State type
export interface WorkflowState {
  nodes: Node[];
  edges: Edge[];
  execution: {
    isExecuting: boolean;
    currentNodeId: string | null;
    completedNodes: string[];
    failedNodes: string[];
    startTime: number | null;
    endTime: number | null;
  };
  ui: {
    activeTab: WorkflowTabValue;
    filteredNodes: Node[];
    selectedNodes: string[];
    isSaving: boolean;
    searchQuery: string;
  };
}

// Action types
export type WorkflowAction =
  | { type: 'SET_NODES'; payload: Node[] }
  | { type: 'SET_EDGES'; payload: Edge[] }
  | { type: 'ADD_NODE'; payload: Node }
  | { type: 'UPDATE_NODE'; payload: { id: string; data: Partial<Node['data']> } }
  | { type: 'REMOVE_NODE'; payload: string }
  | { type: 'ADD_EDGE'; payload: Edge }
  | { type: 'REMOVE_EDGE'; payload: string }
  | { type: 'START_EXECUTION' }
  | { type: 'STOP_EXECUTION' }
  | { type: 'COMPLETE_NODE'; payload: string }
  | { type: 'FAIL_NODE'; payload: { nodeId: string; error: string } }
  | { type: 'SET_CURRENT_NODE'; payload: string | null }
  | { type: 'RESET_EXECUTION' }
  | { type: 'SET_ACTIVE_TAB'; payload: WorkflowTabValue }
  | { type: 'SET_FILTERED_NODES'; payload: Node[] }
  | { type: 'SET_SELECTED_NODES'; payload: string[] }
  | { type: 'SET_SAVING'; payload: boolean }
  | { type: 'SET_SEARCH_QUERY'; payload: string }
  | { type: 'RESET_STATE' };

// Default state
const defaultState: WorkflowState = {
  nodes: [],
  edges: [],
  execution: {
    isExecuting: false,
    currentNodeId: null,
    completedNodes: [],
    failedNodes: [],
    startTime: null,
    endTime: null,
  },
  ui: {
    activeTab: 'canvas',
    filteredNodes: [],
    selectedNodes: [],
    isSaving: false,
    searchQuery: '',
  },
};

// Reducer
function workflowReducer(state: WorkflowState, action: WorkflowAction): WorkflowState {
  switch (action.type) {
    case 'SET_NODES':
      return { ...state, nodes: action.payload };

    case 'SET_EDGES':
      return { ...state, edges: action.payload };

    case 'ADD_NODE':
      return { ...state, nodes: [...state.nodes, action.payload] };

    case 'UPDATE_NODE':
      return {
        ...state,
        nodes: state.nodes.map((node) =>
          node.id === action.payload.id
            ? { ...node, data: { ...node.data, ...action.payload.data } }
            : node
        ),
      };

    case 'REMOVE_NODE':
      return {
        ...state,
        nodes: state.nodes.filter((node) => node.id !== action.payload),
        edges: state.edges.filter(
          (edge) => edge.source !== action.payload && edge.target !== action.payload
        ),
      };

    case 'ADD_EDGE':
      return { ...state, edges: [...state.edges, action.payload] };

    case 'REMOVE_EDGE':
      return {
        ...state,
        edges: state.edges.filter((edge) => edge.id !== action.payload),
      };

    case 'START_EXECUTION':
      return {
        ...state,
        execution: {
          isExecuting: true,
          currentNodeId: null,
          completedNodes: [],
          failedNodes: [],
          startTime: Date.now(),
          endTime: null,
        },
      };

    case 'STOP_EXECUTION':
      return {
        ...state,
        execution: {
          ...state.execution,
          isExecuting: false,
          endTime: Date.now(),
        },
      };

    case 'COMPLETE_NODE':
      return {
        ...state,
        execution: {
          ...state.execution,
          completedNodes: [...state.execution.completedNodes, action.payload],
        },
      };

    case 'FAIL_NODE':
      return {
        ...state,
        execution: {
          ...state.execution,
          failedNodes: [...state.execution.failedNodes, action.payload.nodeId],
        },
      };

    case 'SET_CURRENT_NODE':
      return {
        ...state,
        execution: {
          ...state.execution,
          currentNodeId: action.payload,
        },
      };

    case 'RESET_EXECUTION':
      return {
        ...state,
        execution: {
          isExecuting: false,
          currentNodeId: null,
          completedNodes: [],
          failedNodes: [],
          startTime: null,
          endTime: null,
        },
      };

    case 'SET_ACTIVE_TAB':
      return {
        ...state,
        ui: { ...state.ui, activeTab: action.payload },
      };

    case 'SET_FILTERED_NODES':
      return {
        ...state,
        ui: { ...state.ui, filteredNodes: action.payload },
      };

    case 'SET_SELECTED_NODES':
      return {
        ...state,
        ui: { ...state.ui, selectedNodes: action.payload },
      };

    case 'SET_SAVING':
      return {
        ...state,
        ui: { ...state.ui, isSaving: action.payload },
      };

    case 'SET_SEARCH_QUERY':
      return {
        ...state,
        ui: { ...state.ui, searchQuery: action.payload },
      };

    case 'RESET_STATE':
      return defaultState;

    default:
      return state;
  }
}

/**
 * Unified state management hook for workflow canvas
 */
export function useWorkflowState(initialState?: Partial<WorkflowState>) {
  const [state, dispatch] = useReducer(workflowReducer, {
    ...defaultState,
    ...initialState,
  });

  // Convenience methods
  const actions = {
    setNodes: useCallback((nodes: Node[]) => {
      dispatch({ type: 'SET_NODES', payload: nodes });
    }, []),

    setEdges: useCallback((edges: Edge[]) => {
      dispatch({ type: 'SET_EDGES', payload: edges });
    }, []),

    addNode: useCallback((node: Node) => {
      dispatch({ type: 'ADD_NODE', payload: node });
    }, []),

    updateNode: useCallback((id: string, data: Partial<Node['data']>) => {
      dispatch({ type: 'UPDATE_NODE', payload: { id, data } });
    }, []),

    removeNode: useCallback((id: string) => {
      dispatch({ type: 'REMOVE_NODE', payload: id });
    }, []),

    startExecution: useCallback(() => {
      dispatch({ type: 'START_EXECUTION' });
    }, []),

    stopExecution: useCallback(() => {
      dispatch({ type: 'STOP_EXECUTION' });
    }, []),

    completeNode: useCallback((nodeId: string) => {
      dispatch({ type: 'COMPLETE_NODE', payload: nodeId });
    }, []),

    failNode: useCallback((nodeId: string, error: string) => {
      dispatch({ type: 'FAIL_NODE', payload: { nodeId, error } });
    }, []),

    setCurrentNode: useCallback((nodeId: string | null) => {
      dispatch({ type: 'SET_CURRENT_NODE', payload: nodeId });
    }, []),

    resetExecution: useCallback(() => {
      dispatch({ type: 'RESET_EXECUTION' });
    }, []),

    setActiveTab: useCallback((tab: WorkflowTabValue) => {
      dispatch({ type: 'SET_ACTIVE_TAB', payload: tab });
    }, []),

    setFilteredNodes: useCallback((nodes: Node[]) => {
      dispatch({ type: 'SET_FILTERED_NODES', payload: nodes });
    }, []),

    setSelectedNodes: useCallback((nodeIds: string[]) => {
      dispatch({ type: 'SET_SELECTED_NODES', payload: nodeIds });
    }, []),

    setSaving: useCallback((isSaving: boolean) => {
      dispatch({ type: 'SET_SAVING', payload: isSaving });
    }, []),

    setSearchQuery: useCallback((query: string) => {
      dispatch({ type: 'SET_SEARCH_QUERY', payload: query });
    }, []),

    reset: useCallback(() => {
      dispatch({ type: 'RESET_STATE' });
    }, []),
  };

  return { state, dispatch, actions };
}
