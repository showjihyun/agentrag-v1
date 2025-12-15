'use client';

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Eye, 
  Upload, 
  Image as ImageIcon, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Settings,
  Sparkles
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
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

interface GeminiVisionBlockProps {
  blockId: string;
  config?: {
    model?: string;
    temperature?: number;
    maxTokens?: number;
    prompt?: string;
  };
  onConfigChange?: (config: any) => void;
  onExecute?: (result: any) => void;
  isExecuting?: boolean;
}

interface AnalysisResult {
  success: boolean;
  result?: string;
  structured_data?: any;
  processing_time_seconds?: number;
  usage?: {
    total_tokens: number;
  };
  error?: string;
}

export default function GeminiVisionBlock({
  blockId,
  config = {},
  onConfigChange,
  onExecute,
  isExecuting = false
}: GeminiVisionBlockProps) {
  const { toast } = useToast();
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [prompt, setPrompt] = useState(config.prompt || '');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // 설정 상태
  const [model, setModel] = useState(config.model || 'gemini-1.5-flash');
  const [temperature, setTemperature] = useState(config.temperature || 0.7);
  const [maxTokens, setMaxTokens] = useState(config.maxTokens || 2048);

  // 미리 정의된 프롬프트 템플릿
  const promptTemplates = [
    {
      name: '영수증 분석',
      prompt: '이 영수증을 분석해서 상점명, 날짜, 총액, 구매 항목들을 JSON 형태로 추출해주세요.',
      icon: '🧾'
    },
    {
      name: '제품 설명 생성',
      prompt: '이 제품 이미지를 보고 상세한 제품 설명과 주요 특징을 작성해주세요.',
      icon: '📦'
    },
    {
      name: '차트 데이터 추출',
      prompt: '이 차트나 그래프에서 데이터를 추출해서 표 형태로 정리해주세요.',
      icon: '📊'
    },
    {
      name: '문서 요약',
      prompt: '이 문서의 주요 내용을 요약하고 핵심 포인트를 정리해주세요.',
      icon: '📄'
    },
    {
      name: '손글씨 인식',
      prompt: '이 손글씨를 읽어서 텍스트로 변환해주세요.',
      icon: '✍️'
    }
  ];

  const handleImageUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 파일 크기 검증 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: '파일 크기 초과',
        description: '이미지 파일은 10MB 이하여야 합니다.',
        variant: 'destructive'
      });
      return;
    }

    // 이미지 파일 검증
    if (!file.type.startsWith('image/')) {
      toast({
        title: '잘못된 파일 형식',
        description: '이미지 파일만 업로드할 수 있습니다.',
        variant: 'destructive'
      });
      return;
    }

    setSelectedImage(file);

    // 미리보기 생성
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  }, [toast]);

  const handleAnalyze = useCallback(async () => {
    if (!selectedImage || !prompt.trim()) {
      toast({
        title: '입력 필요',
        description: '이미지와 분석 프롬프트를 모두 입력해주세요.',
        variant: 'destructive'
      });
      return;
    }

    setIsAnalyzing(true);
    setResult(null);

    try {
      // 이미지를 base64로 변환
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64Data = (e.target?.result as string).split(',')[1];

        try {
          const response = await fetch('/api/agent-builder/gemini/analyze-image', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              image_data: base64Data,
              prompt: prompt,
              model: model,
              temperature: temperature,
              max_tokens: maxTokens
            })
          });

          const analysisResult = await response.json();
          
          if (analysisResult.success) {
            setResult(analysisResult);
            onExecute?.(analysisResult);
            
            toast({
              title: '분석 완료',
              description: `${analysisResult.processing_time_seconds?.toFixed(2)}초 만에 분석이 완료되었습니다.`
            });
          } else {
            throw new Error(analysisResult.error || '분석에 실패했습니다.');
          }
        } catch (error) {
          console.error('Analysis failed:', error);
          const errorResult = {
            success: false,
            error: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'
          };
          setResult(errorResult);
          
          toast({
            title: '분석 실패',
            description: errorResult.error,
            variant: 'destructive'
          });
        } finally {
          setIsAnalyzing(false);
        }
      };
      
      reader.readAsDataURL(selectedImage);
    } catch (error) {
      console.error('File reading failed:', error);
      setIsAnalyzing(false);
      toast({
        title: '파일 읽기 실패',
        description: '이미지 파일을 읽는 중 오류가 발생했습니다.',
        variant: 'destructive'
      });
    }
  }, [selectedImage, prompt, model, temperature, maxTokens, onExecute, toast]);

  const handleConfigChange = useCallback((newConfig: any) => {
    onConfigChange?.({
      ...config,
      ...newConfig
    });
  }, [config, onConfigChange]);

  const applyTemplate = useCallback((template: typeof promptTemplates[0]) => {
    setPrompt(template.prompt);
    handleConfigChange({ prompt: template.prompt });
  }, [handleConfigChange]);

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
            <Eye className="h-6 w-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <CardTitle className="flex items-center gap-2">
              Gemini Vision Analyzer
              <Badge variant="secondary" className="bg-purple-100 text-purple-700">
                <Sparkles className="h-3 w-3 mr-1" />
                AI Vision
              </Badge>
            </CardTitle>
            <CardDescription>
              Google Gemini 3.0을 활용한 고급 이미지 분석 및 데이터 추출
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* 이미지 업로드 영역 */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">이미지 업로드</h3>
            {selectedImage && (
              <Badge variant="outline" className="text-green-600">
                <CheckCircle className="h-3 w-3 mr-1" />
                {selectedImage.name}
              </Badge>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 업로드 버튼 */}
            <div className="space-y-2">
              <label htmlFor={`image-upload-${blockId}`} className="cursor-pointer">
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-purple-400 transition-colors">
                  <Upload className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    클릭하여 이미지 업로드
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    JPG, PNG, GIF (최대 10MB)
                  </p>
                </div>
              </label>
              <input
                id={`image-upload-${blockId}`}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
            </div>

            {/* 이미지 미리보기 */}
            {imagePreview && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">미리보기</h4>
                <div className="border rounded-lg overflow-hidden">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="w-full h-48 object-contain bg-gray-50 dark:bg-gray-900"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 프롬프트 템플릿 */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">빠른 템플릿</h3>
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
        </div>

        {/* 분석 프롬프트 */}
        <div className="space-y-2">
          <label className="text-sm font-medium">분석 프롬프트</label>
          <Textarea
            value={prompt}
            onChange={(e) => {
              setPrompt(e.target.value);
              handleConfigChange({ prompt: e.target.value });
            }}
            placeholder="이미지를 어떻게 분석할지 설명해주세요..."
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
                    <SelectItem value="gemini-1.5-flash">Gemini 1.5 Flash (빠름)</SelectItem>
                    <SelectItem value="gemini-1.5-pro">Gemini 1.5 Pro (고품질)</SelectItem>
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
                  min="256"
                  max="8192"
                  value={maxTokens}
                  onChange={(e) => {
                    const value = parseInt(e.target.value);
                    setMaxTokens(value);
                    handleConfigChange({ maxTokens: value });
                  }}
                />
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* 실행 버튼 */}
        <Button
          onClick={handleAnalyze}
          disabled={!selectedImage || !prompt.trim() || isAnalyzing || isExecuting}
          className="w-full bg-purple-600 hover:bg-purple-700"
          size="lg"
        >
          {(isAnalyzing || isExecuting) ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              분석 중...
            </>
          ) : (
            <>
              <Eye className="h-4 w-4 mr-2" />
              이미지 분석 시작
            </>
          )}
        </Button>

        {/* 결과 표시 */}
        {result && (
          <div className="space-y-4 p-4 border rounded-lg bg-gray-50 dark:bg-gray-900">
            <div className="flex items-center gap-2">
              {result.success ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-500" />
              )}
              <h3 className="font-semibold">
                {result.success ? '분석 결과' : '분석 실패'}
              </h3>
              {result.processing_time_seconds && (
                <Badge variant="outline">
                  {result.processing_time_seconds.toFixed(2)}초
                </Badge>
              )}
            </div>

            {result.success ? (
              <div className="space-y-3">
                <div className="p-3 bg-white dark:bg-gray-800 rounded border">
                  <h4 className="text-sm font-medium mb-2">분석 결과</h4>
                  <p className="text-sm whitespace-pre-wrap">{result.result}</p>
                </div>

                {result.structured_data && (
                  <div className="p-3 bg-white dark:bg-gray-800 rounded border">
                    <h4 className="text-sm font-medium mb-2">구조화된 데이터</h4>
                    <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-auto">
                      {JSON.stringify(result.structured_data, null, 2)}
                    </pre>
                  </div>
                )}

                {result.usage && (
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>토큰 사용량: {result.usage.total_tokens}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
                <p className="text-sm text-red-700 dark:text-red-300">{result.error}</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}