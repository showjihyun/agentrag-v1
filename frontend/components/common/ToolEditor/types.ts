/**
 * Type definitions for Tool Editor components
 */

export interface ParameterConfig {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object' | 'select' | 'multiselect' | 'json' | 'code' | 'file' | 'color' | 'date' | 'time' | 'datetime' | 'url' | 'email' | 'password' | 'textarea';
  description?: string;
  required?: boolean;
  default?: any;
  enum?: string[];
  min?: number;
  max?: number;
  pattern?: string;
  placeholder?: string;
  items?: ParameterConfig;
  properties?: Record<string, ParameterConfig>;
  validation?: (value: any) => string | null;
  suggestions?: string[] | ((input: string) => Promise<string[]>);
  helpText?: string;
  group?: string;
  order?: number;
  hidden?: boolean;
  disabled?: boolean;
  dependsOn?: string;
  showIf?: (config: Record<string, any>) => boolean;
}

export interface ToolConfig {
  id: string;
  name: string;
  description: string;
  category: string;
  params: Record<string, ParameterConfig>;
  outputs: Record<string, any>;
  icon?: string;
  bg_color?: string;
  docs_link?: string;
  examples?: Array<{
    name: string;
    description: string;
    config: Record<string, any>;
  }>;
  tags?: string[];
  version?: string;
  author?: string;
}

export interface ToolEditorProps {
  tool: ToolConfig;
  initialConfig?: Record<string, any>;
  onSave: (config: Record<string, any>) => void;
  onClose: () => void;
  mode?: 'modal' | 'inline' | 'sidebar';
  showPreview?: boolean;
  showTemplates?: boolean;
  showAdvanced?: boolean;
  autoSave?: boolean;
  autoSaveDelay?: number;
}

export interface ParameterInputProps {
  name: string;
  config: ParameterConfig;
  value: any;
  onChange: (value: any) => void;
  error?: string;
  disabled?: boolean;
  compact?: boolean;
}

export interface ToolPreviewProps {
  tool: ToolConfig;
  config: Record<string, any>;
  showOutput?: boolean;
}

export interface ToolTemplateGalleryProps {
  tool: ToolConfig;
  onSelectTemplate: (config: Record<string, any>) => void;
}

export interface ValidationResult {
  valid: boolean;
  errors: Record<string, string>;
  warnings: Record<string, string>;
}
