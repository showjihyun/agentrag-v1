"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  BarChart3, 
  Network, 
  TrendingUp, 
  Users, 
  Zap, 
  Target,
  Brain,
  Loader2,
  RefreshCw,
  Download,
  Info,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowUp,
  ArrowDown,
  Minus,
  Eye,
  Filter
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface NetworkMetrics {
  node_count: number;
  edge_count: number;
  density: number;
  average_degree: number;
  clustering_coefficient: number;
  diameter: number;
  connected_components: number;
  largest_component_size: number;
}

interface CentralityMetric {
  entity_id: string;
  entity_name: string;
  degree_centrality: number;
  betweenness_centrality: number;
  closeness_centrality: number;
  eigenvector_centrality: number;
  pagerank: number;
}

interface Community {
  id: number;
  entities: string[];
  size: number;
  density: number;
  modularity: number;
  dominant_types: string[];
  key_relationships: string[];
}

interface KnowledgePattern {
  pattern_type: string;
  description: string;
  entities: string[];
  relationships: string[];
  confidence: number;
  frequency: number;
  examples: Array<Record<string, any>>;
}

interface Recommendation {
  type: string;
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  action: string;
  entities?: string[];
}

interface InsightsSummary {
  summary: {
    total_entities: number;
    total_relationships: number;
    network_density: number;
    connected_components: number;
    communities_found: number;
    patterns_discovered: number;
  };
  key_entities: Array<{
    name: string;
    pagerank: number;
    degree_centrality: number;
  }>;
  largest_communities: Array<{
    id: number;
    size: number;
    dominant_types: string[];
  }>;
  discovered_patterns: Array<{
    type: string;
    description: string;
    confidence: number;
  }>;
}

interface KnowledgeGraphInsightsProps {
  knowledgeGraphId: string;
}

export default function KnowledgeGraphInsights({ knowledgeGraphId }: KnowledgeGraphInsightsProps) {
  const { toast } = useToast();
  
  // State
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  
  // Data
  const [insightsSummary, setInsightsSummary] = useState<InsightsSummary | null>(null);
  const [networkMetrics, setNetworkMetrics] = useState<NetworkMetrics | null>(null);
  const [centralityMetrics, setCentralityMetrics] = useState<CentralityMetric[]>([]);
  const [communities, setCommunities] = useState<Community[]>([]);
  const [patterns, setPatterns] = useState<KnowledgePattern[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [temporalAnalysis, setTemporalAnalysis] = useState<any>(null);

  useEffect(() => {
    loadInsightsSummary();
  }, [knowledgeGraphId]);

  const loadInsightsSummary = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/agent-builder/kg-analytics/${knowledgeGraphId}/insights`);
      if (!response.ok) throw new Error('Failed to load insights');
      
      const data = await response.json();
      setInsightsSummary(data);
    } catch (error) {
      console.error('Error loading insights:', error);
      toast({
        title: "오류",
        description: "인사이트를 불러오는데 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const runFullAnalysis = async () => {
    setIsAnalyzing(true);
    setAnalysisProgress(0);
    
    try {
      // Progress simulation for better UX
      const progressInterval = setInterval(() => {
        setAnalysisProgress(prev => Math.min(prev + 5, 90));
      }, 300);

      const response = await fetch(`/api/agent-builder/kg-analytics/${knowledgeGraphId}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          include_centrality: true,
          include_communities: true,
          include_patterns: true,
          include_temporal: true,
        }),
      });

      if (!response.ok) throw new Error('Analysis failed');
      
      const analysisResults = await response.json();
      
      clearInterval(progressInterval);
      setAnalysisProgress(95);
      
      // Update all data
      setNetworkMetrics(analysisResults.network_metrics);
      setCentralityMetrics(analysisResults.centrality_metrics || []);
      setCommunities(analysisResults.communities || []);
      setPatterns(analysisResults.knowledge_patterns || []);
      setRecommendations(analysisResults.recommendations || []);
      setTemporalAnalysis(analysisResults.temporal_analysis);
      
      // Refresh summary
      await loadInsightsSummary();
      
      setAnalysisProgress(100);
      
      toast({
        title: "🎉 분석 완료!",
        description: `${analysisResults.communities?.length || 0}개 커뮤니티, ${analysisResults.knowledge_patterns?.length || 0}개 패턴을 발견했습니다.`,
      });
      
    } catch (error) {
      console.error('Error running analysis:', error);
      toast({
        title: "오류",
        description: "분석 실행에 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
      setTimeout(() => setAnalysisProgress(0), 2000);
    }
  };

  const loadDetailedData = async (dataType: string) => {
    try {
      let endpoint = '';
      switch (dataType) {
        case 'centrality':
          endpoint = `/api/agent-builder/kg-analytics/${knowledgeGraphId}/centrality`;
          break;
        case 'communities':
          endpoint = `/api/agent-builder/kg-analytics/${knowledgeGraphId}/communities`;
          break;
        case 'patterns':
          endpoint = `/api/agent-builder/kg-analytics/${knowledgeGraphId}/patterns`;
          break;
        case 'recommendations':
          endpoint = `/api/agent-builder/kg-analytics/${knowledgeGraphId}/recommendations`;
          break;
        case 'temporal':
          endpoint = `/api/agent-builder/kg-analytics/${knowledgeGraphId}/temporal-analysis`;
          break;
        default:
          return;
      }

      const response = await fetch(endpoint);
      if (!response.ok) throw new Error(`Failed to load ${dataType}`);
      
      const data = await response.json();
      
      switch (dataType) {
        case 'centrality':
          setCentralityMetrics(data);
          break;
        case 'communities':
          setCommunities(data);
          break;
        case 'patterns':
          setPatterns(data);
          break;
        case 'recommendations':
          setRecommendations(data.recommendations || []);
          break;
        case 'temporal':
          setTemporalAnalysis(data);
          break;
      }
      
    } catch (error) {
      console.error(`Error loading ${dataType}:`, error);
      toast({
        title: "오류",
        description: `${dataType} 데이터를 불러오는데 실패했습니다.`,
        variant: "destructive",
      });
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
        return <ArrowUp className="w-4 h-4 text-red-600" />;
      case 'medium':
        return <Minus className="w-4 h-4 text-yellow-600" />;
      case 'low':
        return <ArrowDown className="w-4 h-4 text-green-600" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const renderOnboardingHelp = () => (
    <Alert className="mb-6 border-purple-200 bg-purple-50">
      <Brain className="h-4 w-4 text-purple-600" />
      <AlertDescription>
        <div className="space-y-3">
          <div className="font-medium text-purple-900">지식 그래프 인사이트 가이드</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-purple-800">
            <div className="space-y-2">
              <div className="font-medium">📊 분석 유형</div>
              <ul className="space-y-1 text-xs">
                <li>• <strong>중심성</strong>: 핵심 엔티티 식별</li>
                <li>• <strong>커뮤니티</strong>: 연관 그룹 발견</li>
                <li>• <strong>패턴</strong>: 구조적 특성 분석</li>
                <li>• <strong>시간 분석</strong>: 변화 추이 파악</li>
              </ul>
            </div>
            <div className="space-y-2">
              <div className="font-medium">🎯 활용 방법</div>
              <ul className="space-y-1 text-xs">
                <li>• 전체 분석으로 종합 인사이트 확인</li>
                <li>• 탭별로 세부 데이터 탐색</li>
                <li>• 추천사항으로 개선점 파악</li>
                <li>• 시각화로 직관적 이해</li>
              </ul>
            </div>
          </div>
        </div>
      </AlertDescription>
    </Alert>
  );

  const formatNumber = (num: number, decimals: number = 2) => {
    return num.toLocaleString('ko-KR', { 
      minimumFractionDigits: decimals, 
      maximumFractionDigits: decimals 
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin mx-auto" />
          <div className="text-sm text-gray-600">인사이트 데이터를 불러오는 중...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Enhanced Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Brain className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">지식 그래프 인사이트</h2>
            <p className="text-gray-600">AI 기반 네트워크 분석 및 패턴 발견</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={() => setShowOnboarding(!showOnboarding)}>
            <Info className="w-4 h-4 mr-2" />
            가이드
          </Button>
          <Button variant="outline" onClick={loadInsightsSummary} disabled={isLoading}>
            <RefreshCw className="w-4 h-4 mr-2" />
            새로고침
          </Button>
          <Button onClick={runFullAnalysis} disabled={isAnalyzing} className="bg-purple-600 hover:bg-purple-700">
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                분석 중... ({analysisProgress}%)
              </>
            ) : (
              <>
                <BarChart3 className="w-4 h-4 mr-2" />
                전체 분석 실행
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <Card className="border-purple-200 bg-purple-50">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Brain className="w-5 h-5 animate-pulse text-purple-600" />
                  <span className="font-medium">AI 분석 진행 중...</span>
                </div>
                <span className="text-sm text-gray-600">{analysisProgress}%</span>
              </div>
              <Progress value={analysisProgress} className="h-2" />
              <div className="text-sm text-gray-600">
                네트워크 구조를 분석하고 패턴을 발견하고 있습니다. 잠시만 기다려주세요.
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Onboarding Help */}
      {showOnboarding && renderOnboardingHelp()}

      {/* Enhanced Overview Cards */}
      {insightsSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                <Network className="w-4 h-4 mr-2 text-blue-600" />
                엔티티
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-blue-600">{insightsSummary.summary.total_entities.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground mt-1 flex items-center space-x-2">
                <span>{insightsSummary.summary.connected_components}개 컴포넌트</span>
                <div className="w-2 h-2 bg-blue-200 rounded-full"></div>
                <span>밀도 {formatNumber(insightsSummary.summary.network_density * 100, 1)}%</span>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                <Zap className="w-4 h-4 mr-2 text-green-600" />
                관계
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-green-600">{insightsSummary.summary.total_relationships.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground mt-1">
                평균 연결도: {insightsSummary.summary.total_entities > 0 ? 
                  formatNumber(insightsSummary.summary.total_relationships / insightsSummary.summary.total_entities, 1) : '0'}
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                <Users className="w-4 h-4 mr-2 text-purple-600" />
                커뮤니티
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-purple-600">{insightsSummary.summary.communities_found}</div>
              <div className="text-xs text-muted-foreground mt-1">
                발견된 그룹
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                <Target className="w-4 h-4 mr-2 text-orange-600" />
                패턴
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-orange-600">{insightsSummary.summary.patterns_discovered}</div>
              <div className="text-xs text-muted-foreground mt-1">
                지식 패턴
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Detailed Analysis Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="centrality">중심성</TabsTrigger>
          <TabsTrigger value="communities">커뮤니티</TabsTrigger>
          <TabsTrigger value="patterns">패턴</TabsTrigger>
          <TabsTrigger value="temporal">시간 분석</TabsTrigger>
          <TabsTrigger value="recommendations">추천</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {insightsSummary && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Key Entities */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <TrendingUp className="w-5 h-5" />
                    <span>핵심 엔티티</span>
                  </CardTitle>
                  <CardDescription>PageRank 기준 상위 엔티티</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {insightsSummary.key_entities.map((entity, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <div className="font-medium">{entity.name}</div>
                          <div className="text-sm text-gray-600">
                            차수 중심성: {formatNumber(entity.degree_centrality, 3)}
                          </div>
                        </div>
                        <Badge variant="outline">
                          {formatNumber(entity.pagerank, 3)}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Largest Communities */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Users className="w-5 h-5" />
                    <span>주요 커뮤니티</span>
                  </CardTitle>
                  <CardDescription>크기 기준 상위 커뮤니티</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {insightsSummary.largest_communities.map((community) => (
                      <div key={community.id} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium">커뮤니티 #{community.id}</span>
                          <Badge variant="outline">{community.size}개 엔티티</Badge>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {community.dominant_types.map((type, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {type}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Discovered Patterns */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Target className="w-5 h-5" />
                    <span>발견된 패턴</span>
                  </CardTitle>
                  <CardDescription>지식 그래프에서 발견된 구조적 패턴</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {insightsSummary.discovered_patterns.map((pattern, index) => (
                      <div key={index} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <Badge variant="outline">{pattern.type}</Badge>
                          <span className="text-sm text-gray-600">
                            신뢰도: {formatNumber(pattern.confidence * 100, 0)}%
                          </span>
                        </div>
                        <p className="text-sm text-gray-700">{pattern.description}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="centrality" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>중심성 분석</CardTitle>
                  <CardDescription>엔티티의 네트워크 내 중요도 측정</CardDescription>
                </div>
                <Button variant="outline" onClick={() => loadDetailedData('centrality')}>
                  <Eye className="w-4 h-4 mr-2" />
                  데이터 로드
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {centralityMetrics.length > 0 ? (
                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {centralityMetrics.map((metric, index) => (
                      <div key={metric.entity_id} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <div className="font-medium">{metric.entity_name}</div>
                          <Badge variant="outline">#{index + 1}</Badge>
                        </div>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">PageRank:</span>
                            <div className="font-medium">{formatNumber(metric.pagerank, 4)}</div>
                          </div>
                          <div>
                            <span className="text-gray-600">차수 중심성:</span>
                            <div className="font-medium">{formatNumber(metric.degree_centrality, 3)}</div>
                          </div>
                          <div>
                            <span className="text-gray-600">매개 중심성:</span>
                            <div className="font-medium">{formatNumber(metric.betweenness_centrality, 3)}</div>
                          </div>
                          <div>
                            <span className="text-gray-600">근접 중심성:</span>
                            <div className="font-medium">{formatNumber(metric.closeness_centrality, 3)}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  중심성 데이터를 로드하려면 위의 버튼을 클릭하세요.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="communities" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>커뮤니티 탐지</CardTitle>
                  <CardDescription>연관된 엔티티들의 그룹 분석</CardDescription>
                </div>
                <Button variant="outline" onClick={() => loadDetailedData('communities')}>
                  <Eye className="w-4 h-4 mr-2" />
                  데이터 로드
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {communities.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {communities.map((community) => (
                    <div key={community.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium">커뮤니티 #{community.id}</h4>
                        <Badge variant="outline">{community.size}개</Badge>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <div>
                          <span className="text-gray-600">밀도:</span>
                          <span className="ml-2 font-medium">{formatNumber(community.density * 100, 1)}%</span>
                        </div>
                        
                        <div>
                          <span className="text-gray-600">주요 타입:</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {community.dominant_types.map((type, index) => (
                              <Badge key={index} variant="secondary" className="text-xs">
                                {type}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        
                        <div>
                          <span className="text-gray-600">주요 관계:</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {community.key_relationships.map((rel, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {rel}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  커뮤니티 데이터를 로드하려면 위의 버튼을 클릭하세요.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="patterns" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>지식 패턴</CardTitle>
                  <CardDescription>구조적 패턴 및 지식 구조 분석</CardDescription>
                </div>
                <Button variant="outline" onClick={() => loadDetailedData('patterns')}>
                  <Eye className="w-4 h-4 mr-2" />
                  데이터 로드
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {patterns.length > 0 ? (
                <div className="space-y-4">
                  {patterns.map((pattern, index) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline">{pattern.pattern_type}</Badge>
                          <span className="text-sm text-gray-600">
                            빈도: {pattern.frequency}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-600">신뢰도:</span>
                          <Progress value={pattern.confidence * 100} className="w-20" />
                          <span className="text-sm font-medium">
                            {formatNumber(pattern.confidence * 100, 0)}%
                          </span>
                        </div>
                      </div>
                      
                      <p className="text-sm text-gray-700 mb-3">{pattern.description}</p>
                      
                      {pattern.examples.length > 0 && (
                        <div>
                          <span className="text-xs text-gray-600 font-medium">예시:</span>
                          <div className="mt-1 space-y-1">
                            {pattern.examples.slice(0, 3).map((example, exIndex) => (
                              <div key={exIndex} className="text-xs bg-gray-50 p-2 rounded">
                                {JSON.stringify(example, null, 2)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  패턴 데이터를 로드하려면 위의 버튼을 클릭하세요.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="temporal" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>시간적 분석</CardTitle>
                  <CardDescription>시간에 따른 지식 그래프 변화 패턴</CardDescription>
                </div>
                <Button variant="outline" onClick={() => loadDetailedData('temporal')}>
                  <Eye className="w-4 h-4 mr-2" />
                  데이터 로드
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {temporalAnalysis ? (
                <div className="space-y-4">
                  {temporalAnalysis.message ? (
                    <Alert>
                      <Clock className="h-4 w-4" />
                      <AlertDescription>{temporalAnalysis.message}</AlertDescription>
                    </Alert>
                  ) : (
                    <>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">
                            {temporalAnalysis.temporal_relationships_count || 0}
                          </div>
                          <div className="text-sm text-blue-800">시간 관계</div>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                          <div className="text-2xl font-bold text-green-600">
                            {formatNumber(temporalAnalysis.average_relationship_duration_days || 0, 0)}
                          </div>
                          <div className="text-sm text-green-800">평균 지속 기간 (일)</div>
                        </div>
                        <div className="text-center p-4 bg-purple-50 rounded-lg">
                          <div className="text-2xl font-bold text-purple-600">
                            {temporalAnalysis.temporal_clusters?.length || 0}
                          </div>
                          <div className="text-sm text-purple-800">시간 클러스터</div>
                        </div>
                      </div>

                      {temporalAnalysis.time_activity && (
                        <div>
                          <h4 className="font-medium mb-3">연도별 활동</h4>
                          <div className="space-y-2">
                            {Object.entries(temporalAnalysis.time_activity).map(([year, count]) => (
                              <div key={year} className="flex items-center justify-between">
                                <span>{year}년</span>
                                <div className="flex items-center space-x-2">
                                  <Progress value={(count as number) * 10} className="w-32" />
                                  <span className="text-sm font-medium">{String(count)}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  시간 분석 데이터를 로드하려면 위의 버튼을 클릭하세요.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>개선 추천사항</CardTitle>
                  <CardDescription>분석 결과를 바탕으로 한 지식 그래프 개선 방안</CardDescription>
                </div>
                <Button variant="outline" onClick={() => loadDetailedData('recommendations')}>
                  <Eye className="w-4 h-4 mr-2" />
                  데이터 로드
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {recommendations.length > 0 ? (
                <div className="space-y-4">
                  {recommendations.map((rec, index) => (
                    <Alert key={index} className={`border-l-4 ${
                      rec.priority === 'high' ? 'border-l-red-500' :
                      rec.priority === 'medium' ? 'border-l-yellow-500' :
                      'border-l-green-500'
                    }`}>
                      <div className="flex items-start space-x-3">
                        {getPriorityIcon(rec.priority)}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium">{rec.title}</h4>
                            <Badge className={getPriorityColor(rec.priority)}>
                              {rec.priority}
                            </Badge>
                          </div>
                          <AlertDescription className="text-sm">
                            {rec.description}
                          </AlertDescription>
                          {rec.entities && rec.entities.length > 0 && (
                            <div className="mt-2">
                              <span className="text-xs text-gray-600">관련 엔티티: </span>
                              <span className="text-xs">{rec.entities.length}개</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </Alert>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  추천사항을 로드하려면 위의 버튼을 클릭하세요.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}