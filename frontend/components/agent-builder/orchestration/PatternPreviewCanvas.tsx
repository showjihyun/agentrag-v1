'use client';

import React, { useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Users,
  ArrowRight,
  Zap,
  GitBranch,
  MessageSquare,
  Route,
  Hexagon,
  Bell,
  RefreshCw,
  Brain,
  Atom,
  Leaf,
  TrendingUp,
  Network,
  Heart,
  Crystal,
  Crown,
  Wrench,
  Eye,
  Merge,
  Star,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  ORCHESTRATION_TYPES,
  AGENT_ROLES,
  type OrchestrationTypeValue,
  type AgentRole,
} from '@/lib/constants/orchestration';

interface PatternPreviewCanvasProps {
  orchestrationType: OrchestrationTypeValue;
  className?: string;
  showMiniMap?: boolean;
  showControls?: boolean;
  interactive?: boolean;
}

// 미니 Agent 노드 컴포넌트
const PreviewAgentNode = ({ data }: { data: any }) => {
  const role = data.role as AgentRole;
  const roleInfo = AGENT_ROLES[role];
  
  const getIconComponent = (iconName: string) => {
    const iconMap: Record<string, React.ComponentType<any>> = {
      Crown, Wrench, Eye, Merge, Users, Star
    };
    return iconMap[iconName] || Users;
  };
  
  const IconComponent = getIconComponent(roleInfo.icon);
  
  return (
    <div
      className={cn(
        'px-3 py-2 rounded-lg border-2 shadow-sm min-w-[120px] bg-white',
        'flex items-center gap-2 text-sm'
      )}
      style={{ borderColor: roleInfo.color }}
    >
      <div
        className="p-1 rounded"
        style={{ backgroundColor: `${roleInfo.color}20`, color: roleInfo.color }}
      >
        <IconComponent className="w-4 h-4" />
      </div>
      <div>
        <div className="font-medium text-xs">{data.name}</div>
        <div className="text-xs text-gray-500">{roleInfo.name}</div>
      </div>
    </div>
  );
};

// 특수 노드 컴포넌트
const PreviewSpecialNode = ({ data }: { data: any }) => {
  const getIconComponent = (type: string) => {
    const iconMap: Record<string, React.ComponentType<any>> = {
      start: ArrowRight,
      end: ArrowRight,
      sync: RefreshCw,
      branch: GitBranch,
      consensus: MessageSquare,
      voting: Users,
    };
    return iconMap[type] || ArrowRight;
  };
  
  const IconComponent = getIconComponent(data.type);
  
  const getNodeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      start: '#10B981',
      end: '#EF4444',
      sync: '#F59E0B',
      branch: '#8B5CF6',
      consensus: '#06B6D4',
      voting: '#EC4899',
    };
    return colorMap[type] || '#6B7280';
  };
  
  const color = getNodeColor(data.type);
  
  return (
    <div
      className="px-3 py-2 rounded-lg border-2 shadow-sm min-w-[100px] bg-white flex items-center gap-2"
      style={{ borderColor: color }}
    >
      <div
        className="p-1 rounded"
        style={{ backgroundColor: `${color}20`, color }}
      >
        <IconComponent className="w-4 h-4" />
      </div>
      <span className="text-sm font-medium">{data.name}</span>
    </div>
  );
};

// 노드 타입 정의
const nodeTypes = {
  agent: PreviewAgentNode,
  special: PreviewSpecialNode,
};

export const PatternPreviewCanvas: React.FC<PatternPreviewCanvasProps> = ({
  orchestrationType,
  className,
  showMiniMap = false,
  showControls = false,
  interactive = false,
}) => {
  const pattern = ORCHESTRATION_TYPES[orchestrationType];
  
  const { nodes, edges } = useMemo(() => {
    const generatePreviewGraph = (type: OrchestrationTypeValue): { nodes: Node[]; edges: Edge[] } => {
      switch (type) {
        case 'sequential':
          return {
            nodes: [
              {
                id: 'start',
                type: 'special',
                position: { x: 50, y: 100 },
                data: { name: '시작', type: 'start' },
              },
              {
                id: 'agent1',
                type: 'agent',
                position: { x: 200, y: 100 },
                data: { name: 'Agent 1', role: 'worker' },
              },
              {
                id: 'agent2',
                type: 'agent',
                position: { x: 400, y: 100 },
                data: { name: 'Agent 2', role: 'worker' },
              },
              {
                id: 'agent3',
                type: 'agent',
                position: { x: 600, y: 100 },
                data: { name: 'Agent 3', role: 'synthesizer' },
              },
              {
                id: 'end',
                type: 'special',
                position: { x: 750, y: 100 },
                data: { name: '완료', type: 'end' },
              },
            ],
            edges: [
              { id: 'e1', source: 'start', target: 'agent1', animated: true },
              { id: 'e2', source: 'agent1', target: 'agent2', animated: true },
              { id: 'e3', source: 'agent2', target: 'agent3', animated: true },
              { id: 'e4', source: 'agent3', target: 'end', animated: true },
            ],
          };
          
        case 'parallel':
          return {
            nodes: [
              {
                id: 'start',
                type: 'special',
                position: { x: 50, y: 200 },
                data: { name: '시작', type: 'start' },
              },
              {
                id: 'agent1',
                type: 'agent',
                position: { x: 250, y: 50 },
                data: { name: 'Agent 1', role: 'worker' },
              },
              {
                id: 'agent2',
                type: 'agent',
                position: { x: 250, y: 200 },
                data: { name: 'Agent 2', role: 'worker' },
              },
              {
                id: 'agent3',
                type: 'agent',
                position: { x: 250, y: 350 },
                data: { name: 'Agent 3', role: 'worker' },
              },
              {
                id: 'synthesizer',
                type: 'agent',
                position: { x: 500, y: 200 },
                data: { name: 'Synthesizer', role: 'synthesizer' },
              },
              {
                id: 'end',
                type: 'special',
                position: { x: 650, y: 200 },
                data: { name: '완료', type: 'end' },
              },
            ],
            edges: [
              { id: 'e1', source: 'start', target: 'agent1', animated: true },
              { id: 'e2', source: 'start', target: 'agent2', animated: true },
              { id: 'e3', source: 'start', target: 'agent3', animated: true },
              { id: 'e4', source: 'agent1', target: 'synthesizer', animated: true },
              { id: 'e5', source: 'agent2', target: 'synthesizer', animated: true },
              { id: 'e6', source: 'agent3', target: 'synthesizer', animated: true },
              { id: 'e7', source: 'synthesizer', target: 'end', animated: true },
            ],
          };
          
        case 'hierarchical':
          return {
            nodes: [
              {
                id: 'start',
                type: 'special',
                position: { x: 50, y: 200 },
                data: { name: '시작', type: 'start' },
              },
              {
                id: 'manager',
                type: 'agent',
                position: { x: 250, y: 200 },
                data: { name: 'Manager', role: 'manager' },
              },
              {
                id: 'worker1',
                type: 'agent',
                position: { x: 450, y: 50 },
                data: { name: 'Worker 1', role: 'worker' },
              },
              {
                id: 'worker2',
                type: 'agent',
                position: { x: 450, y: 200 },
                data: { name: 'Worker 2', role: 'worker' },
              },
              {
                id: 'worker3',
                type: 'agent',
                position: { x: 450, y: 350 },
                data: { name: 'Worker 3', role: 'worker' },
              },
              {
                id: 'critic',
                type: 'agent',
                position: { x: 650, y: 200 },
                data: { name: 'Critic', role: 'critic' },
              },
              {
                id: 'end',
                type: 'special',
                position: { x: 800, y: 200 },
                data: { name: '완료', type: 'end' },
              },
            ],
            edges: [
              { id: 'e1', source: 'start', target: 'manager', animated: true },
              { id: 'e2', source: 'manager', target: 'worker1', animated: true },
              { id: 'e3', source: 'manager', target: 'worker2', animated: true },
              { id: 'e4', source: 'manager', target: 'worker3', animated: true },
              { id: 'e5', source: 'worker1', target: 'critic', animated: true },
              { id: 'e6', source: 'worker2', target: 'critic', animated: true },
              { id: 'e7', source: 'worker3', target: 'critic', animated: true },
              { id: 'e8', source: 'critic', target: 'end', animated: true },
              // 피드백 루프
              { id: 'e9', source: 'critic', target: 'manager', animated: true, style: { strokeDasharray: '5,5' } },
            ],
          };
          
        case 'consensus_building':
          return {
            nodes: [
              {
                id: 'start',
                type: 'special',
                position: { x: 50, y: 200 },
                data: { name: '시작', type: 'start' },
              },
              {
                id: 'expert1',
                type: 'agent',
                position: { x: 250, y: 50 },
                data: { name: 'Expert 1', role: 'specialist' },
              },
              {
                id: 'expert2',
                type: 'agent',
                position: { x: 250, y: 200 },
                data: { name: 'Expert 2', role: 'specialist' },
              },
              {
                id: 'expert3',
                type: 'agent',
                position: { x: 250, y: 350 },
                data: { name: 'Expert 3', role: 'specialist' },
              },
              {
                id: 'consensus',
                type: 'special',
                position: { x: 450, y: 200 },
                data: { name: '합의', type: 'consensus' },
              },
              {
                id: 'coordinator',
                type: 'agent',
                position: { x: 650, y: 200 },
                data: { name: 'Coordinator', role: 'coordinator' },
              },
              {
                id: 'end',
                type: 'special',
                position: { x: 800, y: 200 },
                data: { name: '완료', type: 'end' },
              },
            ],
            edges: [
              { id: 'e1', source: 'start', target: 'expert1', animated: true },
              { id: 'e2', source: 'start', target: 'expert2', animated: true },
              { id: 'e3', source: 'start', target: 'expert3', animated: true },
              { id: 'e4', source: 'expert1', target: 'consensus', animated: true },
              { id: 'e5', source: 'expert2', target: 'consensus', animated: true },
              { id: 'e6', source: 'expert3', target: 'consensus', animated: true },
              { id: 'e7', source: 'consensus', target: 'coordinator', animated: true },
              { id: 'e8', source: 'coordinator', target: 'end', animated: true },
              // 전문가 간 협상
              { id: 'e9', source: 'expert1', target: 'expert2', animated: true, style: { strokeDasharray: '3,3' } },
              { id: 'e10', source: 'expert2', target: 'expert3', animated: true, style: { strokeDasharray: '3,3' } },
              { id: 'e11', source: 'expert3', target: 'expert1', animated: true, style: { strokeDasharray: '3,3' } },
            ],
          };
          
        case 'swarm_intelligence':
          return {
            nodes: [
              {
                id: 'start',
                type: 'special',
                position: { x: 50, y: 200 },
                data: { name: '시작', type: 'start' },
              },
              // 군집 Agent들
              ...Array.from({ length: 6 }, (_, i) => ({
                id: `swarm${i + 1}`,
                type: 'agent',
                position: {
                  x: 250 + (i % 3) * 100,
                  y: 100 + Math.floor(i / 3) * 200,
                },
                data: { name: `Swarm ${i + 1}`, role: 'worker' },
              })),
              {
                id: 'coordinator',
                type: 'agent',
                position: { x: 600, y: 200 },
                data: { name: 'Coordinator', role: 'coordinator' },
              },
              {
                id: 'end',
                type: 'special',
                position: { x: 750, y: 200 },
                data: { name: '완료', type: 'end' },
              },
            ],
            edges: [
              { id: 'e0', source: 'start', target: 'coordinator', animated: true },
              // 군집 간 연결
              ...Array.from({ length: 6 }, (_, i) => ({
                id: `e${i + 1}`,
                source: 'coordinator',
                target: `swarm${i + 1}`,
                animated: true,
              })),
              // 군집 내부 통신 (일부만 표시)
              { id: 'e7', source: 'swarm1', target: 'swarm2', animated: true, style: { strokeDasharray: '2,2' } },
              { id: 'e8', source: 'swarm2', target: 'swarm3', animated: true, style: { strokeDasharray: '2,2' } },
              { id: 'e9', source: 'swarm4', target: 'swarm5', animated: true, style: { strokeDasharray: '2,2' } },
              { id: 'e10', source: 'swarm5', target: 'swarm6', animated: true, style: { strokeDasharray: '2,2' } },
              // 결과 수집
              ...Array.from({ length: 6 }, (_, i) => ({
                id: `er${i + 1}`,
                source: `swarm${i + 1}`,
                target: 'coordinator',
                animated: true,
                style: { strokeDasharray: '5,5' },
              })),
              { id: 'e_final', source: 'coordinator', target: 'end', animated: true },
            ],
          };
          
        default:
          // 기본 순차 패턴
          return {
            nodes: [
              {
                id: 'start',
                type: 'special',
                position: { x: 50, y: 100 },
                data: { name: '시작', type: 'start' },
              },
              {
                id: 'agent1',
                type: 'agent',
                position: { x: 250, y: 100 },
                data: { name: 'Agent 1', role: 'worker' },
              },
              {
                id: 'agent2',
                type: 'agent',
                position: { x: 450, y: 100 },
                data: { name: 'Agent 2', role: 'worker' },
              },
              {
                id: 'end',
                type: 'special',
                position: { x: 650, y: 100 },
                data: { name: '완료', type: 'end' },
              },
            ],
            edges: [
              { id: 'e1', source: 'start', target: 'agent1', animated: true },
              { id: 'e2', source: 'agent1', target: 'agent2', animated: true },
              { id: 'e3', source: 'agent2', target: 'end', animated: true },
            ],
          };
      }
    };
    
    return generatePreviewGraph(orchestrationType);
  }, [orchestrationType]);

  if (!pattern) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-gray-500">
            패턴을 선택해주세요
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <span>{pattern.name} 미리보기</span>
            <Badge variant="outline" className="text-xs">
              {pattern.complexity === 'simple' && '간단'}
              {pattern.complexity === 'medium' && '보통'}
              {pattern.complexity === 'complex' && '복잡'}
            </Badge>
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="h-[400px] border rounded-b-lg">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            nodesDraggable={interactive}
            nodesConnectable={false}
            elementsSelectable={interactive}
            panOnDrag={interactive}
            zoomOnScroll={interactive}
            zoomOnPinch={interactive}
            zoomOnDoubleClick={interactive}
            preventScrolling={!interactive}
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
            {showControls && <Controls />}
            {showMiniMap && (
              <MiniMap
                nodeStrokeColor="#374151"
                nodeColor="#F3F4F6"
                nodeBorderRadius={8}
                maskColor="rgba(0, 0, 0, 0.1)"
                position="bottom-right"
              />
            )}
          </ReactFlow>
        </div>
        
        <div className="p-4 border-t bg-gray-50">
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 border-2 border-blue-500 rounded"></div>
              <span>Agent</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 border-2 border-gray-400 rounded"></div>
              <span>제어 노드</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-0.5 bg-gray-400"></div>
              <span>실행 흐름</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-0.5 bg-gray-400" style={{ backgroundImage: 'repeating-linear-gradient(to right, transparent, transparent 2px, #9CA3AF 2px, #9CA3AF 4px)' }}></div>
              <span>통신/피드백</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};