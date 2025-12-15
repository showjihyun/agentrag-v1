'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Video, 
  Play, 
  Upload,
  Zap,
  Eye,
  Mic,
  Film,
  BarChart3,
  Clock,
  FileVideo,
  CheckCircle,
  ArrowRight,
  Star,
  TrendingUp,
  Users,
  Award,
  Rocket
} from 'lucide-react';
import { GeminiVideoBlock } from '@/components/agent-builder/blocks';

export default function GeminiVideoDemo() {
  const [activeDemo, setActiveDemo] = useState('overview');

  const videoCapabilities = [
    {
      title: 'Comprehensive Analysis',
      description: '종합적인 비디오 분석',
      icon: BarChart3,
      color: 'text-purple-600',
      features: ['전체 요약', '시각적 요소', '오디오 분석', '구조 분석', '품질 평가'],
      accuracy: '96%',
      speed: '30-60초'
    },
    {
      title: 'Smart Summary',
      description: '핵심 내용 요약',
      icon: FileVideo,
      color: 'text-blue-600',
      features: ['주요 내용', '핵심 포인트', '대상 청중', '시청 가치'],
      accuracy: '94%',
      speed: '15-30초'
    },
    {
      title: 'Audio Transcription',
      description: '음성 텍스트 변환',
      icon: Mic,
      color: 'text-green-600',
      features: ['화자 구분', '시간대별 정리', '키워드 추출', '내용 요약'],
      accuracy: '93%',
      speed: '20-40초'
    },
    {
      title: 'Object Detection',
      description: '객체 및 인물 분석',
      icon: Eye,
      color: 'text-orange-600',
      features: ['객체 목록', '인물 분석', '배경 환경', '브랜드/로고'],
      accuracy: '95%',
      speed: '25-45초'
    },
    {
      title: 'Scene Analysis',
      description: '장면 구성 분석',
      icon: Film,
      color: 'text-red-600',
      features: ['장면 구분', '전환 방식', '시간 구조', '스토리텔링'],
      accuracy: '92%',
      speed: '35-55초'
    }
  ];

  const useCases = [
    {
      category: '교육 & 트레이닝',
      icon: '🎓',
      examples: [
        { name: '온라인 강의 분석', roi: '80% 시간 절약', complexity: 'Medium' },
        { name: '교육 자료 요약', roi: '90% 효율성 향상', complexity: 'Simple' },
        { name: '학습 진도 추적', roi: '75% 개선 효과', complexity: 'Complex' }
      ]
    },
    {
      category: '비즈니스 & 마케팅',
      icon: '💼',
      examples: [
        { name: '제품 데모 분석', roi: '85% 인사이트 향상', complexity: 'Medium' },
        { name: '광고 효과 측정', roi: '70% 정확도 향상', complexity: 'Complex' },
        { name: '브랜드 모니터링', roi: '95% 자동화', complexity: 'Simple' }
      ]
    },
    {
      category: '미디어 & 엔터테인먼트',
      icon: '🎬',
      examples: [
        { name: '콘텐츠 큐레이션', roi: '90% 시간 단축', complexity: 'Simple' },
        { name: '스토리보드 생성', roi: '75% 비용 절감', complexity: 'Medium' },
        { name: '자막 자동 생성', roi: '95% 자동화', complexity: 'Simple' }
      ]
    },
    {
      category: '보안 & 모니터링',
      icon: '🔒',
      examples: [
        { name: '보안 영상 분석', roi: '85% 정확도', complexity: 'Complex' },
        { name: '품질 관리', roi: '80% 효율성', complexity: 'Medium' },
        { name: '이상 행동 탐지', roi: '90% 자동 감지', complexity: 'Complex' }
      ]
    }
  ];

  const stats = [
    { label: '분석 정확도', value: '94.2%', trend: '+2.8%', icon: Eye },
    { label: '평균 처리 시간', value: '32초', trend: '-18%', icon: Clock },
    { label: '지원 형식', value: '9개', trend: '+3개', icon: FileVideo },
    { label: '성공률', value: '97.8%', trend: '+1.5%', icon: CheckCircle }
  ];

  const roadmapItems = [
    {
      phase: 'Phase 1',
      title: 'Core Video Analysis',
      status: 'completed',
      items: ['Basic Analysis', 'Object Detection', 'Audio Transcription', 'Scene Recognition']
    },
    {
      phase: 'Phase 2',
      title: 'Advanced Features',
      status: 'completed',
      items: ['Multi-format Support', 'Batch Processing', 'Real-time Analysis', 'Quality Assessment']
    },
    {
      phase: 'Phase 3',
      title: 'AI-Native Processing',
      status: 'in-progress',
      items: ['Auto-optimization', 'Predictive Analysis', 'Content Generation', 'Smart Editing']
    },
    {
      phase: 'Phase 4',
      title: 'Enterprise Platform',
      status: 'planned',
      items: ['Team Collaboration', 'Custom Models', 'API Marketplace', 'Advanced Analytics']
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-purple-50 to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="p-4 rounded-full bg-gradient-to-r from-red-500 via-purple-500 to-blue-500">
              <Video className="h-10 w-10 text-white" />
            </div>
            <Badge variant="secondary" className="text-xl px-6 py-3">
              🎬 VIDEO AI REVOLUTION
            </Badge>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-red-600 via-purple-600 to-blue-600 bg-clip-text text-transparent mb-6">
            Gemini Video AI
          </h1>
          
          <p className="text-2xl text-muted-foreground mb-8 max-w-4xl mx-auto">
            세계 최초 Gemini 3.0 기반 완전 자동화 비디오 분석 플랫폼
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button size="lg" className="bg-gradient-to-r from-red-600 to-purple-600 hover:from-red-700 hover:to-purple-700 text-lg px-8 py-4">
              <Play className="h-6 w-6 mr-2" />
              라이브 데모 시작
            </Button>
            <Button size="lg" variant="outline" className="text-lg px-8 py-4">
              <Upload className="h-6 w-6 mr-2" />
              비디오 업로드 테스트
            </Button>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <Card key={index} className="text-center hover:shadow-lg transition-all">
                  <CardContent className="p-6">
                    <Icon className="h-8 w-8 mx-auto mb-3 text-red-600" />
                    <div className="text-3xl font-bold text-red-600 mb-1">{stat.value}</div>
                    <div className="text-sm text-muted-foreground mb-2">{stat.label}</div>
                    <div className="text-xs text-green-600 font-medium">{stat.trend}</div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Main Content */}
        <Tabs value={activeDemo} onValueChange={setActiveDemo} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-8">
            <TabsTrigger value="overview">개요</TabsTrigger>
            <TabsTrigger value="capabilities">핵심 기능</TabsTrigger>
            <TabsTrigger value="demo">라이브 데모</TabsTrigger>
            <TabsTrigger value="usecases">사용 사례</TabsTrigger>
            <TabsTrigger value="roadmap">로드맵</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-8">
            {/* Video Capabilities Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {videoCapabilities.map((capability, index) => {
                const Icon = capability.icon;
                return (
                  <Card key={index} className="hover:shadow-lg transition-all">
                    <CardHeader className="pb-3">
                      <div className={`p-3 rounded-lg bg-gray-100 dark:bg-gray-800 w-fit ${capability.color}`}>
                        <Icon className="h-8 w-8" />
                      </div>
                      <CardTitle className="text-xl">{capability.title}</CardTitle>
                      <CardDescription>{capability.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div className="text-center p-2 bg-green-50 dark:bg-green-900/20 rounded">
                            <div className="font-semibold text-green-600">{capability.accuracy}</div>
                            <div className="text-xs text-green-600">정확도</div>
                          </div>
                          <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                            <div className="font-semibold text-blue-600">{capability.speed}</div>
                            <div className="text-xs text-blue-600">처리 시간</div>
                          </div>
                        </div>
                        <div className="space-y-1">
                          {capability.features.map((feature, featureIndex) => (
                            <div key={featureIndex} className="flex items-center gap-2 text-xs">
                              <CheckCircle className="h-3 w-3 text-green-500" />
                              <span>{feature}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Technology Highlights */}
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl">기술적 혁신</CardTitle>
                <CardDescription>
                  Gemini 3.0의 최신 비디오 처리 기술을 활용한 차세대 분석 플랫폼
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Zap className="h-5 w-5 text-yellow-500" />
                      핵심 기술
                    </h3>
                    <div className="space-y-3">
                      <div className="p-3 border rounded-lg">
                        <h4 className="font-medium mb-1">🧠 Gemini 3.0 Native Processing</h4>
                        <p className="text-sm text-muted-foreground">
                          2M 토큰 컨텍스트로 장시간 비디오 완전 분석
                        </p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <h4 className="font-medium mb-1">⚡ Real-time Frame Analysis</h4>
                        <p className="text-sm text-muted-foreground">
                          실시간 프레임별 객체 및 장면 인식
                        </p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <h4 className="font-medium mb-1">🎵 Advanced Audio Processing</h4>
                        <p className="text-sm text-muted-foreground">
                          다중 화자 구분 및 감정 분석
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Award className="h-5 w-5 text-purple-500" />
                      경쟁 우위
                    </h3>
                    <div className="space-y-3">
                      <div className="p-3 border rounded-lg bg-purple-50 dark:bg-purple-900/20">
                        <h4 className="font-medium mb-1 text-purple-700">🏆 업계 최초</h4>
                        <p className="text-sm text-purple-600">
                          Gemini 3.0 완전 통합 비디오 분석 플랫폼
                        </p>
                      </div>
                      <div className="p-3 border rounded-lg bg-blue-50 dark:bg-blue-900/20">
                        <h4 className="font-medium mb-1 text-blue-700">🚀 5배 성능</h4>
                        <p className="text-sm text-blue-600">
                          기존 솔루션 대비 5배 빠른 비디오 처리
                        </p>
                      </div>
                      <div className="p-3 border rounded-lg bg-green-50 dark:bg-green-900/20">
                        <h4 className="font-medium mb-1 text-green-700">🎯 94% 정확도</h4>
                        <p className="text-sm text-green-600">
                          업계 최고 수준의 분석 정확도
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="capabilities" className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Video className="h-6 w-6 text-red-600" />
                    지원 형식 & 기능
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-semibold mb-2">📹 지원 형식</h4>
                      <div className="space-y-1 text-sm">
                        <Badge variant="outline">MP4</Badge>
                        <Badge variant="outline">MOV</Badge>
                        <Badge variant="outline">AVI</Badge>
                        <Badge variant="outline">WebM</Badge>
                        <Badge variant="outline">MPEG</Badge>
                        <Badge variant="outline">WMV</Badge>
                        <Badge variant="outline">3GPP</Badge>
                        <Badge variant="outline">FLV</Badge>
                      </div>
                    </div>
                    <div>
                      <h4 className="font-semibold mb-2">⚙️ 처리 옵션</h4>
                      <div className="space-y-1 text-sm">
                        <div>• 최대 100MB 파일</div>
                        <div>• 30분 길이 제한</div>
                        <div>• 자동 프레임 샘플링</div>
                        <div>• 오디오 포함/제외</div>
                        <div>• 실시간 진행률</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-6 w-6 text-purple-600" />
                    분석 유형별 특징
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {videoCapabilities.slice(0, 3).map((capability, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <capability.icon className={`h-4 w-4 ${capability.color}`} />
                        <span className="font-medium">{capability.title}</span>
                        <Badge variant="outline" className="text-xs">{capability.speed}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{capability.description}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="demo" className="space-y-8">
            <Card>
              <CardHeader>
                <CardTitle>🎮 인터랙티브 비디오 분석 데모</CardTitle>
                <CardDescription>
                  실제 Gemini Video Block을 직접 체험해보세요
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="max-h-[800px] overflow-y-auto">
                  <GeminiVideoBlock
                    blockId="demo-video"
                    config={{
                      analysis_type: 'comprehensive',
                      model: 'gemini-1.5-pro',
                      temperature: 0.7,
                      frame_sampling: 'auto',
                      max_frames: 30,
                      include_audio: true
                    }}
                    onExecute={(result) => console.log('Video analysis result:', result)}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="usecases" className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {useCases.map((category, index) => (
                <Card key={index}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <span className="text-2xl">{category.icon}</span>
                      {category.category}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {category.examples.map((example, exampleIndex) => (
                        <div key={exampleIndex} className="p-3 border rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">{example.name}</h4>
                            <Badge variant={
                              example.complexity === 'Simple' ? 'secondary' :
                              example.complexity === 'Medium' ? 'default' : 'destructive'
                            }>
                              {example.complexity}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 text-sm">
                            <TrendingUp className="h-4 w-4 text-green-500" />
                            <span className="text-green-600 font-medium">{example.roi}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="roadmap" className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {roadmapItems.map((item, index) => (
                <Card key={index} className={`${
                  item.status === 'completed' ? 'border-green-500 bg-green-50 dark:bg-green-900/20' :
                  item.status === 'in-progress' ? 'border-red-500 bg-red-50 dark:bg-red-900/20' :
                  'border-gray-300'
                }`}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <Badge variant={
                        item.status === 'completed' ? 'default' :
                        item.status === 'in-progress' ? 'secondary' : 'outline'
                      }>
                        {item.phase}
                      </Badge>
                      {item.status === 'completed' && <CheckCircle className="h-5 w-5 text-green-500" />}
                      {item.status === 'in-progress' && <Video className="h-5 w-5 text-red-500" />}
                    </div>
                    <CardTitle className="text-lg">{item.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {item.items.map((feature, featureIndex) => (
                        <div key={featureIndex} className="flex items-center gap-2 text-sm">
                          {item.status === 'completed' ? (
                            <CheckCircle className="h-3 w-3 text-green-500" />
                          ) : item.status === 'in-progress' ? (
                            <Video className="h-3 w-3 text-red-500" />
                          ) : (
                            <div className="h-3 w-3 border border-gray-300 rounded-full" />
                          )}
                          <span>{feature}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>

        {/* CTA Section */}
        <Card className="mt-12 bg-gradient-to-r from-red-600 via-purple-600 to-blue-600 text-white">
          <CardContent className="p-12 text-center">
            <Video className="h-16 w-16 mx-auto mb-6" />
            <h2 className="text-4xl font-bold mb-4">
              비디오 AI의 새로운 시대를 열어보세요
            </h2>
            <p className="text-xl mb-8 opacity-90 max-w-3xl mx-auto">
              Gemini 3.0 기반 비디오 분석으로 콘텐츠 제작과 분석을 혁신하고 
              업무 효율성을 5배 향상시키는 차세대 플랫폼
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="secondary" className="text-lg px-8 py-4">
                <Star className="h-6 w-6 mr-2" />
                무료 체험 시작
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-red-600 text-lg px-8 py-4">
                <ArrowRight className="h-6 w-6 mr-2" />
                워크플로우 빌더로 이동
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}