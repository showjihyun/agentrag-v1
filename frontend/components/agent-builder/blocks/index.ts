// Gemini MultiModal Blocks
import GeminiVisionBlock from './GeminiVisionBlock';
import GeminiAudioBlock from './GeminiAudioBlock';
import GeminiFusionBlock from './GeminiFusionBlock';
import GeminiVideoBlock from './GeminiVideoBlock';
import GeminiBatchBlock from './GeminiBatchBlock';
import GeminiAutoOptimizerBlock from './GeminiAutoOptimizerBlock';
import PredictiveRoutingBlock from './PredictiveRoutingBlock';
import GeminiBlockRenderer from './GeminiBlockRenderer';

// Re-export for external use
export { 
  GeminiVisionBlock,
  GeminiAudioBlock,
  GeminiFusionBlock,
  GeminiVideoBlock,
  GeminiBatchBlock,
  GeminiAutoOptimizerBlock,
  PredictiveRoutingBlock,
  GeminiBlockRenderer
};

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