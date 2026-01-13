/**
 * Collaborative Workflow Editor
 * 
 * 실시간 협업이 가능한 워크플로우 에디터
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ReactFlow, Node, Edge, useNodesState, useEdgesState, Background, Controls } from 'reactflow';
import { useCollaboration, CollaborativeUser, CursorPosition } from '@/hooks/useCollaboration';
import { UserCursor } from './UserCursor';
import { CollaborationPanel } from './CollaborationPanel';
import { ChangeConflictDialog } from './ChangeConflictDialog';
import { useAuth } from '@/contexts/AuthContext';

interface CollaborativeWorkflowEditorProps {
  workflowId: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
  readOnly?: boolean;
}

export const CollaborativeWorkflowEditor: React.FC<CollaborativeWorkflowEditorProps> = ({
  workflowId,
  initialNodes = [],
  initialEdges = [],
  onNodesChange,
  onEdgesChange,
  readOnly = false
}) => {
  const { user } = useAuth();
  const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);
  const [showCollaborationPanel, setShowCollaborationPanel] = useState(true);
  const [conflictingChanges, setConflictingChanges] = useState<any[]>([]);
  
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

  // 협업 훅 사용
  const {
    collaborativeState,
    updateCursor,
    broadcastSelection,
    broadcastChange,
    applyChange,
    rejectChange,
    isConnected
  } = useCollaboration({
    workflowId,
    enabled: !readOnly,
    conflictResolution: 'last-write-wins'
  });

  // 마우스 움직임 추적
  const handleMouseMove = useCallback((event: React.MouseEvent) => {
    if (!isConnected || readOnly) return;

    const bounds = reactFlowWrapper.current?.getBoundingClientRect();
    if (!bounds) return;

    const x = event.clientX - bounds.left;
    const y = event.clientY - bounds.top;

    // 현재 마우스 위치의 노드 찾기
    const nodeId = findNodeAtPosition(x, y);

    updateCursor({ x, y, nodeId });
  }, [isConnected, readOnly, updateCursor]);

  // 위치에서 노드 찾기
  const findNodeAtPosition = useCallback((x: number, y: number): string | undefined => {
    if (!reactFlowInstance) return undefined;

    const position = reactFlowInstance.project({ x, y });
    
    for (const node of nodes) {
      const nodeElement = document.querySelector(`[data-id="${node.id}"]`);
      if (nodeElement) {
        const rect = nodeElement.getBoundingClientRect();
        const wrapperRect = reactFlowWrapper.current?.getBoundingClientRect();
        
        if (wrapperRect) {
          const relativeRect = {
            left: rect.left - wrapperRect.left,
            top: rect.top - wrapperRect.top,
            right: rect.right - wrapperRect.left,
            bottom: rect.bottom - wrapperRect.top
          };

          if (x >= relativeRect.left && x <= relativeRect.right &&
              y >= relativeRect.top && y <= relativeRect.bottom) {
            return node.id;
          }
        }
      }
    }

    return undefined;
  }, [reactFlowInstance, nodes]);

  // 노드 변경 처리
  const handleNodesChange = useCallback((changes: any[]) => {
    if (readOnly) return;

    // 로컬 상태 업데이트
    onNodesChangeInternal(changes);

    // 협업 변경사항 브로드캐스트
    changes.forEach(change => {
      if (change.type === 'position' || change.type === 'dimensions') {
        broadcastChange({
          type: 'node_update',
          nodeId: change.id,
          changes: change
        });
      }
    });
  }, [readOnly, onNodesChangeInternal, broadcastChange]);

  // 엣지 변경 처리
  const handleEdgesChange = useCallback((changes: any[]) => {
    if (readOnly) return;

    // 로컬 상태 업데이트
    onEdgesChangeInternal(changes);

    // 협업 변경사항 브로드캐스트
    changes.forEach(change => {
      broadcastChange({
        type: 'edge_update',
        edgeId: change.id,
        changes: change
      });
    });
  }, [readOnly, onEdgesChangeInternal, broadcastChange]);

  // 노드 선택 처리
  const handleNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    if (readOnly) return;

    broadcastSelection(node.id, 'select');
  }, [readOnly, broadcastSelection]);

  // 노드 드래그 시작
  const handleNodeDragStart = useCallback((event: React.MouseEvent, node: Node) => {
    if (readOnly) return;

    broadcastSelection(node.id, 'drag');
  }, [readOnly, broadcastSelection]);

  // 원격 변경사항 적용
  useEffect(() => {
    const unappliedChanges = collaborativeState.changes.filter(change => !change.applied);
    
    unappliedChanges.forEach(change => {
      try {
        if (change.type === 'node_update') {
          setNodes(currentNodes => 
            currentNodes.map(node => 
              node.id === change.nodeId 
                ? { ...node, ...change.changes }
                : node
            )
          );
        } else if (change.type === 'edge_update') {
          setEdges(currentEdges =>
            currentEdges.map(edge =>
              edge.id === change.edgeId
                ? { ...edge, ...change.changes }
                : edge
            )
          );
        }

        // 변경사항을 적용됨으로 표시
        applyChange(change.id);
      } catch (error) {
        console.error('Failed to apply remote change:', error);
        // 충돌 발생 시 충돌 해결 다이얼로그에 추가
        setConflictingChanges(prev => [...prev, change]);
      }
    });
  }, [collaborativeState.changes, applyChange, setNodes, setEdges]);

  // 노드/엣지 변경 시 부모 컴포넌트에 알림
  useEffect(() => {
    onNodesChange?.(nodes);
  }, [nodes, onNodesChange]);

  useEffect(() => {
    onEdgesChange?.(edges);
  }, [edges, onEdgesChange]);

  // 다른 사용자의 커서 렌더링
  const renderUserCursors = () => {
    return Array.from(collaborativeState.cursors.entries()).map(([userId, cursor]) => {
      const user = collaborativeState.users.get(userId);
      if (!user || userId === user?.id) return null;

      return (
        <UserCursor
          key={userId}
          user={user}
          position={cursor}
          isVisible={Date.now() - cursor.timestamp.getTime() < 5000} // 5초 후 숨김
        />
      );
    });
  };

  // 선택된 노드 하이라이트
  const getNodeStyle = (nodeId: string) => {
    const selection = collaborativeState.selections.get(nodeId);
    if (!selection || selection.userId === user?.id) return {};

    const user = collaborativeState.users.get(selection.userId);
    if (!user) return {};

    return {
      boxShadow: `0 0 0 2px ${user.color}`,
      borderRadius: '4px'
    };
  };

  return (
    <div className="relative w-full h-full">
      {/* 협업 패널 */}
      {showCollaborationPanel && (
        <CollaborationPanel
          users={Array.from(collaborativeState.users.values())}
          isConnected={isConnected}
          onClose={() => setShowCollaborationPanel(false)}
        />
      )}

      {/* React Flow */}
      <div 
        ref={reactFlowWrapper}
        className="w-full h-full"
        onMouseMove={handleMouseMove}
      >
        <ReactFlow
          nodes={nodes.map(node => ({
            ...node,
            style: { ...node.style, ...getNodeStyle(node.id) }
          }))}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onNodeClick={handleNodeClick}
          onNodeDragStart={handleNodeDragStart}
          onInit={setReactFlowInstance}
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>

        {/* 사용자 커서들 */}
        {renderUserCursors()}
      </div>

      {/* 협업 상태 표시 */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-sm text-gray-600">
          {isConnected ? '연결됨' : '연결 끊김'}
        </span>
        
        {collaborativeState.users.size > 1 && (
          <button
            onClick={() => setShowCollaborationPanel(true)}
            className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            {collaborativeState.users.size - 1}명 협업 중
          </button>
        )}
      </div>

      {/* 충돌 해결 다이얼로그 */}
      {conflictingChanges.length > 0 && (
        <ChangeConflictDialog
          conflicts={conflictingChanges}
          onResolve={(changeId, resolution) => {
            if (resolution === 'accept') {
              applyChange(changeId);
            } else {
              rejectChange(changeId);
            }
            setConflictingChanges(prev => prev.filter(c => c.id !== changeId));
          }}
          onClose={() => setConflictingChanges([])}
        />
      )}
    </div>
  );
};