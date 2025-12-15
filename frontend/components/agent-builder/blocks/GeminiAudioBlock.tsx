'use client';

import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Mic, 
  Upload, 
  Play, 
  Pause,
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Volume2,
  FileAudio
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface GeminiAudioBlockProps {
  blockId: string;
  config?: {
    model?: string;
    context?: string;
  };
  onConfigChange?: (config: any) => void;
  onExecute?: (result: any) => void;
  isExecuting?: boolean;
}

interface AudioAnalysisResult {
  success: boolean;
  transcript?: string;
  analysis?: string;
  processing_time_seconds?: number;
  error?: string;
}

export default function GeminiAudioBlock({
  blockId,
  config = {},
  onConfigChange,
  onExecute,
  isExecuting = false
}: GeminiAudioBlockProps) {
  const { toast } = useToast();
  const [selectedAudio, setSelectedAudio] = useState<File | null>(null);
  const [context, setContext] = useState(config.context || '');
  const [result, setResult] = useState<AudioAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // 미리 정의된 컨텍스트 템플릿
  const contextTemplates = [
    {
      name: '회의 요약',
      context: '이 회의 녹음을 분석해서 주요 논의사항, 결정사항, 액션 아이템을 정리해주세요.',
      icon: '👥'
    },
    {
      name: '고객 통화 분석',
      context: '이 고객 통화를 분석해서 고객의 감정 상태, 주요 요구사항, 만족도를 평가해주세요.',
      icon: '📞'
    },
    {
      name: '강의 요약',
      context: '이 강의 내용을 요약하고 핵심 개념들을 정리해주세요.',
      icon: '🎓'
    },
    {
      name: '인터뷰 분석',
      context: '이 인터뷰를 분석해서 주요 답변과 인사이트를 추출해주세요.',
      icon: '🎤'
    },
    {
      name: '음성 명령 처리',
      context: '이 음성 명령을 인식하고 적절한 액션을 제안해주세요.',
      icon: '🗣️'
    }
  ];

  const handleAudioUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 파일 크기 검증 (25MB)
    if (file.size > 25 * 1024 * 1024) {
      toast({
        title: '파일 크기 초과',
        description: '음성 파일은 25MB 이하여야 합니다.',
        variant: 'destructive'
      });
      return;
    }

    // 음성 파일 검증
    if (!file.type.startsWith('audio/')) {
      toast({
        title: '잘못된 파일 형식',
        description: '음성 파일만 업로드할 수 있습니다.',
        variant: 'destructive'
      });
      return;
    }

    setSelectedAudio(file);
    
    // 오디오 URL 생성 (재생용)
    const url = URL.createObjectURL(file);
    setAudioUrl(url);
  }, [toast]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        const file = new File([blob], 'recording.wav', { type: 'audio/wav' });
        setSelectedAudio(file);
        
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        
        // 스트림 정리
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);

      toast({
        title: '녹음 시작',
        description: '음성 녹음이 시작되었습니다.'
      });
    } catch (error) {
      console.error('Recording failed:', error);
      toast({
        title: '녹음 실패',
        description: '마이크 접근 권한을 확인해주세요.',
        variant: 'destructive'
      });
    }
  }, [toast]);

  const stopRecording = useCallback(() => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setMediaRecorder(null);
      setIsRecording(false);
      
      toast({
        title: '녹음 완료',
        description: '음성 녹음이 완료되었습니다.'
      });
    }
  }, [mediaRecorder, isRecording, toast]);

  const handleAnalyze = useCallback(async () => {
    if (!selectedAudio || !context.trim()) {
      toast({
        title: '입력 필요',
        description: '음성 파일과 분석 컨텍스트를 모두 입력해주세요.',
        variant: 'destructive'
      });
      return;
    }

    setIsAnalyzing(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedAudio);
      formData.append('context', context);
      formData.append('model', config.model || 'gemini-1.5-flash');

      const response = await fetch('/api/agent-builder/gemini/upload-and-analyze-audio', {
        method: 'POST',
        body: formData
      });

      const analysisResult = await response.json();
      
      if (analysisResult.success) {
        setResult(analysisResult);
        onExecute?.(analysisResult);
        
        toast({
          title: '분석 완료',
          description: `음성 분석이 완료되었습니다.`
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
  }, [selectedAudio, context, config.model, onExecute, toast]);

  const handleConfigChange = useCallback((newConfig: any) => {
    onConfigChange?.({
      ...config,
      ...newConfig
    });
  }, [config, onConfigChange]);

  const applyTemplate = useCallback((template: typeof contextTemplates[0]) => {
    setContext(template.context);
    handleConfigChange({ context: template.context });
  }, [handleConfigChange]);

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
            <Mic className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <CardTitle className="flex items-center gap-2">
              Gemini Audio Processor
              <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                <Volume2 className="h-3 w-3 mr-1" />
                AI Audio
              </Badge>
            </CardTitle>
            <CardDescription>
              Google Gemini 3.0을 활용한 고급 음성 분석 및 텍스트 변환
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* 음성 입력 영역 */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">음성 입력</h3>
            {selectedAudio && (
              <Badge variant="outline" className="text-green-600">
                <CheckCircle className="h-3 w-3 mr-1" />
                {selectedAudio.name}
              </Badge>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 파일 업로드 */}
            <div className="space-y-2">
              <label htmlFor={`audio-upload-${blockId}`} className="cursor-pointer">
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
                  <Upload className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    클릭하여 음성 파일 업로드
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    MP3, WAV, M4A (최대 25MB)
                  </p>
                </div>
              </label>
              <input
                id={`audio-upload-${blockId}`}
                type="file"
                accept="audio/*"
                onChange={handleAudioUpload}
                className="hidden"
              />
            </div>

            {/* 실시간 녹음 */}
            <div className="space-y-2">
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
                <Mic className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  실시간 음성 녹음
                </p>
                <Button
                  onClick={isRecording ? stopRecording : startRecording}
                  variant={isRecording ? "destructive" : "outline"}
                  size="sm"
                >
                  {isRecording ? (
                    <>
                      <Pause className="h-4 w-4 mr-2" />
                      녹음 중지
                    </>
                  ) : (
                    <>
                      <Mic className="h-4 w-4 mr-2" />
                      녹음 시작
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* 오디오 재생 */}
          {audioUrl && (
            <div className="p-4 border rounded-lg bg-gray-50 dark:bg-gray-900">
              <div className="flex items-center gap-3">
                <FileAudio className="h-5 w-5 text-blue-500" />
                <span className="text-sm font-medium">음성 미리듣기</span>
              </div>
              <audio controls className="w-full mt-2">
                <source src={audioUrl} type="audio/wav" />
                브라우저가 오디오를 지원하지 않습니다.
              </audio>
            </div>
          )}
        </div>

        {/* 컨텍스트 템플릿 */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">분석 유형</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
            {contextTemplates.map((template, index) => (
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

        {/* 분석 컨텍스트 */}
        <div className="space-y-2">
          <label className="text-sm font-medium">분석 컨텍스트</label>
          <Textarea
            value={context}
            onChange={(e) => {
              setContext(e.target.value);
              handleConfigChange({ context: e.target.value });
            }}
            placeholder="음성을 어떻게 분석할지 설명해주세요..."
            className="min-h-[100px]"
          />
        </div>

        {/* 실행 버튼 */}
        <Button
          onClick={handleAnalyze}
          disabled={!selectedAudio || !context.trim() || isAnalyzing || isExecuting}
          className="w-full bg-blue-600 hover:bg-blue-700"
          size="lg"
        >
          {(isAnalyzing || isExecuting) ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              분석 중...
            </>
          ) : (
            <>
              <Volume2 className="h-4 w-4 mr-2" />
              음성 분석 시작
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
                {result.transcript && (
                  <div className="p-3 bg-white dark:bg-gray-800 rounded border">
                    <h4 className="text-sm font-medium mb-2">음성 텍스트 변환</h4>
                    <p className="text-sm whitespace-pre-wrap">{result.transcript}</p>
                  </div>
                )}

                {result.analysis && result.analysis !== result.transcript && (
                  <div className="p-3 bg-white dark:bg-gray-800 rounded border">
                    <h4 className="text-sm font-medium mb-2">분석 결과</h4>
                    <p className="text-sm whitespace-pre-wrap">{result.analysis}</p>
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