'use client';

import React, { useState, useCallback, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Video, 
  Upload, 
  Play,
  Pause,
  X,
  Loader2, 
  CheckCircle, 
  AlertCircle,
  FileVideo,
  Settings,
  Zap,
  Clock,
  Eye,
  Mic,
  Film,
  BarChart3,
  Download
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

interface VideoFile {
  file: File;
  preview: string;
  metadata?: {
    duration?: number;
    size: number;
    type: string;
  };
}

interface VideoAnalysisResult {
  success: boolean;
  analysis_type: string;
  video_analysis: {
    analysis_text: string;
    video_file_info: any;
    processing_method: string;
    usage: any;
  };
  processing_time_seconds: number;
  error?: string;
}

interface GeminiVideoBlockProps {
  blockId: string;
  config?: {
    analysis_type?: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
    frame_sampling?: string;
    max_frames?: number;
    include_audio?: boolean;
  };
  onConfigChange?: (config: any) => void;
  onExecute?: (result: any) => void;
  isExecuting?: boolean;
}

export default function GeminiVideoBlock({
  blockId,
  config = {},
  onConfigChange,
  onExecute,
  isExecuting = false
}: GeminiVideoBlockProps) {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // 비디오 상태
  const [videoFile, setVideoFile] = useState<VideoFile | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  
  // 설정 상태
  const [analysisType, setAnalysisType] = useState(config.analysis_type || 'comprehensive');
  const [model, setModel] = useState(config.model || 'gemini-1.5-pro');
  const [temperature, setTemperature] = useState(config.temperature || 0.7);
  const [maxTokens, setMaxTokens] = useState(config.max_tokens || 4096);
  const [frameSampling, setFrameSampling] = useState(config.frame_sampling || 'auto');
  const [maxFrames, setMaxFrames] = useState(config.max_frames || 30);
  const [includeAudio, setIncludeAudio] = useState(config.include_audio !== false);
  
  // UI 상태
  const [result, setResult] = useState<VideoAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');

  // 분석 유형 정보
  const analysisTypes = [
    {
      value: 'comprehensive',
      name: '종합 분석',
      description: '비디오의 모든 측면을 상세히 분석',
      icon: BarChart3,
      color: 'text-purple-600',
      estimatedTime: '30-60초',
      features: ['전체 요약', '시각적 요소', '오디오 분석', '구조 분석', '품질 평가']
    },
    {
      value: 'summary',
      name: '요약 분석',
      description: '핵심 내용을 간결하게 요약',
      icon: FileVideo,
      color: 'text-blue-600',
      estimatedTime: '15-30초',
      features: ['주요 내용', '핵심 포인트', '대상 청중', '시청 가치']
    },
    {
      value: 'transcript',
      name: '음성 변환',
      description: '음성을 텍스트로 변환',
      icon: Mic,
      color: 'text-green-600',
      estimatedTime: '20-40초',
      features: ['화자 구분', '시간대별 정리', '키워드 추출', '내용 요약']
    },
    {
      value: 'objects',
      name: '객체 분석',
      description: '객체와 인물을 분석',
      icon: Eye,
      color: 'text-orange-600',
      estimatedTime: '25-45초',
      features: ['객체 목록', '인물 분석', '배경 환경', '브랜드/로고']
    },
    {
      value: 'scenes',
      name: '장면 분석',
      description: '장면 구성과 스토리텔링 분석',
      icon: Film,
      color: 'text-red-600',
      estimatedTime: '35-55초',
      features: ['장면 구분', '전환 방식', '시간 구조', '스토리텔링']
    }
  ];

  // 비디오 파일 업로드 처리
  const handleVideoUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 파일 형식 검증
    if (!file.type.startsWith('video/')) {
      toast({
        title: '잘못된 파일 형식',
        description: '비디오 파일만 업로드할 수 있습니다.',
        variant: 'destructive'
      });
      return;
    }

    // 파일 크기 검증 (100MB)
    if (file.size > 100 * 1024 * 1024) {
      toast({
        title: '파일 크기 초과',
        description: '비디오 파일은 100MB 이하여야 합니다.',
        variant: 'destructive'
      });
      return;
    }

    // 비디오 미리보기 생성
    const videoUrl = URL.createObjectURL(file);
    const video = document.createElement('video');
    
    video.onloadedmetadata = () => {
      const newVideoFile: VideoFile = {
        file,
        preview: videoUrl,
        metadata: {
          duration: video.duration,
          size: file.size,
          type: file.type
        }
      };
      setVideoFile(newVideoFile);
      
      toast({
        title: '비디오 업로드 완료',
        description: `${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`
      });
    };
    
    video.src = videoUrl;
    
    // 입력 초기화
    event.target.value = '';
  }, [toast]);

  // 비디오 제거
  const removeVideo = useCallback(() => {
    if (videoFile) {
      URL.revokeObjectURL(videoFile.preview);
      setVideoFile(null);
      setResult(null);
    }
  }, [videoFile]);

  // 비디오 분석 실행
  const handleVideoAnalysis = useCallback(async () => {
    if (!videoFile) {
      toast({
        title: '비디오 필요',
        description: '분석할 비디오를 업로드해주세요.',
        variant: 'destructive'
      });
      return;
    }

    setIsAnalyzing(true);
    setResult(null);

    try {
      // FormData 생성
      const formData = new FormData();
      formData.append('video_file', videoFile.file);
      formData.append('analysis_type', analysisType);
      formData.append('frame_sampling', frameSampling);
      formData.append('max_frames', maxFrames.toString());
      formData.append('include_audio', includeAudio.toString());
      formData.append('model', model);
      formData.append('temperature', temperature.toString());

      const response = await fetch('/api/agent-builder/gemini-video/upload-and-analyze', {
        method: 'POST',
        body: formData
      });

      const analysisResult = await response.json();
      
      if (analysisResult.success) {
        setResult(analysisResult);
        onExecute?.(analysisResult);
        
        toast({
          title: '비디오 분석 완료',
          description: `${analysisResult.processing_time_seconds?.toFixed(2)}초 만에 분석이 완료되었습니다.`
        });
      } else {
        throw new Error(analysisResult.error || '비디오 분석에 실패했습니다.');
      }
    } catch (error) {
      console.error('Video analysis failed:', error);
      const errorResult = {
        success: false,
        error: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
        analysis_type: analysisType,
        video_analysis: {
          analysis_text: '',
          video_file_info: null,
          processing_method: '',
          usage: null
        },
        processing_time_seconds: 0
      };
      setResult(errorResult);
      
      toast({
        title: '비디오 분석 실패',
        description: errorResult.error,
        variant: 'destructive'
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [videoFile, analysisType, frameSampling, maxFrames, includeAudio, model, temperature, onExecute, toast]);

  // 설정 변경 핸들러
  const handleConfigChange = useCallback((newConfig: any) => {
    onConfigChange?.({
      ...config,
      ...newConfig
    });
  }, [config, onConfigChange]);

  // 시간 포맷팅
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 파일 크기 포맷팅
  const formatFileSize = (bytes: number) => {
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  };

  const selectedAnalysisType = analysisTypes.find(t => t.value === analysisType);
  const AnalysisIcon = selectedAnalysisType?.icon || BarChart3;

  return (
    <Card className="w-full max-w-6xl">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-r from-red-100 to-purple-100 dark:from-red-900 dark:to-purple-900">
            <Video className="h-6 w-6 text-red-600 dark:text-red-400" />
          </div>
          <div>
            <CardTitle className="flex items-center gap-2">
              Gemini Video Analyzer
              <Badge variant="secondary" className="bg-gradient-to-r from-red-100 to-purple-100 text-red-700">
                <Video className="h-3 w-3 mr-1" />
                Video AI
              </Badge>
            </CardTitle>
            <CardDescription>
              Gemini 3.0 기반 고급 비디오 분석 및 콘텐츠 추출
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload">비디오 업로드</TabsTrigger>
            <TabsTrigger value="settings">분석 설정</TabsTrigger>
            <TabsTrigger value="results">분석 결과</TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-6">
            {/* 비디오 업로드 영역 */}
            {!videoFile ? (
              <div 
                className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center cursor-pointer hover:border-red-400 transition-colors"
                onClick={() => fileInputRef.current?.click()}
              >
                <Video className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-semibold mb-2">비디오 파일 업로드</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  클릭하거나 파일을 드래그해서 업로드하세요
                </p>
                <div className="flex flex-wrap justify-center gap-2 text-xs text-gray-500">
                  <Badge variant="outline">MP4</Badge>
                  <Badge variant="outline">MOV</Badge>
                  <Badge variant="outline">AVI</Badge>
                  <Badge variant="outline">WebM</Badge>
                  <Badge variant="outline">최대 100MB</Badge>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*"
                  onChange={handleVideoUpload}
                  className="hidden"
                />
              </div>
            ) : (
              <div className="space-y-4">
                {/* 비디오 미리보기 */}
                <div className="relative border rounded-lg overflow-hidden bg-black">
                  <video
                    src={videoFile.preview}
                    controls
                    className="w-full max-h-96 object-contain"
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                  />
                  <div className="absolute top-2 right-2">
                    <Button
                      onClick={removeVideo}
                      variant="destructive"
                      size="sm"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* 비디오 정보 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="text-center p-3 border rounded">
                    <FileVideo className="h-5 w-5 mx-auto mb-1 text-blue-500" />
                    <div className="font-semibold">{videoFile.file.name}</div>
                    <div className="text-gray-500">파일명</div>
                  </div>
                  <div className="text-center p-3 border rounded">
                    <Clock className="h-5 w-5 mx-auto mb-1 text-green-500" />
                    <div className="font-semibold">
                      {videoFile.metadata?.duration ? formatDuration(videoFile.metadata.duration) : 'N/A'}
                    </div>
                    <div className="text-gray-500">재생시간</div>
                  </div>
                  <div className="text-center p-3 border rounded">
                    <Download className="h-5 w-5 mx-auto mb-1 text-purple-500" />
                    <div className="font-semibold">{formatFileSize(videoFile.metadata?.size || 0)}</div>
                    <div className="text-gray-500">파일크기</div>
                  </div>
                  <div className="text-center p-3 border rounded">
                    <Settings className="h-5 w-5 mx-auto mb-1 text-orange-500" />
                    <div className="font-semibold">{videoFile.metadata?.type || 'Unknown'}</div>
                    <div className="text-gray-500">형식</div>
                  </div>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            {/* 분석 유형 선택 */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">분석 유형</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {analysisTypes.map((type) => {
                  const Icon = type.icon;
                  const isSelected = analysisType === type.value;
                  return (
                    <div
                      key={type.value}
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        isSelected 
                          ? 'border-red-500 bg-red-50 dark:bg-red-900/20' 
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => {
                        setAnalysisType(type.value);
                        handleConfigChange({ analysis_type: type.value });
                      }}
                    >
                      <div className="flex items-start gap-3">
                        <Icon className={`h-5 w-5 ${type.color}`} />
                        <div className="flex-1">
                          <h4 className="font-medium">{type.name}</h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {type.description}
                          </p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="outline" className="text-xs">
                              <Clock className="h-3 w-3 mr-1" />
                              {type.estimatedTime}
                            </Badge>
                          </div>
                          <div className="mt-2 space-y-1">
                            {type.features.slice(0, 3).map((feature, index) => (
                              <div key={index} className="flex items-center gap-1 text-xs text-gray-500">
                                <CheckCircle className="h-3 w-3 text-green-500" />
                                <span>{feature}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
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
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
                    <label className="text-sm font-medium">프레임 샘플링</label>
                    <Select value={frameSampling} onValueChange={(value) => {
                      setFrameSampling(value);
                      handleConfigChange({ frame_sampling: value });
                    }}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="auto">자동</SelectItem>
                        <SelectItem value="uniform">균등 간격</SelectItem>
                        <SelectItem value="keyframes">키프레임</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium">최대 프레임 ({maxFrames})</label>
                    <Input
                      type="range"
                      min="10"
                      max="100"
                      value={maxFrames}
                      onChange={(e) => {
                        const value = parseInt(e.target.value);
                        setMaxFrames(value);
                        handleConfigChange({ max_frames: value });
                      }}
                    />
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
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={includeAudio}
                        onChange={(e) => {
                          setIncludeAudio(e.target.checked);
                          handleConfigChange({ include_audio: e.target.checked });
                        }}
                      />
                      오디오 포함
                    </label>
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
                    {result.success ? '비디오 분석 결과' : '분석 실패'}
                  </h3>
                  {result.processing_time_seconds && (
                    <Badge variant="outline">
                      {result.processing_time_seconds.toFixed(2)}초
                    </Badge>
                  )}
                </div>

                {result.success ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded border">
                      <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                        <AnalysisIcon className="h-4 w-4" />
                        분석 결과 ({result.analysis_type})
                      </h4>
                      <div className="text-sm whitespace-pre-wrap">
                        {result.video_analysis?.analysis_text}
                      </div>
                    </div>

                    {result.video_analysis?.usage && (
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div className="text-center p-3 border rounded">
                          <div className="font-semibold">{result.video_analysis.usage.prompt_tokens}</div>
                          <div className="text-gray-500">입력 토큰</div>
                        </div>
                        <div className="text-center p-3 border rounded">
                          <div className="font-semibold">{result.video_analysis.usage.completion_tokens}</div>
                          <div className="text-gray-500">출력 토큰</div>
                        </div>
                        <div className="text-center p-3 border rounded">
                          <div className="font-semibold">{result.video_analysis.usage.total_tokens}</div>
                          <div className="text-gray-500">총 토큰</div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
                    <p className="text-sm text-red-700 dark:text-red-300">{result.error}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <Video className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-500">비디오 분석을 실행하면 결과가 여기에 표시됩니다</p>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* 실행 버튼 */}
        <Button
          onClick={handleVideoAnalysis}
          disabled={!videoFile || isAnalyzing || isExecuting}
          className="w-full bg-gradient-to-r from-red-600 to-purple-600 hover:from-red-700 hover:to-purple-700"
          size="lg"
        >
          {(isAnalyzing || isExecuting) ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              비디오 분석 중...
            </>
          ) : (
            <>
              <Video className="h-4 w-4 mr-2" />
              비디오 분석 시작
            </>
          )}
        </Button>

        {/* 상태 요약 */}
        <div className="flex items-center justify-center gap-6 text-sm text-gray-500">
          <div className="flex items-center gap-1">
            <Video className="h-4 w-4" />
            <span>{videoFile ? '업로드됨' : '대기중'}</span>
          </div>
          {selectedAnalysisType && (
            <div className="flex items-center gap-1">
              <AnalysisIcon className="h-4 w-4" />
              <span>{selectedAnalysisType.name}</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <Zap className="h-4 w-4" />
            <span>{model}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}