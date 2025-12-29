"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { 
  Search, 
  Network, 
  Users, 
  Building, 
  MapPin, 
  Lightbulb, 
  Calendar,
  Package,
  FileText,
  Hash,
  ArrowRight,
  Loader2,
  Eye,
  Filter,
  Info,
  HelpCircle,
  Sparkles,
  TrendingUp,
  BarChart3,
  RefreshCw,
  Download,
  ExternalLink
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Entity {
  id: string;
  name: string;
  canonical_name: string;
  entity_type: string;
  description?: string;
  confidence_score: number;
  mention_count: number;
  relationship_count: number;
  properties: Record<string, any>;
  aliases: string[];
}

interface Relationship {
  id: string;
  relation_type: string;
  relation_label?: string;
  description?: string;
  confidence_score: number;
  mention_count: number;
  is_bidirectional: boolean;
  properties: Record<string, any>;
  source_entity: {
    id: string;
    name: string;
    entity_type: string;
  };
  target_entity: {
    id: string;
    name: string;
    entity_type: string;
  };
  temporal_start?: string;
  temporal_end?: string;
}

interface KnowledgeGraphVisualizationProps {
  knowledgeGraphId: string;
}

const ENTITY_TYPE_ICONS = {
  person: Users,
  organization: Building,
  location: MapPin,
  concept: Lightbulb,
  event: Calendar,
  product: Package,
  document: FileText,
  topic: Hash,
  custom: Hash,
};

const ENTITY_TYPE_COLORS = {
  person: 'bg-blue-100 text-blue-800 border-blue-200',
  organization: 'bg-green-100 text-green-800 border-green-200',
  location: 'bg-red-100 text-red-800 border-red-200',
  concept: 'bg-purple-100 text-purple-800 border-purple-200',
  event: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  product: 'bg-orange-100 text-orange-800 border-orange-200',
  document: 'bg-gray-100 text-gray-800 border-gray-200',
  topic: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  custom: 'bg-pink-100 text-pink-800 border-pink-200',
};

export default function KnowledgeGraphVisualization({ knowledgeGraphId }: KnowledgeGraphVisualizationProps) {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('entities');
  const [showOnboarding, setShowOnboarding] = useState(false);
  
  // Search states
  const [entityQuery, setEntityQuery] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState('');
  const [relationTypeFilter, setRelationTypeFilter] = useState('');
  const [selectedEntityId, setSelectedEntityId] = useState('');
  
  // Data states
  const [entities, setEntities] = useState<Entity[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [entityTypes, setEntityTypes] = useState<Array<{value: string, label: string}>>([]);
  const [relationTypes, setRelationTypes] = useState<Array<{value: string, label: string}>>([]);
  const [searchStats, setSearchStats] = useState<{total: number, filtered: number} | null>(null);

  // Load entity and relation types
  useEffect(() => {
    const loadTypes = async () => {
      try {
        const [entityTypesRes, relationTypesRes] = await Promise.all([
          fetch('/api/agent-builder/knowledge-graphs/entity-types'),
          fetch('/api/agent-builder/knowledge-graphs/relation-types'),
        ]);

        if (entityTypesRes.ok) {
          const entityTypesData = await entityTypesRes.json();
          setEntityTypes(entityTypesData);
        }

        if (relationTypesRes.ok) {
          const relationTypesData = await relationTypesRes.json();
          setRelationTypes(relationTypesData);
        }
      } catch (error) {
        console.error('Error loading types:', error);
      }
    };

    loadTypes();
  }, []);

  const searchEntities = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/agent-builder/knowledge-graphs/${knowledgeGraphId}/entities/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: entityQuery || undefined,
          entity_types: entityTypeFilter ? [entityTypeFilter] : undefined,
          limit: 50,
        }),
      });

      if (!response.ok) {
        throw new Error('엔티티 검색에 실패했습니다.');
      }

      const data = await response.json();
      setEntities(data.entities);
      setSearchStats({
        total: data.total || data.entities.length,
        filtered: data.entities.length
      });
    } catch (error) {
      console.error('Error searching entities:', error);
      toast({
        title: "오류",
        description: "엔티티 검색에 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const searchRelationships = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/agent-builder/knowledge-graphs/${knowledgeGraphId}/relationships/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entity_id: selectedEntityId || undefined,
          relation_types: relationTypeFilter ? [relationTypeFilter] : undefined,
          limit: 50,
        }),
      });

      if (!response.ok) {
        throw new Error('관계 검색에 실패했습니다.');
      }

      const data = await response.json();
      setRelationships(data.relationships);
    } catch (error) {
      console.error('Error searching relationships:', error);
      toast({
        title: "오류",
        description: "관계 검색에 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const exportData = async () => {
    try {
      const data = {
        entities: entities.map(e => ({
          name: e.name,
          type: e.entity_type,
          confidence: e.confidence_score,
          mentions: e.mention_count,
          relationships: e.relationship_count
        })),
        relationships: relationships.map(r => ({
          source: r.source_entity.name,
          target: r.target_entity.name,
          type: r.relation_type,
          confidence: r.confidence_score
        })),
        metadata: {
          exported_at: new Date().toISOString(),
          total_entities: entities.length,
          total_relationships: relationships.length
        }
      };

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `knowledge-graph-data-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "성공",
        description: "지식 그래프 데이터가 JSON 파일로 내보내졌습니다.",
      });
    } catch (error) {
      console.error('Error exporting data:', error);
      toast({
        title: "오류",
        description: "데이터 내보내기에 실패했습니다.",
        variant: "destructive",
      });
    }
  };

  const renderOnboardingHelp = () => (
    <Alert className="mb-4 border-blue-200 bg-blue-50">
      <Info className="h-4 w-4 text-blue-600" />
      <AlertDescription>
        <div className="space-y-2">
          <div className="font-medium text-blue-900">지식 그래프 탐색 가이드</div>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• <strong>엔티티 탭</strong>: 추출된 개체들을 검색하고 필터링할 수 있습니다</li>
            <li>• <strong>관계 탭</strong>: 엔티티 간의 연결 관계를 탐색할 수 있습니다</li>
            <li>• <strong>검색 기능</strong>: 이름으로 검색하거나 타입별로 필터링하세요</li>
            <li>• <strong>관계 보기</strong>: 엔티티 카드의 "관계 보기" 버튼을 클릭하세요</li>
          </ul>
        </div>
      </AlertDescription>
    </Alert>
  );

  // Initial load
  useEffect(() => {
    if (activeTab === 'entities') {
      searchEntities();
    } else if (activeTab === 'relationships') {
      searchRelationships();
    }
  }, [activeTab, knowledgeGraphId]);

  const getEntityIcon = (entityType: string) => {
    const IconComponent = ENTITY_TYPE_ICONS[entityType as keyof typeof ENTITY_TYPE_ICONS] || Hash;
    return <IconComponent className="w-4 h-4" />;
  };

  const getEntityTypeColor = (entityType: string) => {
    return ENTITY_TYPE_COLORS[entityType as keyof typeof ENTITY_TYPE_COLORS] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const formatConfidenceScore = (score: number) => {
    return `${(score * 100).toFixed(1)}%`;
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Network className="w-5 h-5 text-blue-600" />
            <CardTitle>지식 그래프 탐색</CardTitle>
          </div>
          <div className="flex items-center space-x-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="sm" onClick={() => setShowOnboarding(!showOnboarding)}>
                    <HelpCircle className="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>도움말 보기/숨기기</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Button variant="outline" size="sm" onClick={exportData}>
              <Download className="w-4 h-4 mr-1" />
              내보내기
            </Button>
            <Button variant="outline" size="sm" onClick={() => {
              if (activeTab === 'entities') searchEntities();
              else searchRelationships();
            }}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>
        <CardDescription>
          추출된 엔티티와 관계를 탐색하고 검색할 수 있습니다.
          {searchStats && (
            <span className="ml-2 text-sm font-medium">
              ({searchStats.filtered.toLocaleString()}개 표시 / 전체 {searchStats.total.toLocaleString()}개)
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {showOnboarding && renderOnboardingHelp()}
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="entities" className="flex items-center space-x-2">
              <Users className="w-4 h-4" />
              <span>엔티티</span>
              {entities.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {entities.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="relationships" className="flex items-center space-x-2">
              <Network className="w-4 h-4" />
              <span>관계</span>
              {relationships.length > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs">
                  {relationships.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="entities" className="space-y-4">
            {/* Enhanced Entity Search */}
            <div className="space-y-3">
              <div className="flex space-x-2">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="엔티티 이름으로 검색..."
                    value={entityQuery}
                    onChange={(e) => setEntityQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && searchEntities()}
                    className="pl-10"
                  />
                </div>
                <Select value={entityTypeFilter} onValueChange={setEntityTypeFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="타입 필터" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">모든 타입</SelectItem>
                    {entityTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        <div className="flex items-center space-x-2">
                          {getEntityIcon(type.value)}
                          <span>{type.label}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button onClick={searchEntities} disabled={isLoading}>
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                </Button>
              </div>
              
              {/* Search Statistics */}
              {searchStats && (
                <div className="flex items-center justify-between text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <span>검색 결과: {searchStats.filtered.toLocaleString()}개</span>
                    {entityQuery && (
                      <span>검색어: "{entityQuery}"</span>
                    )}
                    {entityTypeFilter && (
                      <Badge variant="outline" className="text-xs">
                        {entityTypes.find(t => t.value === entityTypeFilter)?.label}
                      </Badge>
                    )}
                  </div>
                  {(entityQuery || entityTypeFilter) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setEntityQuery('');
                        setEntityTypeFilter('');
                        searchEntities();
                      }}
                      className="text-xs"
                    >
                      필터 초기화
                    </Button>
                  )}
                </div>
              )}
            </div>

            {/* Enhanced Entity Results */}
            <ScrollArea className="h-96">
              <div className="space-y-3">
                {entities.map((entity) => (
                  <Card key={entity.id} className="p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          {getEntityIcon(entity.entity_type)}
                          <h4 className="font-medium text-lg">{entity.name}</h4>
                          <Badge className={getEntityTypeColor(entity.entity_type)}>
                            {entity.entity_type}
                          </Badge>
                          {entity.confidence_score >= 0.8 && (
                            <Badge variant="outline" className="text-green-600 border-green-200">
                              <Sparkles className="w-3 h-3 mr-1" />
                              고신뢰도
                            </Badge>
                          )}
                        </div>
                        
                        {entity.description && (
                          <p className="text-sm text-gray-600 mb-3 leading-relaxed">{entity.description}</p>
                        )}
                        
                        {/* Enhanced Statistics */}
                        <div className="grid grid-cols-3 gap-4 mb-3">
                          <div className="text-center p-2 bg-blue-50 rounded-lg">
                            <div className="text-lg font-bold text-blue-600">{formatConfidenceScore(entity.confidence_score)}</div>
                            <div className="text-xs text-blue-800">신뢰도</div>
                          </div>
                          <div className="text-center p-2 bg-green-50 rounded-lg">
                            <div className="text-lg font-bold text-green-600">{entity.mention_count}</div>
                            <div className="text-xs text-green-800">언급 횟수</div>
                          </div>
                          <div className="text-center p-2 bg-purple-50 rounded-lg">
                            <div className="text-lg font-bold text-purple-600">{entity.relationship_count}</div>
                            <div className="text-xs text-purple-800">관계 수</div>
                          </div>
                        </div>

                        {entity.aliases.length > 0 && (
                          <div className="mb-3">
                            <Label className="text-xs text-gray-500 font-medium">별칭:</Label>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {entity.aliases.slice(0, 5).map((alias, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {alias}
                                </Badge>
                              ))}
                              {entity.aliases.length > 5 && (
                                <Badge variant="outline" className="text-xs">
                                  +{entity.aliases.length - 5}개 더
                                </Badge>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Properties */}
                        {Object.keys(entity.properties).length > 0 && (
                          <div className="mb-3">
                            <Label className="text-xs text-gray-500 font-medium">속성:</Label>
                            <div className="mt-1 space-y-1">
                              {Object.entries(entity.properties).slice(0, 3).map(([key, value]) => (
                                <div key={key} className="text-xs bg-gray-50 px-2 py-1 rounded">
                                  <span className="font-medium">{key}:</span> {String(value)}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex flex-col space-y-2 ml-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedEntityId(entity.id);
                            setActiveTab('relationships');
                          }}
                          className="flex items-center space-x-1"
                        >
                          <Eye className="w-3 h-3" />
                          <span>관계 보기</span>
                        </Button>
                        {entity.relationship_count > 0 && (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button variant="ghost" size="sm">
                                  <ExternalLink className="w-3 h-3" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>네트워크에서 보기</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
                
                {entities.length === 0 && !isLoading && (
                  <div className="text-center py-12">
                    <Network className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <div className="text-gray-500 mb-2">검색 결과가 없습니다</div>
                    <div className="text-sm text-gray-400">
                      다른 검색어를 시도하거나 필터를 조정해보세요
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="relationships" className="space-y-4">
            {/* Enhanced Relationship Search */}
            <div className="space-y-3">
              <div className="flex space-x-2">
                <Select value={selectedEntityId} onValueChange={setSelectedEntityId}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="특정 엔티티의 관계 보기 (선택사항)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">모든 엔티티</SelectItem>
                    {entities.map((entity) => (
                      <SelectItem key={entity.id} value={entity.id}>
                        <div className="flex items-center space-x-2">
                          {getEntityIcon(entity.entity_type)}
                          <span>{entity.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {entity.entity_type}
                          </Badge>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                <Select value={relationTypeFilter} onValueChange={setRelationTypeFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="관계 타입" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">모든 관계</SelectItem>
                    {relationTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                <Button onClick={searchRelationships} disabled={isLoading}>
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Filter className="w-4 h-4" />}
                </Button>
              </div>

              {/* Relationship Statistics */}
              {relationships.length > 0 && (
                <div className="flex items-center justify-between text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <span>관계: {relationships.length.toLocaleString()}개</span>
                    {selectedEntityId && (
                      <span>선택된 엔티티: {entities.find(e => e.id === selectedEntityId)?.name}</span>
                    )}
                    {relationTypeFilter && (
                      <Badge variant="outline" className="text-xs">
                        {relationTypes.find(t => t.value === relationTypeFilter)?.label}
                      </Badge>
                    )}
                  </div>
                  {(selectedEntityId || relationTypeFilter) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedEntityId('');
                        setRelationTypeFilter('');
                        searchRelationships();
                      }}
                      className="text-xs"
                    >
                      필터 초기화
                    </Button>
                  )}
                </div>
              )}
            </div>

            {/* Enhanced Relationship Results */}
            <ScrollArea className="h-96">
              <div className="space-y-3">
                {relationships.map((relationship) => (
                  <Card key={relationship.id} className="p-4 hover:shadow-md transition-shadow">
                    <div className="space-y-3">
                      {/* Relationship Header */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="text-sm font-medium">
                            {relationship.relation_type.replace('_', ' ')}
                          </Badge>
                          {relationship.confidence_score >= 0.8 && (
                            <Badge variant="outline" className="text-green-600 border-green-200">
                              <TrendingUp className="w-3 h-3 mr-1" />
                              고신뢰도
                            </Badge>
                          )}
                          {relationship.is_bidirectional && (
                            <Badge variant="outline" className="text-purple-600 border-purple-200">
                              양방향
                            </Badge>
                          )}
                        </div>
                        <div className="text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                          신뢰도: {formatConfidenceScore(relationship.confidence_score)}
                        </div>
                      </div>

                      {/* Enhanced Entities Connection */}
                      <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg">
                        <div className="flex items-center space-x-2 flex-1 p-2 bg-white rounded border">
                          {getEntityIcon(relationship.source_entity.entity_type)}
                          <span className="font-medium">{relationship.source_entity.name}</span>
                          <Badge className={getEntityTypeColor(relationship.source_entity.entity_type)}>
                            {relationship.source_entity.entity_type}
                          </Badge>
                        </div>
                        
                        <div className="flex flex-col items-center">
                          <ArrowRight className="w-5 h-5 text-gray-400" />
                          <span className="text-xs text-gray-500 mt-1">
                            {relationship.relation_label || relationship.relation_type}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-2 flex-1 p-2 bg-white rounded border">
                          {getEntityIcon(relationship.target_entity.entity_type)}
                          <span className="font-medium">{relationship.target_entity.name}</span>
                          <Badge className={getEntityTypeColor(relationship.target_entity.entity_type)}>
                            {relationship.target_entity.entity_type}
                          </Badge>
                        </div>
                      </div>

                      {/* Relationship Details */}
                      {relationship.description && (
                        <div className="p-3 bg-gray-50 rounded-lg">
                          <Label className="text-xs text-gray-600 font-medium">설명:</Label>
                          <p className="text-sm text-gray-700 mt-1">{relationship.description}</p>
                        </div>
                      )}

                      {/* Enhanced Metadata */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                        <div className="text-center p-2 bg-blue-50 rounded">
                          <div className="font-bold text-blue-600">{relationship.mention_count}</div>
                          <div className="text-blue-800">언급 횟수</div>
                        </div>
                        <div className="text-center p-2 bg-green-50 rounded">
                          <div className="font-bold text-green-600">
                            {relationship.confidence_score >= 0.8 ? '높음' : 
                             relationship.confidence_score >= 0.6 ? '보통' : '낮음'}
                          </div>
                          <div className="text-green-800">신뢰도 등급</div>
                        </div>
                        {relationship.temporal_start && (
                          <div className="text-center p-2 bg-purple-50 rounded">
                            <div className="font-bold text-purple-600">
                              {new Date(relationship.temporal_start).getFullYear()}
                            </div>
                            <div className="text-purple-800">시작 연도</div>
                          </div>
                        )}
                        {relationship.temporal_end && (
                          <div className="text-center p-2 bg-orange-50 rounded">
                            <div className="font-bold text-orange-600">
                              {new Date(relationship.temporal_end).getFullYear()}
                            </div>
                            <div className="text-orange-800">종료 연도</div>
                          </div>
                        )}
                      </div>

                      {/* Properties */}
                      {Object.keys(relationship.properties).length > 0 && (
                        <div>
                          <Label className="text-xs text-gray-500 font-medium">추가 속성:</Label>
                          <div className="mt-1 grid grid-cols-1 md:grid-cols-2 gap-1">
                            {Object.entries(relationship.properties).slice(0, 4).map(([key, value]) => (
                              <div key={key} className="text-xs bg-gray-50 px-2 py-1 rounded">
                                <span className="font-medium">{key}:</span> {String(value)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
                
                {relationships.length === 0 && !isLoading && (
                  <div className="text-center py-12">
                    <BarChart3 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <div className="text-gray-500 mb-2">관계 데이터가 없습니다</div>
                    <div className="text-sm text-gray-400">
                      엔티티를 선택하거나 다른 필터를 시도해보세요
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}