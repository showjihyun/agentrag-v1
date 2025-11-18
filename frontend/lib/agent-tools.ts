/**
 * Agent Tools System
 * 
 * Defines tools that AI Agents can use to accomplish tasks.
 * Inspired by n8n's AI Agent tools architecture.
 */

export type ToolCategory = 'search' | 'data' | 'code' | 'api' | 'custom' | 'workflow';

export interface ToolParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  required: boolean;
  description: string;
  default?: any;
  enum?: string[];
  placeholder?: string;
}

export interface AgentToolIntegration {
  inputFormat: string;
  outputFormat: string;
  examples: string[];
  usageInstructions: string;
}

export interface AgentTool {
  id: string;
  name: string;
  description: string;
  category: ToolCategory;
  icon: string;
  version: string;
  
  // Configuration
  parameters: ToolParameter[];
  
  // Agent Integration
  agentIntegration: AgentToolIntegration;
  
  // Metadata
  isBuiltin: boolean;
  requiresAuth: boolean;
  tags: string[];
}

/**
 * Built-in Agent Tools
 */
export const BUILTIN_AGENT_TOOLS: AgentTool[] = [
  {
    id: 'calculator',
    name: 'Calculator',
    description: 'Perform mathematical calculations and evaluate expressions',
    category: 'data',
    icon: 'Calculator',
    version: '1.0.0',
    parameters: [
      {
        name: 'expression',
        type: 'string',
        required: true,
        description: 'Mathematical expression to evaluate',
        placeholder: '2 + 2 * 3'
      }
    ],
    agentIntegration: {
      inputFormat: '{ expression: string }',
      outputFormat: '{ result: number, expression: string }',
      examples: [
        'Calculate: 2 + 2',
        'Evaluate: sqrt(16) + 10',
        'Compute: (100 - 25) * 0.15'
      ],
      usageInstructions: 'Use this tool when you need to perform mathematical calculations. Provide the expression as a string.'
    },
    isBuiltin: true,
    requiresAuth: false,
    tags: ['math', 'calculation', 'numbers']
  },
  {
    id: 'code_executor',
    name: 'Code Executor',
    description: 'Execute Python or JavaScript code in a secure sandbox',
    category: 'code',
    icon: 'Code',
    version: '1.0.0',
    parameters: [
      {
        name: 'code',
        type: 'string',
        required: true,
        description: 'Code to execute',
        placeholder: 'print("Hello, World!")'
      },
      {
        name: 'language',
        type: 'string',
        required: true,
        description: 'Programming language',
        enum: ['python', 'javascript'],
        default: 'python'
      },
      {
        name: 'timeout',
        type: 'number',
        required: false,
        description: 'Execution timeout in seconds',
        default: 30
      }
    ],
    agentIntegration: {
      inputFormat: '{ code: string, language: "python" | "javascript", timeout?: number }',
      outputFormat: '{ result: any, stdout: string, stderr: string, executionTime: number }',
      examples: [
        'Execute Python: print("Hello")',
        'Run JavaScript: console.log("World")',
        'Calculate with Python: sum([1, 2, 3, 4, 5])'
      ],
      usageInstructions: 'Use this tool to execute code snippets. The code runs in a secure sandbox with limited permissions.'
    },
    isBuiltin: true,
    requiresAuth: false,
    tags: ['code', 'python', 'javascript', 'execution']
  },
  {
    id: 'http_request',
    name: 'HTTP Request',
    description: 'Make HTTP requests to external APIs and services',
    category: 'api',
    icon: 'Globe',
    version: '1.0.0',
    parameters: [
      {
        name: 'url',
        type: 'string',
        required: true,
        description: 'URL to request',
        placeholder: 'https://api.example.com/data'
      },
      {
        name: 'method',
        type: 'string',
        required: true,
        description: 'HTTP method',
        enum: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
        default: 'GET'
      },
      {
        name: 'headers',
        type: 'object',
        required: false,
        description: 'Request headers',
        placeholder: '{ "Content-Type": "application/json" }'
      },
      {
        name: 'body',
        type: 'object',
        required: false,
        description: 'Request body (for POST/PUT/PATCH)',
        placeholder: '{ "key": "value" }'
      }
    ],
    agentIntegration: {
      inputFormat: '{ url: string, method: string, headers?: object, body?: object }',
      outputFormat: '{ status: number, data: any, headers: object }',
      examples: [
        'GET request: https://api.github.com/users/octocat',
        'POST data to API',
        'Fetch weather data from external service'
      ],
      usageInstructions: 'Use this tool to interact with external APIs. Supports all standard HTTP methods.'
    },
    isBuiltin: true,
    requiresAuth: false,
    tags: ['http', 'api', 'request', 'fetch']
  },
  {
    id: 'vector_search',
    name: 'Vector Search',
    description: 'Search in vector database using semantic similarity',
    category: 'search',
    icon: 'Search',
    version: '1.0.0',
    parameters: [
      {
        name: 'query',
        type: 'string',
        required: true,
        description: 'Search query',
        placeholder: 'machine learning algorithms'
      },
      {
        name: 'knowledgebase_id',
        type: 'string',
        required: true,
        description: 'Knowledgebase ID to search in',
        placeholder: 'kb-123'
      },
      {
        name: 'top_k',
        type: 'number',
        required: false,
        description: 'Number of results to return',
        default: 5
      },
      {
        name: 'min_score',
        type: 'number',
        required: false,
        description: 'Minimum similarity score (0-1)',
        default: 0.7
      }
    ],
    agentIntegration: {
      inputFormat: '{ query: string, knowledgebase_id: string, top_k?: number, min_score?: number }',
      outputFormat: '{ results: Array<{ text: string, score: number, metadata: object }> }',
      examples: [
        'Search for "machine learning" in kb-123',
        'Find similar documents about "neural networks"',
        'Retrieve top 10 relevant chunks'
      ],
      usageInstructions: 'Use this tool to search for relevant information in a knowledgebase using semantic similarity.'
    },
    isBuiltin: true,
    requiresAuth: false,
    tags: ['search', 'vector', 'semantic', 'rag']
  },
  {
    id: 'workflow_call',
    name: 'Call Workflow',
    description: 'Execute another workflow and get its results',
    category: 'workflow',
    icon: 'Workflow',
    version: '1.0.0',
    parameters: [
      {
        name: 'workflow_id',
        type: 'string',
        required: true,
        description: 'Workflow ID to execute',
        placeholder: 'wf-456'
      },
      {
        name: 'input',
        type: 'object',
        required: false,
        description: 'Input data for the workflow',
        placeholder: '{ "query": "test" }'
      },
      {
        name: 'wait_for_completion',
        type: 'boolean',
        required: false,
        description: 'Wait for workflow to complete',
        default: true
      }
    ],
    agentIntegration: {
      inputFormat: '{ workflow_id: string, input?: object, wait_for_completion?: boolean }',
      outputFormat: '{ output: any, status: string, execution_id: string }',
      examples: [
        'Execute workflow wf-456 with input',
        'Call data processing workflow',
        'Trigger notification workflow'
      ],
      usageInstructions: 'Use this tool to execute other workflows. Useful for modular task decomposition.'
    },
    isBuiltin: true,
    requiresAuth: false,
    tags: ['workflow', 'orchestration', 'automation']
  },
  {
    id: 'web_search',
    name: 'Web Search',
    description: 'Search the web using DuckDuckGo',
    category: 'search',
    icon: 'Globe',
    version: '1.0.0',
    parameters: [
      {
        name: 'query',
        type: 'string',
        required: true,
        description: 'Search query',
        placeholder: 'latest AI news'
      },
      {
        name: 'max_results',
        type: 'number',
        required: false,
        description: 'Maximum number of results',
        default: 5
      }
    ],
    agentIntegration: {
      inputFormat: '{ query: string, max_results?: number }',
      outputFormat: '{ results: Array<{ title: string, url: string, snippet: string }> }',
      examples: [
        'Search for "latest AI developments"',
        'Find information about "Python best practices"',
        'Look up "weather in Seoul"'
      ],
      usageInstructions: 'Use this tool to search the web for current information. No API key required.'
    },
    isBuiltin: true,
    requiresAuth: false,
    tags: ['search', 'web', 'internet', 'duckduckgo']
  },
  {
    id: 'json_parser',
    name: 'JSON Parser',
    description: 'Parse and manipulate JSON data',
    category: 'data',
    icon: 'FileJson',
    version: '1.0.0',
    parameters: [
      {
        name: 'json_string',
        type: 'string',
        required: true,
        description: 'JSON string to parse',
        placeholder: '{"key": "value"}'
      },
      {
        name: 'path',
        type: 'string',
        required: false,
        description: 'JSONPath expression to extract data',
        placeholder: '$.data.items[0]'
      }
    ],
    agentIntegration: {
      inputFormat: '{ json_string: string, path?: string }',
      outputFormat: '{ parsed: any, extracted?: any }',
      examples: [
        'Parse JSON response',
        'Extract specific field from JSON',
        'Validate JSON structure'
      ],
      usageInstructions: 'Use this tool to parse JSON strings and extract specific data using JSONPath.'
    },
    isBuiltin: true,
    requiresAuth: false,
    tags: ['json', 'parse', 'data', 'transform']
  },
  {
    id: 'text_splitter',
    name: 'Text Splitter',
    description: 'Split text into chunks for processing',
    category: 'data',
    icon: 'Split',
    version: '1.0.0',
    parameters: [
      {
        name: 'text',
        type: 'string',
        required: true,
        description: 'Text to split',
        placeholder: 'Long text content...'
      },
      {
        name: 'chunk_size',
        type: 'number',
        required: false,
        description: 'Size of each chunk',
        default: 500
      },
      {
        name: 'chunk_overlap',
        type: 'number',
        required: false,
        description: 'Overlap between chunks',
        default: 50
      }
    ],
    agentIntegration: {
      inputFormat: '{ text: string, chunk_size?: number, chunk_overlap?: number }',
      outputFormat: '{ chunks: string[], total_chunks: number }',
      examples: [
        'Split long document into chunks',
        'Prepare text for embedding',
        'Break down large content'
      ],
      usageInstructions: 'Use this tool to split large texts into manageable chunks for processing.'
    },
    isBuiltin: true,
    requiresAuth: false,
    tags: ['text', 'split', 'chunk', 'processing']
  }
];

/**
 * Get tool by ID
 */
export function getToolById(toolId: string): AgentTool | undefined {
  return BUILTIN_AGENT_TOOLS.find(tool => tool.id === toolId);
}

/**
 * Get tools by category
 */
export function getToolsByCategory(category: ToolCategory): AgentTool[] {
  return BUILTIN_AGENT_TOOLS.filter(tool => tool.category === category);
}

/**
 * Search tools
 */
export function searchTools(query: string): AgentTool[] {
  const lowerQuery = query.toLowerCase();
  return BUILTIN_AGENT_TOOLS.filter(tool =>
    tool.name.toLowerCase().includes(lowerQuery) ||
    tool.description.toLowerCase().includes(lowerQuery) ||
    tool.tags.some(tag => tag.includes(lowerQuery))
  );
}

/**
 * Get all categories
 */
export function getAllCategories(): { category: ToolCategory; count: number; label: string }[] {
  const categories: Record<ToolCategory, string> = {
    search: 'Search',
    data: 'Data Processing',
    code: 'Code Execution',
    api: 'API & HTTP',
    custom: 'Custom Tools',
    workflow: 'Workflow'
  };
  
  return Object.entries(categories).map(([category, label]) => ({
    category: category as ToolCategory,
    count: getToolsByCategory(category as ToolCategory).length,
    label
  }));
}
