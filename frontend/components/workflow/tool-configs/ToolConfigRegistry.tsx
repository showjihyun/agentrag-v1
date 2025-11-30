/**
 * Tool Configuration Registry
 * Maps tool IDs and node types to their configuration components
 * Inspired by n8n, Make.com, and Zapier
 */

import { lazy } from 'react';

// Lazy load tool config components
const OpenAIChatConfig = lazy(() => import('./OpenAIChatConfig'));
const SlackConfig = lazy(() => import('./SlackConfig'));
const GmailConfig = lazy(() => import('./GmailConfig'));
const HttpRequestConfig = lazy(() => import('./HttpRequestConfig'));
const VectorSearchConfig = lazy(() => import('./VectorSearchConfig'));
const PythonCodeConfig = lazy(() => import('./PythonCodeConfig'));
const WebhookConfig = lazy(() => import('./WebhookConfig'));
const ConditionConfig = lazy(() => import('./ConditionConfig'));
const ScheduleTriggerConfig = lazy(() => import('./ScheduleTriggerConfig'));
const CalculatorConfig = lazy(() => import('./CalculatorConfig'));
const CSVParserConfig = lazy(() => import('./CSVParserConfig'));
const JSONTransformConfig = lazy(() => import('./JSONTransformConfig'));
const PostgresConfig = lazy(() => import('./PostgresConfig'));
// Control Flow configs
const LoopConfig = lazy(() => import('./LoopConfig'));
const ParallelConfig = lazy(() => import('./ParallelConfig'));
const DelayConfig = lazy(() => import('./DelayConfig'));
const SwitchConfig = lazy(() => import('./SwitchConfig'));
const MergeConfig = lazy(() => import('./MergeConfig'));
const FilterConfig = lazy(() => import('./FilterConfig'));
const TransformConfig = lazy(() => import('./TransformConfig'));
const TryCatchConfig = lazy(() => import('./TryCatchConfig'));
const HumanApprovalConfig = lazy(() => import('./HumanApprovalConfig'));
// Trigger configs
const ManualTriggerConfig = lazy(() => import('./ManualTriggerConfig'));
const FileTriggerConfig = lazy(() => import('./FileTriggerConfig'));
const SlackTriggerConfig = lazy(() => import('./SlackTriggerConfig'));
const EmailTriggerConfig = lazy(() => import('./EmailTriggerConfig'));
const WebhookTriggerConfig = lazy(() => import('./WebhookTriggerConfig'));
// Block configs
const TextBlockConfig = lazy(() => import('./TextBlockConfig'));
const DatabaseBlockConfig = lazy(() => import('./DatabaseBlockConfig'));
const AIBlockConfig = lazy(() => import('./AIBlockConfig'));
// New tool configs (Search, Data, S3, SendGrid)
const SearchToolsConfig = lazy(() => import('./SearchToolsConfig'));
const DataToolsConfig = lazy(() => import('./DataToolsConfig'));
const S3Config = lazy(() => import('./S3Config'));
const SendGridConfig = lazy(() => import('./SendGridConfig'));
// Enhanced Code Block (Monaco Editor)
const EnhancedCodeConfig = lazy(() => import('./EnhancedCodeConfig'));
// AI Agent config wrapper (adapts AIAgentConfig props to ToolConfigProps)
const AIAgentConfigWrapper = lazy(() => Promise.resolve({
  default: ({ data, onChange }: ToolConfigProps) => {
    const React = require('react');
    const { AIAgentConfig } = require('@/components/agent-builder/tool-configs/AIAgentConfig');
    return React.createElement(AIAgentConfig, {
      initialConfig: data?.config || {},
      initialCredentials: data?.credentials || {},
      onSave: (config: any, credentials: any) => onChange({ config, credentials }),
      onCancel: () => {},
    });
  }
}));

export interface ToolConfigProps {
  data: any;
  onChange: (updates: any) => void;
  onTest?: () => void;
}

export const TOOL_CONFIG_REGISTRY: Record<string, React.ComponentType<ToolConfigProps>> = {
  // AI Tools
  'openai_chat': OpenAIChatConfig,
  'anthropic_claude': OpenAIChatConfig,
  'google_gemini': OpenAIChatConfig,
  'mistral_ai': OpenAIChatConfig,
  'cohere': OpenAIChatConfig,
  'ai_agent': AIAgentConfigWrapper,
  
  // Communication
  'slack': SlackConfig,
  'gmail': GmailConfig,
  'discord': SlackConfig,
  'telegram': SlackConfig,
  'sendgrid': SendGridConfig,
  
  // API & Integration
  'http_request': HttpRequestConfig,
  'webhook': WebhookConfig,
  'graphql': HttpRequestConfig,
  
  // Search Tools - Now using dedicated SearchToolsConfig
  'vector_search': VectorSearchConfig,
  'tavily_search': SearchToolsConfig,
  'serper_search': SearchToolsConfig,
  'exa_search': SearchToolsConfig,
  'wikipedia_search': SearchToolsConfig,
  'arxiv_search': SearchToolsConfig,
  'google_custom_search': SearchToolsConfig,
  'bing_search': SearchToolsConfig,
  'duckduckgo_search': SearchToolsConfig,
  'youtube_search': SearchToolsConfig,
  
  // Data & Database - Now using dedicated DataToolsConfig
  'postgres': PostgresConfig,
  'postgresql_query': PostgresConfig,
  'mysql_query': PostgresConfig,
  'mongodb_insert': DataToolsConfig,
  'supabase_query': DataToolsConfig,
  'redis_set': DataToolsConfig,
  'elasticsearch_index': DataToolsConfig,
  'bigquery_query': DataToolsConfig,
  'csv_parser': CSVParserConfig,
  'json_transform': JSONTransformConfig,
  
  // Vector DB - Now using dedicated DataToolsConfig
  'pinecone_upsert': DataToolsConfig,
  'qdrant_insert': DataToolsConfig,
  
  // Storage - Now using dedicated S3Config
  's3_upload': S3Config,
  's3_download': S3Config,
  's3_delete': S3Config,
  's3_list': S3Config,
  
  // Code & Calculation
  'python_code': EnhancedCodeConfig,
  'javascript_code': EnhancedCodeConfig,
  'typescript_code': EnhancedCodeConfig,
  'sql_code': EnhancedCodeConfig,
  'code': EnhancedCodeConfig,
  'enhanced_code': EnhancedCodeConfig,
  'calculator': CalculatorConfig,
  
  // Control Flow
  'condition': ConditionConfig,
  'switch': SwitchConfig,
  'loop': LoopConfig,
  'parallel': ParallelConfig,
  'delay': DelayConfig,
  'merge': MergeConfig,
  'filter': FilterConfig,
  'transform': TransformConfig,
  'try_catch': TryCatchConfig,
  'human_approval': HumanApprovalConfig,
  
  // Triggers
  'schedule_trigger': ScheduleTriggerConfig,
  'manual_trigger': ManualTriggerConfig,
  'email_trigger': EmailTriggerConfig,
  'file_trigger': FileTriggerConfig,
  'slack_trigger': SlackTriggerConfig,
  'webhook_trigger': WebhookTriggerConfig,
  
  // Blocks
  'text_block': TextBlockConfig,
  'code_block': EnhancedCodeConfig,
  'http_block': HttpRequestConfig,
  'database_block': DatabaseBlockConfig,
  'transform_block': TransformConfig,
  'ai_block': AIBlockConfig,
};

export function getToolConfig(toolId: string) {
  return TOOL_CONFIG_REGISTRY[toolId];
}
