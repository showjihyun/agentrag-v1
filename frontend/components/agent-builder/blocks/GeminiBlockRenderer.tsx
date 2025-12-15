'use client';

import React from 'react';
import GeminiVisionBlock from './GeminiVisionBlock';
import GeminiAudioBlock from './GeminiAudioBlock';
import GeminiFusionBlock from './GeminiFusionBlock';
import GeminiVideoBlock from './GeminiVideoBlock';
import GeminiAutoOptimizerBlock from './GeminiAutoOptimizerBlock';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Eye, Mic, FileText, Sparkles, AlertCircle, Video, Wand2 } from 'lucide-react';

interface GeminiBlockRendererProps {
  blockType: string;
  blockId: string;
  config?: Record<string, any>;
  onConfigChange?: (config: any) => void;
  onExecute?: (result: any) => void;
  isExecuting?: boolean;
  isWorkflowMode?: boolean; // Compact mode for workflow canvas
}

export default function GeminiBlockRenderer({
  blockType,
  blockId,
  config = {},
  onConfigChange,
  onExecute,
  isExecuting = false,
  isWorkflowMode = false
}: GeminiBlockRendererProps) {
  
  // Render compact version for workflow canvas
  if (isWorkflowMode) {
    return (
      <GeminiWorkflowNode
        blockType={blockType}
        blockId={blockId}
        config={config}
        onConfigChange={onConfigChange}
        onExecute={onExecute}
        isExecuting={isExecuting}
      />
    );
  }

  // Render full block components for standalone use
  switch (blockType) {
    case 'gemini_vision':
      return (
        <GeminiVisionBlock
          blockId={blockId}
          config={config}
          onConfigChange={onConfigChange}
          onExecute={onExecute}
          isExecuting={isExecuting}
        />
      );
      
    case 'gemini_audio':
      return (
        <GeminiAudioBlock
          blockId={blockId}
          config={config}
          onConfigChange={onConfigChange}
          onExecute={onExecute}
          isExecuting={isExecuting}
        />
      );
      
    case 'gemini_fusion':
      return (
        <GeminiFusionBlock
          blockId={blockId}
          config={config}
          onConfigChange={onConfigChange}
          onExecute={onExecute}
          isExecuting={isExecuting}
        />
      );
      
    case 'gemini_video':
      return (
        <GeminiVideoBlock
          blockId={blockId}
          config={config}
          onConfigChange={onConfigChange}
          onExecute={onExecute}
          isExecuting={isExecuting}
        />
      );
      
    case 'gemini_auto_optimizer':
      return (
        <GeminiAutoOptimizerBlock
          blockId={blockId}
          config={config}
          onConfigChange={onConfigChange}
          onExecute={onExecute}
          isExecuting={isExecuting}
        />
      );
      
    case 'gemini_document':
      return (
        <GeminiDocumentBlock
          blockId={blockId}
          config={config}
          onConfigChange={onConfigChange}
          onExecute={onExecute}
          isExecuting={isExecuting}
        />
      );
      
    case 'gemini_multimodal':
      return (
        <GeminiMultiModalBlock
          blockId={blockId}
          config={config}
          onConfigChange={onConfigChange}
          onExecute={onExecute}
          isExecuting={isExecuting}
        />
      );
      
    default:
      return (
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-5 w-5" />
              Unknown Block Type
            </CardTitle>
            <CardDescription>
              Block type "{blockType}" is not recognized
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Please check the block configuration or contact support.
            </p>
          </CardContent>
        </Card>
      );
  }
}

// Compact workflow node component
function GeminiWorkflowNode({
  blockType,
  blockId,
  config,
  onConfigChange,
  onExecute,
  isExecuting
}: Omit<GeminiBlockRendererProps, 'isWorkflowMode'>) {
  
  const getBlockInfo = (type: string) => {
    switch (type) {
      case 'gemini_vision':
        return {
          name: 'Gemini Vision',
          icon: Eye,
          color: 'purple',
          description: 'Image analysis'
        };
      case 'gemini_audio':
        return {
          name: 'Gemini Audio',
          icon: Mic,
          color: 'blue',
          description: 'Audio processing'
        };
      case 'gemini_video':
        return {
          name: 'Gemini Video',
          icon: Video,
          color: 'red',
          description: 'Video analysis'
        };
      case 'gemini_auto_optimizer':
        return {
          name: 'Auto-optimizer',
          icon: Wand2,
          color: 'purple',
          description: 'AI optimization'
        };
      case 'gemini_fusion':
        return {
          name: 'Gemini Fusion',
          icon: Sparkles,
          color: 'purple',
          description: 'MultiModal fusion'
        };
      case 'gemini_document':
        return {
          name: 'Gemini Document',
          icon: FileText,
          color: 'green',
          description: 'Document analysis'
        };
      case 'gemini_multimodal':
        return {
          name: 'Gemini MultiModal',
          icon: Sparkles,
          color: 'orange',
          description: 'Combined processing'
        };
      default:
        return {
          name: 'Unknown',
          icon: AlertCircle,
          color: 'gray',
          description: 'Unknown block'
        };
    }
  };

  const blockInfo = getBlockInfo(blockType);
  const Icon = blockInfo.icon;

  return (
    <div className={`
      relative p-3 rounded-lg border-2 min-w-[180px] transition-all
      ${isExecuting ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' : 'border-gray-300 bg-white dark:bg-gray-800'}
      hover:shadow-md cursor-pointer
    `}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <div className={`p-1.5 rounded-md bg-${blockInfo.color}-100 dark:bg-${blockInfo.color}-900`}>
          <Icon className={`h-4 w-4 text-${blockInfo.color}-600 dark:text-${blockInfo.color}-400`} />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm truncate">{blockInfo.name}</h4>
          <p className="text-xs text-muted-foreground">{blockInfo.description}</p>
        </div>
        <Badge variant="secondary" className="text-xs">
          <Sparkles className="h-3 w-3 mr-1" />
          AI
        </Badge>
      </div>

      {/* Configuration Summary */}
      {config && Object.keys(config).length > 0 && (
        <div className="text-xs text-muted-foreground mb-2">
          {config.model && (
            <div>Model: {config.model}</div>
          )}
          {config.prompt && (
            <div className="truncate">Prompt: {config.prompt.substring(0, 30)}...</div>
          )}
        </div>
      )}

      {/* Status Indicator */}
      {isExecuting && (
        <div className="absolute top-1 right-1">
          <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse" />
        </div>
      )}

      {/* Input/Output Ports */}
      <div className="flex justify-between items-center mt-2">
        <div className="flex gap-1">
          <div className="h-2 w-2 bg-gray-400 rounded-full" title="Input" />
        </div>
        <div className="flex gap-1">
          <div className="h-2 w-2 bg-gray-400 rounded-full" title="Output" />
        </div>
      </div>
    </div>
  );
}

// Placeholder components for document and multimodal blocks
function GeminiDocumentBlock({
  blockId,
  config = {},
  onConfigChange,
  onExecute,
  isExecuting = false
}: {
  blockId: string;
  config?: Record<string, any>;
  onConfigChange?: (config: any) => void;
  onExecute?: (result: any) => void;
  isExecuting?: boolean;
}) {
  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900">
            <FileText className="h-6 w-6 text-green-600 dark:text-green-400" />
          </div>
          <div>
            <CardTitle className="flex items-center gap-2">
              Gemini Document Analyzer
              <Badge variant="secondary" className="bg-green-100 text-green-700">
                <FileText className="h-3 w-3 mr-1" />
                Document AI
              </Badge>
            </CardTitle>
            <CardDescription>
              Advanced document structure analysis and data extraction
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8 text-muted-foreground">
          <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="font-medium">Document Analysis Block</p>
          <p className="text-sm mt-2">
            This block will analyze document structure and extract structured data
          </p>
          <Badge variant="outline" className="mt-4">
            Coming Soon
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

function GeminiMultiModalBlock({
  blockId,
  config = {},
  onConfigChange,
  onExecute,
  isExecuting = false
}: {
  blockId: string;
  config?: Record<string, any>;
  onConfigChange?: (config: any) => void;
  onExecute?: (result: any) => void;
  isExecuting?: boolean;
}) {
  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-900">
            <Sparkles className="h-6 w-6 text-orange-600 dark:text-orange-400" />
          </div>
          <div>
            <CardTitle className="flex items-center gap-2">
              Gemini MultiModal Processor
              <Badge variant="secondary" className="bg-orange-100 text-orange-700">
                <Sparkles className="h-3 w-3 mr-1" />
                MultiModal AI
              </Badge>
            </CardTitle>
            <CardDescription>
              Combined text, image, audio, and video processing
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8 text-muted-foreground">
          <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="font-medium">Advanced MultiModal Processing</p>
          <p className="text-sm mt-2">
            This block will process multiple types of media simultaneously
          </p>
          <Badge variant="outline" className="mt-4">
            Coming Soon
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}