/**
 * Common Tool Config Components
 * 
 * Centralized exports for reusable tool configuration components
 */

// Header
export { ToolConfigHeader, TOOL_HEADER_PRESETS } from './ToolConfigHeader';
export type { ToolConfigHeaderProps, ToolHeaderPreset } from './ToolConfigHeader';

// Fields
export {
  FieldWrapper,
  TextField,
  NumberField,
  TextareaField,
  SelectField,
  SwitchField,
  KeyValueListField,
  InfoBox,
} from './ToolConfigField';

// Re-export hook
export { useToolConfig, useArrayField } from '@/hooks/useToolConfig';
export type { UseToolConfigOptions, UseToolConfigReturn, ArrayFieldHelpers } from '@/hooks/useToolConfig';
