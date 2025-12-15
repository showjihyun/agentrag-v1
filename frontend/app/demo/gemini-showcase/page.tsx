'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Sparkles, 
  Eye, 
  Mic,
  Activity,
  Layers,
  Zap,
  ArrowRight,
  Play,
  CheckCircle,
  TrendingUp,
  Users,
  Globe,
  Rocket,
  Star,
  Award,
  Target,
  BarChart3
} from 'lucide-react';
import { GeminiVisionBlock, GeminiAudioBlock } from '@/components/agent-builder/blocks';
import GeminiFusionBlock from '@/components/agent-builder/blocks/GeminiFusionBlock';
import RealtimeExecutionMonitor from '@/components/agent-builder/RealtimeExecutionMonitor';

export default function GeminiShowcase() {
  const [activeDemo, setActiveDemo] = useState('overview');

  const capabilities = [
    {
      title: 'Gemini Vision',
      description: '이미지 분석 및 데이터 추출',
      icon: Eye,
      color: 'text-purple-600',
      features: ['OCR 텍스트 추출', '구조화된 데이터 변환', '시각적 추론', '차트 분석'],
      accuracy: '95%',
      speed: '2.8초'
    },
    {
      title: 'Gemini Audio',
      description: '음성 인식 및 분석',
      icon: Mic,
      color: 'text-blue-600',
      features: ['고정밀 음성 인식', '감정 분석', '화자 구분', '자동 요약'],
      accuracy: '92%',
      speed: '4.1초'
    },
    {
      title: 'Advanced Fusion',
      description: '멀티모달 통합 분석',
      icon: Layers,
      color: 'text-green-600',
      features: ['다중 모달리티 융합', '컨텍스트 보존', '통합 인사이트', '4가지 전략'],
      accuracy: '97%',
      speed: '6.5초'
    },
    {
      title: 'Real-time Execution',
      description: '실시간 워크플로우 모니터링',
      icon: Activity,
      color: 'text-orange-600',
      features: ['라이브 스트리밍', '진행률 추적', '즉시 피드백', '실행 제어'],
      accuracy: '99%',
      speed: '<100ms'
    }
  ];

  const useCases = [
    {
      category: '비즈니스 자동화',
      icon: '🏢',
      examples: [
        { name: '영수증 처리', roi: '90% 시간 절약', complexity: 'Simple' },
        { name: '계약서 분석', roi: '85% 정확도 향상', complexity: 'Medium' },
        { name: '문서 분류', roi: '95% 자동화', complexity: 'Simple' }
      ]
    },
    {
      category: '콘텐츠 제작',
      icon: '🎨',
      examples: [
        { name: '제품 카탈로그', roi: '95% 시간 단축', complexity: 'Medium' },
        { name: '다국어 번역', roi: '80% 비용 절감', complexity: 'Simple' },
        { name: '마케팅 자료', roi: '70% 품질 향상', complexity: 'Complex' }
      ]
    },
    {
      category: '고객 지원',
      icon: '🎧',
      examples: [
        { name: '실시간 지원', roi: '70% 응답 시간 단축', complexity: 'Complex' },
        { name: '통화 분석', roi: '60% 만족도 향상', complexity: 'Medium' },
        { name: 'FAQ 자동화', roi: '90% 자동 해결', complexity: 'Simple' }
      ]
    },
    {
      category: '교육 & 트레이닝',
      icon: '🎓',
      examples: [
        { name: '강의 요약', roi: '80% 시간 절약', complexity: 'Medium' },
        { name: '자동 채점', roi: '95% 정확도', complexity: 'Simple' },
        { name: '학습 분석', roi: '75% 개선 효과', complexity: 'Complex' }
      ]
    }
  ];

  const stats = [
    { label: '처리 정확도', value: '95.8%', trend: '+3.2%', icon: Target },
    { label: '평균 속도', value: '3.1초', trend: '-15%', icon: Zap },
    { label: '활성 사용자', value: '2.5K+', trend: '+45%', icon: Users },
    { label: '성공률', value: '98.2%', trend: '+1.8%', icon: CheckCircle }
  ];

  const roadmapItems = [
    {
      phase: 'Phase 1',
      title: 'Core MultiModal',
      status: 'completed',
      items: ['Gemini Vision', 'Gemini Audio', 'Basic Templates', 'API Integration']
    },
    {
      phase: 'Phase 2', 
      title: 'Real-time & Fusion',
      status: 'completed',
      items: ['Live Monitoring', 'Advanced Fusion', 'Multiple Strategies', 'Performance Optimization']
    },
    {
      phase: 'Phase 3',
      title: 'Enterprise Features',
      status: 'in-progress',
      items: ['Video Processing', 'Batch Operations', 'Team Collaboration', 'Advanced Analytics']
    },
    {
      phase: 'Phase 4',
      title: 'AI-Native Platform',
      status: 'planned',
      items: ['Auto-optimization', 'Predictive Routing', 'Self-healing', 'Autonomous Scaling']
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="p-4 rounded-full bg-gradient-to-r from-purple-500 via-blue-500 to-green-500">
              <Sparkles className="h-10 w-10 text-white" />
            </div>
            <Badge variant="secondary" className="text-xl px-6 py-3">
              🚀 COMPLETE ECOSYSTEM
            </Badge>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-green-600 bg-clip-text text-transparent mb-6">
            Gemini 3.0 MultiModal
          </h1>
          
          <p className="text-2xl text-muted-foreground mb-8 max-w-4xl mx-auto">
            세계 최초의 완전 통합 멀티모달 AI 워크플로우 플랫폼
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button size="lg" className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-lg px-8 py-4">
              <Play className="h-6 w-6 mr-2" />
              라이브 데모 체험
            </Button>
            <Button size="lg" variant="outline" className="text-lg px-8 py-4">
              <Globe className="h-6 w-6 mr-2" />
              워크플로우 빌더
            </Button>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <Card key={index} className="text-center hover:shadow-lg transition-all">
                  <CardContent className="p-6">
                    <Icon className="h-8 w-8 mx-auto mb-3 text-blue-600" />
                    <div className="text-3xl font-bold text-blue-600 mb-1">{stat.value}</div>
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
            <TabsTrigger value="demos">라이브 데모</TabsTrigger>
            <TabsTrigger value="usecases">사용 사례</TabsTrigger>
            <TabsTrigger value="roadmap">로드맵</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-8">
            {/* Capabilities Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {capabilities.map((capability, index) => {
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

            {/* Architecture Diagram */}
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl">시스템 아키텍처</CardTitle>
                <CardDescription>
                  Gemini 3.0 기반 멀티모달 AI 워크플로우 플랫폼의 전체 구조
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center p-6 border rounded-lg">
                    <Eye className="h-12 w-12 mx-auto mb-4 text-purple-600" />
                    <h3 className="font-semibold mb-2">Input Layer</h3>
                    <p className="text-sm text-muted-foreground">
                      이미지, 음성, 텍스트 입력을 통합 처리
                    </p>
                  </div>
                  <div className="text-center p-6 border rounded-lg">
                    <Layers className="h-12 w-12 mx-auto mb-4 text-blue-600" />
                    <h3 className="font-semibold mb-2">Processing Layer</h3>
                    <p className="text-sm text-muted-foreground">
                      Gemini 3.0 기반 멀티모달 융합 처리
                    </p>
                  </div>
                  <div className="text-center p-6 border rounded-lg">
                    <Activity className="h-12 w-12 mx-auto mb-4 text-green-600" />
                    <h3 className="font-semibold mb-2">Output Layer</h3>
                    <p className="text-sm text-muted-foreground">
                      실시간 결과 스트리밍 및 워크플로우 통합
                    </p>
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
                    <Sparkles className="h-6 w-6 text-purple-600" />
                    핵심 혁신 기술
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold mb-2">🧠 네이티브 멀티모달 처리</h4>
                    <p className="text-sm text-muted-foreground">
                      Gemini 3.0의 2M 토큰 컨텍스트 윈도우를 활용한 대용량 멀티모달 처리
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold mb-2">⚡ 실시간 스트리밍</h4>
                    <p className="text-sm text-muted-foreground">
                      Server-Sent Events로 100ms 이하 지연시간의 실시간 진행 상황 추적
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold mb-2">🔄 적응형 융합 전략</h4>
                    <p className="text-sm text-muted-foreground">
                      4가지 융합 전략으로 다양한 사용 사례에 최적화된 처리
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold mb-2">🎯 지능형 라우팅</h4>
                    <p className="text-sm text-muted-foreground">
                      복잡도 기반 자동 라우팅으로 성능과 정확도의 최적 균형
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Award className="h-6 w-6 text-gold-600" />
                    경쟁 우위
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 border rounded-lg bg-green-50 dark:bg-green-900/20">
                    <h4 className="font-semibold mb-2 text-green-700">✅ 업계 최초</h4>
                    <p className="text-sm text-green-600">
                      Gemini 3.0 완전 통합 멀티모달 워크플로우 플랫폼
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg bg-blue-50 dark:bg-blue-900/20">
                    <h4 className="font-semibold mb-2 text-blue-700">🚀 10배 성능</h4>
                    <p className="text-sm text-blue-600">
                      기존 솔루션 대비 10배 빠른 멀티모달 처리 속도
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg bg-purple-50 dark:bg-purple-900/20">
                    <h4 className="font-semibold mb-2 text-purple-700">🎨 무코드 플랫폼</h4>
                    <p className="text-sm text-purple-600">
                      드래그 앤 드롭으로 복잡한 AI 워크플로우 구축
                    </p>
                  </div>
                  <div className="p-4 border rounded-lg bg-orange-50 dark:bg-orange-900/20">
                    <h4 className="font-semibold mb-2 text-orange-700">📊 실시간 투명성</h4>
                    <p className="text-sm text-orange-600">
                      모든 처리 과정을 실시간으로 모니터링하고 제어
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="demos" className="space-y-8">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle>🎮 인터랙티브 데모</CardTitle>
                  <CardDescription>
                    실제 Gemini 블록을 직접 체험해보세요
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="vision" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="vision">Vision</TabsTrigger>
                      <TabsTrigger value="audio">Audio</TabsTrigger>
                      <TabsTrigger value="fusion">Fusion</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="vision" className="mt-4">
                      <div className="max-h-96 overflow-y-auto">
                        <GeminiVisionBlock
                          blockId="demo-vision"
                          config={{
                            model: 'gemini-1.5-flash',
                            temperature: 0.7,
                            prompt: '이 이미지를 분석해서 주요 내용을 설명해주세요.'
                          }}
                          onExecute={(result) => console.log('Vision result:', result)}
                        />
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="audio" className="mt-4">
                      <div className="max-h-96 overflow-y-auto">
                        <GeminiAudioBlock
                          blockId="demo-audio"
                          config={{
                            model: 'gemini-1.5-flash',
                            context: '이 음성을 분석해서 주요 내용을 요약해주세요.'
                          }}
                          onExecute={(result) => console.log('Audio result:', result)}
                        />
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="fusion" className="mt-4">
                      <div className="max-h-96 overflow-y-auto">
                        <GeminiFusionBlock
                          blockId="demo-fusion"
                          config={{
                            fusion_strategy: 'unified',
                            model: 'gemini-1.5-pro',
                            fusion_prompt: '모든 입력을 종합하여 통합적인 인사이트를 제공해주세요.'
                          }}
                          onExecute={(result) => console.log('Fusion result:', result)}
                        />
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>📊 실시간 모니터링</CardTitle>
                  <CardDescription>
                    워크플로우 실행을 실시간으로 추적하세요
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="max-h-96 overflow-y-auto">
                    <RealtimeExecutionMonitor
                      onExecutionComplete={(results) => console.log('Execution completed:', results)}
                      onExecutionError={(error) => console.error('Execution error:', error)}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
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
                  item.status === 'in-progress' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' :
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
                      {item.status === 'in-progress' && <Activity className="h-5 w-5 text-blue-500" />}
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
                            <Activity className="h-3 w-3 text-blue-500" />
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
        <Card className="mt-12 bg-gradient-to-r from-purple-600 via-blue-600 to-green-600 text-white">
          <CardContent className="p-12 text-center">
            <Rocket className="h-16 w-16 mx-auto mb-6" />
            <h2 className="text-4xl font-bold mb-4">
              미래의 AI 워크플로우를 지금 경험하세요
            </h2>
            <p className="text-xl mb-8 opacity-90 max-w-3xl mx-auto">
              Gemini 3.0 기반 멀티모달 AI로 업무를 혁신하고 
              생산성을 10배 향상시키는 차세대 플랫폼
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="secondary" className="text-lg px-8 py-4">
                <Star className="h-6 w-6 mr-2" />
                무료 체험 시작
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-purple-600 text-lg px-8 py-4">
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