// Gemini MultiModal Blocks
export { default as GeminiVisionBlock } from './GeminiVisionBlock';
export { default as GeminiAudioBlock } from './GeminiAudioBlock';
export { default as GeminiFusionBlock } from './GeminiFusionBlock';
export { default as GeminiVideoBlock } from './GeminiVideoBlock';
export { default as GeminiBatchBlock } from './GeminiBatchBlock';
export { default as GeminiAutoOptimizerBlock } from './GeminiAutoOptimizerBlock';
export { default as PredictiveRoutingBlock } from './PredictiveRoutingBlock';
export { default as GeminiBlockRenderer } from './GeminiBlockRenderer';

// Block type definitions
export interface BlockConfig {
  blockId: string;
  config?: Record<string, any>;
  onConfigChange?: (config: any) => void;
  onExecute?: (result: any) => void;
  isExecuting?: boolean;
}

// Block registry for dynamic loading
export const BLOCK_REGISTRY = {
  gemini_vision: GeminiVisionBlock,
  gemini_audio: GeminiAudioBlock,
  gemini_fusion: GeminiFusionBlock,
  gemini_video: GeminiVideoBlock,
  gemini_batch: GeminiBatchBlock,
  gemini_auto_optimizer: GeminiAutoOptimizerBlock,
  predictive_routing: PredictiveRoutingBlock,
} as const;

export type BlockType = keyof typeof BLOCK_REGISTRY;