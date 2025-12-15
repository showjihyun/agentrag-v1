'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Eye, 
  Mic, 
  FileText, 
  Sparkles, 
  ArrowRight, 
  Play,
  Zap,
  TrendingUp,
  Users,
  Clock
} from 'lucide-react';
import { GeminiVisionBlock, GeminiAudioBlock, GeminiBlockRenderer } from '@/components/agent-builder/blocks';

export default function GeminiMultiModalDemo() {
  const [activeDemo, setActiveDemo] = useState<string>('vision');

  const demoStats = {
    accuracy: '95%',
    speed: '2.3s',
    languages: '100+',
    users: '10K+'
  };

  const useCases = [
    {
      title: '영수증 자동 처리',
      description: '영수증 사진을 업로드하면 자동으로 데이터를 추출하고 회계 시스템에 입력',
      icon: '🧾',
      category: 'Business',
      time: '30초',
      roi: '90% 시간 절약'
    },
    {
      title: '회의록 자동 생성',
      description: '회의 녹음을 업로드하면 자동으로 요약과 액션 아이템을 생성',
      icon: '👥',
      category: 'Productivity',
      time: '2분',
      roi: '80% 자동화'
    },
    {
      title: '제품 카탈로그 생성',
      description: '제품 사진으로 자동 설명 생성 및 다국어 카탈로그 제작',
      icon: '📦',
      category: 'E-commerce',
      time: '1분',
      roi: '95% 시간 단축'
    },
    {
      title: '고객 지원 자동화',
      description: '화면 공유와 음성을 실시간 분석해서 문제 해결',
      icon: '🎧',
      category: 'Support',
      time: '실시간',
      roi: '70% 응답 시간 단축'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="p-3 rounded-full bg-gradient-to-r from-purple-500 to-blue-500">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
            <Badge variant="secondary" className="text-lg px-4 py-2">
              🚀 NEW
            </Badge>
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-4">
            Gemini 3.0 MultiModal
          </h1>
          
          <p className="text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            Google의 최신 Gemini 3.0을 활용한 혁신적인 멀티모달 AI 워크플로우. 
            이미지, 음성, 텍스트를 동시에 처리하는 차세대 자동화 플랫폼.
          </p>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 max-w-2xl mx-auto">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{demoStats.accuracy}</div>
              <div className="text-sm text-muted-foreground">정확도</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{demoStats.speed}</div>
              <div className="text-sm text-muted-foreground">평균 처리 시간</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{demoStats.languages}</div>
              <div className="text-sm text-muted-foreground">지원 언어</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{demoStats.users}</div>
              <div className="text-sm text-muted-foreground">활성 사용자</div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700">
              <Play className="h-5 w-5 mr-2" />
              지금 체험하기
            </Button>
            <Button size="lg" variant="outline">
              <FileText className="h-5 w-5 mr-2" />
              문서 보기
            </Button>
          </div>
        </div>

        {/* Use Cases Grid */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-center mb-8">실제 사용 사례</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {useCases.map((useCase, index) => (
              <Card key={index} className="hover:shadow-lg transition-all cursor-pointer group">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-3xl">{useCase.icon}</span>
                    <Badge variant="outline">{useCase.category}</Badge>
                  </div>
                  <CardTitle className="text-lg group-hover:text-purple-600 transition-colors">
                    {useCase.title}
                  </CardTitle>
                  <CardDescription className="text-sm">
                    {useCase.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      {useCase.time}
                    </div>
                    <div className="flex items-center gap-1 text-green-600">
                      <TrendingUp className="h-4 w-4" />
                      {useCase.roi}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Interactive Demo */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="text-2xl text-center">
              🎮 인터랙티브 데모
            </CardTitle>
            <CardDescription className="text-center">
              실제 Gemini 3.0 블록을 체험해보세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={activeDemo} onValueChange={setActiveDemo} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="vision" className="flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  Vision
                </TabsTrigger>
                <TabsTrigger value="audio" className="flex items-center gap-2">
                  <Mic className="h-4 w-4" />
                  Audio
                </TabsTrigger>
                <TabsTrigger value="multimodal" className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4" />
                  MultiModal
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="vision" className="mt-6">
                <GeminiVisionBlock
                  blockId="demo-vision"
                  config={{
                    model: 'gemini-1.5-flash',
                    temperature: 0.7,
                    prompt: '이 이미지를 분석해서 주요 내용을 설명해주세요.'
                  }}
                  onExecute={(result) => {
                    console.log('Vision analysis result:', result);
                  }}
                />
              </TabsContent>
              
              <TabsContent value="audio" className="mt-6">
                <GeminiAudioBlock
                  blockId="demo-audio"
                  config={{
                    model: 'gemini-1.5-flash',
                    context: '이 음성을 분석해서 주요 내용을 요약해주세요.'
                  }}
                  onExecute={(result) => {
                    console.log('Audio analysis result:', result);
                  }}
                />
              </TabsContent>
              
              <TabsContent value="multimodal" className="mt-6">
                <div className="text-center py-12">
                  <Sparkles className="h-16 w-16 mx-auto mb-4 text-purple-500" />
                  <h3 className="text-xl font-semibold mb-2">고급 멀티모달 처리</h3>
                  <p className="text-muted-foreground mb-6">
                    텍스트, 이미지, 음성을 동시에 처리하는 차세대 AI 블록
                  </p>
                  <Badge variant="outline" className="text-lg px-6 py-2">
                    🚧 개발 중
                  </Badge>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Features Grid */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-center mb-8">핵심 기능</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <div className="p-3 rounded-full bg-purple-100 dark:bg-purple-900 w-fit">
                  <Eye className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <CardTitle>고급 이미지 분석</CardTitle>
                <CardDescription>
                  영수증, 문서, 차트, 제품 사진 등 모든 이미지를 정확하게 분석
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="text-sm space-y-2 text-muted-foreground">
                  <li>• OCR 및 텍스트 추출</li>
                  <li>• 구조화된 데이터 변환</li>
                  <li>• 다국어 지원</li>
                  <li>• 실시간 처리</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="p-3 rounded-full bg-blue-100 dark:bg-blue-900 w-fit">
                  <Mic className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <CardTitle>스마트 음성 처리</CardTitle>
                <CardDescription>
                  회의 녹음, 고객 통화, 팟캐스트 등 모든 음성을 지능적으로 분석
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="text-sm space-y-2 text-muted-foreground">
                  <li>• 고정밀 음성 인식</li>
                  <li>• 감정 및 의도 분석</li>
                  <li>• 자동 요약 생성</li>
                  <li>• 화자 구분</li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="p-3 rounded-full bg-green-100 dark:bg-green-900 w-fit">
                  <Zap className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
                <CardTitle>워크플로우 통합</CardTitle>
                <CardDescription>
                  드래그 앤 드롭으로 복잡한 멀티모달 워크플로우를 쉽게 구성
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="text-sm space-y-2 text-muted-foreground">
                  <li>• 비주얼 워크플로우 빌더</li>
                  <li>• 70+ 도구 연동</li>
                  <li>• 실시간 모니터링</li>
                  <li>• 자동 스케일링</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* CTA Section */}
        <Card className="bg-gradient-to-r from-purple-600 to-blue-600 text-white">
          <CardContent className="p-8 text-center">
            <h2 className="text-3xl font-bold mb-4">
              지금 시작하세요
            </h2>
            <p className="text-lg mb-6 opacity-90">
              Gemini 3.0 멀티모달 AI로 업무를 혁신하고 생산성을 10배 향상시키세요
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="secondary">
                <Users className="h-5 w-5 mr-2" />
                무료 체험 시작
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-purple-600">
                <ArrowRight className="h-5 w-5 mr-2" />
                워크플로우 빌더로 이동
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}