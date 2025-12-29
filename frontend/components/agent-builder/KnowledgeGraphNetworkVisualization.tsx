"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  Network, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Download, 
  Settings, 
  Filter,
  Search,
  Loader2,
  Info,
  Eye,
  EyeOff,
  Maximize2,
  Minimize2,
  Play,
  Pause,
  SkipForward,
  Users,
  Building,
  MapPin,
  Lightbulb,
  Calendar,
  Package,
  FileText,
  Hash
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface NetworkNode {
  id: string;
  name: string;
  type: string;
  size: number;
  color: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
  properties: Record<string, any>;
  confidence: number;
  mentionCount: number;
  relationshipCount: number;
}

interface NetworkLink {
  id: string;
  source: string | NetworkNode;
  target: string | NetworkNode;
  type: string;
  strength: number;
  color: string;
  confidence: number;
  properties: Record<string, any>;
}

interface NetworkData {
  nodes: NetworkNode[];
  links: NetworkLink[];
}

interface KnowledgeGraphNetworkVisualizationProps {
  knowledgeGraphId: string;
  width?: number;
  height?: number;
}

const ENTITY_TYPE_COLORS = {
  person: '#3B82F6',      // Blue
  organization: '#10B981', // Green
  location: '#EF4444',     // Red
  concept: '#8B5CF6',      // Purple
  event: '#F59E0B',        // Yellow
  product: '#F97316',      // Orange
  document: '#6B7280',     // Gray
  topic: '#6366F1',        // Indigo
  custom: '#EC4899',       // Pink
};

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

export default function KnowledgeGraphNetworkVisualization({
  knowledgeGraphId,
  width = 800,
  height = 600,
}: KnowledgeGraphNetworkVisualizationProps) {
  const { toast } = useToast();
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<any>(null);
  
  // State
  const [networkData, setNetworkData] = useState<NetworkData>({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null);
  const [selectedLink, setSelectedLink] = useState<NetworkLink | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isSimulationRunning, setIsSimulationRunning] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  
  // Filters and settings
  const [entityTypeFilter, setEntityTypeFilter] = useState<string[]>([]);
  const [relationTypeFilter, setRelationTypeFilter] = useState<string[]>([]);
  const [confidenceThreshold, setConfidenceThreshold] = useState([0.5]);
  const [nodeSize, setNodeSize] = useState([1.0]);
  const [linkStrength, setLinkStrength] = useState([1.0]);
  const [showLabels, setShowLabels] = useState(true);
  const [showArrows, setShowArrows] = useState(true);
  const [layoutType, setLayoutType] = useState('force');
  
  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  
  // Performance and UX
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [networkStats, setNetworkStats] = useState<{
    totalNodes: number;
    visibleNodes: number;
    totalLinks: number;
    visibleLinks: number;
    density: number;
  } | null>(null);

  // Load network data
  useEffect(() => {
    loadNetworkData();
  }, [knowledgeGraphId, entityTypeFilter, relationTypeFilter, confidenceThreshold]);

  // Initialize D3 simulation
  useEffect(() => {
    if (networkData.nodes.length > 0) {
      initializeSimulation();
    }
  }, [networkData, nodeSize, linkStrength, layoutType]);

  // Search functionality
  useEffect(() => {
    if (searchQuery) {
      const highlighted = new Set<string>();
      networkData.nodes.forEach(node => {
        if (node.name.toLowerCase().includes(searchQuery.toLowerCase())) {
          highlighted.add(node.id);
        }
      });
      setHighlightedNodes(highlighted);
    } else {
      setHighlightedNodes(new Set());
    }
  }, [searchQuery, networkData]);

  const loadNetworkData = async () => {
    setIsLoading(true);
    setLoadingProgress(0);
    
    try {
      // Progress simulation for better UX
      const progressInterval = setInterval(() => {
        setLoadingProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      // Load entities
      setLoadingProgress(20);
      const entitiesResponse = await fetch(`/api/agent-builder/knowledge-graphs/${knowledgeGraphId}/entities/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_types: entityTypeFilter.length > 0 ? entityTypeFilter : undefined,
          limit: 100,
        }),
      });

      if (!entitiesResponse.ok) throw new Error('Failed to load entities');
      const entitiesData = await entitiesResponse.json();
      setLoadingProgress(50);

      // Load relationships
      const relationshipsResponse = await fetch(`/api/agent-builder/knowledge-graphs/${knowledgeGraphId}/relationships/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          relation_types: relationTypeFilter.length > 0 ? relationTypeFilter : undefined,
          limit: 200,
        }),
      });

      if (!relationshipsResponse.ok) throw new Error('Failed to load relationships');
      const relationshipsData = await relationshipsResponse.json();
      setLoadingProgress(70);

      // Convert to network format
      const nodes: NetworkNode[] = entitiesData.entities
        .filter((entity: any) => entity.confidence_score >= confidenceThreshold[0])
        .map((entity: any) => ({
          id: entity.id,
          name: entity.name,
          type: entity.entity_type,
          size: Math.max(5, Math.min(20, entity.mention_count * 2)),
          color: ENTITY_TYPE_COLORS[entity.entity_type as keyof typeof ENTITY_TYPE_COLORS] || '#6B7280',
          properties: entity.properties,
          confidence: entity.confidence_score,
          mentionCount: entity.mention_count,
          relationshipCount: entity.relationship_count,
        }));

      const nodeIds = new Set(nodes.map(n => n.id));
      const links: NetworkLink[] = relationshipsData.relationships
        .filter((rel: any) => 
          rel.confidence_score >= confidenceThreshold[0] &&
          nodeIds.has(rel.source_entity.id) &&
          nodeIds.has(rel.target_entity.id)
        )
        .map((rel: any) => ({
          id: rel.id,
          source: rel.source_entity.id,
          target: rel.target_entity.id,
          type: rel.relation_type,
          strength: rel.confidence_score,
          color: '#94A3B8',
          confidence: rel.confidence_score,
          properties: rel.properties,
        }));

      setLoadingProgress(90);
      setNetworkData({ nodes, links });

      // Calculate network statistics
      const density = nodes.length > 1 ? (2 * links.length) / (nodes.length * (nodes.length - 1)) : 0;
      setNetworkStats({
        totalNodes: entitiesData.entities.length,
        visibleNodes: nodes.length,
        totalLinks: relationshipsData.relationships.length,
        visibleLinks: links.length,
        density: density
      });

      clearInterval(progressInterval);
      setLoadingProgress(100);

      if (nodes.length === 0) {
        toast({
          title: "정보",
          description: "현재 필터 조건에 맞는 데이터가 없습니다. 필터를 조정해보세요.",
        });
      }

    } catch (error) {
      console.error('Error loading network data:', error);
      toast({
        title: "오류",
        description: "네트워크 데이터를 불러오는데 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
      setTimeout(() => setLoadingProgress(0), 1000);
    }
  };

  const initializeSimulation = async () => {
    if (!svgRef.current || typeof window === 'undefined') return;

    try {
      // Dynamic import for D3 (client-side only)
      const d3 = await import('d3');
      const svg = d3.select(svgRef.current);
      svg.selectAll("*").remove();

      const actualWidth = isFullscreen ? window.innerWidth : width;
      const actualHeight = isFullscreen ? window.innerHeight : height;

      // Create zoom behavior
      const zoom = d3.zoom()
        .scaleExtent([0.1, 10])
        .on('zoom', (event) => {
          container.attr('transform', event.transform);
        });

      svg.call(zoom as any);

      // Create container for zoomable content
      const container = svg.append('g');

      // Create simulation
      const simulation = d3.forceSimulation(networkData.nodes as any)
        .force('link', d3.forceLink(networkData.links)
          .id((d: any) => d.id)
          .strength(d => (d as NetworkLink).strength * linkStrength[0])
        )
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(actualWidth / 2, actualHeight / 2))
        .force('collision', d3.forceCollide().radius(d => (d as NetworkNode).size + 5));

      simulationRef.current = simulation;

      // Create arrow markers
      if (showArrows) {
        const defs = svg.append('defs');
        defs.selectAll('marker')
          .data(['arrow'])
          .enter()
          .append('marker')
          .attr('id', 'arrow')
          .attr('viewBox', '0 -5 10 10')
          .attr('refX', 15)
          .attr('refY', 0)
          .attr('markerWidth', 6)
          .attr('markerHeight', 6)
          .attr('orient', 'auto')
          .append('path')
          .attr('d', 'M0,-5L10,0L0,5')
          .attr('fill', '#94A3B8');
      }

      // Create links
      const link = container.append('g')
        .selectAll('line')
        .data(networkData.links)
        .enter()
        .append('line')
        .attr('stroke', d => d.color)
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.max(1, d.strength * 3))
        .attr('marker-end', showArrows ? 'url(#arrow)' : null)
        .style('cursor', 'pointer')
        .on('click', (event, d) => {
          setSelectedLink(d);
          setSelectedNode(null);
        });

      // Create nodes
      const node = container.append('g')
        .selectAll('circle')
        .data(networkData.nodes)
        .enter()
        .append('circle')
        .attr('r', d => d.size * nodeSize[0])
        .attr('fill', d => d.color)
        .attr('stroke', d => highlightedNodes.has(d.id) ? '#FFD700' : '#fff')
        .attr('stroke-width', d => highlightedNodes.has(d.id) ? 3 : 1.5)
        .style('cursor', 'pointer')
        .call(d3.drag<SVGCircleElement, NetworkNode>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
        )
        .on('click', (event, d) => {
          setSelectedNode(d);
          setSelectedLink(null);
        });

      // Create labels
      let labels: any = null;
      if (showLabels) {
        labels = container.append('g')
          .selectAll('text')
          .data(networkData.nodes)
          .enter()
          .append('text')
          .text(d => d.name)
          .attr('font-size', '12px')
          .attr('font-family', 'Arial, sans-serif')
          .attr('fill', '#374151')
          .attr('text-anchor', 'middle')
          .attr('dy', d => d.size * nodeSize[0] + 15)
          .style('pointer-events', 'none');
      }

      // Update positions on simulation tick
      simulation.on('tick', () => {
        link
          .attr('x1', (d: any) => d.source.x)
          .attr('y1', (d: any) => d.source.y)
          .attr('x2', (d: any) => d.target.x)
          .attr('y2', (d: any) => d.target.y);

        node
          .attr('cx', (d: any) => d.x)
          .attr('cy', (d: any) => d.y);

        if (labels) {
          labels
            .attr('x', (d: any) => d.x)
            .attr('y', (d: any) => d.y);
        }
      });

      // Control simulation
      if (!isSimulationRunning) {
        simulation.stop();
      }
    } catch (error) {
      console.error('Failed to initialize D3 simulation:', error);
    }
  };

  const handleZoomIn = async () => {
    if (svgRef.current && typeof window !== 'undefined') {
      try {
        const d3 = await import('d3');
        d3.select(svgRef.current).transition().call(
          d3.zoom().scaleBy as any, 1.5
        );
      } catch (error) {
        console.error('Failed to load D3:', error);
      }
    }
  };

  const handleZoomOut = async () => {
    if (svgRef.current && typeof window !== 'undefined') {
      try {
        const d3 = await import('d3');
        d3.select(svgRef.current).transition().call(
          d3.zoom().scaleBy as any, 0.67
        );
      } catch (error) {
        console.error('Failed to load D3:', error);
      }
    }
  };

  const handleReset = async () => {
    if (svgRef.current && typeof window !== 'undefined') {
      try {
        const d3 = await import('d3');
        d3.select(svgRef.current).transition().call(
          d3.zoom().transform as any,
          d3.zoomIdentity
        );
      } catch (error) {
        console.error('Failed to load D3:', error);
      }
    }
  };

  const handleExport = () => {
    if (!svgRef.current) return;

    const svgElement = svgRef.current;
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `knowledge-graph-${Date.now()}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "성공",
      description: "지식 그래프가 SVG 파일로 내보내졌습니다.",
    });
  };

  const toggleSimulation = () => {
    if (simulationRef.current) {
      if (isSimulationRunning) {
        simulationRef.current.stop();
      } else {
        simulationRef.current.restart();
      }
      setIsSimulationRunning(!isSimulationRunning);
    }
  };

  const getEntityIcon = (entityType: string) => {
    const IconComponent = ENTITY_TYPE_ICONS[entityType as keyof typeof ENTITY_TYPE_ICONS] || Hash;
    return <IconComponent className="w-4 h-4" />;
  };

  const renderOnboardingHelp = () => (
    <Alert className="mb-4 border-blue-200 bg-blue-50">
      <Info className="h-4 w-4 text-blue-600" />
      <AlertDescription>
        <div className="space-y-3">
          <div className="font-medium text-blue-900">네트워크 시각화 사용법</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-blue-800">
            <div className="space-y-2">
              <div className="font-medium">🖱️ 마우스 조작</div>
              <ul className="space-y-1 text-xs">
                <li>• 드래그: 노드 이동</li>
                <li>• 휠: 확대/축소</li>
                <li>• 클릭: 노드/링크 선택</li>
              </ul>
            </div>
            <div className="space-y-2">
              <div className="font-medium">🎛️ 컨트롤</div>
              <ul className="space-y-1 text-xs">
                <li>• 검색: 노드 하이라이트</li>
                <li>• 필터: 신뢰도/타입 조정</li>
                <li>• 시뮬레이션: 일시정지/재생</li>
              </ul>
            </div>
          </div>
        </div>
      </AlertDescription>
    </Alert>
  );

  const renderSettingsPanel = () => (
    <Card className="mb-4">
      <CardHeader>
        <CardTitle className="text-lg flex items-center space-x-2">
          <Settings className="w-5 h-5" />
          <span>고급 설정</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-medium">레이아웃 알고리즘</Label>
            <Select value={layoutType} onValueChange={setLayoutType}>
              <SelectTrigger className="mt-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="force">Force-directed</SelectItem>
                <SelectItem value="circular">원형 배치</SelectItem>
                <SelectItem value="hierarchical">계층적 배치</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-sm font-medium">노드 색상 기준</Label>
            <Select defaultValue="type">
              <SelectTrigger className="mt-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="type">엔티티 타입</SelectItem>
                <SelectItem value="confidence">신뢰도</SelectItem>
                <SelectItem value="centrality">중심성</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-2">
            <Switch checked={showLabels} onCheckedChange={setShowLabels} />
            <Label className="text-sm">노드 라벨</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Switch checked={showArrows} onCheckedChange={setShowArrows} />
            <Label className="text-sm">방향 화살표</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Switch checked={isSimulationRunning} onCheckedChange={toggleSimulation} />
            <Label className="text-sm">물리 시뮬레이션</Label>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const actualWidth = isFullscreen ? (typeof window !== 'undefined' ? window.innerWidth : 800) : width;
  const actualHeight = isFullscreen ? (typeof window !== 'undefined' ? window.innerHeight : 600) : height;

  return (
    <div className={`space-y-4 ${isFullscreen ? 'fixed inset-0 z-50 bg-white p-4' : ''}`}>
      {/* Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Network className="w-5 h-5 text-blue-600" />
              <CardTitle>지식 그래프 네트워크</CardTitle>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={handleZoomIn}>
                <ZoomIn className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={handleZoomOut}>
                <ZoomOut className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={handleReset}>
                <RotateCcw className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={toggleSimulation}>
                {isSimulationRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </Button>
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={() => setIsFullscreen(!isFullscreen)}>
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div>
              <Label className="text-sm font-medium">검색</Label>
              <Input
                placeholder="엔티티 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="mt-1"
              />
            </div>

            {/* Confidence Threshold */}
            <div>
              <Label className="text-sm font-medium">신뢰도 임계값: {confidenceThreshold[0].toFixed(2)}</Label>
              <Slider
                value={confidenceThreshold}
                onValueChange={setConfidenceThreshold}
                max={1}
                min={0}
                step={0.1}
                className="mt-2"
              />
            </div>

            {/* Node Size */}
            <div>
              <Label className="text-sm font-medium">노드 크기: {nodeSize[0].toFixed(1)}x</Label>
              <Slider
                value={nodeSize}
                onValueChange={setNodeSize}
                max={3}
                min={0.5}
                step={0.1}
                className="mt-2"
              />
            </div>

            {/* Link Strength */}
            <div>
              <Label className="text-sm font-medium">링크 강도: {linkStrength[0].toFixed(1)}x</Label>
              <Slider
                value={linkStrength}
                onValueChange={setLinkStrength}
                max={3}
                min={0.1}
                step={0.1}
                className="mt-2"
              />
            </div>
          </div>

          <div className="flex items-center space-x-6 mt-4">
            <div className="flex items-center space-x-2">
              <Switch checked={showLabels} onCheckedChange={setShowLabels} />
              <Label className="text-sm">라벨 표시</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Switch checked={showArrows} onCheckedChange={setShowArrows} />
              <Label className="text-sm">화살표 표시</Label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Network Visualization */}
      <div className="flex gap-4">
        <Card className="flex-1">
          <CardContent className="p-0">
            {isLoading ? (
              <div className="flex items-center justify-center" style={{ width: actualWidth, height: actualHeight }}>
                <Loader2 className="w-8 h-8 animate-spin" />
              </div>
            ) : (
              <svg
                ref={svgRef}
                width={actualWidth}
                height={actualHeight}
                style={{ border: '1px solid #e5e7eb', borderRadius: '8px' }}
              />
            )}
          </CardContent>
        </Card>

        {/* Details Panel */}
        {!isFullscreen && (selectedNode || selectedLink) && (
          <Card className="w-80">
            <CardHeader>
              <CardTitle className="text-lg">
                {selectedNode ? '엔티티 정보' : '관계 정보'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {selectedNode && (
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    {getEntityIcon(selectedNode.type)}
                    <span className="font-medium">{selectedNode.name}</span>
                    <Badge style={{ backgroundColor: selectedNode.color, color: 'white' }}>
                      {selectedNode.type}
                    </Badge>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium">신뢰도:</span> {(selectedNode.confidence * 100).toFixed(1)}%
                    </div>
                    <div>
                      <span className="font-medium">언급 횟수:</span> {selectedNode.mentionCount}
                    </div>
                    <div>
                      <span className="font-medium">관계 수:</span> {selectedNode.relationshipCount}
                    </div>
                  </div>

                  {Object.keys(selectedNode.properties).length > 0 && (
                    <div>
                      <Label className="text-sm font-medium">속성</Label>
                      <div className="mt-1 space-y-1">
                        {Object.entries(selectedNode.properties).map(([key, value]) => (
                          <div key={key} className="text-xs">
                            <span className="font-medium">{key}:</span> {String(value)}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {selectedLink && (
                <div className="space-y-4">
                  <div>
                    <Badge variant="outline">{selectedLink.type}</Badge>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium">신뢰도:</span> {(selectedLink.confidence * 100).toFixed(1)}%
                    </div>
                    <div>
                      <span className="font-medium">강도:</span> {selectedLink.strength.toFixed(2)}
                    </div>
                  </div>

                  {Object.keys(selectedLink.properties).length > 0 && (
                    <div>
                      <Label className="text-sm font-medium">속성</Label>
                      <div className="mt-1 space-y-1">
                        {Object.entries(selectedLink.properties).map(([key, value]) => (
                          <div key={key} className="text-xs">
                            <span className="font-medium">{key}:</span> {String(value)}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">네트워크 통계</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{networkData.nodes.length}</div>
              <div className="text-sm text-gray-600">엔티티</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{networkData.links.length}</div>
              <div className="text-sm text-gray-600">관계</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {networkData.nodes.length > 0 ? (networkData.links.length / networkData.nodes.length).toFixed(1) : '0'}
              </div>
              <div className="text-sm text-gray-600">평균 연결도</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-600">
                {new Set(networkData.nodes.map(n => n.type)).size}
              </div>
              <div className="text-sm text-gray-600">엔티티 타입</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}