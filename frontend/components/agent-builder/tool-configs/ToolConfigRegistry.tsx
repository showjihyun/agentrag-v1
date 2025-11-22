"use client";

/**
 * Tool Config Registry
 * 
 * 50+ Tools의 상세한 Config 스키마 정의
 * 각 Tool별로 맞춤형 Select Box와 입력 필드 제공
 */

export interface ToolParamSchema {
  type: 'string' | 'number' | 'boolean' | 'select' | 'textarea' | 'code' | 'json' | 'password' | 'array';
  description: string;
  required: boolean;
  default?: any;
  enum?: string[];
  min?: number;
  max?: number;
  placeholder?: string;
  helpText?: string;
  pattern?: string;
  language?: string;
}

export interface ToolConfigSchema {
  id: string;
  name: string;
  category: string;
  description: string;
  icon?: string;
  bg_color?: string;
  params: Record<string, ToolParamSchema>;
  credentials?: Record<string, ToolParamSchema>;
  examples?: Array<{
    name: string;
    description: string;
    config: Record<string, any>;
  }>;
  docs_link?: string;
}

/**
 * 모든 Tool의 Config 스키마
 */
export const TOOL_CONFIG_REGISTRY: Record<string, ToolConfigSchema> = {

  // ==================== AI Tools ====================
  
  ai_agent: {
    id: 'ai_agent',
    name: 'AI Agent',
    category: 'ai',
    description: 'Advanced AI Agent with Memory Management (n8n style)',
    icon: '🤖',
    bg_color: '#8B5CF6',
    params: {
      // Core Settings
      provider: {
        type: 'select',
        description: 'LLM Provider',
        required: true,
        enum: ['ollama', 'openai', 'claude', 'gemini', 'grok'],
        default: 'ollama',
        helpText: 'Choose your AI provider'
      },
      model: {
        type: 'select',
        description: 'Model',
        required: true,
        enum: [
          // Ollama (Local)
          'llama3.3:70b',
          'llama3.1:70b',
          'qwen2.5:72b',
          'deepseek-r1:70b',
          'mixtral:8x7b',
          // OpenAI
          'gpt-5',
          'o3',
          'o3-mini',
          'gpt-4o',
          'gpt-4o-mini',
          // Claude
          'claude-4.5-sonnet',
          'claude-4-sonnet',
          'claude-3.7-sonnet',
          'claude-3.5-sonnet',
          'claude-3-opus',
          // Gemini
          'gemini-2.0-flash',
          'gemini-2.0-pro',
          'gemini-1.5-pro',
          'gemini-1.5-flash',
          'gemini-ultra',
          // Grok
          'grok-3',
          'grok-2.5',
          'grok-2',
          'grok-2-mini',
          'grok-vision'
        ],
        default: 'llama3.3:70b',
        helpText: 'Select the AI model to use'
      },
      
      // Chat UI Mode
      enable_chat_ui: {
        type: 'boolean',
        description: 'Enable Real-time Chat UI',
        required: false,
        default: false,
        helpText: 'Show interactive chat interface for real-time conversations'
      },
      chat_ui_position: {
        type: 'select',
        description: 'Chat UI Position',
        required: false,
        enum: ['right', 'bottom', 'modal', 'inline'],
        default: 'right',
        helpText: 'Where to display the chat interface'
      },
      
      // Prompt Configuration
      system_prompt: {
        type: 'textarea',
        description: 'System Prompt',
        required: false,
        placeholder: 'You are a helpful AI assistant...',
        helpText: 'Define the agent\'s behavior and personality'
      },
      user_message: {
        type: 'textarea',
        description: 'User Message',
        required: true,
        placeholder: 'Enter your message or use {{input.message}}',
        helpText: 'The message to send to the AI'
      },
      
      // Memory Configuration
      enable_memory: {
        type: 'boolean',
        description: 'Enable Memory',
        required: false,
        default: true,
        helpText: 'Use conversation memory'
      },
      memory_type: {
        type: 'select',
        description: 'Memory Type',
        required: false,
        enum: ['short_term', 'mid_term', 'long_term', 'all'],
        default: 'short_term',
        helpText: 'Short: Current session, Mid: Session context, Long: Persistent knowledge'
      },
      memory_window: {
        type: 'select',
        description: 'Memory Window',
        required: false,
        enum: ['5', '10', '20', '50', '100'],
        default: '10',
        helpText: 'Number of messages to remember'
      },
      session_id: {
        type: 'string',
        description: 'Session ID',
        required: false,
        placeholder: 'auto-generated or custom',
        helpText: 'Unique identifier for this conversation'
      },
      
      // Generation Parameters
      temperature: {
        type: 'number',
        description: 'Temperature',
        required: false,
        default: 0.7,
        min: 0,
        max: 2,
        helpText: '0 = deterministic, 2 = very creative'
      },
      max_tokens: {
        type: 'number',
        description: 'Max Tokens',
        required: false,
        default: 1000,
        min: 1,
        max: 4096,
        helpText: 'Maximum length of response'
      },
      top_p: {
        type: 'number',
        description: 'Top P',
        required: false,
        default: 1,
        min: 0,
        max: 1,
        helpText: 'Nucleus sampling parameter'
      },
      frequency_penalty: {
        type: 'number',
        description: 'Frequency Penalty',
        required: false,
        default: 0,
        min: 0,
        max: 2,
        helpText: 'Reduce repetition'
      },
      presence_penalty: {
        type: 'number',
        description: 'Presence Penalty',
        required: false,
        default: 0,
        min: 0,
        max: 2,
        helpText: 'Encourage new topics'
      },
      
      // Advanced Options
      response_format: {
        type: 'select',
        description: 'Response Format',
        required: false,
        enum: ['text', 'json', 'json_object'],
        default: 'text',
        helpText: 'Format of the response'
      },
      stop_sequences: {
        type: 'array',
        description: 'Stop Sequences',
        required: false,
        placeholder: '\\n\\n, END, STOP',
        helpText: 'Sequences that stop generation'
      },
      timeout: {
        type: 'select',
        description: 'Timeout (seconds)',
        required: false,
        enum: ['30', '60', '120', '300'],
        default: '60',
        helpText: 'Request timeout'
      },
      
      // Context Management
      include_context: {
        type: 'boolean',
        description: 'Include Previous Context',
        required: false,
        default: true,
        helpText: 'Include conversation history'
      },
      context_window: {
        type: 'select',
        description: 'Context Window',
        required: false,
        enum: ['5', '10', '20', 'full'],
        default: '10',
        helpText: 'Number of previous messages to include'
      },
      
      // Output Options
      extract_json: {
        type: 'boolean',
        description: 'Extract JSON from Response',
        required: false,
        default: false,
        helpText: 'Parse JSON from markdown code blocks'
      },
      return_metadata: {
        type: 'boolean',
        description: 'Return Metadata',
        required: false,
        default: true,
        helpText: 'Include usage stats and metadata'
      }
    },
    credentials: {
      api_key: {
        type: 'password',
        description: 'API Key',
        required: true,
        placeholder: 'Your API key for the selected provider',
        helpText: 'OpenAI: sk-..., Anthropic: sk-ant-...'
      }
    },
    examples: [
      {
        name: 'Simple Chat',
        description: 'Basic conversation with memory',
        config: {
          provider: 'openai',
          model: 'gpt-4',
          user_message: 'Hello! How can you help me today?',
          system_prompt: 'You are a helpful AI assistant.',
          enable_memory: true,
          memory_type: 'short_term',
          temperature: 0.7
        }
      },
      {
        name: 'JSON Response',
        description: 'Get structured JSON output',
        config: {
          provider: 'openai',
          model: 'gpt-4',
          user_message: 'Extract key information from: {{input.text}}',
          system_prompt: 'You extract structured data and return JSON.',
          response_format: 'json_object',
          extract_json: true,
          temperature: 0.3
        }
      },
      {
        name: 'Long-term Memory',
        description: 'Agent with persistent knowledge',
        config: {
          provider: 'anthropic',
          model: 'claude-3-5-sonnet-20241022',
          user_message: '{{input.query}}',
          system_prompt: 'You are a knowledgeable assistant with access to previous conversations.',
          enable_memory: true,
          memory_type: 'all',
          memory_window: '50',
          temperature: 0.7,
          max_tokens: 2000
        }
      },
      {
        name: 'Creative Writing',
        description: 'High temperature for creativity',
        config: {
          provider: 'openai',
          model: 'gpt-4',
          user_message: 'Write a creative story about: {{input.topic}}',
          system_prompt: 'You are a creative writer.',
          temperature: 1.2,
          max_tokens: 2000,
          enable_memory: false
        }
      }
    ],
    docs_link: 'https://docs.agenticrag.com/tools/ai-agent'
  },
  
  openai_chat: {
    id: 'openai_chat',
    name: 'OpenAI Chat',
    category: 'ai',
    description: 'Chat completion using OpenAI GPT models',
    icon: '🤖',
    bg_color: '#10A37F',
    params: {
      prompt: {
        type: 'textarea',
        description: 'Prompt or message to send',
        required: true,
        placeholder: 'Enter your prompt here...',
        helpText: 'The main input text for GPT to process'
      },
      model: {
        type: 'select',
        description: 'OpenAI model to use',
        required: false,
        default: 'gpt-4',
        enum: ['gpt-4', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
        helpText: 'GPT-4: Most capable, GPT-3.5: Faster and cheaper'
      },
      temperature: {
        type: 'number',
        description: 'Sampling temperature (0-2)',
        required: false,
        default: 0.7,
        min: 0,
        max: 2,
        helpText: 'Lower = more focused, Higher = more creative'
      },
      max_tokens: {
        type: 'number',
        description: 'Maximum tokens to generate',
        required: false,
        default: 1000,
        min: 1,
        max: 4096,
        helpText: 'Higher values allow longer responses'
      },
      top_p: {
        type: 'number',
        description: 'Nucleus sampling (0-1)',
        required: false,
        default: 1,
        min: 0,
        max: 1,
        helpText: 'Alternative to temperature for controlling randomness'
      },
      frequency_penalty: {
        type: 'number',
        description: 'Frequency penalty (0-2)',
        required: false,
        default: 0,
        min: 0,
        max: 2,
        helpText: 'Reduces repetition of token sequences'
      },
      presence_penalty: {
        type: 'number',
        description: 'Presence penalty (0-2)',
        required: false,
        default: 0,
        min: 0,
        max: 2,
        helpText: 'Increases likelihood of new topics'
      }
    },
    credentials: {
      api_key: {
        type: 'password',
        description: 'OpenAI API Key',
        required: true,
        placeholder: 'sk-...',
        helpText: 'Get your API key from platform.openai.com'
      }
    },
    examples: [
      {
        name: 'Simple Chat',
        description: 'Basic chat completion',
        config: {
          prompt: 'Explain quantum computing in simple terms',
          model: 'gpt-4',
          temperature: 0.7
        }
      },
      {
        name: 'Creative Writing',
        description: 'High temperature for creative output',
        config: {
          prompt: 'Write a short story about a time traveler',
          model: 'gpt-4',
          temperature: 1.2,
          max_tokens: 2000
        }
      }
    ],
    docs_link: 'https://platform.openai.com/docs/api-reference/chat'
  },

  anthropic_claude: {
    id: 'anthropic_claude',
    name: 'Anthropic Claude',
    category: 'ai',
    description: 'Chat with Claude AI models',
    icon: '🧠',
    bg_color: '#D97757',
    params: {
      prompt: {
        type: 'textarea',
        description: 'Message or prompt to send to Claude',
        required: true,
        placeholder: 'Enter your prompt here...',
        helpText: 'The main input text for Claude to process'
      },
      model: {
        type: 'select',
        description: 'Claude model to use',
        required: false,
        default: 'claude-3-5-sonnet-20241022',
        enum: [
          'claude-3-5-sonnet-20241022',
          'claude-3-5-haiku-20241022',
          'claude-3-opus-20240229',
          'claude-3-sonnet-20240229',
          'claude-3-haiku-20240307'
        ],
        helpText: 'Sonnet: Balanced, Opus: Most capable, Haiku: Fastest'
      },
      max_tokens: {
        type: 'number',
        description: 'Maximum tokens to generate',
        required: false,
        default: 1024,
        min: 1,
        max: 4096,
        helpText: 'Higher values allow longer responses'
      },
      temperature: {
        type: 'number',
        description: 'Sampling temperature (0-1)',
        required: false,
        default: 1.0,
        min: 0,
        max: 1,
        helpText: 'Lower = more focused, Higher = more creative'
      },
      system: {
        type: 'textarea',
        description: 'System prompt (optional)',
        required: false,
        placeholder: 'You are a helpful assistant...',
        helpText: 'Sets the behavior and context for Claude'
      },
      top_p: {
        type: 'number',
        description: 'Nucleus sampling (0-1)',
        required: false,
        default: 1,
        min: 0,
        max: 1
      },
      top_k: {
        type: 'number',
        description: 'Top-k sampling',
        required: false,
        default: 0,
        min: 0,
        max: 100
      }
    },
    credentials: {
      api_key: {
        type: 'password',
        description: 'Anthropic API Key',
        required: true,
        placeholder: 'sk-ant-...',
        helpText: 'Get your API key from console.anthropic.com'
      }
    },
    examples: [
      {
        name: 'Analysis Task',
        description: 'Detailed analysis with Claude',
        config: {
          prompt: 'Analyze the pros and cons of remote work',
          model: 'claude-3-5-sonnet-20241022',
          temperature: 0.7,
          max_tokens: 2000
        }
      }
    ],
    docs_link: 'https://docs.anthropic.com/claude/reference/messages_post'
  },

  // ==================== Search Tools ====================
  
  google_search: {
    id: 'google_search',
    name: 'Google Search',
    category: 'search',
    description: 'Search the web using Google',
    icon: '🔍',
    bg_color: '#4285F4',
    params: {
      query: {
        type: 'string',
        description: 'Search query',
        required: true,
        placeholder: 'Enter search query...',
        helpText: 'Keywords to search for'
      },
      max_results: {
        type: 'select',
        description: 'Maximum number of results',
        required: false,
        default: '10',
        enum: ['5', '10', '20', '50', '100'],
        helpText: 'Number of search results to return'
      },
      language: {
        type: 'select',
        description: 'Search language',
        required: false,
        default: 'ko',
        enum: ['en', 'ko', 'ja', 'zh', 'es', 'fr', 'de', 'it', 'pt', 'ru'],
        helpText: 'Language for search results'
      },
      safe_search: {
        type: 'select',
        description: 'Safe search level',
        required: false,
        default: 'moderate',
        enum: ['off', 'moderate', 'strict'],
        helpText: 'Filter explicit content'
      },
      time_range: {
        type: 'select',
        description: 'Time range filter',
        required: false,
        default: 'any',
        enum: ['any', 'day', 'week', 'month', 'year'],
        helpText: 'Filter results by publication date'
      }
    },
    credentials: {
      api_key: {
        type: 'password',
        description: 'Google API Key',
        required: true,
        placeholder: 'AIza...',
        helpText: 'Get from Google Cloud Console'
      },
      search_engine_id: {
        type: 'string',
        description: 'Custom Search Engine ID',
        required: true,
        placeholder: 'cx...',
        helpText: 'Create at programmablesearchengine.google.com'
      }
    },
    examples: [
      {
        name: 'Basic Search',
        description: 'Simple web search',
        config: {
          query: 'artificial intelligence trends 2024',
          max_results: '10',
          language: 'en'
        }
      }
    ],
    docs_link: 'https://developers.google.com/custom-search/v1/overview'
  },

  duckduckgo_search: {
    id: 'duckduckgo_search',
    name: 'DuckDuckGo Search',
    category: 'search',
    description: 'Privacy-focused web search (no API key required)',
    icon: '🦆',
    bg_color: '#DE5833',
    params: {
      query: {
        type: 'string',
        description: 'Search query',
        required: true,
        placeholder: 'Enter search query...',
        helpText: 'Keywords to search for'
      },
      max_results: {
        type: 'select',
        description: 'Maximum number of results',
        required: false,
        default: '10',
        enum: ['5', '10', '20', '30', '50'],
        helpText: 'Number of search results to return'
      },
      region: {
        type: 'select',
        description: 'Search region',
        required: false,
        default: 'wt-wt',
        enum: ['wt-wt', 'us-en', 'uk-en', 'kr-kr', 'jp-jp', 'cn-zh', 'de-de', 'fr-fr'],
        helpText: 'Regional search preferences'
      },
      safesearch: {
        type: 'select',
        description: 'Safe search',
        required: false,
        default: 'moderate',
        enum: ['off', 'moderate', 'strict'],
        helpText: 'Filter explicit content'
      },
      time_range: {
        type: 'select',
        description: 'Time range',
        required: false,
        default: 'any',
        enum: ['any', 'd', 'w', 'm', 'y'],
        helpText: 'd=day, w=week, m=month, y=year'
      }
    },
    examples: [
      {
        name: 'Quick Search',
        description: 'Fast web search without API key',
        config: {
          query: 'latest tech news',
          max_results: '10',
          region: 'us-en'
        }
      }
    ],
    docs_link: 'https://pypi.org/project/duckduckgo-search/'
  },

  // ==================== Communication Tools ====================
  
  send_email: {
    id: 'send_email',
    name: 'Send Email',
    category: 'communication',
    description: 'Send emails via SMTP',
    icon: '📧',
    bg_color: '#EA4335',
    params: {
      to: {
        type: 'string',
        description: 'Recipient email address',
        required: true,
        placeholder: 'recipient@example.com',
        pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
        helpText: 'Email address of the recipient'
      },
      subject: {
        type: 'string',
        description: 'Email subject',
        required: true,
        placeholder: 'Subject line',
        helpText: 'Subject line of the email'
      },
      body: {
        type: 'textarea',
        description: 'Email body content',
        required: true,
        placeholder: 'Enter your message here...',
        helpText: 'Main content of the email'
      },
      content_type: {
        type: 'select',
        description: 'Email content type',
        required: false,
        default: 'plain',
        enum: ['plain', 'html'],
        helpText: 'Plain text or HTML formatted email'
      },
      cc: {
        type: 'string',
        description: 'CC email addresses (comma-separated)',
        required: false,
        placeholder: 'cc1@example.com, cc2@example.com',
        helpText: 'Carbon copy recipients'
      },
      bcc: {
        type: 'string',
        description: 'BCC email addresses (comma-separated)',
        required: false,
        placeholder: 'bcc1@example.com',
        helpText: 'Blind carbon copy recipients'
      },
      priority: {
        type: 'select',
        description: 'Email priority',
        required: false,
        default: 'normal',
        enum: ['low', 'normal', 'high'],
        helpText: 'Priority level of the email'
      },
      from: {
        type: 'string',
        description: 'Sender email address (optional)',
        required: false,
        placeholder: 'sender@example.com',
        helpText: 'Override default sender address'
      }
    },
    credentials: {
      smtp_host: {
        type: 'string',
        description: 'SMTP Server Host',
        required: true,
        placeholder: 'smtp.gmail.com',
        default: 'smtp.gmail.com'
      },
      smtp_port: {
        type: 'select',
        description: 'SMTP Port',
        required: true,
        default: '587',
        enum: ['25', '465', '587', '2525']
      },
      smtp_user: {
        type: 'string',
        description: 'SMTP Username',
        required: true,
        placeholder: 'your-email@gmail.com'
      },
      smtp_password: {
        type: 'password',
        description: 'SMTP Password',
        required: true,
        placeholder: 'App password or account password'
      },
      use_tls: {
        type: 'boolean',
        description: 'Use TLS',
        required: false,
        default: true
      }
    },
    examples: [
      {
        name: 'Simple Email',
        description: 'Send a plain text email',
        config: {
          to: 'recipient@example.com',
          subject: 'Hello from Workflow',
          body: 'This is an automated email from your workflow.',
          content_type: 'plain'
        }
      },
      {
        name: 'HTML Email',
        description: 'Send formatted HTML email',
        config: {
          to: 'recipient@example.com',
          subject: 'Weekly Report',
          body: '<h1>Report</h1><p>Your weekly summary...</p>',
          content_type: 'html',
          priority: 'high'
        }
      }
    ],
    docs_link: 'https://docs.python.org/3/library/smtplib.html'
  },

  slack: {
    id: 'slack',
    name: 'Slack',
    category: 'communication',
    description: 'Send messages to Slack channels',
    icon: '💬',
    bg_color: '#4A154B',
    params: {
      channel: {
        type: 'string',
        description: 'Slack channel name or ID',
        required: true,
        placeholder: '#general or C1234567890',
        helpText: 'Channel name (with #) or channel ID'
      },
      message: {
        type: 'textarea',
        description: 'Message to send',
        required: true,
        placeholder: 'Enter your message here...',
        helpText: 'Text content of the message'
      },
      username: {
        type: 'string',
        description: 'Bot username (optional)',
        required: false,
        placeholder: 'My Bot',
        helpText: 'Display name for the bot'
      },
      icon_emoji: {
        type: 'string',
        description: 'Bot icon emoji (optional)',
        required: false,
        placeholder: ':robot_face:',
        helpText: 'Emoji to use as bot icon'
      },
      thread_ts: {
        type: 'string',
        description: 'Thread timestamp (for replies)',
        required: false,
        placeholder: '1234567890.123456',
        helpText: 'Reply to a specific thread'
      },
      link_names: {
        type: 'boolean',
        description: 'Link channel names and usernames',
        required: false,
        default: true,
        helpText: 'Auto-link @mentions and #channels'
      }
    },
    credentials: {
      webhook_url: {
        type: 'password',
        description: 'Slack Webhook URL (Option 1)',
        required: false,
        placeholder: 'https://hooks.slack.com/services/...',
        helpText: 'Incoming webhook URL from Slack'
      },
      bot_token: {
        type: 'password',
        description: 'Bot Token (Option 2)',
        required: false,
        placeholder: 'xoxb-...',
        helpText: 'Bot user OAuth token'
      }
    },
    examples: [
      {
        name: 'Simple Message',
        description: 'Send a basic message',
        config: {
          channel: '#general',
          message: 'Hello from workflow automation!'
        }
      },
      {
        name: 'Custom Bot',
        description: 'Message with custom bot appearance',
        config: {
          channel: '#notifications',
          message: 'Task completed successfully!',
          username: 'Workflow Bot',
          icon_emoji: ':white_check_mark:'
        }
      }
    ],
    docs_link: 'https://api.slack.com/messaging/webhooks'
  },

  // ==================== Developer Tools ====================
  
  http_request: {
    id: 'http_request',
    name: 'HTTP Request',
    category: 'developer',
    description: 'Make HTTP requests to any API endpoint',
    icon: '🌐',
    bg_color: '#FF6B6B',
    params: {
      url: {
        type: 'string',
        description: 'Request URL',
        required: true,
        placeholder: 'https://api.example.com/endpoint',
        helpText: 'Full URL including protocol'
      },
      method: {
        type: 'select',
        description: 'HTTP method',
        required: false,
        default: 'GET',
        enum: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'],
        helpText: 'HTTP request method'
      },
      headers: {
        type: 'json',
        description: 'Request headers (JSON)',
        required: false,
        default: {},
        placeholder: '{"Content-Type": "application/json"}',
        helpText: 'Custom HTTP headers'
      },
      body: {
        type: 'json',
        description: 'Request body (JSON)',
        required: false,
        placeholder: '{"key": "value"}',
        helpText: 'Request payload for POST/PUT/PATCH'
      },
      query_params: {
        type: 'json',
        description: 'Query parameters (JSON)',
        required: false,
        placeholder: '{"page": 1, "limit": 10}',
        helpText: 'URL query parameters'
      },
      timeout: {
        type: 'select',
        description: 'Request timeout',
        required: false,
        default: '30',
        enum: ['5', '10', '30', '60', '120', '300'],
        helpText: 'Timeout in seconds'
      },
      follow_redirects: {
        type: 'boolean',
        description: 'Follow redirects',
        required: false,
        default: true,
        helpText: 'Automatically follow HTTP redirects'
      },
      verify_ssl: {
        type: 'boolean',
        description: 'Verify SSL certificates',
        required: false,
        default: true,
        helpText: 'Validate SSL/TLS certificates'
      }
    },
    credentials: {
      api_key: {
        type: 'password',
        description: 'API Key (optional)',
        required: false,
        placeholder: 'Your API key',
        helpText: 'Added as Authorization: Bearer header'
      }
    },
    examples: [
      {
        name: 'GET Request',
        description: 'Fetch data from API',
        config: {
          url: 'https://api.github.com/users/octocat',
          method: 'GET',
          headers: { 'Accept': 'application/json' }
        }
      },
      {
        name: 'POST Request',
        description: 'Send data to API',
        config: {
          url: 'https://api.example.com/data',
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: { 'name': 'John', 'email': 'john@example.com' }
        }
      }
    ],
    docs_link: 'https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods'
  },

  github: {
    id: 'github',
    name: 'GitHub',
    category: 'developer',
    description: 'Interact with GitHub repositories',
    icon: '🐙',
    bg_color: '#181717',
    params: {
      operation: {
        type: 'select',
        description: 'GitHub operation',
        required: true,
        enum: ['create_issue', 'create_pr', 'get_repo', 'list_issues', 'list_prs', 'create_comment', 'merge_pr'],
        helpText: 'Action to perform on GitHub'
      },
      owner: {
        type: 'string',
        description: 'Repository owner',
        required: true,
        placeholder: 'octocat',
        helpText: 'GitHub username or organization'
      },
      repo: {
        type: 'string',
        description: 'Repository name',
        required: true,
        placeholder: 'Hello-World',
        helpText: 'Name of the repository'
      },
      title: {
        type: 'string',
        description: 'Issue/PR title',
        required: false,
        placeholder: 'Bug: Something is broken',
        helpText: 'Title for issue or pull request'
      },
      body: {
        type: 'textarea',
        description: 'Issue/PR body',
        required: false,
        placeholder: 'Detailed description...',
        helpText: 'Markdown content for issue or PR'
      },
      labels: {
        type: 'array',
        description: 'Labels (comma-separated)',
        required: false,
        placeholder: 'bug, urgent',
        helpText: 'Labels to add to issue/PR'
      },
      branch: {
        type: 'string',
        description: 'Branch name (for PR)',
        required: false,
        placeholder: 'feature/new-feature',
        helpText: 'Source branch for pull request'
      },
      base: {
        type: 'select',
        description: 'Base branch (for PR)',
        required: false,
        default: 'main',
        enum: ['main', 'master', 'develop', 'staging'],
        helpText: 'Target branch for pull request'
      },
      state: {
        type: 'select',
        description: 'Issue/PR state filter',
        required: false,
        default: 'open',
        enum: ['open', 'closed', 'all'],
        helpText: 'Filter by state'
      },
      per_page: {
        type: 'select',
        description: 'Results per page',
        required: false,
        default: '30',
        enum: ['10', '30', '50', '100'],
        helpText: 'Number of items to return'
      }
    },
    credentials: {
      token: {
        type: 'password',
        description: 'GitHub Personal Access Token',
        required: true,
        placeholder: 'ghp_...',
        helpText: 'Generate at github.com/settings/tokens'
      }
    },
    examples: [
      {
        name: 'Create Issue',
        description: 'Create a new GitHub issue',
        config: {
          operation: 'create_issue',
          owner: 'octocat',
          repo: 'Hello-World',
          title: 'Found a bug',
          body: 'Steps to reproduce...',
          labels: ['bug']
        }
      },
      {
        name: 'List Issues',
        description: 'Get repository issues',
        config: {
          operation: 'list_issues',
          owner: 'octocat',
          repo: 'Hello-World',
          state: 'open',
          per_page: '30'
        }
      }
    ],
    docs_link: 'https://docs.github.com/en/rest'
  },

  // ==================== Productivity Tools ====================
  
  notion: {
    id: 'notion',
    name: 'Notion',
    category: 'productivity',
    description: 'Create and manage Notion pages and databases',
    icon: '📝',
    bg_color: '#000000',
    params: {
      operation: {
        type: 'select',
        description: 'Notion operation',
        required: true,
        enum: ['create_page', 'update_page', 'query_database', 'get_page', 'delete_page'],
        helpText: 'Action to perform in Notion'
      },
      database_id: {
        type: 'string',
        description: 'Database ID',
        required: false,
        placeholder: '32-character ID',
        helpText: 'Required for database operations'
      },
      page_id: {
        type: 'string',
        description: 'Page ID',
        required: false,
        placeholder: '32-character ID',
        helpText: 'Required for page operations'
      },
      properties: {
        type: 'json',
        description: 'Page properties (JSON)',
        required: false,
        placeholder: '{"Name": {"title": [{"text": {"content": "New Page"}}]}}',
        helpText: 'Notion property values'
      },
      content: {
        type: 'json',
        description: 'Page content blocks (JSON)',
        required: false,
        placeholder: '[{"object": "block", "type": "paragraph", ...}]',
        helpText: 'Notion block content'
      },
      filter: {
        type: 'json',
        description: 'Database filter (JSON)',
        required: false,
        placeholder: '{"property": "Status", "select": {"equals": "Done"}}',
        helpText: 'Filter for database queries'
      },
      sorts: {
        type: 'json',
        description: 'Sort configuration (JSON)',
        required: false,
        placeholder: '[{"property": "Created", "direction": "descending"}]',
        helpText: 'Sort order for results'
      },
      page_size: {
        type: 'select',
        description: 'Results per page',
        required: false,
        default: '100',
        enum: ['10', '25', '50', '100'],
        helpText: 'Number of items to return'
      }
    },
    credentials: {
      api_key: {
        type: 'password',
        description: 'Notion Integration Token',
        required: true,
        placeholder: 'secret_...',
        helpText: 'Create integration at notion.so/my-integrations'
      }
    },
    examples: [
      {
        name: 'Create Page',
        description: 'Create a new page in database',
        config: {
          operation: 'create_page',
          database_id: 'your-database-id',
          properties: {
            'Name': { 'title': [{ 'text': { 'content': 'New Task' } }] },
            'Status': { 'select': { 'name': 'In Progress' } }
          }
        }
      },
      {
        name: 'Query Database',
        description: 'Search database with filters',
        config: {
          operation: 'query_database',
          database_id: 'your-database-id',
          filter: { 'property': 'Status', 'select': { 'equals': 'Done' } },
          page_size: '50'
        }
      }
    ],
    docs_link: 'https://developers.notion.com/reference/intro'
  },

  google_calendar: {
    id: 'google_calendar',
    name: 'Google Calendar',
    category: 'productivity',
    description: 'Manage Google Calendar events',
    icon: '📅',
    bg_color: '#4285F4',
    params: {
      operation: {
        type: 'select',
        description: 'Calendar operation',
        required: true,
        enum: ['create_event', 'list_events', 'update_event', 'delete_event', 'get_event'],
        helpText: 'Action to perform on calendar'
      },
      calendar_id: {
        type: 'string',
        description: 'Calendar ID',
        required: false,
        default: 'primary',
        placeholder: 'primary or email@gmail.com',
        helpText: 'Calendar to operate on'
      },
      summary: {
        type: 'string',
        description: 'Event title',
        required: false,
        placeholder: 'Team Meeting',
        helpText: 'Title of the calendar event'
      },
      description: {
        type: 'textarea',
        description: 'Event description',
        required: false,
        placeholder: 'Discuss project updates...',
        helpText: 'Detailed description of the event'
      },
      start_time: {
        type: 'string',
        description: 'Start time (ISO 8601)',
        required: false,
        placeholder: '2024-01-15T10:00:00Z',
        helpText: 'Event start time in ISO format'
      },
      end_time: {
        type: 'string',
        description: 'End time (ISO 8601)',
        required: false,
        placeholder: '2024-01-15T11:00:00Z',
        helpText: 'Event end time in ISO format'
      },
      attendees: {
        type: 'array',
        description: 'Attendee emails (comma-separated)',
        required: false,
        placeholder: 'user1@gmail.com, user2@gmail.com',
        helpText: 'Email addresses of attendees'
      },
      location: {
        type: 'string',
        description: 'Event location',
        required: false,
        placeholder: 'Conference Room A',
        helpText: 'Physical or virtual location'
      },
      time_min: {
        type: 'string',
        description: 'List events after (ISO 8601)',
        required: false,
        placeholder: '2024-01-01T00:00:00Z',
        helpText: 'Start of time range for listing'
      },
      max_results: {
        type: 'select',
        description: 'Maximum results',
        required: false,
        default: '10',
        enum: ['5', '10', '25', '50', '100'],
        helpText: 'Number of events to return'
      },
      event_id: {
        type: 'string',
        description: 'Event ID',
        required: false,
        placeholder: 'event-id-string',
        helpText: 'Required for update/delete/get operations'
      }
    },
    credentials: {
      access_token: {
        type: 'password',
        description: 'Google OAuth Access Token',
        required: true,
        placeholder: 'ya29...',
        helpText: 'OAuth 2.0 access token'
      }
    },
    examples: [
      {
        name: 'Create Event',
        description: 'Schedule a new calendar event',
        config: {
          operation: 'create_event',
          summary: 'Team Standup',
          start_time: '2024-01-15T09:00:00Z',
          end_time: '2024-01-15T09:30:00Z',
          attendees: ['team@example.com']
        }
      },
      {
        name: 'List Events',
        description: 'Get upcoming events',
        config: {
          operation: 'list_events',
          calendar_id: 'primary',
          max_results: '10'
        }
      }
    ],
    docs_link: 'https://developers.google.com/calendar/api/v3/reference'
  },

  google_sheets: {
    id: 'google_sheets',
    name: 'Google Sheets',
    category: 'productivity',
    description: 'Read and write Google Sheets data',
    icon: '📊',
    bg_color: '#0F9D58',
    params: {
      operation: {
        type: 'select',
        description: 'Sheets operation',
        required: true,
        enum: ['read', 'write', 'append', 'update', 'clear', 'create_sheet'],
        helpText: 'Action to perform on spreadsheet'
      },
      spreadsheet_id: {
        type: 'string',
        description: 'Spreadsheet ID',
        required: true,
        placeholder: 'From spreadsheet URL',
        helpText: 'ID from the spreadsheet URL'
      },
      range: {
        type: 'string',
        description: 'Cell range (A1 notation)',
        required: true,
        placeholder: 'Sheet1!A1:D10',
        helpText: 'Range in A1 notation (e.g., Sheet1!A1:B10)'
      },
      values: {
        type: 'json',
        description: 'Data to write (2D array)',
        required: false,
        placeholder: '[["Name", "Age"], ["John", 30]]',
        helpText: 'Array of rows to write'
      },
      value_input_option: {
        type: 'select',
        description: 'Value input option',
        required: false,
        default: 'USER_ENTERED',
        enum: ['RAW', 'USER_ENTERED'],
        helpText: 'RAW: as-is, USER_ENTERED: parse formulas'
      },
      major_dimension: {
        type: 'select',
        description: 'Major dimension',
        required: false,
        default: 'ROWS',
        enum: ['ROWS', 'COLUMNS'],
        helpText: 'How to interpret data array'
      }
    },
    credentials: {
      access_token: {
        type: 'password',
        description: 'Google OAuth Access Token',
        required: true,
        placeholder: 'ya29...',
        helpText: 'OAuth 2.0 access token'
      }
    },
    examples: [
      {
        name: 'Read Data',
        description: 'Read cells from sheet',
        config: {
          operation: 'read',
          spreadsheet_id: 'your-spreadsheet-id',
          range: 'Sheet1!A1:D10'
        }
      },
      {
        name: 'Append Row',
        description: 'Add new row to sheet',
        config: {
          operation: 'append',
          spreadsheet_id: 'your-spreadsheet-id',
          range: 'Sheet1!A:D',
          values: [['John Doe', 'john@example.com', '2024-01-15', 'Active']]
        }
      }
    ],
    docs_link: 'https://developers.google.com/sheets/api/reference/rest'
  },

  // ==================== Data Tools ====================
  
  database_query: {
    id: 'database_query',
    name: 'Database Query',
    category: 'data',
    description: 'Execute SQL queries on databases',
    icon: '🗄️',
    bg_color: '#336791',
    params: {
      query: {
        type: 'code',
        description: 'SQL query to execute',
        required: true,
        placeholder: 'SELECT * FROM users WHERE status = ?',
        language: 'sql',
        helpText: 'SQL query with optional parameters'
      },
      parameters: {
        type: 'json',
        description: 'Query parameters (array)',
        required: false,
        default: [],
        placeholder: '["active"]',
        helpText: 'Values for parameterized queries'
      },
      database_type: {
        type: 'select',
        description: 'Database type',
        required: true,
        enum: ['postgresql', 'mysql', 'sqlite', 'mssql', 'oracle'],
        helpText: 'Type of database to connect to'
      },
      timeout: {
        type: 'select',
        description: 'Query timeout',
        required: false,
        default: '30',
        enum: ['10', '30', '60', '120', '300'],
        helpText: 'Timeout in seconds'
      },
      fetch_size: {
        type: 'select',
        description: 'Maximum rows to fetch',
        required: false,
        default: '1000',
        enum: ['100', '500', '1000', '5000', '10000'],
        helpText: 'Limit number of returned rows'
      }
    },
    credentials: {
      connection_string: {
        type: 'password',
        description: 'Database Connection String',
        required: true,
        placeholder: 'postgresql://user:pass@localhost:5432/dbname',
        helpText: 'Full database connection URL'
      }
    },
    examples: [
      {
        name: 'Select Query',
        description: 'Fetch data from database',
        config: {
          query: 'SELECT id, name, email FROM users WHERE status = ? LIMIT 100',
          parameters: ['active'],
          database_type: 'postgresql'
        }
      },
      {
        name: 'Insert Data',
        description: 'Insert new record',
        config: {
          query: 'INSERT INTO logs (event, timestamp) VALUES (?, NOW())',
          parameters: ['user_login'],
          database_type: 'mysql'
        }
      }
    ],
    docs_link: 'https://docs.sqlalchemy.org/en/20/'
  },

  csv_parser: {
    id: 'csv_parser',
    name: 'CSV Parser',
    category: 'data',
    description: 'Parse and manipulate CSV data',
    icon: '📄',
    bg_color: '#21BA45',
    params: {
      operation: {
        type: 'select',
        description: 'CSV operation',
        required: true,
        enum: ['parse', 'filter', 'transform', 'aggregate', 'merge'],
        helpText: 'Operation to perform on CSV data'
      },
      csv_data: {
        type: 'textarea',
        description: 'CSV data or file path',
        required: true,
        placeholder: 'name,age,city\nJohn,30,NYC\nJane,25,LA',
        helpText: 'CSV content or path to CSV file'
      },
      delimiter: {
        type: 'select',
        description: 'CSV delimiter',
        required: false,
        default: ',',
        enum: [',', ';', '\\t', '|'],
        helpText: 'Character separating values'
      },
      has_header: {
        type: 'boolean',
        description: 'First row is header',
        required: false,
        default: true,
        helpText: 'Whether first row contains column names'
      },
      encoding: {
        type: 'select',
        description: 'File encoding',
        required: false,
        default: 'utf-8',
        enum: ['utf-8', 'utf-16', 'ascii', 'iso-8859-1', 'cp949'],
        helpText: 'Character encoding of the file'
      },
      filter_expression: {
        type: 'string',
        description: 'Filter expression (for filter operation)',
        required: false,
        placeholder: 'age > 25',
        helpText: 'Python expression to filter rows'
      },
      columns: {
        type: 'array',
        description: 'Columns to select (comma-separated)',
        required: false,
        placeholder: 'name, age, city',
        helpText: 'Specific columns to include'
      }
    },
    examples: [
      {
        name: 'Parse CSV',
        description: 'Convert CSV to JSON',
        config: {
          operation: 'parse',
          csv_data: 'name,age\nJohn,30\nJane,25',
          delimiter: ',',
          has_header: true
        }
      },
      {
        name: 'Filter Rows',
        description: 'Filter CSV by condition',
        config: {
          operation: 'filter',
          csv_data: 'name,age\nJohn,30\nJane,25',
          filter_expression: 'age > 25'
        }
      }
    ],
    docs_link: 'https://docs.python.org/3/library/csv.html'
  },

  json_processor: {
    id: 'json_processor',
    name: 'JSON Processor',
    category: 'data',
    description: 'Parse, transform, and query JSON data',
    icon: '{ }',
    bg_color: '#F7DF1E',
    params: {
      operation: {
        type: 'select',
        description: 'JSON operation',
        required: true,
        enum: ['parse', 'stringify', 'query', 'transform', 'merge', 'validate'],
        helpText: 'Operation to perform on JSON'
      },
      json_data: {
        type: 'textarea',
        description: 'JSON data',
        required: true,
        placeholder: '{"name": "John", "age": 30}',
        helpText: 'JSON string or object'
      },
      json_path: {
        type: 'string',
        description: 'JSONPath query (for query operation)',
        required: false,
        placeholder: '$.users[*].name',
        helpText: 'JSONPath expression to extract data'
      },
      transform_expression: {
        type: 'code',
        description: 'Transform expression (Python)',
        required: false,
        placeholder: 'data["age"] = data["age"] + 1',
        language: 'python',
        helpText: 'Python code to transform data'
      },
      schema: {
        type: 'json',
        description: 'JSON Schema (for validation)',
        required: false,
        placeholder: '{"type": "object", "properties": {...}}',
        helpText: 'JSON Schema to validate against'
      },
      pretty_print: {
        type: 'boolean',
        description: 'Pretty print output',
        required: false,
        default: true,
        helpText: 'Format JSON with indentation'
      },
      indent: {
        type: 'select',
        description: 'Indentation spaces',
        required: false,
        default: '2',
        enum: ['2', '4', '8'],
        helpText: 'Number of spaces for indentation'
      }
    },
    examples: [
      {
        name: 'Parse JSON',
        description: 'Parse JSON string to object',
        config: {
          operation: 'parse',
          json_data: '{"name": "John", "age": 30}',
          pretty_print: true
        }
      },
      {
        name: 'Query JSON',
        description: 'Extract data with JSONPath',
        config: {
          operation: 'query',
          json_data: '{"users": [{"name": "John"}, {"name": "Jane"}]}',
          json_path: '$.users[*].name'
        }
      }
    ],
    docs_link: 'https://jsonpath.com/'
  },

  // ==================== Code Tools ====================
  
  python_code: {
    id: 'python_code',
    name: 'Python Code',
    category: 'code',
    description: 'Execute Python code in secure sandbox',
    icon: '🐍',
    bg_color: '#3776AB',
    params: {
      code: {
        type: 'code',
        description: 'Python code to execute',
        required: true,
        placeholder: '# Access input data\nresult = input["value"] * 2\nprint(result)',
        language: 'python',
        helpText: 'Python code with access to input data'
      },
      mode: {
        type: 'select',
        description: 'Execution mode',
        required: false,
        default: 'simple',
        enum: ['simple', 'advanced'],
        helpText: 'Simple: expressions, Advanced: full scripts with imports'
      },
      timeout: {
        type: 'select',
        description: 'Execution timeout',
        required: false,
        default: '5',
        enum: ['1', '3', '5', '10', '30'],
        helpText: 'Maximum execution time in seconds'
      },
      return_type: {
        type: 'select',
        description: 'Output format',
        required: false,
        default: 'text',
        enum: ['text', 'json', 'dataframe'],
        helpText: 'How to format the execution result'
      },
      variables: {
        type: 'json',
        description: 'Input variables (JSON)',
        required: false,
        default: {},
        placeholder: '{"x": 10, "y": 20}',
        helpText: 'Variables accessible in the code'
      },
      allowed_modules: {
        type: 'array',
        description: 'Additional allowed modules (comma-separated)',
        required: false,
        placeholder: 'requests, pandas, numpy',
        helpText: 'Extra modules to allow (security permitting)'
      }
    },
    examples: [
      {
        name: 'Simple Calculation',
        description: 'Basic arithmetic',
        config: {
          code: 'result = sum(input["numbers"])',
          mode: 'simple',
          timeout: '5'
        }
      },
      {
        name: 'Data Processing',
        description: 'Filter and transform data',
        config: {
          code: `items = input['items']
filtered = [x for x in items if x['status'] == 'active']
result = {'total': len(filtered), 'items': filtered}`,
          mode: 'advanced',
          timeout: '10'
        }
      },
      {
        name: 'JSON Processing',
        description: 'Parse and manipulate JSON',
        config: {
          code: `import json
data = json.loads(input['json_string'])
result = {'keys': list(data.keys()), 'count': len(data)}`,
          mode: 'advanced',
          timeout: '5'
        }
      }
    ],
    docs_link: 'https://docs.python.org/3/'
  },

  javascript_code: {
    id: 'javascript_code',
    name: 'JavaScript Code',
    category: 'code',
    description: 'Execute JavaScript code in sandbox',
    icon: '📜',
    bg_color: '#F7DF1E',
    params: {
      code: {
        type: 'code',
        description: 'JavaScript code to execute',
        required: true,
        placeholder: '// Access input data\nconst result = input.value * 2;\nreturn result;',
        language: 'javascript',
        helpText: 'JavaScript code with access to input object'
      },
      timeout: {
        type: 'select',
        description: 'Execution timeout',
        required: false,
        default: '5',
        enum: ['1', '3', '5', '10', '30'],
        helpText: 'Maximum execution time in seconds'
      },
      return_type: {
        type: 'select',
        description: 'Output format',
        required: false,
        default: 'auto',
        enum: ['auto', 'json', 'string', 'number'],
        helpText: 'How to format the return value'
      },
      strict_mode: {
        type: 'boolean',
        description: 'Use strict mode',
        required: false,
        default: true,
        helpText: 'Enable JavaScript strict mode'
      }
    },
    examples: [
      {
        name: 'Array Processing',
        description: 'Filter and map array',
        config: {
          code: `const items = input.items;
const filtered = items.filter(x => x.status === 'active');
return { total: filtered.length, items: filtered };`,
          timeout: '5'
        }
      },
      {
        name: 'String Manipulation',
        description: 'Transform text',
        config: {
          code: `const text = input.text;
return text.toUpperCase().split(' ').join('-');`,
          timeout: '3'
        }
      }
    ],
    docs_link: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript'
  },

  regex_matcher: {
    id: 'regex_matcher',
    name: 'Regex Matcher',
    category: 'code',
    description: 'Match and extract data using regular expressions',
    icon: '🔤',
    bg_color: '#FF6B6B',
    params: {
      operation: {
        type: 'select',
        description: 'Regex operation',
        required: true,
        enum: ['match', 'search', 'findall', 'replace', 'split', 'validate'],
        helpText: 'Type of regex operation'
      },
      pattern: {
        type: 'string',
        description: 'Regular expression pattern',
        required: true,
        placeholder: '\\d{3}-\\d{4}',
        helpText: 'Regex pattern to match'
      },
      text: {
        type: 'textarea',
        description: 'Text to process',
        required: true,
        placeholder: 'Enter text to match against...',
        helpText: 'Input text for regex operation'
      },
      replacement: {
        type: 'string',
        description: 'Replacement text (for replace)',
        required: false,
        placeholder: 'New text',
        helpText: 'Text to replace matches with'
      },
      flags: {
        type: 'select',
        description: 'Regex flags',
        required: false,
        default: 'none',
        enum: ['none', 'i', 'g', 'ig', 'm', 'im', 'gm', 'igm'],
        helpText: 'i=case-insensitive, g=global, m=multiline'
      },
      max_matches: {
        type: 'select',
        description: 'Maximum matches',
        required: false,
        default: '0',
        enum: ['0', '1', '10', '100', '1000'],
        helpText: '0 = unlimited'
      }
    },
    examples: [
      {
        name: 'Extract Emails',
        description: 'Find all email addresses',
        config: {
          operation: 'findall',
          pattern: '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}',
          text: 'Contact us at info@example.com or support@example.com',
          flags: 'g'
        }
      },
      {
        name: 'Validate Phone',
        description: 'Check phone number format',
        config: {
          operation: 'validate',
          pattern: '^\\d{3}-\\d{3}-\\d{4}$',
          text: '123-456-7890'
        }
      }
    ],
    docs_link: 'https://regex101.com/'
  },

  // ==================== File Tools ====================
  
  file_reader: {
    id: 'file_reader',
    name: 'File Reader',
    category: 'file',
    description: 'Read files from various formats',
    icon: '📖',
    bg_color: '#95A5A6',
    params: {
      file_path: {
        type: 'string',
        description: 'File path or URL',
        required: true,
        placeholder: '/path/to/file.txt or https://example.com/file.pdf',
        helpText: 'Local path or remote URL'
      },
      file_type: {
        type: 'select',
        description: 'File type',
        required: false,
        default: 'auto',
        enum: ['auto', 'text', 'json', 'csv', 'xml', 'pdf', 'docx', 'xlsx'],
        helpText: 'Auto-detect or specify format'
      },
      encoding: {
        type: 'select',
        description: 'Text encoding',
        required: false,
        default: 'utf-8',
        enum: ['utf-8', 'utf-16', 'ascii', 'iso-8859-1', 'cp949', 'euc-kr'],
        helpText: 'Character encoding for text files'
      },
      extract_text: {
        type: 'boolean',
        description: 'Extract text from documents',
        required: false,
        default: true,
        helpText: 'Extract plain text from PDF/DOCX'
      },
      max_size_mb: {
        type: 'select',
        description: 'Maximum file size (MB)',
        required: false,
        default: '10',
        enum: ['1', '5', '10', '50', '100'],
        helpText: 'Reject files larger than this'
      }
    },
    examples: [
      {
        name: 'Read Text File',
        description: 'Read plain text file',
        config: {
          file_path: '/data/document.txt',
          file_type: 'text',
          encoding: 'utf-8'
        }
      },
      {
        name: 'Parse PDF',
        description: 'Extract text from PDF',
        config: {
          file_path: '/documents/report.pdf',
          file_type: 'pdf',
          extract_text: true
        }
      }
    ],
    docs_link: 'https://docs.python.org/3/library/io.html'
  },

  file_writer: {
    id: 'file_writer',
    name: 'File Writer',
    category: 'file',
    description: 'Write data to files',
    icon: '💾',
    bg_color: '#3498DB',
    params: {
      file_path: {
        type: 'string',
        description: 'Output file path',
        required: true,
        placeholder: '/path/to/output.txt',
        helpText: 'Where to save the file'
      },
      content: {
        type: 'textarea',
        description: 'Content to write',
        required: true,
        placeholder: 'File content...',
        helpText: 'Data to write to file'
      },
      file_type: {
        type: 'select',
        description: 'File format',
        required: false,
        default: 'text',
        enum: ['text', 'json', 'csv', 'xml', 'html'],
        helpText: 'Output file format'
      },
      encoding: {
        type: 'select',
        description: 'Text encoding',
        required: false,
        default: 'utf-8',
        enum: ['utf-8', 'utf-16', 'ascii'],
        helpText: 'Character encoding'
      },
      mode: {
        type: 'select',
        description: 'Write mode',
        required: false,
        default: 'overwrite',
        enum: ['overwrite', 'append', 'create_new'],
        helpText: 'How to handle existing files'
      },
      create_dirs: {
        type: 'boolean',
        description: 'Create parent directories',
        required: false,
        default: true,
        helpText: 'Auto-create missing directories'
      }
    },
    examples: [
      {
        name: 'Write Text',
        description: 'Save text to file',
        config: {
          file_path: '/output/result.txt',
          content: 'Processing complete!',
          file_type: 'text',
          mode: 'overwrite'
        }
      },
      {
        name: 'Save JSON',
        description: 'Write JSON data',
        config: {
          file_path: '/data/output.json',
          content: '{"status": "success", "count": 42}',
          file_type: 'json'
        }
      }
    ]
  },

  // ==================== Image Tools ====================
  
  image_processor: {
    id: 'image_processor',
    name: 'Image Processor',
    category: 'image',
    description: 'Process and transform images',
    icon: '🖼️',
    bg_color: '#E74C3C',
    params: {
      operation: {
        type: 'select',
        description: 'Image operation',
        required: true,
        enum: ['resize', 'crop', 'rotate', 'convert', 'compress', 'filter', 'watermark'],
        helpText: 'Transformation to apply'
      },
      image_path: {
        type: 'string',
        description: 'Input image path or URL',
        required: true,
        placeholder: '/path/to/image.jpg',
        helpText: 'Source image location'
      },
      output_path: {
        type: 'string',
        description: 'Output image path',
        required: false,
        placeholder: '/path/to/output.jpg',
        helpText: 'Where to save processed image'
      },
      width: {
        type: 'number',
        description: 'Width (pixels)',
        required: false,
        min: 1,
        max: 10000,
        placeholder: '800',
        helpText: 'Target width for resize'
      },
      height: {
        type: 'number',
        description: 'Height (pixels)',
        required: false,
        min: 1,
        max: 10000,
        placeholder: '600',
        helpText: 'Target height for resize'
      },
      format: {
        type: 'select',
        description: 'Output format',
        required: false,
        default: 'jpg',
        enum: ['jpg', 'png', 'webp', 'gif', 'bmp'],
        helpText: 'Image file format'
      },
      quality: {
        type: 'select',
        description: 'Quality (1-100)',
        required: false,
        default: '85',
        enum: ['50', '70', '85', '90', '95', '100'],
        helpText: 'Compression quality'
      },
      maintain_aspect: {
        type: 'boolean',
        description: 'Maintain aspect ratio',
        required: false,
        default: true,
        helpText: 'Keep original proportions'
      }
    },
    examples: [
      {
        name: 'Resize Image',
        description: 'Scale image to specific size',
        config: {
          operation: 'resize',
          image_path: '/images/photo.jpg',
          width: 800,
          height: 600,
          maintain_aspect: true
        }
      },
      {
        name: 'Convert Format',
        description: 'Change image format',
        config: {
          operation: 'convert',
          image_path: '/images/photo.png',
          format: 'webp',
          quality: '85'
        }
      }
    ],
    docs_link: 'https://pillow.readthedocs.io/'
  },

  ocr_reader: {
    id: 'ocr_reader',
    name: 'OCR Reader',
    category: 'image',
    description: 'Extract text from images using OCR',
    icon: '👁️',
    bg_color: '#9B59B6',
    params: {
      image_path: {
        type: 'string',
        description: 'Image path or URL',
        required: true,
        placeholder: '/path/to/image.jpg',
        helpText: 'Image containing text'
      },
      language: {
        type: 'select',
        description: 'OCR language',
        required: false,
        default: 'en',
        enum: ['en', 'ko', 'ja', 'zh', 'es', 'fr', 'de', 'multi'],
        helpText: 'Language of text in image'
      },
      engine: {
        type: 'select',
        description: 'OCR engine',
        required: false,
        default: 'paddleocr',
        enum: ['paddleocr', 'tesseract', 'easyocr'],
        helpText: 'OCR processing engine'
      },
      detect_orientation: {
        type: 'boolean',
        description: 'Auto-detect text orientation',
        required: false,
        default: true,
        helpText: 'Correct rotated text'
      },
      extract_tables: {
        type: 'boolean',
        description: 'Extract table structures',
        required: false,
        default: false,
        helpText: 'Detect and parse tables'
      },
      confidence_threshold: {
        type: 'select',
        description: 'Minimum confidence',
        required: false,
        default: '0.5',
        enum: ['0.3', '0.5', '0.7', '0.9'],
        helpText: 'Filter low-confidence results'
      }
    },
    examples: [
      {
        name: 'Extract Text',
        description: 'Read text from image',
        config: {
          image_path: '/images/document.jpg',
          language: 'en',
          engine: 'paddleocr'
        }
      },
      {
        name: 'Korean OCR',
        description: 'Extract Korean text',
        config: {
          image_path: '/images/korean_doc.jpg',
          language: 'ko',
          engine: 'paddleocr',
          detect_orientation: true
        }
      }
    ],
    docs_link: 'https://github.com/PaddlePaddle/PaddleOCR'
  },

  // ==================== Utility Tools ====================
  
  datetime_formatter: {
    id: 'datetime_formatter',
    name: 'DateTime Formatter',
    category: 'utility',
    description: 'Parse, format, and manipulate dates and times',
    icon: '🕐',
    bg_color: '#16A085',
    params: {
      operation: {
        type: 'select',
        description: 'DateTime operation',
        required: true,
        enum: ['format', 'parse', 'add', 'subtract', 'diff', 'now', 'convert_timezone'],
        helpText: 'Operation to perform'
      },
      datetime_input: {
        type: 'string',
        description: 'Input date/time',
        required: false,
        placeholder: '2024-01-15T10:30:00Z',
        helpText: 'Date/time string or timestamp'
      },
      input_format: {
        type: 'select',
        description: 'Input format',
        required: false,
        default: 'iso8601',
        enum: ['iso8601', 'unix', 'custom'],
        helpText: 'Format of input datetime'
      },
      output_format: {
        type: 'select',
        description: 'Output format',
        required: false,
        default: 'iso8601',
        enum: ['iso8601', 'unix', 'custom', 'human'],
        helpText: 'Desired output format'
      },
      custom_format: {
        type: 'string',
        description: 'Custom format string',
        required: false,
        placeholder: '%Y-%m-%d %H:%M:%S',
        helpText: 'Python strftime format'
      },
      timezone: {
        type: 'select',
        description: 'Timezone',
        required: false,
        default: 'UTC',
        enum: ['UTC', 'America/New_York', 'Europe/London', 'Asia/Seoul', 'Asia/Tokyo'],
        helpText: 'Target timezone'
      },
      amount: {
        type: 'number',
        description: 'Amount to add/subtract',
        required: false,
        placeholder: '7',
        helpText: 'Number of units'
      },
      unit: {
        type: 'select',
        description: 'Time unit',
        required: false,
        default: 'days',
        enum: ['seconds', 'minutes', 'hours', 'days', 'weeks', 'months', 'years'],
        helpText: 'Unit for add/subtract/diff'
      }
    },
    examples: [
      {
        name: 'Current Time',
        description: 'Get current timestamp',
        config: {
          operation: 'now',
          output_format: 'iso8601',
          timezone: 'UTC'
        }
      },
      {
        name: 'Add Days',
        description: 'Add 7 days to date',
        config: {
          operation: 'add',
          datetime_input: '2024-01-15T00:00:00Z',
          amount: 7,
          unit: 'days'
        }
      },
      {
        name: 'Format Date',
        description: 'Convert to custom format',
        config: {
          operation: 'format',
          datetime_input: '2024-01-15T10:30:00Z',
          output_format: 'custom',
          custom_format: '%B %d, %Y at %I:%M %p'
        }
      }
    ],
    docs_link: 'https://docs.python.org/3/library/datetime.html'
  },

  text_transformer: {
    id: 'text_transformer',
    name: 'Text Transformer',
    category: 'utility',
    description: 'Transform and manipulate text',
    icon: '✏️',
    bg_color: '#E67E22',
    params: {
      operation: {
        type: 'select',
        description: 'Text operation',
        required: true,
        enum: ['uppercase', 'lowercase', 'titlecase', 'trim', 'replace', 'split', 'join', 'extract', 'count'],
        helpText: 'Transformation to apply'
      },
      text: {
        type: 'textarea',
        description: 'Input text',
        required: true,
        placeholder: 'Enter text to transform...',
        helpText: 'Text to process'
      },
      find: {
        type: 'string',
        description: 'Text to find (for replace)',
        required: false,
        placeholder: 'old text',
        helpText: 'String to search for'
      },
      replace_with: {
        type: 'string',
        description: 'Replacement text',
        required: false,
        placeholder: 'new text',
        helpText: 'String to replace with'
      },
      delimiter: {
        type: 'string',
        description: 'Delimiter (for split/join)',
        required: false,
        default: ',',
        placeholder: ',',
        helpText: 'Character to split/join on'
      },
      case_sensitive: {
        type: 'boolean',
        description: 'Case sensitive',
        required: false,
        default: true,
        helpText: 'Match case when finding text'
      },
      trim_whitespace: {
        type: 'boolean',
        description: 'Trim whitespace',
        required: false,
        default: true,
        helpText: 'Remove leading/trailing spaces'
      }
    },
    examples: [
      {
        name: 'To Uppercase',
        description: 'Convert text to uppercase',
        config: {
          operation: 'uppercase',
          text: 'hello world'
        }
      },
      {
        name: 'Replace Text',
        description: 'Find and replace',
        config: {
          operation: 'replace',
          text: 'Hello World',
          find: 'World',
          replace_with: 'Universe'
        }
      },
      {
        name: 'Split String',
        description: 'Split by delimiter',
        config: {
          operation: 'split',
          text: 'apple,banana,orange',
          delimiter: ','
        }
      }
    ]
  },

  hash_generator: {
    id: 'hash_generator',
    name: 'Hash Generator',
    category: 'utility',
    description: 'Generate cryptographic hashes',
    icon: '🔐',
    bg_color: '#34495E',
    params: {
      algorithm: {
        type: 'select',
        description: 'Hash algorithm',
        required: true,
        enum: ['md5', 'sha1', 'sha256', 'sha512', 'blake2b'],
        helpText: 'Hashing algorithm to use'
      },
      input: {
        type: 'textarea',
        description: 'Input data',
        required: true,
        placeholder: 'Data to hash...',
        helpText: 'Text or data to hash'
      },
      encoding: {
        type: 'select',
        description: 'Input encoding',
        required: false,
        default: 'utf-8',
        enum: ['utf-8', 'ascii', 'latin-1'],
        helpText: 'Character encoding'
      },
      output_format: {
        type: 'select',
        description: 'Output format',
        required: false,
        default: 'hex',
        enum: ['hex', 'base64', 'binary'],
        helpText: 'Format of hash output'
      },
      salt: {
        type: 'string',
        description: 'Salt (optional)',
        required: false,
        placeholder: 'random-salt',
        helpText: 'Add salt for extra security'
      }
    },
    examples: [
      {
        name: 'SHA256 Hash',
        description: 'Generate SHA256 hash',
        config: {
          algorithm: 'sha256',
          input: 'Hello World',
          output_format: 'hex'
        }
      },
      {
        name: 'MD5 with Salt',
        description: 'MD5 hash with salt',
        config: {
          algorithm: 'md5',
          input: 'password123',
          salt: 'random-salt-value',
          output_format: 'hex'
        }
      }
    ],
    docs_link: 'https://docs.python.org/3/library/hashlib.html'
  },

  uuid_generator: {
    id: 'uuid_generator',
    name: 'UUID Generator',
    category: 'utility',
    description: 'Generate unique identifiers',
    icon: '🆔',
    bg_color: '#1ABC9C',
    params: {
      version: {
        type: 'select',
        description: 'UUID version',
        required: false,
        default: '4',
        enum: ['1', '4', '5'],
        helpText: 'v1: timestamp, v4: random, v5: namespace'
      },
      count: {
        type: 'select',
        description: 'Number of UUIDs',
        required: false,
        default: '1',
        enum: ['1', '5', '10', '50', '100'],
        helpText: 'How many UUIDs to generate'
      },
      format: {
        type: 'select',
        description: 'Output format',
        required: false,
        default: 'standard',
        enum: ['standard', 'hex', 'int', 'urn'],
        helpText: 'UUID format style'
      },
      uppercase: {
        type: 'boolean',
        description: 'Uppercase letters',
        required: false,
        default: false,
        helpText: 'Use uppercase hex digits'
      },
      namespace: {
        type: 'string',
        description: 'Namespace (for v5)',
        required: false,
        placeholder: 'my-namespace',
        helpText: 'Namespace for UUID v5'
      },
      name: {
        type: 'string',
        description: 'Name (for v5)',
        required: false,
        placeholder: 'my-name',
        helpText: 'Name for UUID v5'
      }
    },
    examples: [
      {
        name: 'Random UUID',
        description: 'Generate random UUID v4',
        config: {
          version: '4',
          count: '1',
          format: 'standard'
        }
      },
      {
        name: 'Multiple UUIDs',
        description: 'Generate 10 UUIDs',
        config: {
          version: '4',
          count: '10',
          format: 'standard'
        }
      }
    ],
    docs_link: 'https://docs.python.org/3/library/uuid.html'
  },

  wait_delay: {
    id: 'wait_delay',
    name: 'Wait / Delay',
    category: 'utility',
    description: 'Pause workflow execution',
    icon: '⏱️',
    bg_color: '#7F8C8D',
    params: {
      duration: {
        type: 'number',
        description: 'Wait duration',
        required: true,
        min: 0.1,
        max: 3600,
        placeholder: '5',
        helpText: 'How long to wait'
      },
      unit: {
        type: 'select',
        description: 'Time unit',
        required: false,
        default: 'seconds',
        enum: ['milliseconds', 'seconds', 'minutes'],
        helpText: 'Unit of time'
      },
      resume_on_webhook: {
        type: 'boolean',
        description: 'Resume on webhook',
        required: false,
        default: false,
        helpText: 'Allow webhook to resume early'
      },
      webhook_url: {
        type: 'string',
        description: 'Webhook URL (if enabled)',
        required: false,
        placeholder: 'https://...',
        helpText: 'URL to receive resume signal'
      }
    },
    examples: [
      {
        name: 'Wait 5 Seconds',
        description: 'Simple delay',
        config: {
          duration: 5,
          unit: 'seconds'
        }
      },
      {
        name: 'Wait 2 Minutes',
        description: 'Longer delay',
        config: {
          duration: 2,
          unit: 'minutes'
        }
      }
    ]
  },

  // ==================== CRM Tools ====================
  
  salesforce: {
    id: 'salesforce',
    name: 'Salesforce',
    category: 'crm',
    description: 'Interact with Salesforce CRM',
    icon: '☁️',
    bg_color: '#00A1E0',
    params: {
      operation: {
        type: 'select',
        description: 'Salesforce operation',
        required: true,
        enum: ['query', 'create', 'update', 'delete', 'upsert', 'search'],
        helpText: 'CRUD operation to perform'
      },
      object_type: {
        type: 'select',
        description: 'Salesforce object',
        required: true,
        enum: ['Account', 'Contact', 'Lead', 'Opportunity', 'Case', 'Task', 'Custom'],
        helpText: 'Type of Salesforce object'
      },
      soql_query: {
        type: 'textarea',
        description: 'SOQL query (for query operation)',
        required: false,
        placeholder: 'SELECT Id, Name FROM Account WHERE Industry = \'Technology\'',
        helpText: 'Salesforce Object Query Language'
      },
      record_id: {
        type: 'string',
        description: 'Record ID (for update/delete)',
        required: false,
        placeholder: '0011234567890ABC',
        helpText: 'Salesforce record ID'
      },
      fields: {
        type: 'json',
        description: 'Field values (JSON)',
        required: false,
        placeholder: '{"Name": "Acme Corp", "Industry": "Technology"}',
        helpText: 'Fields to create/update'
      },
      external_id_field: {
        type: 'string',
        description: 'External ID field (for upsert)',
        required: false,
        placeholder: 'External_ID__c',
        helpText: 'Field to use for upsert matching'
      },
      limit: {
        type: 'select',
        description: 'Query limit',
        required: false,
        default: '100',
        enum: ['10', '50', '100', '500', '1000'],
        helpText: 'Maximum records to return'
      }
    },
    credentials: {
      instance_url: {
        type: 'string',
        description: 'Salesforce Instance URL',
        required: true,
        placeholder: 'https://yourinstance.salesforce.com',
        helpText: 'Your Salesforce instance URL'
      },
      access_token: {
        type: 'password',
        description: 'Access Token',
        required: true,
        placeholder: 'OAuth access token',
        helpText: 'OAuth 2.0 access token'
      }
    },
    examples: [
      {
        name: 'Query Accounts',
        description: 'Find accounts by industry',
        config: {
          operation: 'query',
          object_type: 'Account',
          soql_query: 'SELECT Id, Name, Industry FROM Account WHERE Industry = \'Technology\' LIMIT 10'
        }
      },
      {
        name: 'Create Lead',
        description: 'Create new lead',
        config: {
          operation: 'create',
          object_type: 'Lead',
          fields: {
            'FirstName': 'John',
            'LastName': 'Doe',
            'Company': 'Acme Corp',
            'Email': 'john@acme.com'
          }
        }
      }
    ],
    docs_link: 'https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/'
  },

  hubspot: {
    id: 'hubspot',
    name: 'HubSpot',
    category: 'crm',
    description: 'Manage HubSpot CRM data',
    icon: '🧲',
    bg_color: '#FF7A59',
    params: {
      operation: {
        type: 'select',
        description: 'HubSpot operation',
        required: true,
        enum: ['get_contact', 'create_contact', 'update_contact', 'search_contacts', 'get_company', 'create_deal'],
        helpText: 'CRM operation to perform'
      },
      contact_id: {
        type: 'string',
        description: 'Contact ID',
        required: false,
        placeholder: '12345',
        helpText: 'HubSpot contact ID'
      },
      email: {
        type: 'string',
        description: 'Email address',
        required: false,
        placeholder: 'contact@example.com',
        helpText: 'Contact email for lookup'
      },
      properties: {
        type: 'json',
        description: 'Contact properties (JSON)',
        required: false,
        placeholder: '{"firstname": "John", "lastname": "Doe"}',
        helpText: 'Properties to set'
      },
      search_query: {
        type: 'string',
        description: 'Search query',
        required: false,
        placeholder: 'company:Acme',
        helpText: 'Search criteria'
      },
      limit: {
        type: 'select',
        description: 'Results limit',
        required: false,
        default: '100',
        enum: ['10', '50', '100', '500'],
        helpText: 'Maximum results'
      }
    },
    credentials: {
      api_key: {
        type: 'password',
        description: 'HubSpot API Key',
        required: true,
        placeholder: 'pat-na1-...',
        helpText: 'Private app access token'
      }
    },
    examples: [
      {
        name: 'Create Contact',
        description: 'Add new contact',
        config: {
          operation: 'create_contact',
          properties: {
            'email': 'john@example.com',
            'firstname': 'John',
            'lastname': 'Doe',
            'company': 'Acme Corp'
          }
        }
      },
      {
        name: 'Search Contacts',
        description: 'Find contacts by company',
        config: {
          operation: 'search_contacts',
          search_query: 'company:Acme',
          limit: '50'
        }
      }
    ],
    docs_link: 'https://developers.hubspot.com/docs/api/overview'
  },

  // ==================== Marketing Tools ====================
  
  mailchimp: {
    id: 'mailchimp',
    name: 'Mailchimp',
    category: 'marketing',
    description: 'Manage email marketing campaigns',
    icon: '📬',
    bg_color: '#FFE01B',
    params: {
      operation: {
        type: 'select',
        description: 'Mailchimp operation',
        required: true,
        enum: ['add_subscriber', 'update_subscriber', 'remove_subscriber', 'create_campaign', 'send_campaign', 'get_lists'],
        helpText: 'Marketing operation'
      },
      list_id: {
        type: 'string',
        description: 'Audience/List ID',
        required: false,
        placeholder: 'abc123def456',
        helpText: 'Mailchimp audience ID'
      },
      email: {
        type: 'string',
        description: 'Subscriber email',
        required: false,
        placeholder: 'subscriber@example.com',
        helpText: 'Email address'
      },
      merge_fields: {
        type: 'json',
        description: 'Merge fields (JSON)',
        required: false,
        placeholder: '{"FNAME": "John", "LNAME": "Doe"}',
        helpText: 'Subscriber data fields'
      },
      status: {
        type: 'select',
        description: 'Subscription status',
        required: false,
        default: 'subscribed',
        enum: ['subscribed', 'unsubscribed', 'cleaned', 'pending'],
        helpText: 'Subscriber status'
      },
      tags: {
        type: 'array',
        description: 'Tags (comma-separated)',
        required: false,
        placeholder: 'customer, vip',
        helpText: 'Tags to apply'
      },
      double_optin: {
        type: 'boolean',
        description: 'Require double opt-in',
        required: false,
        default: false,
        helpText: 'Send confirmation email'
      }
    },
    credentials: {
      api_key: {
        type: 'password',
        description: 'Mailchimp API Key',
        required: true,
        placeholder: 'abc123...-us1',
        helpText: 'API key from Mailchimp account'
      }
    },
    examples: [
      {
        name: 'Add Subscriber',
        description: 'Add contact to list',
        config: {
          operation: 'add_subscriber',
          list_id: 'your-list-id',
          email: 'new@example.com',
          merge_fields: { 'FNAME': 'John', 'LNAME': 'Doe' },
          status: 'subscribed'
        }
      }
    ],
    docs_link: 'https://mailchimp.com/developer/marketing/api/'
  },

  sendgrid: {
    id: 'sendgrid',
    name: 'SendGrid',
    category: 'marketing',
    description: 'Send transactional and marketing emails',
    icon: '✉️',
    bg_color: '#1A82E2',
    params: {
      operation: {
        type: 'select',
        description: 'SendGrid operation',
        required: true,
        enum: ['send_email', 'send_template', 'add_contact', 'create_list', 'get_stats'],
        helpText: 'Email operation'
      },
      to_email: {
        type: 'string',
        description: 'Recipient email',
        required: false,
        placeholder: 'recipient@example.com',
        helpText: 'Email recipient'
      },
      from_email: {
        type: 'string',
        description: 'Sender email',
        required: false,
        placeholder: 'sender@yourdomain.com',
        helpText: 'Verified sender email'
      },
      subject: {
        type: 'string',
        description: 'Email subject',
        required: false,
        placeholder: 'Welcome to our service',
        helpText: 'Subject line'
      },
      content: {
        type: 'textarea',
        description: 'Email content',
        required: false,
        placeholder: 'Email body...',
        helpText: 'HTML or plain text content'
      },
      content_type: {
        type: 'select',
        description: 'Content type',
        required: false,
        default: 'text/html',
        enum: ['text/plain', 'text/html'],
        helpText: 'Email content format'
      },
      template_id: {
        type: 'string',
        description: 'Template ID (for send_template)',
        required: false,
        placeholder: 'd-abc123...',
        helpText: 'Dynamic template ID'
      },
      template_data: {
        type: 'json',
        description: 'Template variables (JSON)',
        required: false,
        placeholder: '{"name": "John", "code": "ABC123"}',
        helpText: 'Data for template substitution'
      }
    },
    credentials: {
      api_key: {
        type: 'password',
        description: 'SendGrid API Key',
        required: true,
        placeholder: 'SG.abc123...',
        helpText: 'API key from SendGrid'
      }
    },
    examples: [
      {
        name: 'Send Email',
        description: 'Send simple email',
        config: {
          operation: 'send_email',
          to_email: 'recipient@example.com',
          from_email: 'sender@yourdomain.com',
          subject: 'Hello!',
          content: '<p>Welcome to our service!</p>',
          content_type: 'text/html'
        }
      },
      {
        name: 'Send Template',
        description: 'Send using template',
        config: {
          operation: 'send_template',
          to_email: 'recipient@example.com',
          from_email: 'sender@yourdomain.com',
          template_id: 'd-abc123',
          template_data: { 'name': 'John', 'code': 'WELCOME10' }
        }
      }
    ],
    docs_link: 'https://docs.sendgrid.com/api-reference'
  },

  // ==================== Analytics Tools ====================
  
  google_analytics: {
    id: 'google_analytics',
    name: 'Google Analytics',
    category: 'analytics',
    description: 'Query Google Analytics data',
    icon: '📈',
    bg_color: '#E37400',
    params: {
      operation: {
        type: 'select',
        description: 'Analytics operation',
        required: true,
        enum: ['run_report', 'get_realtime', 'get_metadata'],
        helpText: 'Type of analytics query'
      },
      property_id: {
        type: 'string',
        description: 'GA4 Property ID',
        required: true,
        placeholder: '123456789',
        helpText: 'Google Analytics 4 property ID'
      },
      date_range: {
        type: 'select',
        description: 'Date range',
        required: false,
        default: 'last_7_days',
        enum: ['today', 'yesterday', 'last_7_days', 'last_30_days', 'last_90_days', 'custom'],
        helpText: 'Time period for data'
      },
      start_date: {
        type: 'string',
        description: 'Start date (for custom range)',
        required: false,
        placeholder: '2024-01-01',
        helpText: 'YYYY-MM-DD format'
      },
      end_date: {
        type: 'string',
        description: 'End date (for custom range)',
        required: false,
        placeholder: '2024-01-31',
        helpText: 'YYYY-MM-DD format'
      },
      metrics: {
        type: 'array',
        description: 'Metrics (comma-separated)',
        required: false,
        default: 'sessions,users',
        placeholder: 'sessions, users, pageviews',
        helpText: 'Metrics to retrieve'
      },
      dimensions: {
        type: 'array',
        description: 'Dimensions (comma-separated)',
        required: false,
        placeholder: 'country, city, deviceCategory',
        helpText: 'Dimensions to group by'
      },
      limit: {
        type: 'select',
        description: 'Row limit',
        required: false,
        default: '100',
        enum: ['10', '50', '100', '500', '1000'],
        helpText: 'Maximum rows to return'
      }
    },
    credentials: {
      service_account_json: {
        type: 'password',
        description: 'Service Account JSON',
        required: true,
        placeholder: '{"type": "service_account", ...}',
        helpText: 'Service account credentials JSON'
      }
    },
    examples: [
      {
        name: 'Weekly Traffic',
        description: 'Get last 7 days traffic',
        config: {
          operation: 'run_report',
          property_id: '123456789',
          date_range: 'last_7_days',
          metrics: ['sessions', 'users', 'pageviews'],
          dimensions: ['date']
        }
      }
    ],
    docs_link: 'https://developers.google.com/analytics/devguides/reporting/data/v1'
  },

  // ==================== Storage Tools ====================
  
  aws_s3: {
    id: 'aws_s3',
    name: 'AWS S3',
    category: 'storage',
    description: 'Store and retrieve files from Amazon S3',
    icon: '☁️',
    bg_color: '#FF9900',
    params: {
      operation: {
        type: 'select',
        description: 'S3 operation',
        required: true,
        enum: ['upload', 'download', 'list', 'delete', 'copy', 'get_url'],
        helpText: 'File operation to perform'
      },
      bucket: {
        type: 'string',
        description: 'S3 bucket name',
        required: true,
        placeholder: 'my-bucket',
        helpText: 'Name of the S3 bucket'
      },
      key: {
        type: 'string',
        description: 'Object key (path)',
        required: false,
        placeholder: 'folder/file.txt',
        helpText: 'Path to file in bucket'
      },
      file_content: {
        type: 'textarea',
        description: 'File content (for upload)',
        required: false,
        placeholder: 'File content...',
        helpText: 'Data to upload'
      },
      content_type: {
        type: 'select',
        description: 'Content type',
        required: false,
        default: 'application/octet-stream',
        enum: ['text/plain', 'application/json', 'image/jpeg', 'image/png', 'application/pdf', 'application/octet-stream'],
        helpText: 'MIME type of file'
      },
      acl: {
        type: 'select',
        description: 'Access control',
        required: false,
        default: 'private',
        enum: ['private', 'public-read', 'public-read-write', 'authenticated-read'],
        helpText: 'File access permissions'
      },
      prefix: {
        type: 'string',
        description: 'Prefix filter (for list)',
        required: false,
        placeholder: 'folder/',
        helpText: 'Filter objects by prefix'
      },
      max_keys: {
        type: 'select',
        description: 'Max objects (for list)',
        required: false,
        default: '100',
        enum: ['10', '50', '100', '500', '1000'],
        helpText: 'Maximum objects to list'
      },
      expiration: {
        type: 'select',
        description: 'URL expiration (for get_url)',
        required: false,
        default: '3600',
        enum: ['300', '900', '3600', '86400'],
        helpText: 'Presigned URL expiration in seconds'
      }
    },
    credentials: {
      aws_access_key_id: {
        type: 'string',
        description: 'AWS Access Key ID',
        required: true,
        placeholder: 'AKIA...',
        helpText: 'AWS access key'
      },
      aws_secret_access_key: {
        type: 'password',
        description: 'AWS Secret Access Key',
        required: true,
        placeholder: 'Secret key',
        helpText: 'AWS secret key'
      },
      region: {
        type: 'select',
        description: 'AWS Region',
        required: false,
        default: 'us-east-1',
        enum: ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-northeast-1', 'ap-northeast-2'],
        helpText: 'AWS region'
      }
    },
    examples: [
      {
        name: 'Upload File',
        description: 'Upload text file to S3',
        config: {
          operation: 'upload',
          bucket: 'my-bucket',
          key: 'data/file.txt',
          file_content: 'Hello World',
          content_type: 'text/plain',
          acl: 'private'
        }
      },
      {
        name: 'List Files',
        description: 'List objects in bucket',
        config: {
          operation: 'list',
          bucket: 'my-bucket',
          prefix: 'data/',
          max_keys: '100'
        }
      }
    ],
    docs_link: 'https://docs.aws.amazon.com/s3/'
  },

  google_drive: {
    id: 'google_drive',
    name: 'Google Drive',
    category: 'storage',
    description: 'Manage files in Google Drive',
    icon: '📁',
    bg_color: '#4285F4',
    params: {
      operation: {
        type: 'select',
        description: 'Drive operation',
        required: true,
        enum: ['upload', 'download', 'list', 'delete', 'share', 'create_folder', 'search'],
        helpText: 'File operation'
      },
      file_id: {
        type: 'string',
        description: 'File ID',
        required: false,
        placeholder: '1abc...xyz',
        helpText: 'Google Drive file ID'
      },
      file_name: {
        type: 'string',
        description: 'File name',
        required: false,
        placeholder: 'document.pdf',
        helpText: 'Name of the file'
      },
      file_content: {
        type: 'textarea',
        description: 'File content (for upload)',
        required: false,
        placeholder: 'File content...',
        helpText: 'Data to upload'
      },
      mime_type: {
        type: 'select',
        description: 'MIME type',
        required: false,
        default: 'application/octet-stream',
        enum: ['text/plain', 'application/pdf', 'image/jpeg', 'image/png', 'application/vnd.google-apps.document', 'application/vnd.google-apps.spreadsheet'],
        helpText: 'File type'
      },
      parent_folder_id: {
        type: 'string',
        description: 'Parent folder ID',
        required: false,
        placeholder: 'folder-id',
        helpText: 'Where to place the file'
      },
      search_query: {
        type: 'string',
        description: 'Search query',
        required: false,
        placeholder: 'name contains \'report\'',
        helpText: 'Drive search query'
      },
      share_with: {
        type: 'string',
        description: 'Email to share with',
        required: false,
        placeholder: 'user@example.com',
        helpText: 'Share file with user'
      },
      role: {
        type: 'select',
        description: 'Share role',
        required: false,
        default: 'reader',
        enum: ['reader', 'writer', 'commenter', 'owner'],
        helpText: 'Permission level'
      }
    },
    credentials: {
      access_token: {
        type: 'password',
        description: 'Google OAuth Access Token',
        required: true,
        placeholder: 'ya29...',
        helpText: 'OAuth 2.0 access token'
      }
    },
    examples: [
      {
        name: 'Upload File',
        description: 'Upload text file',
        config: {
          operation: 'upload',
          file_name: 'notes.txt',
          file_content: 'My notes...',
          mime_type: 'text/plain'
        }
      },
      {
        name: 'Search Files',
        description: 'Find files by name',
        config: {
          operation: 'search',
          search_query: 'name contains \'report\' and mimeType = \'application/pdf\''
        }
      }
    ],
    docs_link: 'https://developers.google.com/drive/api/v3/reference'
  },

  // ==================== Webhook Tools ====================
  
  webhook_trigger: {
    id: 'webhook_trigger',
    name: 'Webhook Trigger',
    category: 'webhook',
    description: 'Receive data via webhook',
    icon: '🪝',
    bg_color: '#8E44AD',
    params: {
      method: {
        type: 'select',
        description: 'HTTP method',
        required: false,
        default: 'POST',
        enum: ['GET', 'POST', 'PUT', 'PATCH'],
        helpText: 'Allowed HTTP methods'
      },
      path: {
        type: 'string',
        description: 'Webhook path',
        required: false,
        placeholder: '/webhook/my-workflow',
        helpText: 'Custom webhook URL path'
      },
      authentication: {
        type: 'select',
        description: 'Authentication type',
        required: false,
        default: 'none',
        enum: ['none', 'basic', 'bearer', 'api_key', 'hmac'],
        helpText: 'How to authenticate requests'
      },
      response_mode: {
        type: 'select',
        description: 'Response mode',
        required: false,
        default: 'immediate',
        enum: ['immediate', 'wait_for_completion', 'async'],
        helpText: 'When to respond to webhook'
      },
      response_data: {
        type: 'json',
        description: 'Response data (JSON)',
        required: false,
        placeholder: '{"status": "received"}',
        helpText: 'Data to return in response'
      }
    },
    examples: [
      {
        name: 'Simple Webhook',
        description: 'Basic POST webhook',
        config: {
          method: 'POST',
          authentication: 'none',
          response_mode: 'immediate'
        }
      },
      {
        name: 'Secure Webhook',
        description: 'Webhook with API key',
        config: {
          method: 'POST',
          authentication: 'api_key',
          response_mode: 'wait_for_completion'
        }
      }
    ]
  },

  webhook_call: {
    id: 'webhook_call',
    name: 'Webhook Call',
    category: 'webhook',
    description: 'Send data to external webhook',
    icon: '📤',
    bg_color: '#2ECC71',
    params: {
      url: {
        type: 'string',
        description: 'Webhook URL',
        required: true,
        placeholder: 'https://example.com/webhook',
        helpText: 'Target webhook endpoint'
      },
      method: {
        type: 'select',
        description: 'HTTP method',
        required: false,
        default: 'POST',
        enum: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
        helpText: 'HTTP request method'
      },
      headers: {
        type: 'json',
        description: 'HTTP headers (JSON)',
        required: false,
        placeholder: '{"Content-Type": "application/json"}',
        helpText: 'Custom headers'
      },
      body: {
        type: 'json',
        description: 'Request body (JSON)',
        required: false,
        placeholder: '{"event": "user.created", "data": {...}}',
        helpText: 'Payload to send'
      },
      timeout: {
        type: 'select',
        description: 'Request timeout',
        required: false,
        default: '30',
        enum: ['5', '10', '30', '60', '120'],
        helpText: 'Timeout in seconds'
      },
      retry_on_failure: {
        type: 'boolean',
        description: 'Retry on failure',
        required: false,
        default: true,
        helpText: 'Automatically retry failed requests'
      },
      max_retries: {
        type: 'select',
        description: 'Maximum retries',
        required: false,
        default: '3',
        enum: ['1', '3', '5', '10'],
        helpText: 'Number of retry attempts'
      }
    },
    examples: [
      {
        name: 'Simple POST',
        description: 'Send JSON data',
        config: {
          url: 'https://example.com/webhook',
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: { 'event': 'workflow.completed', 'status': 'success' }
        }
      }
    ]
  },

  // ==================== Conditional Tools ====================
  
  if_condition: {
    id: 'if_condition',
    name: 'If Condition',
    category: 'control',
    description: 'Conditional branching based on logic',
    icon: '🔀',
    bg_color: '#F39C12',
    params: {
      condition_type: {
        type: 'select',
        description: 'Condition type',
        required: true,
        enum: ['simple', 'expression', 'multiple'],
        helpText: 'Type of condition check'
      },
      field: {
        type: 'string',
        description: 'Field to check',
        required: false,
        placeholder: 'input.status',
        helpText: 'Field path to evaluate'
      },
      operator: {
        type: 'select',
        description: 'Comparison operator',
        required: false,
        default: 'equals',
        enum: ['equals', 'not_equals', 'greater_than', 'less_than', 'contains', 'starts_with', 'ends_with', 'is_empty', 'is_not_empty', 'regex_match'],
        helpText: 'How to compare values'
      },
      value: {
        type: 'string',
        description: 'Value to compare',
        required: false,
        placeholder: 'active',
        helpText: 'Expected value'
      },
      expression: {
        type: 'code',
        description: 'Custom expression (Python)',
        required: false,
        placeholder: 'input["age"] > 18 and input["verified"] == True',
        language: 'python',
        helpText: 'Boolean expression'
      },
      case_sensitive: {
        type: 'boolean',
        description: 'Case sensitive',
        required: false,
        default: true,
        helpText: 'Match case for string comparisons'
      }
    },
    examples: [
      {
        name: 'Simple Check',
        description: 'Check if status is active',
        config: {
          condition_type: 'simple',
          field: 'input.status',
          operator: 'equals',
          value: 'active'
        }
      },
      {
        name: 'Complex Expression',
        description: 'Multiple conditions',
        config: {
          condition_type: 'expression',
          expression: 'input["age"] > 18 and input["country"] == "US"'
        }
      }
    ]
  },

  switch_case: {
    id: 'switch_case',
    name: 'Switch Case',
    category: 'control',
    description: 'Multi-way branching',
    icon: '🔄',
    bg_color: '#E67E22',
    params: {
      input_value: {
        type: 'string',
        description: 'Value to switch on',
        required: true,
        placeholder: 'input.type',
        helpText: 'Field to evaluate'
      },
      cases: {
        type: 'json',
        description: 'Cases (JSON array)',
        required: true,
        placeholder: '[{"value": "A", "output": "Route A"}, {"value": "B", "output": "Route B"}]',
        helpText: 'Array of case conditions'
      },
      default_output: {
        type: 'string',
        description: 'Default output',
        required: false,
        placeholder: 'default',
        helpText: 'Output if no case matches'
      },
      case_sensitive: {
        type: 'boolean',
        description: 'Case sensitive',
        required: false,
        default: true,
        helpText: 'Match case for comparisons'
      }
    },
    examples: [
      {
        name: 'Route by Type',
        description: 'Branch based on type field',
        config: {
          input_value: 'input.type',
          cases: [
            { 'value': 'email', 'output': 'email_route' },
            { 'value': 'sms', 'output': 'sms_route' },
            { 'value': 'push', 'output': 'push_route' }
          ],
          default_output: 'unknown_route'
        }
      }
    ]
  }
};

// Helper function to get tool config by ID
export function getToolConfig(toolId: string): ToolConfigSchema | undefined {
  return TOOL_CONFIG_REGISTRY[toolId];
}

// Helper function to get all tools by category
export function getToolsByCategory(category: string): ToolConfigSchema[] {
  return Object.values(TOOL_CONFIG_REGISTRY).filter(
    tool => tool.category === category
  );
}

// Helper function to get all categories
export function getAllCategories(): string[] {
  const categories = new Set(
    Object.values(TOOL_CONFIG_REGISTRY).map(tool => tool.category)
  );
  return Array.from(categories).sort();
}

// Helper function to search tools
export function searchTools(query: string): ToolConfigSchema[] {
  const lowerQuery = query.toLowerCase();
  return Object.values(TOOL_CONFIG_REGISTRY).filter(
    tool =>
      tool.name.toLowerCase().includes(lowerQuery) ||
      tool.description.toLowerCase().includes(lowerQuery) ||
      tool.category.toLowerCase().includes(lowerQuery)
  );
}
