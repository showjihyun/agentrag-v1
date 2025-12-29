"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Search, 
  Loader2, 
  FileText, 
  Users, 
  Building, 
  MapPin, 
  Lightbulb, 
  Calendar,
  Package,
  Hash,
  ArrowRight,
  Network,
  Zap,
  Settings,
  Info
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface SearchResult {
  documents: Array<{
    type: string;
    document_id: string;
    chunk_id: string;
    content: string;
    score: number;
    metadata: Record<string, any>;
  }>;
  entities: Array<{
    type: string;
    entity_id: string;
    name: string;
    entity_type: string;
    description?: string;
    confidence_score: number;
    mention_count: number;
    relationship_count: number;
    properties: Record<string, any>;
    expansion_relation?: string;
    expansion_source?: string;
  }>;
  relationships: Array<{
    type: string;
    relationship_id: string;
    relation_type: string;
    relation_label?: string;
    description?: string;
    confidence_score: number;
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
    is_bidirectional: boolean;
    properties: Record<string, any>;
  }>;
  metadata: {
    query: string;
    strategy: string;
    vector_weight: number;
    graph_weight: number;
    total_results: number;
    error?: string;
    fallback?: string;
  };
}

interface HybridSearchProps {
  knowledgebaseId: string;
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

export default function HybridSearch({ knowledgebaseId }: HybridSearchProps) {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Search parameters
  const [query, setQuery] = useState('');
  const [searchStrategy, setSearchStrategy] = useState('hybrid');
  const [vectorWeight, setVectorWeight] = useState([0.7]);
  const [graphWeight, setGraphWeight] = useState([0.3]);
  const [includeEntities, setIncludeEntities] = useState(true);
  const [includeRelationships, setIncludeRelationships] = useState(true);
  const [entityExpansionDepth, setEntityExpansionDepth] = useState(1);
  const [limit, setLimit] = useState(10);
  
  // Search results
  const [results, setResults] = useState<SearchResult | null>(null);
  const [availableStrategies, setAvailableStrategies] = useState<Array<{
    value: string;
    label: string;
    description: string;
    available: boolean;
  }>>([]);

  // Load available search strategies
  useEffect(() => {
    const loadStrategies = async () => {
      try {
        const response = await fetch(`/api/agent-builder/hybrid-search/${knowledgebaseId}/search-strategies`);
        if (response.ok) {
          const data = await response.json();
          setAvailableStrategies(data.strategies);
          setSearchStrategy(data.default_strategy);
        }
      } catch (error) {
        console.error('Error loading search strategies:', error);
      }
    };

    loadStrategies();
  }, [knowledgebaseId]);

  // Update weights when one changes
  useEffect(() => {
    const total = vectorWeight[0] + graphWeight[0];
    if (total > 1) {
      if (vectorWeight[0] !== 0.7) {
        setGraphWeight([1 - vectorWeight[0]]);
      } else {
        setVectorWeight([1 - graphWeight[0]]);
      }
    }
  }, [vectorWeight, graphWeight]);

  const handleSearch = async () => {
    if (!query.trim()) {
      toast({
        title: "오류",
        description: "검색어를 입력해주세요.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`/api/agent-builder/hybrid-search/${knowledgebaseId}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          limit,
          search_strategy: searchStrategy,
          vector_weight: vectorWeight[0],
          graph_weight: graphWeight[0],
          include_entities: includeEntities,
          include_relationships: includeRelationships,
          entity_expansion_depth: entityExpansionDepth,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '검색에 실패했습니다.');
      }

      const searchResults = await response.json();
      setResults(searchResults);

      if (searchResults.metadata.error) {
        toast({
          title: "경고",
          description: `검색 중 오류가 발생했습니다: ${searchResults.metadata.error}`,
          variant: "destructive",
        });
      } else if (searchResults.metadata.fallback) {
        toast({
          title: "알림",
          description: searchResults.metadata.fallback,
        });
      }

    } catch (error) {
      console.error('Search error:', error);
      toast({
        title: "오류",
        description: error instanceof Error ? error.message : "검색에 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getEntityIcon = (entityType: string) => {
    const IconComponent = ENTITY_TYPE_ICONS[entityType as keyof typeof ENTITY_TYPE_ICONS] || Hash;
    return <IconComponent className="w-4 h-4" />;
  };

  const getEntityTypeColor = (entityType: string) => {
    return ENTITY_TYPE_COLORS[entityType as keyof typeof ENTITY_TYPE_COLORS] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const formatScore = (score: number) => {
    return `${(score * 100).toFixed(1)}%`;
  };

  const truncateText = (text: string, maxLength: number = 200) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="space-y-6">
      {/* Search Interface */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-blue-600" />
              <CardTitle>하이브리드 검색</CardTitle>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              <Settings className="w-4 h-4 mr-2" />
              고급 설정
            </Button>
          </div>
          <CardDescription>
            벡터 검색과 지식 그래프를 결합한 고급 검색 기능
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Basic Search */}
          <div className="flex space-x-2">
            <div className="flex-1">
              <Input
                placeholder="검색어를 입력하세요..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <Select value={searchStrategy} onValueChange={setSearchStrategy}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {availableStrategies.map((strategy) => (
                  <SelectItem 
                    key={strategy.value} 
                    value={strategy.value}
                    disabled={!strategy.available}
                  >
                    {strategy.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={handleSearch} disabled={isLoading}>
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            </Button>
          </div>

          {/* Advanced Settings */}
          {showAdvanced && (
            <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">결과 수</Label>
                  <Input
                    type="number"
                    value={limit}
                    onChange={(e) => setLimit(parseInt(e.target.value) || 10)}
                    min={1}
                    max={100}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label className="text-sm font-medium">엔티티 확장 깊이</Label>
                  <Input
                    type="number"
                    value={entityExpansionDepth}
                    onChange={(e) => setEntityExpansionDepth(parseInt(e.target.value) || 1)}
                    min={0}
                    max={3}
                    className="mt-1"
                  />
                </div>
              </div>

              {searchStrategy === 'hybrid' && (
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm font-medium">벡터 검색 가중치: {vectorWeight[0].toFixed(2)}</Label>
                    <Slider
                      value={vectorWeight}
                      onValueChange={setVectorWeight}
                      max={1}
                      min={0}
                      step={0.1}
                      className="mt-2"
                    />
                  </div>
                  <div>
                    <Label className="text-sm font-medium">그래프 검색 가중치: {graphWeight[0].toFixed(2)}</Label>
                    <Slider
                      value={graphWeight}
                      onValueChange={setGraphWeight}
                      max={1}
                      min={0}
                      step={0.1}
                      className="mt-2"
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={includeEntities}
                    onCheckedChange={setIncludeEntities}
                  />
                  <Label className="text-sm">엔티티 포함</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={includeRelationships}
                    onCheckedChange={setIncludeRelationships}
                  />
                  <Label className="text-sm">관계 포함</Label>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Search Results */}
      {results && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>검색 결과</CardTitle>
              <div className="flex items-center space-x-2">
                <Badge variant="outline">
                  총 {results.metadata.total_results}개 결과
                </Badge>
                <Badge variant="secondary">
                  {results.metadata.strategy}
                </Badge>
              </div>
            </div>
            <CardDescription>
              "{results.metadata.query}" 검색 결과
            </CardDescription>
          </CardHeader>
          <CardContent>
            {results.metadata.error && (
              <Alert variant="destructive" className="mb-4">
                <AlertDescription>
                  {results.metadata.error}
                </AlertDescription>
              </Alert>
            )}

            {results.metadata.fallback && (
              <Alert className="mb-4">
                <Info className="h-4 w-4" />
                <AlertDescription>
                  {results.metadata.fallback}
                </AlertDescription>
              </Alert>
            )}

            <Tabs defaultValue="documents" className="space-y-4">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="documents">
                  문서 ({results.documents.length})
                </TabsTrigger>
                <TabsTrigger value="entities">
                  엔티티 ({results.entities.length})
                </TabsTrigger>
                <TabsTrigger value="relationships">
                  관계 ({results.relationships.length})
                </TabsTrigger>
              </TabsList>

              <TabsContent value="documents">
                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {results.documents.map((doc, index) => (
                      <Card key={`${doc.document_id}-${doc.chunk_id}-${index}`} className="p-4">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <FileText className="w-4 h-4 text-blue-600" />
                              <span className="font-medium">문서 청크</span>
                            </div>
                            <Badge variant="outline">
                              점수: {formatScore(doc.score)}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-700">
                            {truncateText(doc.content)}
                          </p>
                          <div className="text-xs text-gray-500">
                            문서 ID: {doc.document_id} | 청크 ID: {doc.chunk_id}
                          </div>
                        </div>
                      </Card>
                    ))}
                    
                    {results.documents.length === 0 && (
                      <div className="text-center py-8 text-gray-500">
                        문서 결과가 없습니다.
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="entities">
                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {results.entities.map((entity, index) => (
                      <Card key={`${entity.entity_id}-${index}`} className="p-4">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              {getEntityIcon(entity.entity_type)}
                              <span className="font-medium">{entity.name}</span>
                              <Badge className={getEntityTypeColor(entity.entity_type)}>
                                {entity.entity_type}
                              </Badge>
                            </div>
                            <Badge variant="outline">
                              신뢰도: {formatScore(entity.confidence_score)}
                            </Badge>
                          </div>
                          
                          {entity.description && (
                            <p className="text-sm text-gray-700">{entity.description}</p>
                          )}
                          
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span>언급: {entity.mention_count}회</span>
                            <span>관계: {entity.relationship_count}개</span>
                          </div>

                          {entity.expansion_relation && (
                            <div className="text-xs text-blue-600">
                              {entity.expansion_source}와(과) {entity.expansion_relation} 관계로 확장됨
                            </div>
                          )}
                        </div>
                      </Card>
                    ))}
                    
                    {results.entities.length === 0 && (
                      <div className="text-center py-8 text-gray-500">
                        엔티티 결과가 없습니다.
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="relationships">
                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {results.relationships.map((rel, index) => (
                      <Card key={`${rel.relationship_id}-${index}`} className="p-4">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <Badge variant="outline" className="text-sm">
                              {rel.relation_type.replace('_', ' ')}
                            </Badge>
                            <Badge variant="outline">
                              신뢰도: {formatScore(rel.confidence_score)}
                            </Badge>
                          </div>

                          <div className="flex items-center space-x-3">
                            <div className="flex items-center space-x-2 flex-1">
                              {getEntityIcon(rel.source_entity.entity_type)}
                              <span className="font-medium">{rel.source_entity.name}</span>
                              <Badge className={getEntityTypeColor(rel.source_entity.entity_type)}>
                                {rel.source_entity.entity_type}
                              </Badge>
                            </div>
                            
                            <ArrowRight className="w-4 h-4 text-gray-400" />
                            
                            <div className="flex items-center space-x-2 flex-1">
                              {getEntityIcon(rel.target_entity.entity_type)}
                              <span className="font-medium">{rel.target_entity.name}</span>
                              <Badge className={getEntityTypeColor(rel.target_entity.entity_type)}>
                                {rel.target_entity.entity_type}
                              </Badge>
                            </div>
                          </div>

                          {rel.description && (
                            <p className="text-sm text-gray-700">{rel.description}</p>
                          )}

                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            {rel.is_bidirectional && <span>양방향</span>}
                          </div>
                        </div>
                      </Card>
                    ))}
                    
                    {results.relationships.length === 0 && (
                      <div className="text-center py-8 text-gray-500">
                        관계 결과가 없습니다.
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
}