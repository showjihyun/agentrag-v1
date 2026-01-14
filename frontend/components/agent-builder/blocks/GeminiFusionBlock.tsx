'use client';

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Sparkles, 
  Upload, 
  Plus,
  X,
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Eye,
  Mic,
  FileText,
  Zap,
  Settings,
  Layers,
  GitBranch,
  BarChart3
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

interface TextInput {
  id: string;
  content: string;
  metadata?: Record<string, any>;
}

interface ImageInput {
  id: string;
  file: File;
  preview: string;
  metadata?: Record<string, any>;
}

interface AudioInput {
  id: string;
  file: File;
  metadata?: Record<string, any>;
}

interface FusionResult {
  success: boolean;
  fusion_strategy: string;
  input_modalities: Record<string, number>;
  fusion_result: any;
  processing_time_seconds: number;
  error?: string;
}

interface GeminiFusionBlockProps {
  blockId: string;
  config?: {
    fusion_strategy?: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
    fusion_prompt?: string;
  };
  onConfigChange?: (config: any) => void;
  onExecute?: (result: any) => void;
  isExecuting?: boolean;
}

export default function GeminiFusionBlock({
  blockId,
  config = {},
  onConfigChange,
  onExecute,
  isExecuting = false
}: GeminiFusionBlockProps) {
  const { toast } = useToast();
  
  // Input state
  const [textInputs, setTextInputs] = useState<TextInput[]>([]);
  const [imageInputs, setImageInputs] = useState<ImageInput[]>([]);
  const [audioInputs, setAudioInputs] = useState<AudioInput[]>([]);
  
  // Settings state
  const [fusionPrompt, setFusionPrompt] = useState(config.fusion_prompt || '');
  const [fusionStrategy, setFusionStrategy] = useState(config.fusion_strategy || 'unified');
  const [model, setModel] = useState(config.model || 'gemini-1.5-pro');
  const [temperature, setTemperature] = useState(config.temperature || 0.7);
  const [maxTokens, setMaxTokens] = useState(config.max_tokens || 4096);
  
  // UI state
  const [result, setResult] = useState<FusionResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeTab, setActiveTab] = useState('inputs');

  // Fusion strategy info
  const fusionStrategies = [
    {
      value: 'unified',
      name: 'Unified Processing',
      description: 'Process all modalities at once (Most accurate)',
      icon: Sparkles,
      color: 'text-purple-600',
      estimatedTime: '5-10s'
    },
    {
      value: 'parallel',
      name: 'Parallel Processing',
      description: 'Process each modality in parallel then fuse (Fastest)',
      icon: Zap,
      color: 'text-blue-600',
      estimatedTime: '2-5s'
    },
    {
      value: 'sequential',
      name: 'Sequential Processing',
      description: 'Process sequentially with cumulative context (Most detailed)',
      icon: GitBranch,
      color: 'text-green-600',
      estimatedTime: '8-15s'
    },
    {
      value: 'hierarchical',
      name: 'Hierarchical Processing',
      description: 'Systematic analysis through hierarchical fusion (Most systematic)',
      icon: Layers,
      color: 'text-orange-600',
      estimatedTime: '6-12s'
    }
  ];

  // Prompt templates
  const promptTemplates = [
    {
      name: 'Comprehensive Analysis',
      prompt: 'Synthesize all provided information to derive key insights and conclusions.',
      icon: '🔍'
    },
    {
      name: 'Comparative Analysis',
      prompt: 'Analyze commonalities and differences between inputs and explain their relationships.',
      icon: '⚖️'
    },
    {
      name: 'Summary',
      prompt: 'Summarize all information and organize the key points.',
      icon: '📋'
    },
    {
      name: 'Problem Solving',
      prompt: 'Identify problems based on the provided information and suggest solutions.',
      icon: '💡'
    },
    {
      name: 'Trend Analysis',
      prompt: 'Find patterns and trends in the data and present future outlook.',
      icon: '📈'
    }
  ];

  // Add text input
  const addTextInput = useCallback(() => {
    const newInput: TextInput = {
      id: `text_${Date.now()}`,
      content: '',
      metadata: {}
    };
    setTextInputs(prev => [...prev, newInput]);
  }, []);

  // Remove text input
  const removeTextInput = useCallback((id: string) => {
    setTextInputs(prev => prev.filter(input => input.id !== id));
  }, []);

  // Update text content
  const updateTextInput = useCallback((id: string, content: string) => {
    setTextInputs(prev => prev.map(input => 
      input.id === id ? { ...input, content } : input
    ));
  }, []);

  // Add image file
  const handleImageUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    
    files.forEach(file => {
      if (!file.type.startsWith('image/')) {
        toast({
          title: 'Invalid File Format',
          description: 'Only image files can be uploaded.',
          variant: 'destructive'
        });
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        toast({
          title: 'File Size Exceeded',
          description: 'Image files must be 10MB or less.',
          variant: 'destructive'
        });
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        const newInput: ImageInput = {
          id: `image_${Date.now()}_${Math.random()}`,
          file,
          preview: e.target?.result as string,
          metadata: {
            filename: file.name,
            size: file.size,
            type: file.type
          }
        };
        setImageInputs(prev => [...prev, newInput]);
      };
      reader.readAsDataURL(file);
    });

    // Reset input
    event.target.value = '';
  }, [toast]);

  // Remove image input
  const removeImageInput = useCallback((id: string) => {
    setImageInputs(prev => prev.filter(input => input.id !== id));
  }, []);

  // Add audio file
  const handleAudioUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    
    files.forEach(file => {
      if (!file.type.startsWith('audio/')) {
        toast({
          title: 'Invalid File Format',
          description: 'Only audio files can be uploaded.',
          variant: 'destructive'
        });
        return;
      }

      if (file.size > 25 * 1024 * 1024) {
        toast({
          title: 'File Size Exceeded',
          description: 'Audio files must be 25MB or less.',
          variant: 'destructive'
        });
        return;
      }

      const newInput: AudioInput = {
        id: `audio_${Date.now()}_${Math.random()}`,
        file,
        metadata: {
          filename: file.name,
          size: file.size,
          type: file.type
        }
      };
      setAudioInputs(prev => [...prev, newInput]);
    });

    // Reset input
    event.target.value = '';
  }, [toast]);

  // Remove audio input
  const removeAudioInput = useCallback((id: string) => {
    setAudioInputs(prev => prev.filter(input => input.id !== id));
  }, []);

  // Execute fusion analysis
  const handleFusionAnalysis = useCallback(async () => {
    // Input validation
    const totalInputs = textInputs.length + imageInputs.length + audioInputs.length;
    if (totalInputs < 2) {
      toast({
        title: 'Insufficient Inputs',
        description: 'At least 2 inputs are required.',
        variant: 'destructive'
      });
      return;
    }

    const modalityCount = [textInputs, imageInputs, audioInputs].filter(arr => arr.length > 0).length;
    if (modalityCount < 2) {
      toast({
        title: 'Insufficient Modalities',
        description: 'At least 2 different types of inputs are required.',
        variant: 'destructive'
      });
      return;
    }

    if (!fusionPrompt.trim()) {
      toast({
        title: 'Prompt Required',
        description: 'Please enter a fusion analysis prompt.',
        variant: 'destructive'
      });
      return;
    }

    setIsAnalyzing(true);
    setResult(null);

    try {
      // Create FormData
      const formData = new FormData();
      formData.append('fusion_prompt', fusionPrompt);
      formData.append('fusion_strategy', fusionStrategy);
      formData.append('model', model);
      formData.append('temperature', temperature.toString());

      // Add text inputs
      if (textInputs.length > 0) {
        const combinedText = textInputs.map(input => input.content).join('\n\n');
        formData.append('text_content', combinedText);
      }

      // Add image files
      imageInputs.forEach(input => {
        formData.append('image_files', input.file);
      });

      // Add audio files
      audioInputs.forEach(input => {
        formData.append('audio_files', input.file);
      });

      const response = await fetch('/api/agent-builder/gemini-fusion/upload-and-fuse', {
        method: 'POST',
        body: formData
      });

      const analysisResult = await response.json();
      
      if (analysisResult.success) {
        setResult(analysisResult);
        onExecute?.(analysisResult);
        
        toast({
          title: 'Fusion Analysis Complete',
          description: `Analysis completed in ${analysisResult.processing_time_seconds?.toFixed(2)} seconds.`
        });
      } else {
        throw new Error(analysisResult.error || 'Fusion analysis failed.');
      }
    } catch (error) {
      console.error('Fusion analysis failed:', error);
      const errorResult = {
        success: false,
        error: error instanceof Error ? error.message : 'An unknown error occurred.',
        fusion_strategy: fusionStrategy,
        input_modalities: {
          text: textInputs.length,
          image: imageInputs.length,
          audio: audioInputs.length
        },
        fusion_result: null,
        processing_time_seconds: 0
      };
      setResult(errorResult);
      
      toast({
        title: 'Fusion Analysis Failed',
        description: errorResult.error,
        variant: 'destructive'
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [textInputs, imageInputs, audioInputs, fusionPrompt, fusionStrategy, model, temperature, onExecute, toast]);

  // Config change handler
  const handleConfigChange = useCallback((newConfig: any) => {
    onConfigChange?.({
      ...config,
      ...newConfig
    });
  }, [config, onConfigChange]);

  // Apply prompt template
  const applyTemplate = useCallback((template: typeof promptTemplates[0]) => {
    setFusionPrompt(template.prompt);
    handleConfigChange({ fusion_prompt: template.prompt });
  }, [handleConfigChange]);

  const selectedStrategy = fusionStrategies.find(s => s.value === fusionStrategy);
  const StrategyIcon = selectedStrategy?.icon || Sparkles;

  return (
    <Card className="w-full max-w-6xl">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-r from-purple-100 to-blue-100 dark:from-purple-900 dark:to-blue-900">
            <Sparkles className="h-6 w-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <CardTitle className="flex items-center gap-2">
              Gemini Advanced Fusion
              <Badge variant="secondary" className="bg-gradient-to-r from-purple-100 to-blue-100 text-purple-700">
                <Layers className="h-3 w-3 mr-1" />
                MultiModal AI
              </Badge>
            </CardTitle>
            <CardDescription>
              Analyze multiple types of media simultaneously to generate integrated insights
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="inputs">Input Data</TabsTrigger>
            <TabsTrigger value="settings">Fusion Settings</TabsTrigger>
            <TabsTrigger value="results">Analysis Results</TabsTrigger>
          </TabsList>

          <TabsContent value="inputs" className="space-y-6">
            {/* Text Input Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Text Input
                </h3>
                <Button onClick={addTextInput} variant="outline" size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Text
                </Button>
              </div>
              
              {textInputs.map((input, index) => (
                <div key={input.id} className="flex gap-2">
                  <Textarea
                    value={input.content}
                    onChange={(e) => updateTextInput(input.id, e.target.value)}
                    placeholder={`Text input ${index + 1}`}
                    className="flex-1"
                  />
                  <Button
                    onClick={() => removeTextInput(input.id)}
                    variant="outline"
                    size="sm"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              
              {textInputs.length === 0 && (
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
                  <FileText className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Add text input
                  </p>
                </div>
              )}
            </div>

            {/* Image Input Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  Image Input
                </h3>
                <label htmlFor={`image-upload-${blockId}`} className="cursor-pointer">
                  <Button variant="outline" size="sm" asChild>
                    <span>
                      <Upload className="h-4 w-4 mr-2" />
                      Add Image
                    </span>
                  </Button>
                </label>
                <input
                  id={`image-upload-${blockId}`}
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleImageUpload}
                  className="hidden"
                />
              </div>
              
              {imageInputs.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {imageInputs.map((input) => (
                    <div key={input.id} className="relative border rounded-lg overflow-hidden">
                      <img
                        src={input.preview}
                        alt={input.metadata?.filename}
                        className="w-full h-32 object-cover"
                      />
                      <div className="absolute top-2 right-2">
                        <Button
                          onClick={() => removeImageInput(input.id)}
                          variant="destructive"
                          size="sm"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                      <div className="p-2 bg-white dark:bg-gray-800">
                        <p className="text-xs truncate">{input.metadata?.filename}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
                  <Eye className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Upload image files
                  </p>
                </div>
              )}
            </div>

            {/* Audio Input Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Mic className="h-5 w-5" />
                  Audio Input
                </h3>
                <label htmlFor={`audio-upload-${blockId}`} className="cursor-pointer">
                  <Button variant="outline" size="sm" asChild>
                    <span>
                      <Upload className="h-4 w-4 mr-2" />
                      Add Audio
                    </span>
                  </Button>
                </label>
                <input
                  id={`audio-upload-${blockId}`}
                  type="file"
                  accept="audio/*"
                  multiple
                  onChange={handleAudioUpload}
                  className="hidden"
                />
              </div>
              
              {audioInputs.length > 0 ? (
                <div className="space-y-2">
                  {audioInputs.map((input) => (
                    <div key={input.id} className="flex items-center gap-3 p-3 border rounded-lg">
                      <Mic className="h-5 w-5 text-blue-500" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{input.metadata?.filename}</p>
                        <p className="text-xs text-gray-500">
                          {(input.metadata?.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      <Button
                        onClick={() => removeAudioInput(input.id)}
                        variant="outline"
                        size="sm"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
                  <Mic className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Upload audio files
                  </p>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            {/* Fusion Strategy Selection */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Fusion Strategy</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {fusionStrategies.map((strategy) => {
                  const Icon = strategy.icon;
                  const isSelected = fusionStrategy === strategy.value;
                  return (
                    <div
                      key={strategy.value}
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        isSelected 
                          ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => {
                        setFusionStrategy(strategy.value);
                        handleConfigChange({ fusion_strategy: strategy.value });
                      }}
                    >
                      <div className="flex items-start gap-3">
                        <Icon className={`h-5 w-5 ${strategy.color}`} />
                        <div className="flex-1">
                          <h4 className="font-medium">{strategy.name}</h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {strategy.description}
                          </p>
                          <Badge variant="outline" className="mt-2 text-xs">
                            {strategy.estimatedTime}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Prompt Templates */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Fusion Prompt</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
                {promptTemplates.map((template, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => applyTemplate(template)}
                    className="h-auto p-3 flex flex-col items-center gap-2"
                  >
                    <span className="text-lg">{template.icon}</span>
                    <span className="text-xs text-center">{template.name}</span>
                  </Button>
                ))}
              </div>
              
              <Textarea
                value={fusionPrompt}
                onChange={(e) => {
                  setFusionPrompt(e.target.value);
                  handleConfigChange({ fusion_prompt: e.target.value });
                }}
                placeholder="Describe how to analyze and fuse all inputs..."
                className="min-h-[100px]"
              />
            </div>

            {/* Advanced Settings */}
            <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="w-full justify-between">
                  <span className="flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    Advanced Settings
                  </span>
                  <span className="text-xs text-gray-500">
                    {showAdvanced ? 'Hide' : 'Show'}
                  </span>
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-4 pt-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Model</label>
                    <Select value={model} onValueChange={(value) => {
                      setModel(value);
                      handleConfigChange({ model: value });
                    }}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gemini-1.5-pro">Gemini 1.5 Pro (High Quality)</SelectItem>
                        <SelectItem value="gemini-1.5-flash">Gemini 1.5 Flash (Fast)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Creativity ({temperature})</label>
                    <Input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => {
                        const value = parseFloat(e.target.value);
                        setTemperature(value);
                        handleConfigChange({ temperature: value });
                      }}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Max Tokens</label>
                    <Input
                      type="number"
                      min="512"
                      max="8192"
                      value={maxTokens}
                      onChange={(e) => {
                        const value = parseInt(e.target.value);
                        setMaxTokens(value);
                        handleConfigChange({ max_tokens: value });
                      }}
                    />
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>
          </TabsContent>

          <TabsContent value="results" className="space-y-6">
            {result ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  {result.success ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                  <h3 className="font-semibold">
                    {result.success ? 'Fusion Analysis Results' : 'Analysis Failed'}
                  </h3>
                  {result.processing_time_seconds && (
                    <Badge variant="outline">
                      {result.processing_time_seconds.toFixed(2)}s
                    </Badge>
                  )}
                </div>

                {result.success ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div className="text-center p-3 border rounded">
                        <div className="font-semibold">{result.input_modalities.text || 0}</div>
                        <div className="text-gray-500">Text</div>
                      </div>
                      <div className="text-center p-3 border rounded">
                        <div className="font-semibold">{result.input_modalities.image || 0}</div>
                        <div className="text-gray-500">Image</div>
                      </div>
                      <div className="text-center p-3 border rounded">
                        <div className="font-semibold">{result.input_modalities.audio || 0}</div>
                        <div className="text-gray-500">Audio</div>
                      </div>
                    </div>

                    <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded border">
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <StrategyIcon className="h-4 w-4" />
                        Fusion Result ({result.fusion_strategy})
                      </h4>
                      <div className="text-sm whitespace-pre-wrap">
                        {JSON.stringify(result.fusion_result, null, 2)}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
                    <p className="text-sm text-red-700 dark:text-red-300">{result.error}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-500">Results will be displayed here after running fusion analysis</p>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Execute Button */}
        <Button
          onClick={handleFusionAnalysis}
          disabled={isAnalyzing || isExecuting}
          className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
          size="lg"
        >
          {(isAnalyzing || isExecuting) ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              Start Multimodal Fusion Analysis
            </>
          )}
        </Button>

        {/* Input Summary */}
        <div className="flex items-center justify-center gap-6 text-sm text-gray-500">
          <div className="flex items-center gap-1">
            <FileText className="h-4 w-4" />
            <span>{textInputs.length} Text</span>
          </div>
          <div className="flex items-center gap-1">
            <Eye className="h-4 w-4" />
            <span>{imageInputs.length} Image</span>
          </div>
          <div className="flex items-center gap-1">
            <Mic className="h-4 w-4" />
            <span>{audioInputs.length} Audio</span>
          </div>
          {selectedStrategy && (
            <div className="flex items-center gap-1">
              <StrategyIcon className="h-4 w-4" />
              <span>{selectedStrategy.name}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}