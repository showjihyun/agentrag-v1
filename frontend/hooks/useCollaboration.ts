/**
 * Real-time Collaboration Hook
 * 
 * 실시간 협업 기능을 위한 React Hook
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';

export interface CollaborativeUser {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  color: string;
  isOnline: boolean;
  lastSeen: Date;
}

export interface CursorPosition {
  x: number;
  y: number;
  nodeId?: string;
  timestamp: Date;
}

export interface NodeSelection {
  nodeId: string;
  userId: string;
  timestamp: Date;
  type: 'select' | 'edit' | 'drag';
}

export interface CollaborationChange {
  id: string;
  type: 'node_update' | 'node_add' | 'node_delete' | 'edge_update' | 'edge_add' | 'edge_delete';
  nodeId?: string;
  edgeId?: string;
  changes: any;
  userId: string;
  timestamp: Date;
  applied: boolean;
}

export interface CollaborativeState {
  users: Map<string, CollaborativeUser>;
  cursors: Map<string, CursorPosition>;
  selections: Map<string, NodeSelection>;
  changes: CollaborationChange[];
  isConnected: boolean;
  roomId: string;
}

interface UseCollaborationOptions {
  workflowId: string;
  enabled?: boolean;
  conflictResolution?: 'last-write-wins' | 'operational-transform';
}

export const useCollaboration = (options: UseCollaborationOptions) => {
  const { user } = useAuth();
  const [collaborativeState, setCollaborativeState] = useState<CollaborativeState>({
    users: new Map(),
    cursors: new Map(),
    selections: new Map(),
    changes: [],
    isConnected: false,
    roomId: options.workflowId
  });

  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const changeQueueRef = useRef<CollaborationChange[]>([]);

  // 사용자 색상 생성
  const generateUserColor = useCallback((userId: string): string => {
    const colors = [
      '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
      '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'
    ];
    const hash = userId.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    return colors[Math.abs(hash) % colors.length];
  }, []);

  // WebSocket 연결
  const connect = useCallback(() => {
    if (!options.enabled || !user) return;

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/collaboration/${options.workflowId}`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Collaboration WebSocket connected');
        
        // 사용자 정보 전송
        const joinMessage = {
          type: 'user_join',
          user: {
            id: user.id,
            name: user.name,
            email: user.email,
            avatar: user.avatar,
            color: generateUserColor(user.id)
          }
        };
        
        wsRef.current?.send(JSON.stringify(joinMessage));
        
        setCollaborativeState(prev => ({
          ...prev,
          isConnected: true
        }));

        // 하트비트 시작
        startHeartbeat();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('Failed to parse collaboration message:', error);
        }
      };

      wsRef.current.onclose = () => {
        console.log('Collaboration WebSocket disconnected');
        setCollaborativeState(prev => ({
          ...prev,
          isConnected: false
        }));
        
        stopHeartbeat();
        
        // 자동 재연결
        if (options.enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('Collaboration WebSocket error:', error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [options.enabled, options.workflowId, user, generateUserColor]);

  // 메시지 처리
  const handleMessage = useCallback((message: any) => {
    switch (message.type) {
      case 'user_joined':
        setCollaborativeState(prev => {
          const newUsers = new Map(prev.users);
          newUsers.set(message.user.id, {
            ...message.user,
            isOnline: true,
            lastSeen: new Date()
          });
          return { ...prev, users: newUsers };
        });
        break;

      case 'user_left':
        setCollaborativeState(prev => {
          const newUsers = new Map(prev.users);
          const user = newUsers.get(message.userId);
          if (user) {
            newUsers.set(message.userId, {
              ...user,
              isOnline: false,
              lastSeen: new Date()
            });
          }
          return { ...prev, users: newUsers };
        });
        break;

      case 'cursor_update':
        if (message.userId !== user?.id) {
          setCollaborativeState(prev => {
            const newCursors = new Map(prev.cursors);
            newCursors.set(message.userId, {
              x: message.position.x,
              y: message.position.y,
              nodeId: message.position.nodeId,
              timestamp: new Date(message.timestamp)
            });
            return { ...prev, cursors: newCursors };
          });
        }
        break;

      case 'node_selection':
        if (message.userId !== user?.id) {
          setCollaborativeState(prev => {
            const newSelections = new Map(prev.selections);
            newSelections.set(message.nodeId, {
              nodeId: message.nodeId,
              userId: message.userId,
              timestamp: new Date(message.timestamp),
              type: message.selectionType
            });
            return { ...prev, selections: newSelections };
          });
        }
        break;

      case 'workflow_change':
        if (message.userId !== user?.id) {
          const change: CollaborationChange = {
            id: message.changeId,
            type: message.changeType,
            nodeId: message.nodeId,
            edgeId: message.edgeId,
            changes: message.changes,
            userId: message.userId,
            timestamp: new Date(message.timestamp),
            applied: false
          };
          
          setCollaborativeState(prev => ({
            ...prev,
            changes: [...prev.changes, change]
          }));
        }
        break;

      case 'users_list':
        setCollaborativeState(prev => {
          const newUsers = new Map();
          message.users.forEach((u: any) => {
            newUsers.set(u.id, {
              ...u,
              lastSeen: new Date(u.lastSeen)
            });
          });
          return { ...prev, users: newUsers };
        });
        break;
    }
  }, [user?.id]);

  // 하트비트
  const startHeartbeat = useCallback(() => {
    heartbeatRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'heartbeat' }));
      }
    }, 30000); // 30초마다
  }, []);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }
  }, []);

  // 커서 위치 업데이트
  const updateCursor = useCallback((position: { x: number; y: number; nodeId?: string }) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const message = {
      type: 'cursor_update',
      position: {
        ...position,
        timestamp: new Date().toISOString()
      }
    };

    wsRef.current.send(JSON.stringify(message));
  }, []);

  // 노드 선택 브로드캐스트
  const broadcastSelection = useCallback((nodeId: string, selectionType: 'select' | 'edit' | 'drag') => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const message = {
      type: 'node_selection',
      nodeId,
      selectionType,
      timestamp: new Date().toISOString()
    };

    wsRef.current.send(JSON.stringify(message));
  }, []);

  // 변경사항 브로드캐스트
  const broadcastChange = useCallback((change: Omit<CollaborationChange, 'id' | 'userId' | 'timestamp' | 'applied'>) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const changeId = `${user?.id}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const message = {
      type: 'workflow_change',
      changeId,
      changeType: change.type,
      nodeId: change.nodeId,
      edgeId: change.edgeId,
      changes: change.changes,
      timestamp: new Date().toISOString()
    };

    wsRef.current.send(JSON.stringify(message));

    // 로컬 변경사항 큐에 추가
    const localChange: CollaborationChange = {
      ...change,
      id: changeId,
      userId: user?.id || '',
      timestamp: new Date(),
      applied: true
    };

    changeQueueRef.current.push(localChange);
  }, [user?.id]);

  // 변경사항 적용
  const applyChange = useCallback((changeId: string) => {
    setCollaborativeState(prev => ({
      ...prev,
      changes: prev.changes.map(change => 
        change.id === changeId ? { ...change, applied: true } : change
      )
    }));
  }, []);

  // 변경사항 거부
  const rejectChange = useCallback((changeId: string) => {
    setCollaborativeState(prev => ({
      ...prev,
      changes: prev.changes.filter(change => change.id !== changeId)
    }));
  }, []);

  // 연결 해제
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    stopHeartbeat();
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setCollaborativeState(prev => ({
      ...prev,
      isConnected: false,
      users: new Map(),
      cursors: new Map(),
      selections: new Map()
    }));
  }, [stopHeartbeat]);

  // 효과
  useEffect(() => {
    if (options.enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [options.enabled, connect, disconnect]);

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    collaborativeState,
    updateCursor,
    broadcastSelection,
    broadcastChange,
    applyChange,
    rejectChange,
    connect,
    disconnect,
    isConnected: collaborativeState.isConnected
  };
};