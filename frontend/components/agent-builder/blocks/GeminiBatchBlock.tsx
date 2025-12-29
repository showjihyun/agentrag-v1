'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Layers, 
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
  BarChart3,
  Users,
  TrendingUp,
  Download,
  RefreshCw,
  StopCircle
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface VideoFile {
  file: File;
  preview: string;
  id: string;
}

interface BatchJob {
  job_id: string;
  job_name: string;
  status: string;
  total_items: number;
  processed_items: number;
  completed_items: number;
  failed_items: number;
  progress_percentage: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  estimated_remaining_time?: number;
  average_processing_time: number;
}

interface BatchResult {
  item_id: string;
  status: string;
  result?: any;
  error?: string;
  processing_time_seconds: number;
  analysis_config: any;
}

interface GeminiBatchBlockProps {
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

export default function GeminiBatchBlock({
  blockId,
  config = {},
  onConfigChange,
  onExecute,
  isExecuting = false
}: GeminiBatchBlockProps) {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // 비디오 파일 상태
  const [videoFiles, setVideoFiles] = useState<VideoFile[]>([]);
  const [jobName, setJobName] = useState('');
  
  // 설정 상태
  const [analysisType, setAnalysisType] = useState(config.analysis_type || 'comprehensive');
  const [model, setModel] = useState(config.model || 'gemini-1.5-pro');
  const [temperature, setTemperature] = useState(config.temperature || 0.7);
  const [frameSampling, setFrameSampling] = useState(config.frame_sampling || 'auto');
  const [maxFrames, setMaxFrames] = useState(config.max_frames || 30);
  const [includeAudio, setIncludeAudio] = useState(config.include_audio !== false);
  
  // 배치 작업 상태
  const [currentJob, setCurrentJob] = useState<BatchJob | null>(null);
  const [batchResults, setBatchResults] = useState<BatchResult[]>([]);
  const [isCreatingJob, setIsCreatingJob] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('setup');

  // 비디오 파일 업로드 처리
  const handleVideoUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    
    const newVideoFiles: VideoFile[] = [];
    
    files.forEach(file => {
      if (!file.type.startsWith('video/')) {
        toast({
          title: '잘못된 파일 형식',
          description: `${file.name}은 비디오 파일이 아닙니다.`,
          variant: 'destructive'
        });
        return;
      }

      if (file.size > 100 * 1024 * 1024) {
        toast({
          title: '파일 크기 초과',
          description: `${file.name}은 100MB를 초과합니다.`,
          variant: 'destructive'
        });
        return;
      }

      const videoUrl = URL.createObjectURL(file);
      newVideoFiles.push({
        file,
        preview: videoUrl,
        id: `${Date.now()}_${Math.random()}`
      });
    });

    setVideoFiles(prev => [...prev, ...newVideoFiles]);
    
    if (newVideoFiles.length > 0) {
      toast({
        title: '비디오 추가 완료',
        description: `${newVideoFiles.length}개 파일이 추가되었습니다.`
      });
    }
    
    // 입력 초기화
    event.target.value = '';
  }, [toast]);

  // 비디오 파일 제거
  const removeVideoFile = useCallback((id: string) => {
    setVideoFiles(prev => {
      const fileToRemove = prev.find(f => f.id === id);
      if (fileToRemove) {
        URL.revokeObjectURL(fileToRemove.preview);
      }
      return prev.filter(f => f.id !== id);
    });
  }, []);

  // 모든 파일 제거
  const clearAllFiles = useCallback(() => {
    videoFiles.forEach(file => URL.revokeObjectURL(file.preview));
    setVideoFiles([]);
  }, [videoFiles]);

  // 배치 작업 생성 및 시작
  const handleStartBatch = useCallback(async () => {
    if (videoFiles.length === 0) {
      toast({
        title: '비디오 파일 필요',
        description: '최소 1개 이상의 비디오 파일을 추가해주세요.',
        variant: 'destructive'
      });
      return;
    }

    if (!jobName.trim()) {
      toast({
        title: '작업 이름 필요',
        description: '배치 작업 이름을 입력해주세요.',
        variant: 'destructive'
      });
      return;
    }

    setIsCreatingJob(true);

    try {
      // 1. 배치 작업 생성
      const createResponse = await fetch('/api/agent-builder/gemini-batch/create-job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_name: jobName,
          analysis_type: analysisType,
          model: model,
          temperature: temperature,
          frame_sampling: frameSampling,
          max_frames: maxFrames,
          include_audio: includeAudio
        })
      });

      const createResult = await createResponse.json();
      if (!createResponse.ok) {
        throw new Error(createResult.detail || '배치 작업 생성 실패');
      }

      const jobId = createResult.job_id;

      // 2. 비디오 파일들 추가
      const formData = new FormData();
      formData.append('analysis_type', analysisType);
      formData.append('model', model);
      formData.append('temperature', temperature.toString());
      formData.append('frame_sampling', frameSampling);
      formData.append('max_frames', maxFrames.toString());
      formData.append('include_audio', includeAudio.toString());

      videoFiles.forEach(videoFile => {
        formData.append('video_files', videoFile.file);
      });

      const addResponse = await fetch(`/api/agent-builder/gemini-batch/jobs/${jobId}/add-videos`, {
        method: 'POST',
        body: formData
      });

      const addResult = await addResponse.json();
      if (!addResponse.ok) {
        throw new Error(addResult.detail || '비디오 파일 추가 실패');
      }

      // 3. 배치 처리 시작
      const startResponse = await fetch(`/api/agent-builder/gemini-batch/jobs/${jobId}/start`, {
        method: 'POST'
      });

      const startResult = await startResponse.json();
      if (!startResponse.ok) {
        throw new Error(startResult.detail || '배치 처리 시작 실패');
      }

      // 상태 업데이트
      setIsProcessing(true);
      setActiveTab('progress');
      
      // 진행률 폴링 시작
      startProgressPolling(jobId);

      toast({
        title: '배치 처리 시작',
        description: `${videoFiles.length}개 파일의 분석이 시작되었습니다.`
      });

    } catch (error) {
      console.error('Batch processing failed:', error);
      toast({
        title: '배치 처리 실패',
        description: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.',
        variant: 'destructive'
      });
    } finally {
      setIsCreatingJob(false);
    }
  }, [videoFiles, jobName, analysisType, model, temperature, frameSampling, maxFrames, includeAudio, toast]);

  // 진행률 폴링
  const startProgressPolling = useCallback((jobId: string) => {
    const pollProgress = async () => {
      try {
        const response = await fetch(`/api/agent-builder/gemini-batch/jobs/${jobId}/status`);
        const job = await response.json();
        
        setCurrentJob(job);
        
        if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
          setIsProcessing(false);
          
          // 결과 조회
          const resultsResponse = await fetch(`/api/agent-builder/gemini-batch/jobs/${jobId}/results`);
          const resultsData = await resultsResponse.json();
          setBatchResults(resultsData.results || []);
          
          // 폴링 중단
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          
          setActiveTab('results');
          
          if (job.status === 'completed') {
            toast({
              title: '배치 처리 완료',
              description: `${job.completed_items}개 파일이 성공적으로 분석되었습니다.`
            });
            onExecute?.(resultsData);
          }
        }
      } catch (error) {
        console.error('Progress polling failed:', error);
      }
    };

    // 즉시 실행
    pollProgress();
    
    // 2초마다 폴링
    pollIntervalRef.current = setInterval(pollProgress, 2000);
  }, [toast, onExecute]);

  // 배치 작업 취소
  const handleCancelBatch = useCallback(async () => {
    if (!currentJob) return;

    try {
      const response = await fetch(`/api/agent-builder/gemini-batch/jobs/${currentJob.job_id}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setIsProcessing(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        
        toast({
          title: '배치 작업 취소',
          description: '배치 처리가 취소되었습니다.'
        });
      }
    } catch (error) {
      console.error('Cancel batch failed:', error);
      toast({
        title: '취소 실패',
        description: '배치 작업 취소에 실패했습니다.',
        variant: 'destructive'
      });
    }
  }, [currentJob, toast]);

  // 설정 변경 핸들러
  const handleConfigChange = useCallback((newConfig: any) => {
    onConfigChange?.({
      ...config,
      ...newConfig
    });
  }, [config, onConfigChange]);

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      videoFiles.forEach(file => URL.revokeObjectURL(file.preview));
    };
  }, [videoFiles]);

  // 파일 크기 포맷팅
  const formatFileSize = (bytes: number) => {
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  };

  // 시간 포맷팅
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Card className="w-full max-w-6xl">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-r from-blue-100 to-green-100 dark:from-blue-900 dark:to-green-900">
            <Layers className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <CardTitle className="flex items-center gap-2">
              Gemini Batch Processor
              <Badge variant="secondary" className="bg-gradient-to-r from-blue-100 to-green-100 text-blue-700">
                <Users className="h-3 w-3 mr-1" />
                Batch AI
              </Badge>
            </CardTitle>
            <CardDescription>
              여러 비디오를 동시에 처리하는 고성능 배치 분석 시스템
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="setup">배치 설정</TabsTrigger>
            <TabsTrigger value="progress">진행 상황</TabsTrigger>
            <TabsTrigger value="results">분석 결과</TabsTrigger>
          </TabsList>

          <TabsContent value="setup" className="space-y-6">
            {/* 작업 이름 */}
            <div className="space-y-2">
              <label className="text-sm font-medium">배치 작업 이름</label>
              <Input
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                placeholder="예: 마케팅 비디오 분석 2024-12"
                disabled={isProcessing}
              />
            </div>

            {/* 비디오 파일 업로드 */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">비디오 파일 ({videoFiles.length}개)</h3>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isProcessing}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    파일 추가
                  </Button>
                  {videoFiles.length > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={clearAllFiles}
                      disabled={isProcessing}
                    >
                      <X className="h-4 w-4 mr-2" />
                      전체 삭제
                    </Button>
                  )}
                </div>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                multiple
                onChange={handleVideoUpload}
                className="hidden"
              />

              {videoFiles.length === 0 ? (
                <div 
                  className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Layers className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-semibold mb-2">여러 비디오 파일 업로드</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    클릭하거나 파일을 드래그해서 여러 비디오를 한 번에 업로드하세요
                  </p>
                  <div className="flex flex-wrap justify-center gap-2 text-xs text-gray-500">
                    <Badge variant="outline">다중 선택 지원</Badge>
                    <Badge variant="outline">최대 100MB/파일</Badge>
                    <Badge variant="outline">동시 처리</Badge>
                  </div>
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {videoFiles.map((videoFile, index) => (
                    <div key={videoFile.id} className="flex items-center gap-3 p-3 border rounded-lg">
                      <FileVideo className="h-5 w-5 text-blue-500" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{videoFile.file.name}</p>
                        <p className="text-xs text-gray-500">
                          {formatFileSize(videoFile.file.size)} • {videoFile.file.type}
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removeVideoFile(videoFile.id)}
                        disabled={isProcessing}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 분석 설정 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">분석 유형</label>
                <Select value={analysisType} onValueChange={(value) => {
                  setAnalysisType(value);
                  handleConfigChange({ analysis_type: value });
                }}>
                  <SelectTrigger disabled={isProcessing}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="comprehensive">종합 분석</SelectItem>
                    <SelectItem value="summary">요약 분석</SelectItem>
                    <SelectItem value="transcript">음성 변환</SelectItem>
                    <SelectItem value="objects">객체 분석</SelectItem>
                    <SelectItem value="scenes">장면 분석</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">모델</label>
                <Select value={model} onValueChange={(value) => {
                  setModel(value);
                  handleConfigChange({ model: value });
                }}>
                  <SelectTrigger disabled={isProcessing}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gemini-1.5-pro">Gemini 1.5 Pro (고품질)</SelectItem>
                    <SelectItem value="gemini-1.5-flash">Gemini 1.5 Flash (빠름)</SelectItem>
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
                  disabled={isProcessing}
                />
              </div>
            </div>

            {/* 시작 버튼 */}
            <Button
              onClick={handleStartBatch}
              disabled={videoFiles.length === 0 || !jobName.trim() || isCreatingJob || isProcessing}
              className="w-full bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700"
              size="lg"
            >
              {isCreatingJob ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  배치 작업 생성 중...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  배치 분석 시작 ({videoFiles.length}개 파일)
                </>
              )}
            </Button>
          </TabsContent>

          <TabsContent value="progress" className="space-y-6">
            {currentJob ? (
              <div className="space-y-6">
                {/* 작업 정보 */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="p-4 text-center">
                      <BarChart3 className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                      <div className="text-2xl font-bold">{currentJob.progress_percentage.toFixed(1)}%</div>
                      <div className="text-sm text-gray-500">진행률</div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4 text-center">
                      <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
                      <div className="text-2xl font-bold">{currentJob.completed_items}</div>
                      <div className="text-sm text-gray-500">완료된 파일</div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4 text-center">
                      <Clock className="h-8 w-8 mx-auto mb-2 text-orange-500" />
                      <div className="text-2xl font-bold">
                        {currentJob.estimated_remaining_time ? formatTime(currentJob.estimated_remaining_time) : '--'}
                      </div>
                      <div className="text-sm text-gray-500">예상 남은 시간</div>
                    </CardContent>
                  </Card>
                </div>

                {/* 진행률 바 */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{currentJob.job_name}</span>
                    <span>{currentJob.processed_items} / {currentJob.total_items}</span>
                  </div>
                  <Progress value={currentJob.progress_percentage} className="h-3" />
                </div>

                {/* 상태 정보 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="text-center p-3 border rounded">
                    <div className="font-semibold text-blue-600">{currentJob.total_items}</div>
                    <div className="text-gray-500">총 파일</div>
                  </div>
                  <div className="text-center p-3 border rounded">
                    <div className="font-semibold text-green-600">{currentJob.completed_items}</div>
                    <div className="text-gray-500">완료</div>
                  </div>
                  <div className="text-center p-3 border rounded">
                    <div className="font-semibold text-red-600">{currentJob.failed_items}</div>
                    <div className="text-gray-500">실패</div>
                  </div>
                  <div className="text-center p-3 border rounded">
                    <div className="font-semibold text-orange-600">
                      {currentJob.average_processing_time.toFixed(1)}초
                    </div>
                    <div className="text-gray-500">평균 시간</div>
                  </div>
                </div>

                {/* 제어 버튼 */}
                {isProcessing && (
                  <div className="flex justify-center">
                    <Button
                      onClick={handleCancelBatch}
                      variant="destructive"
                      size="sm"
                    >
                      <StopCircle className="h-4 w-4 mr-2" />
                      배치 작업 취소
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <Layers className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-500">배치 작업을 시작하면 진행 상황이 여기에 표시됩니다</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="results" className="space-y-6">
            {batchResults.length > 0 ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">배치 분석 결과</h3>
                  <Badge variant="outline">
                    {batchResults.length}개 결과
                  </Badge>
                </div>

                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>파일</TableHead>
                        <TableHead>상태</TableHead>
                        <TableHead>처리 시간</TableHead>
                        <TableHead>결과</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {batchResults.map((result, index) => (
                        <TableRow key={result.item_id}>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <FileVideo className="h-4 w-4" />
                              <span className="text-sm">
                                {result.analysis_config?.item_name || `Video ${index + 1}`}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            {result.status === 'completed' ? (
                              <Badge variant="default" className="bg-green-100 text-green-700">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                완료
                              </Badge>
                            ) : result.status === 'failed' ? (
                              <Badge variant="destructive">
                                <AlertCircle className="h-3 w-3 mr-1" />
                                실패
                              </Badge>
                            ) : (
                              <Badge variant="outline">
                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                처리중
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <span className="text-sm">
                              {result.processing_time_seconds.toFixed(1)}초
                            </span>
                          </TableCell>
                          <TableCell>
                            {result.status === 'completed' && result.result ? (
                              <Button variant="outline" size="sm">
                                <Download className="h-3 w-3 mr-1" />
                                결과 보기
                              </Button>
                            ) : result.status === 'failed' ? (
                              <span className="text-xs text-red-600">{result.error}</span>
                            ) : (
                              <span className="text-xs text-gray-500">처리 중...</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-500">배치 분석이 완료되면 결과가 여기에 표시됩니다</p>
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* 상태 요약 */}
        <div className="flex items-center justify-center gap-6 text-sm text-gray-500">
          <div className="flex items-center gap-1">
            <Layers className="h-4 w-4" />
            <span>{videoFiles.length} 파일</span>
          </div>
          <div className="flex items-center gap-1">
            <Zap className="h-4 w-4" />
            <span>{analysisType}</span>
          </div>
          <div className="flex items-center gap-1">
            <Settings className="h-4 w-4" />
            <span>{model}</span>
          </div>
          {currentJob && (
            <div className="flex items-center gap-1">
              <TrendingUp className="h-4 w-4" />
              <span>{currentJob.progress_percentage.toFixed(0)}% 완료</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}