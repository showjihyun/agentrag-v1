"use client";

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  ArrowLeft, 
  Database, 
  FileText, 
  Upload, 
  Search, 
  Settings, 
  Network,
  BarChart3,
  AlertCircle,
  CheckCircle2,
  Loader2
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, Knowledgebase } from '@/lib/api/agent-builder';
import KnowledgeGraphConfig from '@/components/agent-builder/KnowledgeGraphConfig';
import KnowledgeGraphVisualization from '@/components/agent-builder/KnowledgeGraphVisualization';
import KnowledgeGraphNetworkVisualization from '@/components/agent-builder/KnowledgeGraphNetworkVisualization';
import KnowledgeGraphInsights from '@/components/agent-builder/KnowledgeGraphInsights';

interface KnowledgeGraph {
  id: string;
  knowledgebase_id: string;
  name: string;
  description?: string;
  auto_extraction_enabled: boolean;
  entity_extraction_model: string;
  relation_extraction_model: string;
  entity_count: number;
  relationship_count: number;
  processing_status: string;
  processing_error?: string;
  last_processed_at?: string;
  created_at: string;
  updated_at: string;
}

export default function KnowledgebaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const knowledgebaseId = params.id as string;

  const [knowledgebase, setKnowledgebase] = useState<Knowledgebase | null>(null);
  const [knowledgeGraph, setKnowledgeGraph] = useState<KnowledgeGraph | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadKnowledgebaseData();
  }, [knowledgebaseId]);

  const loadKnowledgebaseData = async () => {
    try {
      setIsLoading(true);
      
      // Load knowledgebase details
      const kbData = await agentBuilderAPI.getKnowledgebase(knowledgebaseId);
      setKnowledgebase(kbData);

      // Check if knowledge graph exists
      if (kbData.kg_enabled) {
        try {
          const response = await fetch(`/api/agent-builder/knowledge-graphs?knowledgebase_id=${knowledgebaseId}`);
          if (response.ok) {
            const kgData = await response.json();
            if (kgData.length > 0) {
              setKnowledgeGraph(kgData[0]);
            }
          }
        } catch (error) {
          console.error('Error loading knowledge graph:', error);
        }
      }
    } catch (error: any) {
      console.error('Error loading knowledgebase:', error);
      toast({
        title: "오류",
        description: "지식베이스 정보를 불러오는데 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKnowledgeGraphCreated = (kg: KnowledgeGraph) => {
    setKnowledgeGraph(kg);
    // Update knowledgebase to reflect KG is enabled
    if (knowledgebase) {
      setKnowledgebase({
        ...knowledgebase,
        kg_enabled: true,
      });
    }
    toast({
      title: "성공",
      description: "지식 그래프가 생성되었습니다.",
    });
  };

  const formatBytes = (bytes: number = 0) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getKbTypeLabel = (type: string) => {
    switch (type) {
      case 'vector':
        return '벡터 검색';
      case 'graph':
        return '지식 그래프';
      case 'hybrid':
        return '하이브리드';
      default:
        return type;
    }
  };

  const getKbTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'vector':
        return 'bg-blue-100 text-blue-800';
      case 'graph':
        return 'bg-green-100 text-green-800';
      case 'hybrid':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
      </div>
    );
  }

  if (!knowledgebase) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            지식베이스를 찾을 수 없습니다.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.back()}
            className="flex items-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>뒤로</span>
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{knowledgebase.name}</h1>
            <p className="text-muted-foreground">
              {knowledgebase.description || '설명이 없습니다.'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Badge className={getKbTypeBadgeColor(knowledgebase.kb_type || 'vector')}>
            {getKbTypeLabel(knowledgebase.kb_type || 'vector')}
          </Badge>
          <Button
            variant="outline"
            onClick={() => router.push(`/agent-builder/knowledgebases/${knowledgebaseId}/upload`)}
          >
            <Upload className="w-4 h-4 mr-2" />
            문서 업로드
          </Button>
          <Button
            variant="outline"
            onClick={() => router.push(`/agent-builder/knowledgebases/${knowledgebaseId}/search`)}
          >
            <Search className="w-4 h-4 mr-2" />
            검색
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <FileText className="w-4 h-4 mr-2" />
              문서 수
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-3xl font-bold">{knowledgebase.document_count || 0}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
              <Database className="w-4 h-4 mr-2" />
              총 크기
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-3xl font-bold">{formatBytes(knowledgebase.total_size)}</div>
          </CardContent>
        </Card>

        {knowledgeGraph && (
          <>
            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                  <Network className="w-4 h-4 mr-2" />
                  엔티티
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="text-3xl font-bold">{knowledgeGraph.entity_count}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                  <BarChart3 className="w-4 h-4 mr-2" />
                  관계
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="text-3xl font-bold">{knowledgeGraph.relationship_count}</div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="documents">문서</TabsTrigger>
          <TabsTrigger value="knowledge-graph">지식 그래프</TabsTrigger>
          <TabsTrigger value="settings">설정</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle>기본 정보</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">이름</label>
                  <p className="text-sm text-gray-900">{knowledgebase.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">설명</label>
                  <p className="text-sm text-gray-900">{knowledgebase.description || '설명 없음'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">생성일</label>
                  <p className="text-sm text-gray-900">{formatDate(knowledgebase.created_at)}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">마지막 수정</label>
                  <p className="text-sm text-gray-900">{formatDate(knowledgebase.updated_at)}</p>
                </div>
              </CardContent>
            </Card>

            {/* Configuration */}
            <Card>
              <CardHeader>
                <CardTitle>구성</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">임베딩 모델</label>
                  <p className="text-sm text-gray-900 font-mono bg-gray-100 px-2 py-1 rounded">
                    {knowledgebase.embedding_model}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">청크 크기</label>
                  <p className="text-sm text-gray-900">{knowledgebase.chunk_size} 문자</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">청크 겹침</label>
                  <p className="text-sm text-gray-900">{knowledgebase.chunk_overlap} 문자</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">검색 전략</label>
                  <p className="text-sm text-gray-900">{knowledgebase.search_strategy || 'vector'}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Knowledge Graph Status */}
          {knowledgebase.kg_enabled && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Network className="w-5 h-5" />
                  <span>지식 그래프 상태</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {knowledgeGraph ? (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <CheckCircle2 className="w-5 h-5 text-green-600" />
                        <span className="font-medium">활성화됨</span>
                      </div>
                      <div className="text-sm text-gray-600">
                        엔티티 {knowledgeGraph.entity_count}개, 관계 {knowledgeGraph.relationship_count}개
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => setActiveTab('knowledge-graph')}
                    >
                      지식 그래프 보기
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-5 h-5 text-yellow-600" />
                      <span>지식 그래프가 설정되지 않았습니다.</span>
                    </div>
                    <Button
                      onClick={() => setActiveTab('knowledge-graph')}
                    >
                      지식 그래프 생성
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="documents" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>문서 관리</CardTitle>
              <CardDescription>
                지식베이스에 포함된 문서를 관리합니다.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">문서 관리 기능은 곧 추가될 예정입니다.</p>
                <Button
                  onClick={() => router.push(`/agent-builder/knowledgebases/${knowledgebaseId}/upload`)}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  문서 업로드
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="knowledge-graph" className="space-y-6">
          {knowledgeGraph ? (
            <div className="space-y-6">
              {/* Configuration and Basic Visualization */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <KnowledgeGraphConfig
                  knowledgebaseId={knowledgebaseId}
                  knowledgeGraph={knowledgeGraph}
                  onKnowledgeGraphUpdated={(kg) => setKnowledgeGraph(kg)}
                />
                <KnowledgeGraphVisualization knowledgeGraphId={knowledgeGraph.id} />
              </div>

              {/* Advanced Network Visualization */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Network className="w-5 h-5" />
                    <span>네트워크 시각화</span>
                  </CardTitle>
                  <CardDescription>
                    인터랙티브 네트워크 그래프로 엔티티 간 관계를 탐색하세요.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <KnowledgeGraphNetworkVisualization 
                    knowledgeGraphId={knowledgeGraph.id}
                    width={800}
                    height={500}
                  />
                </CardContent>
              </Card>

              {/* Analytics and Insights */}
              <KnowledgeGraphInsights knowledgeGraphId={knowledgeGraph.id} />
            </div>
          ) : (
            <KnowledgeGraphConfig
              knowledgebaseId={knowledgebaseId}
              onKnowledgeGraphCreated={handleKnowledgeGraphCreated}
            />
          )}
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Settings className="w-5 h-5" />
                <span>설정</span>
              </CardTitle>
              <CardDescription>
                지식베이스 설정을 관리합니다.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Settings className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">설정 관리 기능은 곧 추가될 예정입니다.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}