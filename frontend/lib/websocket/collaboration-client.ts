'use client';

import { EventEmitter } from 'events';

export interface CollaborationUser {
  id: string;
  name: string;
  email: string;
  color: string;
  cursor?: { x: number; y: number };
  selection?: { start: number; end: number };
}

export interface CollaborationChange {
  type: 'insert' | 'delete' | 'update' | 'cursor' | 'selection';
  userId: string;
  timestamp: number;
  data: any;
  path?: string;
}

export interface CollaborationState {
  users: CollaborationUser[];
  changes: CollaborationChange[];
  version: number;
}

export class CollaborationClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private resourceId: string;
  private resourceType: 'agent' | 'workflow' | 'block';
  private userId: string;
  private connected = false;

  constructor(
    resourceType: 'agent' | 'workflow' | 'block',
    resourceId: string,
    userId: string
  ) {
    super();
    this.resourceType = resourceType;
    this.resourceId = resourceId;
    this.userId = userId;
  }

  connect() {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    const url = `${wsUrl}/ws/collaboration/${this.resourceType}/${this.resourceId}?user_id=${this.userId}`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.connected = true;
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        this.emit('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.connected = false;
        this.stopHeartbeat();
        this.emit('disconnected');
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.emit('error', error);
    }
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connected = false;
  }

  isConnected(): boolean {
    return this.connected && this.ws?.readyState === WebSocket.OPEN;
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.emit('reconnect-failed');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping' });
      }
    }, 30000); // 30 seconds
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private handleMessage(message: any) {
    switch (message.type) {
      case 'state':
        this.emit('state', message.data as CollaborationState);
        break;
      case 'user-joined':
        this.emit('user-joined', message.data as CollaborationUser);
        break;
      case 'user-left':
        this.emit('user-left', message.data.userId);
        break;
      case 'change':
        this.emit('change', message.data as CollaborationChange);
        break;
      case 'cursor':
        this.emit('cursor', message.data);
        break;
      case 'selection':
        this.emit('selection', message.data);
        break;
      case 'conflict':
        this.emit('conflict', message.data);
        break;
      case 'pong':
        // Heartbeat response
        break;
      default:
        console.warn('Unknown message type:', message.type);
    }
  }

  send(message: any) {
    if (!this.isConnected()) {
      console.warn('WebSocket not connected, message not sent');
      return false;
    }

    try {
      this.ws!.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Failed to send message:', error);
      return false;
    }
  }

  // Public API methods
  sendChange(change: Omit<CollaborationChange, 'userId' | 'timestamp'>) {
    this.send({
      type: 'change',
      data: {
        ...change,
        userId: this.userId,
        timestamp: Date.now(),
      },
    });
  }

  sendCursor(position: { x: number; y: number }) {
    this.send({
      type: 'cursor',
      data: {
        userId: this.userId,
        position,
      },
    });
  }

  sendSelection(selection: { start: number; end: number }) {
    this.send({
      type: 'selection',
      data: {
        userId: this.userId,
        selection,
      },
    });
  }

  requestState() {
    this.send({ type: 'get-state' });
  }
}

// Hook for using collaboration client
export function useCollaboration(
  resourceType: 'agent' | 'workflow' | 'block',
  resourceId: string,
  userId: string
) {
  const [client] = React.useState(
    () => new CollaborationClient(resourceType, resourceId, userId)
  );
  const [users, setUsers] = React.useState<CollaborationUser[]>([]);
  const [connected, setConnected] = React.useState(false);

  React.useEffect(() => {
    client.on('connected', () => setConnected(true));
    client.on('disconnected', () => setConnected(false));
    client.on('state', (state: CollaborationState) => setUsers(state.users));
    client.on('user-joined', (user: CollaborationUser) => {
      setUsers((prev) => [...prev, user]);
    });
    client.on('user-left', (userId: string) => {
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    });

    client.connect();

    return () => {
      client.disconnect();
      client.removeAllListeners();
    };
  }, [client]);

  return { client, users, connected };
}

// React import for hook
import React from 'react';
