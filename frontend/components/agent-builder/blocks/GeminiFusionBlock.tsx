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
  
  // 입력 상태
  const [textInputs, setTextInputs] = useState<TextInput[]>([]);
  const [imageInputs, setImageInputs] = useState<ImageInput[]>([]);
  const [audioInputs, setAudioInputs] = useState<AudioInput[]>([]);
  
  // 설정 상태
  const [fusionPrompt, setFusionPrompt] = useState(config.fusion_prompt || '');
  const [fusionStrategy, setFusionStrategy] = useState(config.fusion_strategy || 'unified');
  const [model, setModel] = useState(config.model || 'gemini-1.5-pro');
  const [temperature, setTemperature] = useState(config.temperature || 0.7);
  const [maxTokens, setMaxTokens] = useState(config.max_tokens || 4096);
  
  // UI 상태
  const [result, setResult] = useState<FusionResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeTab, setActiveTab] = useState('inputs');

  // 융합 전략 정보
  const fusionStrategies = [
    {
      value: 'unified',
      name: '통합 처리',
      description: '모든 모달리티를 한번에 처리 (가장 정확)',
      icon: Sparkles,
      color: 'text-purple-600',
      estimatedTime: '5-10초'
    },
    {
      value: 'parallel',
      name: '병렬 처리',
      description: '각 모달리티를 병렬 처리 후 융합 (가장 빠름)',
      icon: Zap,
      color: 'text-blue-600',
      estimatedTime: '2-5초'
    },
    {
      value: 'sequential',
      name: '순차 처리',
      description: '순차적으로 처리하며 컨텍스트 누적 (가장 상세)',
      icon: GitBranch,
      color: 'text-green-600',
      estimatedTime: '8-15초'
    },
    {
      value: 'hierarchical',
      name: '계층적 처리',
      description: '계층적 융합으로 체계적 분석 (가장 체계적)',
      icon: Layers,
      color: 'text-orange-600',
      estimatedTime: '6-12초'
    }
  ];

  // 프롬프트 템플릿
  const promptTemplates = [
    {
      name: '종합 분석',
      prompt: '제공된 모든 정보를 종합하여 핵심 인사이트와 결론을 도출해주세요.',
      icon: '🔍'
    },
    {
      name: '비교 분석',
      prompt: '각 입력 간의 공통점과 차이점을 분석하고 상호 관계를 설명해주세요.',
      icon: '⚖️'
    },
    {
      name: '요약 정리',
      prompt: '모든 정보를 요약하고 주요 포인트를 정리해주세요.',
      icon: '📋'
    },
    {
      name: '문제 해결',
      prompt: '제시된 정보를 바탕으로 문제점을 파악하고 해결책을 제안해주세요.',
      icon: '💡'
    },
    {
      name: '트렌드 분석',
      prompt: '데이터에서 패턴과 트렌드를 찾아 미래 전망을 제시해주세요.',
      icon: '📈'
    }
  ];

  // 텍스트 입력 추가
  const addTextInput = useCallback(() => {
    const newInput: TextInput = {
      id: `text_${Date.now()}`,
      content: '',
      metadata: {}
    };
    setTextInputs(prev => [...prev, newInput]);
  }, []);

  // 텍스트 입력 제거
  const removeTextInput = useCallback((id: string) => {
    setTextInputs(prev => prev.filter(input => input.id !== id));
  }, []);

  // 텍스트 내용 업데이트
  const updateTextInput = useCallback((id: string, content: string) => {
    setTextInputs(prev => prev.map(input => 
      input.id === id ? { ...input, content } : input
    ));
  }, []);

  // 이미지 파일 추가
  const handleImageUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    
    files.forEach(file => {
      if (!file.type.startsWith('image/')) {
        toast({
          title: '잘못된 파일 형식',
          description: '이미지 파일만 업로드할 수 있습니다.',
          variant: 'destructive'
        });
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        toast({
          title: '파일 크기 초과',
          description: '이미지 파일은 10MB 이하여야 합니다.',
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

    // 입력 초기화
    event.target.value = '';
  }, [toast]);

  // 이미지 입력 제거
  const removeImageInput = useCallback((id: string) => {
    setImageInputs(prev => prev.filter(input => input.id !== id));
  }, []);

  // 음성 파일 추가
  const handleAudioUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    
    files.forEach(file => {
      if (!file.type.startsWith('audio/')) {
        toast({
          title: '잘못된 파일 형식',
          description: '음성 파일만 업로드할 수 있습니다.',
          variant: 'destructive'
        });
        return;
      }

      if (file.size > 25 * 1024 * 1024) {
        toast({
          title: '파일 크기 초과',
          description: '음성 파일은 25MB 이하여야 합니다.',
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

    // 입력 초기화
    event.target.value = '';
  }, [toast]);

  // 음성 입력 제거
  const removeAudioInput = useCallback((id: string) => {
    setAudioInputs(prev => prev.filter(input => input.id !== id));
  }, []);

  // 융합 분석 실행
  const handleFusionAnalysis = useCallback(async () => {
    // 입력 검증
    const totalInputs = textInputs.length + imageInputs.length + audioInputs.length;
    if (totalInputs < 2) {
      toast({
        title: '입력 부족',
        description: '최소 2개 이상의 입력이 필요합니다.',
        variant: 'destructive'
      });
      return;
    }

    const modalityCount = [textInputs, imageInputs, audioInputs].filter(arr => arr.length > 0).length;
    if (modalityCount < 2) {
      toast({
        title: '모달리티 부족',
        description: '최소 2개 이상의 다른 종류 입력이 필요합니다.',
        variant: 'destructive'
      });
      return;
    }

    if (!fusionPrompt.trim()) {
      toast({
        title: '프롬프트 필요',
        description: '융합 분석 프롬프트를 입력해주세요.',
        variant: 'destructive'
      });
      return;
    }

    setIsAnalyzing(true);
    setResult(null);

    try {
      // FormData 생성
      const formData = new FormData();
      formData.append('fusion_prompt', fusionPrompt);
      formData.append('fusion_strategy', fusionStrategy);
      formData.append('model', model);
      formData.append('temperature', temperature.toString());

      // 텍스트 입력 추가
      if (textInputs.length > 0) {
        const combinedText = textInputs.map(input => input.content).join('\n\n');
        formData.append('text_content', combinedText);
      }

      // 이미지 파일 추가
      imageInputs.forEach(input => {
        formData.append('image_files', input.file);
      });

      // 음성 파일 추가
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
          title: '융합 분석 완료',
          description: `${analysisResult.processing_time_seconds?.toFixed(2)}초 만에 분석이 완료되었습니다.`
        });
      } else {
        throw new Error(analysisResult.error || '융합 분석에 실패했습니다.');
      }
    } catch (error) {
      console.error('Fusion analysis failed:', error);
      const errorResult = {
        success: false,
        error: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
        fusion_strategy: fusionStrategy,
        input_modalities: {
          text: textInputs.length,
          image: imageInputs.length,
          audio: audioInputs.length
        },
        processing_time_seconds: 0
      };
      setResult(errorResult);
      
      toast({
        title: '융합 분석 실패',
        description: errorResult.error,
        variant: 'destructive'
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [textInputs, imageInputs, audioInputs, fusionPrompt, fusionStrategy, model, temperature, onExecute, toast]);

  // 설정 변경 핸들러
  const handleConfigChange = useCallback((newConfig: any) => {
    onConfigChange?.({
      ...config,
      ...newConfig
    });
  }, [config, onConfigChange]);

  // 프롬프트 템플릿 적용
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
              여러 종류의 미디어를 동시에 분석하여 통합적인 인사이트를 생성합니다
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="inputs">입력 데이터</TabsTrigger>
            <TabsTrigger value="settings">융합 설정</TabsTrigger>
            <TabsTrigger value="results">분석 결과</TabsTrigger>
          </TabsList>

          <TabsContent value="inputs" className="space-y-6">
            {/* 텍스트 입력 섹션 */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  텍스트 입력
                </h3>
                <Button onClick={addTextInput} variant="outline" size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  텍스트 추가
                </Button>
              </div>
              
              {textInputs.map((input, index) => (
                <div key={input.id} className="flex gap-2">
                  <Textarea
                    value={input.content}
                    onChange={(e) => updateTextInput(input.id, e.target.value)}
                    placeholder={`텍스트 입력 ${index + 1}`}
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
                    텍스트 입력을 추가하세요
                  </p>
                </div>
              )}
            </div>

            {/* 이미지 입력 섹션 */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  이미지 입력
                </h3>
                <label htmlFor={`image-upload-${blockId}`} className="cursor-pointer">
                  <Button variant="outline" size="sm" asChild>
                    <span>
                      <Upload className="h-4 w-4 mr-2" />
                      이미지 추가
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
                    이미지 파일을 업로드하세요
                  </p>
                </div>
              )}
            </div>

            {/* 음성 입력 섹션 */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Mic className="h-5 w-5" />
                  음성 입력
                </h3>
                <label htmlFor={`audio-upload-${blockId}`} className="cursor-pointer">
                  <Button variant="outline" size="sm" asChild>
                    <span>
                      <Upload className="h-4 w-4 mr-2" />
                      음성 추가
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
                    음성 파일을 업로드하세요
                  </p>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            {/* 융합 전략 선택 */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">융합 전략</h3>
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

            {/* 프롬프트 템플릿 */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">융합 프롬프트</h3>
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
                placeholder="모든 입력을 어떻게 융합 분석할지 설명해주세요..."
                className="min-h-[100px]"
              />
            </div>

            {/* 고급 설정 */}
            <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="w-full justify-between">
                  <span className="flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    고급 설정
                  </span>
                  <span className="text-xs text-gray-500">
                    {showAdvanced ? '숨기기' : '보기'}
                  </span>
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-4 pt-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">모델</label>
                    <Select value={model} onValueChange={(value) => {
                      setModel(value);
                      handleConfigChange({ model: value });
                    }}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gemini-1.5-pro">Gemini 1.5 Pro (고품질)</SelectItem>
                        <SelectItem value="gemini-1.5-flash">Gemini 1.5 Flash (빠름)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium">창의성 ({temperature})</label>
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
                    <label className="text-sm font-medium">최대 토큰</label>
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
                    {result.success ? '융합 분석 결과' : '분석 실패'}
                  </h3>
                  {result.processing_time_seconds && (
                    <Badge variant="outline">
                      {result.processing_time_seconds.toFixed(2)}초
                    </Badge>
                  )}
                </div>

                {result.success ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div className="text-center p-3 border rounded">
                        <div className="font-semibold">{result.input_modalities.text || 0}</div>
                        <div className="text-gray-500">텍스트</div>
                      </div>
                      <div className="text-center p-3 border rounded">
                        <div className="font-semibold">{result.input_modalities.image || 0}</div>
                        <div className="text-gray-500">이미지</div>
                      </div>
                      <div className="text-center p-3 border rounded">
                        <div className="font-semibold">{result.input_modalities.audio || 0}</div>
                        <div className="text-gray-500">음성</div>
                      </div>
                    </div>

                    <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded border">
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <StrategyIcon className="h-4 w-4" />
                        융합 결과 ({result.fusion_strategy})
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
                <p className="text-gray-500">융합 분석을 실행하면 결과가 여기에 표시됩니다</p>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* 실행 버튼 */}
        <Button
          onClick={handleFusionAnalysis}
          disabled={isAnalyzing || isExecuting}
          className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
          size="lg"
        >
          {(isAnalyzing || isExecuting) ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              융합 분석 중...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              멀티모달 융합 분석 시작
            </>
          )}
        </Button>

        {/* 입력 요약 */}
        <div className="flex items-center justify-center gap-6 text-sm text-gray-500">
          <div className="flex items-center gap-1">
            <FileText className="h-4 w-4" />
            <span>{textInputs.length} 텍스트</span>
          </div>
          <div className="flex items-center gap-1">
            <Eye className="h-4 w-4" />
            <span>{imageInputs.length} 이미지</span>
          </div>
          <div className="flex items-center gap-1">
            <Mic className="h-4 w-4" />
            <span>{audioInputs.length} 음성</span>
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