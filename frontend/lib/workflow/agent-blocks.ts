/**
 * Agent Block Definitions for Workflow Platform
 * 
 * Integrates Agent Plugin system into workflow blocks
 */

import { BlockDefinition, BlockCategory } from '@/lib/types/workflow';
import { Bot, Network, Search, FileText, Zap, UserCheck } from 'lucide-react';

// Agent Execution Block Definition
export const agentExecutionBlock: BlockDefinition = {
  id: 'agent_execution',
  name: 'Agent Execution',
  description: 'Execute a single AI Agent to perform specific tasks',
  category: BlockCategory.AI_AGENTS,
  icon: Bot,
  version: '1.0.0',
  
  inputs: [
    {
      id: 'agent_type',
      name: 'Agent Type',
      type: 'select',
      required: true,
      options: [
        { value: 'vector_search', label: 'Vector Search Agent', description: 'Perform semantic search' },
        { value: 'web_search', label: 'Web Search Agent', description: 'Perform web search' },
        { value: 'local_data', label: 'Local Data Agent', description: 'Process local files' },
        { value: 'aggregator', label: 'Aggregator Agent', description: 'Coordinate multiple agents' }
      ],
      defaultValue: 'vector_search'
    },
    {
      id: 'input_data',
      name: 'Input Data',
      type: 'json',
      required: true,
      placeholder: '{"query": "search content"}',
      description: 'Input data to pass to the agent (JSON format)'
    },
    {
      id: 'session_id',
      name: 'Session ID',
      type: 'string',
      required: false,
      description: 'ID for session tracking (optional)'
    }
  ],
  
  outputs: [
    {
      id: 'result',
      name: 'Execution Result',
      type: 'json',
      description: 'Agent execution result'
    },
    {
      id: 'success',
      name: 'Success Status',
      type: 'boolean',
      description: 'Execution success status'
    },
    {
      id: 'agent_type',
      name: 'Agent Type',
      type: 'string',
      description: 'Executed agent type'
    },
    {
      id: 'execution_time',
      name: 'Execution Time',
      type: 'number',
      description: 'Execution time in seconds'
    }
  ],
  
  settings: {
    timeout: {
      name: 'Timeout',
      type: 'number',
      defaultValue: 30,
      min: 5,
      max: 300,
      description: 'Execution timeout in seconds'
    },
    retry_count: {
      name: 'Retry Count',
      type: 'number',
      defaultValue: 1,
      min: 0,
      max: 5,
      description: 'Number of retries on failure'
    }
  },
  
  validation: {
    required: ['agent_type', 'input_data'],
    custom: (data) => {
      const errors: string[] = [];
      
      // JSON format validation
      if (data.input_data) {
        try {
          JSON.parse(data.input_data);
        } catch {
          errors.push('Input data must be in valid JSON format');
        }
      }
      
      return errors;
    }
  },
  
  examples: [
    {
      name: 'Document Search',
      description: 'Document search using Vector Search Agent',
      config: {
        agent_type: 'vector_search',
        input_data: '{"query": "AI technology trends", "limit": 5}'
      }
    },
    {
      name: 'Web Search',
      description: 'Web search using Web Search Agent',
      config: {
        agent_type: 'web_search',
        input_data: '{"query": "latest AI news", "max_results": 10}'
      }
    }
  ]
};

// Agent Orchestration Block Definition
export const agentOrchestrationBlock: BlockDefinition = {
  id: 'agent_orchestration',
  name: 'Agent Orchestration',
  description: 'Coordinate multiple AI Agents to perform complex tasks',
  category: BlockCategory.AI_AGENTS,
  icon: Network,
  version: '1.0.0',
  
  inputs: [
    {
      id: 'pattern',
      name: 'Orchestration Pattern',
      type: 'select',
      required: true,
      options: [
        { value: 'sequential', label: 'Sequential', description: 'Execute agents in sequence' },
        { value: 'parallel', label: 'Parallel', description: 'Execute all agents simultaneously' },
        { value: 'consensus', label: 'Consensus', description: 'Voting and consensus between agents' },
        { value: 'swarm', label: 'Swarm Intelligence', description: 'Optimization using swarm intelligence' },
        { value: 'dynamic_routing', label: 'Dynamic Routing', description: 'Performance-based agent selection' }
      ],
      defaultValue: 'sequential'
    },
    {
      id: 'agents',
      name: 'Participating Agents',
      type: 'multi-select',
      required: true,
      options: [
        { value: 'vector_search', label: 'Vector Search' },
        { value: 'web_search', label: 'Web Search' },
        { value: 'local_data', label: 'Local Data' }
      ],
      description: 'List of agents to participate in orchestration'
    },
    {
      id: 'task',
      name: 'Task Definition',
      type: 'json',
      required: true,
      placeholder: '{"objective": "task objective", "requirements": ["requirement1"]}',
      description: 'Definition of the task to perform (JSON format)'
    },
    {
      id: 'session_id',
      name: 'Session ID',
      type: 'string',
      required: false,
      description: 'ID for session tracking (optional)'
    }
  ],
  
  outputs: [
    {
      id: 'orchestration_result',
      name: 'Orchestration Result',
      type: 'json',
      description: 'Complete orchestration result'
    },
    {
      id: 'agent_results',
      name: 'Individual Agent Results',
      type: 'array',
      description: 'Individual execution results from each agent'
    },
    {
      id: 'pattern',
      name: 'Used Pattern',
      type: 'string',
      description: 'Actually used orchestration pattern'
    },
    {
      id: 'execution_summary',
      name: 'Execution Summary',
      type: 'json',
      description: 'Execution statistics and summary information'
    }
  ],
  
  settings: {
    timeout: {
      name: 'Timeout',
      type: 'number',
      defaultValue: 120,
      min: 30,
      max: 600,
      description: 'Orchestration timeout in seconds'
    },
    consensus_threshold: {
      name: 'Consensus Threshold',
      type: 'number',
      defaultValue: 0.7,
      min: 0.5,
      max: 1.0,
      step: 0.1,
      description: 'Threshold to use in consensus pattern',
      condition: { field: 'pattern', value: 'consensus' }
    },
    max_iterations: {
      name: 'Max Iterations',
      type: 'number',
      defaultValue: 5,
      min: 1,
      max: 20,
      description: 'Maximum iterations for swarm intelligence pattern',
      condition: { field: 'pattern', value: 'swarm' }
    }
  },
  
  validation: {
    required: ['pattern', 'agents', 'task'],
    custom: (data) => {
      const errors: string[] = [];
      
      // Minimum agent count validation
      if (!data.agents || data.agents.length < 1) {
        errors.push('At least 1 agent must be selected');
      }
      
      // Pattern-specific agent count validation
      if (data.pattern === 'consensus' && data.agents && data.agents.length < 2) {
        errors.push('Consensus pattern requires at least 2 agents');
      }
      
      // JSON format validation
      if (data.task) {
        try {
          JSON.parse(data.task);
        } catch {
          errors.push('Task definition must be in valid JSON format');
        }
      }
      
      return errors;
    }
  },
  
  examples: [
    {
      name: 'Sequential Search and Analysis',
      description: 'Sequential workflow that complements document search with web search',
      config: {
        pattern: 'sequential',
        agents: ['vector_search', 'web_search'],
        task: '{"objective": "AI technology trend analysis", "query": "GPT-4 performance improvements"}'
      }
    },
    {
      name: 'Parallel Information Gathering',
      description: 'Collect information simultaneously from multiple sources',
      config: {
        pattern: 'parallel',
        agents: ['vector_search', 'web_search', 'local_data'],
        task: '{"objective": "comprehensive information gathering", "topic": "latest machine learning trends"}'
      }
    }
  ]
};

// Vector Search Dedicated Block
export const vectorSearchBlock: BlockDefinition = {
  id: 'vector_search',
  name: 'Vector Search',
  description: 'Find related documents through semantic search',
  category: BlockCategory.AI_AGENTS,
  icon: Search,
  version: '1.0.0',
  
  inputs: [
    {
      id: 'query',
      name: 'Search Query',
      type: 'string',
      required: true,
      description: 'Content to search for'
    },
    {
      id: 'limit',
      name: 'Result Count',
      type: 'number',
      defaultValue: 10,
      min: 1,
      max: 100,
      description: 'Number of results to return'
    },
    {
      id: 'similarity_threshold',
      name: 'Similarity Threshold',
      type: 'number',
      defaultValue: 0.7,
      min: 0.0,
      max: 1.0,
      step: 0.1,
      description: 'Minimum similarity threshold'
    }
  ],
  
  outputs: [
    {
      id: 'results',
      name: 'Search Results',
      type: 'array',
      description: 'List of found documents'
    },
    {
      id: 'total_count',
      name: 'Total Count',
      type: 'number',
      description: 'Total number of documents found'
    }
  ]
};

// Web Search Dedicated Block
export const webSearchBlock: BlockDefinition = {
  id: 'web_search',
  name: 'Web Search',
  description: 'Search for latest information on the web',
  category: BlockCategory.AI_AGENTS,
  icon: Zap,
  version: '1.0.0',
  
  inputs: [
    {
      id: 'query',
      name: 'Search Query',
      type: 'string',
      required: true,
      description: 'Content to search for on the web'
    },
    {
      id: 'max_results',
      name: 'Max Results',
      type: 'number',
      defaultValue: 10,
      min: 1,
      max: 50,
      description: 'Maximum number of results to return'
    },
    {
      id: 'time_range',
      name: 'Time Range',
      type: 'select',
      options: [
        { value: '', label: 'All' },
        { value: 'd', label: 'Last 1 day' },
        { value: 'w', label: 'Last 1 week' },
        { value: 'm', label: 'Last 1 month' },
        { value: 'y', label: 'Last 1 year' }
      ],
      defaultValue: '',
      description: 'Search time range'
    }
  ],
  
  outputs: [
    {
      id: 'results',
      name: 'Search Results',
      type: 'array',
      description: 'Web search results list'
    },
    {
      id: 'total_results',
      name: 'Total Results',
      type: 'number',
      description: 'Total number of search results'
    }
  ]
};

// Local Data Dedicated Block
export const localDataBlock: BlockDefinition = {
  id: 'local_data',
  name: 'Local Data',
  description: 'Read and process local files',
  category: BlockCategory.AI_AGENTS,
  icon: FileText,
  version: '1.0.0',
  
  inputs: [
    {
      id: 'file_path',
      name: 'File Path',
      type: 'string',
      required: true,
      description: 'Path of the file to process'
    },
    {
      id: 'extract_text',
      name: 'Extract Text',
      type: 'boolean',
      defaultValue: true,
      description: 'Whether to extract text from the file'
    },
    {
      id: 'extract_metadata',
      name: 'Extract Metadata',
      type: 'boolean',
      defaultValue: true,
      description: 'Whether to extract file metadata'
    }
  ],
  
  outputs: [
    {
      id: 'content',
      name: 'File Content',
      type: 'string',
      description: 'Extracted text content'
    },
    {
      id: 'metadata',
      name: 'Metadata',
      type: 'json',
      description: 'File metadata'
    }
  ]
};

// Custom Agent Execution Block
export const customAgentExecutionBlock: BlockDefinition = {
  id: 'custom_agent_execution',
  name: 'Custom Agent Execution',
  description: 'Execute user-created Custom Agents',
  category: BlockCategory.AI_AGENTS,
  icon: UserCheck,
  version: '1.0.0',
  
  inputs: [
    {
      id: 'agent_id',
      name: 'Custom Agent',
      type: 'select',
      required: true,
      dynamic_options: true,
      options_endpoint: '/api/v1/agent-plugins/custom-agents',
      option_value_field: 'agent_id',
      option_label_field: 'agent_name',
      description: 'Select Custom Agent to execute'
    },
    {
      id: 'input_data',
      name: 'Input Data',
      type: 'json',
      required: true,
      placeholder: '{"input": "user input", "context": {}}',
      description: 'Input data to pass to Custom Agent (JSON format)'
    },
    {
      id: 'session_id',
      name: 'Session ID',
      type: 'string',
      required: false,
      description: 'ID for session tracking (optional)'
    }
  ],
  
  outputs: [
    {
      id: 'response',
      name: 'Agent Response',
      type: 'string',
      description: 'Response from Custom Agent'
    },
    {
      id: 'success',
      name: 'Success Status',
      type: 'boolean',
      description: 'Execution success status'
    },
    {
      id: 'agent_name',
      name: 'Agent Name',
      type: 'string',
      description: 'Name of executed agent'
    },
    {
      id: 'tool_results',
      name: 'Tool Execution Results',
      type: 'array',
      description: 'Execution results of tools used by the agent'
    },
    {
      id: 'kb_results',
      name: 'Knowledge Base Search Results',
      type: 'array',
      description: 'Knowledge base search results'
    },
    {
      id: 'execution_metadata',
      name: 'Execution Metadata',
      type: 'json',
      description: 'Execution-related metadata'
    }
  ],
  
  settings: {
    timeout: {
      name: 'Timeout',
      type: 'number',
      defaultValue: 60,
      min: 10,
      max: 300,
      description: 'Execution timeout in seconds'
    },
    retry_count: {
      name: 'Retry Count',
      type: 'number',
      defaultValue: 1,
      min: 0,
      max: 3,
      description: 'Number of retries on failure'
    },
    enable_tools: {
      name: 'Enable Tools',
      type: 'boolean',
      defaultValue: true,
      description: 'Whether to allow agent to use tools'
    },
    enable_knowledgebase: {
      name: 'Enable Knowledge Base',
      type: 'boolean',
      defaultValue: true,
      description: 'Whether to allow agent to use knowledge base'
    }
  },
  
  validation: {
    required: ['agent_id', 'input_data'],
    custom: (data) => {
      const errors: string[] = [];
      
      // JSON format validation
      if (data.input_data) {
        try {
          JSON.parse(data.input_data);
        } catch {
          errors.push('Input data must be in valid JSON format');
        }
      }
      
      return errors;
    }
  },
  
  examples: [
    {
      name: 'Customer Support Agent',
      description: 'Handle inquiries using Custom customer support agent',
      config: {
        agent_id: 'custom_agent_123',
        input_data: '{"input": "Please tell me how to use the product", "customer_id": "12345"}'
      }
    },
    {
      name: 'Data Analysis Agent',
      description: 'Generate reports using Custom data analysis agent',
      config: {
        agent_id: 'custom_agent_456',
        input_data: '{"input": "Please analyze last month\'s sales", "period": "2024-12"}'
      }
    }
  ]
};

// Export all Agent block definitions
export const agentBlocks: BlockDefinition[] = [
  agentExecutionBlock,
  agentOrchestrationBlock,
  customAgentExecutionBlock,  // Add Custom Agent block
  vectorSearchBlock,
  webSearchBlock,
  localDataBlock
];

// Agent block category definition
export const agentBlockCategory: BlockCategory = {
  id: 'ai_agents',
  name: 'AI Agents',
  description: 'AI Agent execution and orchestration blocks',
  icon: Bot,
  color: '#3B82F6',
  blocks: agentBlocks
};