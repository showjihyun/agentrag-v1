'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  X, 
  Bot,
  Send,
  Trash2,
  Maximize2,
  Minimize2,
  Sparkles,
  Copy,
  RotateCcw,
  Terminal,
  MessageSquare,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ExecutionLog {
  id: string;
  nodeId: string;
  nodeName: string;
  status: 'running' | 'success' | 'error' | 'warning';
  message: string;
  timestamp: Date;
  duration?: number;
}

interface AIAgentChatPanelProps {
  isOpen: boolean;
  onToggle: () => void;
  chatMessages: ChatMessage[];
  onSendMessage: (message: string) => Promise<void>;
  isSending: boolean;
  llmProvider?: string;
  llmModel?: string;
  defaultWidth?: number; // percentage (0-100)
  minWidth?: number; // percentage
  maxWidth?: number; // percentage
  executionLogs?: ExecutionLog[];
  onClearLogs?: () => void;
}

const darkStyles = {
  input: {
    backgroundColor: '#1a1a1a',
    borderColor: '#3a3a3a',
    color: '#e0e0e0',
  },
};

export const AIAgentChatPanel = ({
  isOpen,
  onToggle,
  chatMessages,
  onSendMessage,
  isSending,
  llmProvider = 'ollama',
  llmModel = 'llama3.3:70b',
  defaultWidth = 30,
  minWidth = 20,
  maxWidth = 50,
  executionLogs = [],
  onClearLogs,
}: AIAgentChatPanelProps) => {
  const [chatInput, setChatInput] = useState('');
  const [panelWidth, setPanelWidth] = useState(defaultWidth);
  const [isResizing, setIsResizing] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: window.innerHeight - (window.innerHeight * 0.5) });
  const [activeTab, setActiveTab] = useState<'chat' | 'logs'>('chat');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const dragStartPos = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (activeTab === 'chat') {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    } else {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, executionLogs, activeTab]);

  const getStatusIcon = (status: ExecutionLog['status']) => {
    switch (status) {
      case 'running':
        return <Clock className="h-4 w-4 animate-spin" style={{ color: '#3b82f6' }} />;
      case 'success':
        return <CheckCircle2 className="h-4 w-4" style={{ color: '#10b981' }} />;
      case 'error':
        return <XCircle className="h-4 w-4" style={{ color: '#ef4444' }} />;
      case 'warning':
        return <AlertCircle className="h-4 w-4" style={{ color: '#f59e0b' }} />;
    }
  };

  const getStatusColor = (status: ExecutionLog['status']) => {
    switch (status) {
      case 'running': return '#3b82f6';
      case 'success': return '#10b981';
      case 'error': return '#ef4444';
      case 'warning': return '#f59e0b';
    }
  };

  const handleSend = async () => {
    if (!chatInput.trim() || isSending) return;
    
    const message = chatInput.trim();
    setChatInput('');
    await onSendMessage(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: isCollapsed ? '60px' : `${panelWidth}%`,
        height: '50vh',
        minWidth: isCollapsed ? '60px' : `${minWidth}%`,
        maxWidth: `${maxWidth}%`,
        background: 'linear-gradient(to top, #0a0a0a, #0f0f0f)',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        borderRadius: '16px',
        boxShadow: isDragging 
          ? '0 20px 60px rgba(59, 130, 246, 0.3), 0 0 100px rgba(0, 0, 0, 0.8)' 
          : '4px 4px 32px rgba(59, 130, 246, 0.15), 0 0 80px rgba(0, 0, 0, 0.5)',
        zIndex: 9995,
        display: 'flex',
        flexDirection: 'column',
        transition: isDragging || isResizing ? 'none' : 'all 0.3s ease-in-out',
        backdropFilter: 'blur(20px)',
        cursor: isDragging ? 'grabbing' : 'default',
        overflow: 'hidden',
      }}
    >
      {/* Resize Handle (Right) */}
      {!isCollapsed && (
        <div
          onMouseDown={(e) => {
            setIsResizing(true);
            const startX = e.clientX;
            const startWidth = panelWidth;

            const handleMouseMove = (e: MouseEvent) => {
              const deltaX = e.clientX - startX;
              const windowWidth = window.innerWidth;
              const deltaPercent = (deltaX / windowWidth) * 100;
              const newWidth = Math.min(Math.max(startWidth + deltaPercent, minWidth), maxWidth);
              setPanelWidth(newWidth);
            };

            const handleMouseUp = () => {
              setIsResizing(false);
              document.removeEventListener('mousemove', handleMouseMove);
              document.removeEventListener('mouseup', handleMouseUp);
            };

            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
          }}
          style={{
            position: 'absolute',
            right: 0,
            top: 0,
            bottom: 0,
            width: '6px',
            cursor: 'ew-resize',
            backgroundColor: 'transparent',
            borderRight: '2px solid transparent',
            transition: 'border-color 0.2s',
            zIndex: 10,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderRightColor = '#3b82f6';
          }}
          onMouseLeave={(e) => {
            if (!isResizing) {
              e.currentTarget.style.borderRightColor = 'transparent';
            }
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: '50%',
              right: '50%',
              transform: 'translate(50%, -50%)',
              width: '4px',
              height: '40px',
              backgroundColor: '#3a3a3a',
              borderRadius: '2px',
            }}
          />
        </div>
      )}

      {/* Header - Modern Design with Drag Handle */}
      <div
        onMouseDown={(e) => {
          // Only start dragging if clicking on the header area (not buttons)
          if ((e.target as HTMLElement).closest('button')) return;
          
          setIsDragging(true);
          dragStartPos.current = {
            x: e.clientX - position.x,
            y: e.clientY - position.y,
          };

          const handleMouseMove = (e: MouseEvent) => {
            const newX = Math.max(0, Math.min(e.clientX - dragStartPos.current.x, window.innerWidth - 400));
            const newY = Math.max(0, Math.min(e.clientY - dragStartPos.current.y, window.innerHeight - 200));
            setPosition({ x: newX, y: newY });
          };

          const handleMouseUp = () => {
            setIsDragging(false);
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
          };

          document.addEventListener('mousemove', handleMouseMove);
          document.addEventListener('mouseup', handleMouseUp);
        }}
        style={{
          padding: '16px 24px',
          borderBottom: '1px solid rgba(59, 130, 246, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'linear-gradient(to bottom, rgba(15, 15, 15, 0.95), rgba(10, 10, 10, 0.95))',
          backdropFilter: 'blur(10px)',
          cursor: isDragging ? 'grabbing' : 'grab',
          userSelect: 'none',
          borderTopLeftRadius: '16px',
          borderTopRightRadius: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {/* Drag Indicator */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '3px',
            padding: '8px 4px',
            cursor: 'grab',
          }}>
            <div style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: '#606060' }} />
            <div style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: '#606060' }} />
            <div style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: '#606060' }} />
          </div>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(59, 130, 246, 0.4)',
          }}>
            <Sparkles className="h-5 w-5" style={{ color: '#ffffff' }} />
          </div>
          {!isCollapsed && (
            <>
              <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'chat' | 'logs')}>
                <TabsList
                  style={{
                    backgroundColor: 'rgba(26, 26, 26, 0.8)',
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    padding: '3px',
                    height: '40px',
                    borderRadius: '10px',
                    backdropFilter: 'blur(10px)',
                  }}
                >
                  <TabsTrigger
                    value="chat"
                    style={{
                      color: activeTab === 'chat' ? '#ffffff' : '#808080',
                      backgroundColor: activeTab === 'chat' ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                      fontSize: '13px',
                      fontWeight: 600,
                      padding: '6px 12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      borderRadius: '8px',
                      transition: 'all 0.2s ease',
                      border: activeTab === 'chat' ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid transparent',
                    }}
                  >
                    <MessageSquare className="h-3.5 w-3.5" style={{ color: activeTab === 'chat' ? '#3b82f6' : '#808080' }} />
                    Chat
                    {chatMessages.length > 0 && (
                      <Badge
                        style={{
                          fontSize: '10px',
                          padding: '2px 6px',
                          height: '18px',
                          marginLeft: '2px',
                          backgroundColor: '#3b82f6',
                          color: '#ffffff',
                          border: 'none',
                        }}
                      >
                        {chatMessages.length}
                      </Badge>
                    )}
                  </TabsTrigger>
                  <TabsTrigger
                    value="logs"
                    style={{
                      color: activeTab === 'logs' ? '#ffffff' : '#808080',
                      backgroundColor: activeTab === 'logs' ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                      fontSize: '13px',
                      fontWeight: 600,
                      padding: '6px 12px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      borderRadius: '8px',
                      transition: 'all 0.2s ease',
                      border: activeTab === 'logs' ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid transparent',
                    }}
                  >
                    <Terminal className="h-3.5 w-3.5" style={{ color: activeTab === 'logs' ? '#3b82f6' : '#808080' }} />
                    Logs
                    {executionLogs.length > 0 && (
                      <Badge
                        style={{
                          fontSize: '10px',
                          padding: '2px 6px',
                          height: '18px',
                          marginLeft: '2px',
                          backgroundColor: '#10b981',
                          color: '#ffffff',
                          border: 'none',
                        }}
                      >
                        {executionLogs.length}
                      </Badge>
                    )}
                  </TabsTrigger>
                </TabsList>
              </Tabs>
              {activeTab === 'chat' && (
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '6px',
                  padding: '4px 10px',
                  backgroundColor: 'rgba(59, 130, 246, 0.1)',
                  borderRadius: '6px',
                  border: '1px solid rgba(59, 130, 246, 0.2)',
                }}>
                  <div style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor: '#10b981',
                    boxShadow: '0 0 8px rgba(16, 185, 129, 0.6)',
                  }} />
                  <span style={{ fontSize: '11px', color: '#a0a0a0', fontWeight: 500 }}>
                    {llmProvider} • {llmModel}
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {!isCollapsed && activeTab === 'logs' && executionLogs.length > 0 && onClearLogs && (
            <Button
              onClick={onClearLogs}
              variant="ghost"
              size="sm"
              style={{
                color: '#ef4444',
                fontSize: '13px',
                height: '36px',
                padding: '0 14px',
                gap: '6px',
                borderRadius: '8px',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                backgroundColor: 'rgba(239, 68, 68, 0.05)',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.05)';
              }}
            >
              <Trash2 className="h-4 w-4" />
              Clear All
            </Button>
          )}
          <Button
            onClick={() => setIsCollapsed(!isCollapsed)}
            variant="ghost"
            size="sm"
            style={{
              color: '#a0a0a0',
              padding: '8px',
              height: '36px',
              width: '36px',
              borderRadius: '8px',
              border: '1px solid rgba(160, 160, 160, 0.2)',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(160, 160, 160, 0.1)';
              e.currentTarget.style.color = '#ffffff';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = '#a0a0a0';
            }}
          >
            {isCollapsed ? <Maximize2 className="h-5 w-5" /> : <Minimize2 className="h-5 w-5" />}
          </Button>
          <Button
            onClick={onToggle}
            variant="ghost"
            size="sm"
            style={{
              color: '#a0a0a0',
              padding: '8px',
              height: '36px',
              width: '36px',
              borderRadius: '8px',
              border: '1px solid rgba(160, 160, 160, 0.2)',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
              e.currentTarget.style.color = '#ef4444';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = '#a0a0a0';
            }}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <>
          {/* Chat Tab */}
          {activeTab === 'chat' && (
            <div
            className="custom-scrollbar"
            style={{
              flex: 1,
              overflowY: 'auto',
              overflowX: 'hidden',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
              background: 'radial-gradient(ellipse at top, rgba(59, 130, 246, 0.04), transparent 60%)',
              scrollBehavior: 'smooth',
            }}
          >
            {chatMessages.length === 0 && (
              <div
                style={{
                  textAlign: 'center',
                  padding: '80px 20px',
                  color: '#707070',
                  fontSize: '15px',
                }}
              >
                <div style={{
                  width: '100px',
                  height: '100px',
                  margin: '0 auto 24px',
                  background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(147, 51, 234, 0.2))',
                  borderRadius: '24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  animation: 'pulse 3s ease-in-out infinite',
                }}>
                  <Sparkles className="h-12 w-12" style={{ color: '#3b82f6' }} />
                </div>
                <p style={{ fontWeight: 700, marginBottom: '12px', fontSize: '20px', color: '#ffffff' }}>
                  AI Agent Ready
                </p>
                <p style={{ fontSize: '15px', color: '#909090', maxWidth: '450px', margin: '0 auto', lineHeight: '1.6' }}>
                  Start chatting with your AI agent powered by<br />
                  <span style={{ color: '#3b82f6', fontWeight: 600 }}>{llmProvider}</span> • <span style={{ color: '#8b5cf6', fontWeight: 600 }}>{llmModel}</span>
                </p>
              </div>
            )}

            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  animation: 'fadeIn 0.4s ease-in-out',
                  gap: '10px',
                }}
              >
                {msg.role === 'assistant' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: '6px' }}>
                    <div style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '8px',
                      background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 2px 8px rgba(59, 130, 246, 0.4)',
                    }}>
                      <Bot className="h-4 w-4" style={{ color: '#ffffff' }} />
                    </div>
                    <span style={{ fontSize: '13px', color: '#909090', fontWeight: 600 }}>AI Assistant</span>
                  </div>
                )}
                <div
                  style={{
                    maxWidth: '85%',
                    padding: '16px 20px',
                    borderRadius: msg.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                    background: msg.role === 'user' 
                      ? 'linear-gradient(135deg, #3b82f6, #2563eb)' 
                      : 'rgba(26, 26, 26, 0.9)',
                    color: '#ffffff',
                    fontSize: '16px',
                    lineHeight: '1.7',
                    wordBreak: 'break-word',
                    boxShadow: msg.role === 'user' 
                      ? '0 6px 16px rgba(59, 130, 246, 0.35)' 
                      : '0 6px 16px rgba(0, 0, 0, 0.4)',
                    border: msg.role === 'assistant' ? '1px solid rgba(59, 130, 246, 0.25)' : 'none',
                    backdropFilter: msg.role === 'assistant' ? 'blur(12px)' : 'none',
                    position: 'relative',
                  }}
                >
                  {msg.content}
                  {msg.role === 'assistant' && (
                    <div style={{
                      marginTop: '14px',
                      paddingTop: '14px',
                      borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                      display: 'flex',
                      gap: '10px',
                    }}>
                      <button
                        style={{
                          padding: '6px 12px',
                          fontSize: '12px',
                          color: '#c0c0c0',
                          backgroundColor: 'rgba(255, 255, 255, 0.06)',
                          border: '1px solid rgba(255, 255, 255, 0.12)',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          transition: 'all 0.2s ease',
                          fontWeight: 500,
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.12)';
                          e.currentTarget.style.color = '#ffffff';
                          e.currentTarget.style.transform = 'translateY(-1px)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.06)';
                          e.currentTarget.style.color = '#c0c0c0';
                          e.currentTarget.style.transform = 'translateY(0)';
                        }}
                        onClick={() => navigator.clipboard.writeText(msg.content)}
                      >
                        <Copy className="h-3.5 w-3.5" />
                        Copy
                      </button>
                      <button
                        style={{
                          padding: '6px 12px',
                          fontSize: '12px',
                          color: '#c0c0c0',
                          backgroundColor: 'rgba(255, 255, 255, 0.06)',
                          border: '1px solid rgba(255, 255, 255, 0.12)',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          transition: 'all 0.2s ease',
                          fontWeight: 500,
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.12)';
                          e.currentTarget.style.color = '#ffffff';
                          e.currentTarget.style.transform = 'translateY(-1px)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.06)';
                          e.currentTarget.style.color = '#c0c0c0';
                          e.currentTarget.style.transform = 'translateY(0)';
                        }}
                      >
                        <RotateCcw className="h-3.5 w-3.5" />
                        Regenerate
                      </button>
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <span style={{ fontSize: '12px', color: '#707070', marginRight: '6px', fontWeight: 500 }}>
                    {msg.timestamp.toLocaleTimeString()}
                  </span>
                )}
              </div>
            ))}

            {isSending && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: '6px' }}>
                  <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 2px 8px rgba(59, 130, 246, 0.4)',
                  }}>
                    <Bot className="h-4 w-4" style={{ color: '#ffffff' }} />
                  </div>
                  <span style={{ fontSize: '13px', color: '#909090', fontWeight: 600 }}>AI Assistant</span>
                </div>
                <div
                  style={{
                    padding: '16px 20px',
                    borderRadius: '18px 18px 18px 4px',
                    background: 'rgba(26, 26, 26, 0.9)',
                    border: '1px solid rgba(59, 130, 246, 0.25)',
                    backdropFilter: 'blur(12px)',
                    display: 'flex',
                    gap: '8px',
                    alignItems: 'center',
                  }}
                >
                  <div
                    style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: '#3b82f6',
                      animation: 'bounce 1s infinite',
                      boxShadow: '0 0 10px rgba(59, 130, 246, 0.6)',
                    }}
                  />
                  <div
                    style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: '#3b82f6',
                      animation: 'bounce 1s infinite 0.15s',
                      boxShadow: '0 0 10px rgba(59, 130, 246, 0.6)',
                    }}
                  />
                  <div
                    style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: '#3b82f6',
                      animation: 'bounce 1s infinite 0.3s',
                      boxShadow: '0 0 10px rgba(59, 130, 246, 0.6)',
                    }}
                  />
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>
          )}

          {/* Logs Tab */}
          {activeTab === 'logs' && (
            <div
              className="custom-scrollbar"
              style={{
                flex: 1,
                overflowY: 'auto',
                overflowX: 'hidden',
                padding: '20px 24px',
                background: 'radial-gradient(ellipse at top, rgba(16, 185, 129, 0.03), transparent 50%)',
                scrollBehavior: 'smooth',
              }}
            >
              {executionLogs.length === 0 && (
                <div
                  style={{
                    textAlign: 'center',
                    padding: '80px 20px',
                    color: '#707070',
                    fontSize: '15px',
                  }}
                >
                  <div style={{
                    width: '100px',
                    height: '100px',
                    margin: '0 auto 24px',
                    background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2))',
                    borderRadius: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <Terminal className="h-12 w-12" style={{ color: '#10b981' }} />
                  </div>
                  <p style={{ fontWeight: 700, marginBottom: '12px', fontSize: '20px', color: '#ffffff' }}>
                    No Execution History
                  </p>
                  <p style={{ fontSize: '15px', color: '#909090', maxWidth: '450px', margin: '0 auto', lineHeight: '1.6' }}>
                    Run your workflow to see execution logs and performance metrics here
                  </p>
                </div>
              )}

              {executionLogs.map((log) => (
                <div
                  key={log.id}
                  style={{
                    padding: '16px 20px',
                    marginBottom: '12px',
                    background: 'rgba(15, 15, 15, 0.8)',
                    border: `1px solid ${getStatusColor(log.status)}30`,
                    borderLeft: `4px solid ${getStatusColor(log.status)}`,
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '14px',
                    animation: 'slideIn 0.2s ease-out',
                    backdropFilter: 'blur(10px)',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(26, 26, 26, 0.9)';
                    e.currentTarget.style.transform = 'translateX(4px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(15, 15, 15, 0.8)';
                    e.currentTarget.style.transform = 'translateX(0)';
                  }}
                >
                  <div style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '10px',
                    backgroundColor: `${getStatusColor(log.status)}20`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    {getStatusIcon(log.status)}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '15px', fontWeight: 600, color: '#ffffff' }}>
                        {log.nodeName}
                      </span>
                      <Badge
                        style={{
                          fontSize: '11px',
                          padding: '4px 10px',
                          height: '22px',
                          backgroundColor: `${getStatusColor(log.status)}20`,
                          color: getStatusColor(log.status),
                          border: `1px solid ${getStatusColor(log.status)}40`,
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: '0.5px',
                        }}
                      >
                        {log.status}
                      </Badge>
                      {log.duration && (
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '4px 10px',
                          backgroundColor: 'rgba(59, 130, 246, 0.1)',
                          borderRadius: '6px',
                          border: '1px solid rgba(59, 130, 246, 0.2)',
                        }}>
                          <Clock className="h-3 w-3" style={{ color: '#3b82f6' }} />
                          <span style={{ fontSize: '12px', color: '#3b82f6', fontWeight: 500 }}>
                            {log.duration}ms
                          </span>
                        </div>
                      )}
                    </div>
                    <div style={{ 
                      fontSize: '14px', 
                      color: '#c0c0c0', 
                      lineHeight: '1.6',
                      marginBottom: '8px',
                      fontFamily: 'monospace',
                      backgroundColor: 'rgba(0, 0, 0, 0.3)',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                    }}>
                      {log.message}
                    </div>
                    <div style={{ 
                      fontSize: '12px', 
                      color: '#707070',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}>
                      <Clock className="h-3 w-3" />
                      {log.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}

              <div ref={logsEndRef} />
            </div>
          )}

          {/* Input - Modern Design (Only for Chat Tab) */}
          {activeTab === 'chat' && (
          <div
            style={{
              padding: '20px 24px 24px',
              borderTop: '1px solid rgba(59, 130, 246, 0.15)',
              background: 'linear-gradient(to top, rgba(15, 15, 15, 0.95), rgba(10, 10, 10, 0.95))',
              backdropFilter: 'blur(10px)',
            }}
          >
            <div style={{ 
              display: 'flex', 
              gap: '12px',
              padding: '14px',
              backgroundColor: 'rgba(26, 26, 26, 0.7)',
              borderRadius: '18px',
              border: '1px solid rgba(59, 130, 246, 0.25)',
              backdropFilter: 'blur(12px)',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)',
            }}>
              <Input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask your AI agent anything..."
                disabled={isSending}
                style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: '#ffffff',
                  height: '52px',
                  fontSize: '16px',
                  flex: 1,
                  outline: 'none',
                  boxShadow: 'none',
                  fontWeight: 400,
                }}
              />
              <Button
                onClick={handleSend}
                disabled={!chatInput.trim() || isSending}
                style={{
                  background: chatInput.trim() && !isSending 
                    ? 'linear-gradient(135deg, #3b82f6, #2563eb)' 
                    : 'rgba(42, 42, 42, 0.6)',
                  color: 'white',
                  border: 'none',
                  height: '52px',
                  width: '52px',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '14px',
                  flexShrink: 0,
                  cursor: chatInput.trim() && !isSending ? 'pointer' : 'not-allowed',
                  transition: 'all 0.2s ease',
                  boxShadow: chatInput.trim() && !isSending 
                    ? '0 6px 16px rgba(59, 130, 246, 0.5)' 
                    : 'none',
                }}
                onMouseEnter={(e) => {
                  if (chatInput.trim() && !isSending) {
                    e.currentTarget.style.transform = 'scale(1.05)';
                    e.currentTarget.style.boxShadow = '0 8px 20px rgba(59, 130, 246, 0.6)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                  if (chatInput.trim() && !isSending) {
                    e.currentTarget.style.boxShadow = '0 6px 16px rgba(59, 130, 246, 0.5)';
                  }
                }}
              >
                <Send className="h-5 w-5" />
              </Button>
            </div>
            <div style={{ 
              fontSize: '13px', 
              color: '#808080', 
              marginTop: '14px', 
              textAlign: 'center',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '20px',
              fontWeight: 500,
            }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <kbd style={{
                  padding: '2px 6px',
                  backgroundColor: 'rgba(255, 255, 255, 0.08)',
                  borderRadius: '4px',
                  fontSize: '11px',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                }}>⏎</kbd>
                Send
              </span>
              <span style={{ color: '#505050' }}>•</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <kbd style={{
                  padding: '2px 6px',
                  backgroundColor: 'rgba(255, 255, 255, 0.08)',
                  borderRadius: '4px',
                  fontSize: '11px',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                }}>⇧ ⏎</kbd>
                New line
              </span>
            </div>
          </div>
          )}
        </>
      )}
    </div>
  );
};
