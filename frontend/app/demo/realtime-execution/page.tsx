'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  Zap, 
  Eye, 
  Mic,
  Globe,
  Play,
  Clock,
  TrendingUp,
  Sparkles,
  ArrowRight,
  CheckCircle,
  Users,
  BarChart3
} from 'lucide-react';
import RealtimeExecutionMonitor from '@/components/agent-builder/RealtimeExecutionMonitor';

export default function RealtimeExecutionDemo() {
  const [activeTab, setActiveTab] = useState('monitor');

  const features = [
    {
      icon: Activity,
      title: '실시간 스트리밍',
      description: 'Server-Sent Events로 실시간 진행 상황 추적',
      color: 'text-blue-600'
    },
    {
      icon: Eye,
      title: '블록별 모니터링',
      description: '각 워크플로우 블록의 상세한 실행 상태',
      color: 'text-purple-600'
    },
    {
      icon: TrendingUp,
      title: '진행률 시각화',
      description: '직관적인 프로그레스 바와 통계',
      color: 'text-green-600'
    },
    {
      icon: Zap,
      title: '즉시 피드백',
      description: '오류 발생 시 즉시 알림 및 디버깅 정보',
      color: 'text-orange-600'
    }
  ];

  const sampleWorkflows = [
    {
      name: '멀티모달 데모',
      description: '이미지 분석 + 음성 처리 + API 호출',
      blocks: ['Gemini Vision', 'Gemini Audio', 'HTTP Request'],
      duration: '~10초',
      complexity: 'Medium'
    },
    {
      name: '영수증 처리',
      description: '영수증 이미지 → 데이터 추출 → Excel 저장',
      blocks: ['Image Upload', 'Gemini Vision', 'Excel Export'],
      duration: '~5초',
      complexity: 'Simple'
    },
    {
      name: '회의록 생성',
      description: '음성 녹음 → 텍스트 변환 → 요약 → 공유',
      blocks: ['Audio Upload', 'Gemini Audio', 'Summarization', 'Slack'],
      duration: '~15초',
      complexity: 'Complex'
    }
  ];

  const performanceMetrics = [
    { label: '평균 응답 시간', value: '2.3초', trend: '+15%' },
    { label: '성공률', value: '98.5%', trend: '+2%' },
    { label: '동시 실행', value: '50+', trend: '+25%' },
    { label: '처리량', value: '1K/시간', trend: '+30%' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="p-3 rounded-full bg-gradient-to-r from-blue-500 to-purple-500">
              <Activity className="h-8 w-8 text-white" />
            </div>
            <Badge variant="secondary" className="text-lg px-4 py-2">
              ⚡ REAL-TIME
            </Badge>
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
            실시간 워크플로우 실행
          </h1>
          
          <p className="text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            멀티모달 AI 워크플로우의 실행 과정을 실시간으로 모니터링하고 
            각 단계별 진행 상황을 라이브로 확인하세요.
          </p>

          {/* Performance Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 max-w-4xl mx-auto">
            {performanceMetrics.map((metric, index) => (
              <Card key={index} className="text-center">
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-blue-600">{metric.value}</div>
                  <div className="text-sm text-muted-foreground">{metric.label}</div>
                  <div className="text-xs text-green-600 mt-1">{metric.trend}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card key={index} className="hover:shadow-lg transition-all">
                <CardHeader className="pb-3">
                  <div className={`p-3 rounded-lg bg-gray-100 dark:bg-gray-800 w-fit ${feature.color}`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                  <CardDescription className="text-sm">
                    {feature.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            );
          })}
        </div>

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="monitor" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              실시간 모니터
            </TabsTrigger>
            <TabsTrigger value="workflows" className="flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              샘플 워크플로우
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              성능 분석
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="monitor" className="mt-6">
            <RealtimeExecutionMonitor 
              onExecutionComplete={(results) => {
                console.log('Execution completed:', results);
              }}
              onExecutionError={(error) => {
                console.error('Execution error:', error);
              }}
            />
          </TabsContent>
          
          <TabsContent value="workflows" className="mt-6">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>샘플 워크플로우</CardTitle>
                  <CardDescription>
                    다양한 복잡도의 멀티모달 워크플로우를 체험해보세요
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {sampleWorkflows.map((workflow, index) => (
                      <Card key={index} className="hover:shadow-md transition-all">
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between mb-2">
                            <Badge variant={
                              workflow.complexity === 'Simple' ? 'secondary' :
                              workflow.complexity === 'Medium' ? 'default' : 'destructive'
                            }>
                              {workflow.complexity}
                            </Badge>
                            <div className="flex items-center gap-1 text-sm text-muted-foreground">
                              <Clock className="h-4 w-4" />
                              {workflow.duration}
                            </div>
                          </div>
                          <CardTitle className="text-lg">{workflow.name}</CardTitle>
                          <CardDescription className="text-sm">
                            {workflow.description}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            <div>
                              <p className="text-sm font-medium mb-2">워크플로우 블록:</p>
                              <div className="flex flex-wrap gap-1">
                                {workflow.blocks.map((block, blockIndex) => (
                                  <Badge key={blockIndex} variant="outline" className="text-xs">
                                    {block}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                            <Button className="w-full gap-2" variant="outline">
                              <Play className="h-4 w-4" />
                              실행해보기
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          
          <TabsContent value="analytics" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>실행 통계</CardTitle>
                  <CardDescription>
                    실시간 워크플로우 실행 성능 지표
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center gap-3">
                        <CheckCircle className="h-5 w-5 text-green-500" />
                        <span>성공한 실행</span>
                      </div>
                      <span className="font-semibold">1,247</span>
                    </div>
                    
                    <div className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center gap-3">
                        <Clock className="h-5 w-5 text-blue-500" />
                        <span>평균 실행 시간</span>
                      </div>
                      <span className="font-semibold">8.3초</span>
                    </div>
                    
                    <div className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center gap-3">
                        <Users className="h-5 w-5 text-purple-500" />
                        <span>활성 사용자</span>
                      </div>
                      <span className="font-semibold">156</span>
                    </div>
                    
                    <div className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center gap-3">
                        <TrendingUp className="h-5 w-5 text-orange-500" />
                        <span>처리량 (시간당)</span>
                      </div>
                      <span className="font-semibold">892</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>블록 타입별 성능</CardTitle>
                  <CardDescription>
                    각 블록 타입의 평균 실행 시간
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Eye className="h-4 w-4 text-purple-500" />
                        <span className="text-sm">Gemini Vision</span>
                      </div>
                      <span className="text-sm font-medium">2.8초</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Mic className="h-4 w-4 text-blue-500" />
                        <span className="text-sm">Gemini Audio</span>
                      </div>
                      <span className="text-sm font-medium">4.1초</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Globe className="h-4 w-4 text-green-500" />
                        <span className="text-sm">HTTP Request</span>
                      </div>
                      <span className="text-sm font-medium">0.9초</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4 text-orange-500" />
                        <span className="text-sm">Code Execution</span>
                      </div>
                      <span className="text-sm font-medium">1.5초</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {/* CTA Section */}
        <Card className="mt-12 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
          <CardContent className="p-8 text-center">
            <h2 className="text-3xl font-bold mb-4">
              실시간 모니터링으로 워크플로우를 완전히 제어하세요
            </h2>
            <p className="text-lg mb-6 opacity-90">
              각 단계별 진행 상황을 실시간으로 추적하고, 문제 발생 시 즉시 대응할 수 있습니다
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="secondary">
                <Activity className="h-5 w-5 mr-2" />
                지금 체험하기
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