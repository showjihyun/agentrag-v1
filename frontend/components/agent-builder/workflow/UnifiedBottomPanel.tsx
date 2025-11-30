'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
  Bot, 
  Send, 
  X, 
  ChevronUp, 
  ChevronDown, 
  Terminal, 
  MessageSquare,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Trash2,
  Sparkles,
  Copy,
  RotateCcw
} from 'lucide-react';

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

interface UnifiedBottomPanelProps {
  isOpen: boolean;
  onToggle: () => void;
  rightPanelWidth?: number;
  
  // Chat props
  chatMessages: ChatMessage[];
  onSendMessage: (message: string) => Promise<void>;
  isSending: boolean;
  llmProvider?: string;
  llmModel?: string;
  
  // Execution logs props
  executionLogs: ExecutionLog[];
  onClearLogs?: () => void;
}

const darkStyles = {
  input: {
    backgroundColor: '#1a1a1a',
    borderColor: '#3a3a3a',
    color: '#e0e0e0',
  },
};

export const UnifiedBottomPanel = ({
  isOpen,
  onToggle,
  rightPanelWidth = 0,
  chatMessages,
  onSendMessage,
  isSending,
  llmProvider = 'ollama',
  llmModel = 'llama3.3:70b',
  executionLogs,
  onClearLogs,
}: UnifiedBottomPanelProps) => {
  const [activeTab, setActiveTab] = useState<'chat' | 'logs'>('chat');
  const [chatInput, setChatInput] = useState('');
  const [panelHeight, setPanelHeight] = useState(350);
  const [isResizing, setIsResizing] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    if (activeTab === 'chat') {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    } else {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, executionLogs, activeTab]);

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

  const getStatusIcon = (status: ExecutionLog['status']) => {
    switch (status) {
      case 'running':
        return <Clock className="h-3.5 w-3.5 animate-spin" style={{ color: '#3b82f6' }} />;
      case 'success':
        return <CheckCircle2 className="h-3.5 w-3.5" style={{ color: '#10b981' }} />;
      case 'error':
        return <XCircle className="h-3.5 w-3.5" style={{ color: '#ef4444' }} />;
      case 'warning':
        return <AlertCircle className="h-3.5 w-3.5" style={{ color: '#f59e0b' }} />;
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

  if (!isOpen) {
    return (
      <div
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: rightPanelWidth > 0 ? `${rightPanelWidth}px` : 0,
          height: '40px',
          backgroundColor: '#0f0f0f',
          borderTop: '1px solid #2a2a2a',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          zIndex: 9996,
          transition: 'right 0.3s ease-in-out',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Badge variant="outline" style={{ fontSize: '11px', padding: '2px 8px' }}>
            {chatMessages.length} messages
          </Badge>
          <Badge variant="outline" style={{ fontSize: '11px', padding: '2px 8px' }}>
            {executionLogs.length} logs
          </Badge>
        </div>
        <Button
          onClick={onToggle}
          variant="ghost"
          size="sm"
          style={{
            color: '#808080',
            fontSize: '11px',
            height: '28px',
            padding: '0 10px',
            gap: '6px'
          }}
        >
          <ChevronUp className="h-3.5 w-3.5" />
          Show Panel
        </Button>
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: rightPanelWidth > 0 ? `${rightPanelWidth}px` : 0,
        height: isCollapsed ? '48px' : `${panelHeight}px`,
        minHeight: isCollapsed ? '48px' : '200px',
        maxHeight: '80vh',
        backgroundColor: '#0a0a0a',
        borderTop: '1px solid #2a2a2a',
        boxShadow: '0 -4px 24px rgba(0, 0, 0, 0.5)',
        zIndex: 9996,
        display: 'flex',
        flexDirection: 'column',
        transition: isResizing ? 'none' : 'right 0.3s ease-in-out, height 0.3s ease-in-out',
      }}
    >
      {/* Resize Handle */}
      {!isCollapsed && (
        <div
          onMouseDown={(e) => {
            setIsResizing(true);
            const startY = e.clientY;
            const startHeight = panelHeight;

            const handleMouseMove = (e: MouseEvent) => {
              const deltaY = startY - e.clientY;
              const newHeight = Math.min(Math.max(startHeight + deltaY, 200), window.innerHeight * 0.8);
              setPanelHeight(newHeight);
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
            height: '6px',
            cursor: 'ns-resize',
            backgroundColor: 'transparent',
            borderTop: '2px solid transparent',
            transition: 'border-color 0.2s',
            position: 'relative',
            zIndex: 10,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderTopColor = '#3b82f6';
          }}
          onMouseLeave={(e) => {
            if (!isResizing) {
              e.currentTarget.style.borderTopColor = 'transparent';
            }
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '40px',
              height: '4px',
              backgroundColor: '#3a3a3a',
              borderRadius: '2px',
            }}
          />
        </div>
      )}

      {/* Header - Redesigned */}
      <div
        style={{
          padding: '14px 24px',
          borderBottom: isCollapsed ? 'none' : '1px solid rgba(59, 130, 246, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'linear-gradient(to bottom, #0f0f0f, #0a0a0a)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
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
                  fontSize: '14px',
                  fontWeight: 600,
                  padding: '8px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  borderRadius: '8px',
                  transition: 'all 0.2s ease',
                  border: activeTab === 'chat' ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid transparent',
                }}
              >
                <Sparkles className="h-4 w-4" style={{ color: activeTab === 'chat' ? '#3b82f6' : '#808080' }} />
                AI Chat
                {chatMessages.length > 0 && (
                  <Badge
                    style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      height: '20px',
                      marginLeft: '4px',
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
                  fontSize: '14px',
                  fontWeight: 600,
                  padding: '8px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  borderRadius: '8px',
                  transition: 'all 0.2s ease',
                  border: activeTab === 'logs' ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid transparent',
                }}
              >
                <Terminal className="h-4 w-4" style={{ color: activeTab === 'logs' ? '#3b82f6' : '#808080' }} />
                Execution History
                {executionLogs.length > 0 && (
                  <Badge
                    style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      height: '20px',
                      marginLeft: '4px',
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

          {activeTab === 'chat' && !isCollapsed && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              padding: '6px 12px',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderRadius: '8px',
              border: '1px solid rgba(59, 130, 246, 0.2)',
            }}>
              <Bot className="h-4 w-4" style={{ color: '#3b82f6' }} />
              <span style={{ fontSize: '13px', color: '#a0a0a0', fontWeight: 500 }}>
                {llmProvider} • {llmModel}
              </span>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {activeTab === 'logs' && executionLogs.length > 0 && onClearLogs && (
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
            {isCollapsed ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
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
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              {/* Messages - Redesigned */}
              <div
                className="custom-scrollbar"
                style={{
                  flex: 1,
                  overflowY: 'auto',
                  overflowX: 'hidden',
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                  background: 'radial-gradient(ellipse at top, rgba(59, 130, 246, 0.03), transparent 50%)',
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
                      width: '80px',
                      height: '80px',
                      margin: '0 auto 20px',
                      background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(147, 51, 234, 0.2))',
                      borderRadius: '20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}>
                      <Sparkles className="h-10 w-10" style={{ color: '#3b82f6' }} />
                    </div>
                    <p style={{ fontWeight: 600, marginBottom: '10px', fontSize: '17px', color: '#e0e0e0' }}>
                      AI Agent Ready
                    </p>
                    <p style={{ fontSize: '14px', color: '#808080', maxWidth: '400px', margin: '0 auto' }}>
                      Start chatting with your AI agent powered by {llmProvider} • {llmModel}
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
                      animation: 'fadeIn 0.3s ease-in-out',
                      gap: '8px',
                    }}
                  >
                    {msg.role === 'assistant' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '4px' }}>
                        <div style={{
                          width: '24px',
                          height: '24px',
                          borderRadius: '6px',
                          background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}>
                          <Bot className="h-3.5 w-3.5" style={{ color: '#ffffff' }} />
                        </div>
                        <span style={{ fontSize: '12px', color: '#808080', fontWeight: 500 }}>AI Assistant</span>
                      </div>
                    )}
                    <div
                      style={{
                        maxWidth: '80%',
                        padding: '14px 18px',
                        borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                        background: msg.role === 'user' 
                          ? 'linear-gradient(135deg, #3b82f6, #2563eb)' 
                          : 'rgba(26, 26, 26, 0.8)',
                        color: '#ffffff',
                        fontSize: '15px',
                        lineHeight: '1.7',
                        wordBreak: 'break-word',
                        boxShadow: msg.role === 'user' 
                          ? '0 4px 12px rgba(59, 130, 246, 0.3)' 
                          : '0 4px 12px rgba(0, 0, 0, 0.3)',
                        border: msg.role === 'assistant' ? '1px solid rgba(59, 130, 246, 0.2)' : 'none',
                        backdropFilter: msg.role === 'assistant' ? 'blur(10px)' : 'none',
                        position: 'relative',
                      }}
                    >
                      {msg.content}
                      {msg.role === 'assistant' && (
                        <div style={{
                          marginTop: '12px',
                          paddingTop: '12px',
                          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                          display: 'flex',
                          gap: '8px',
                        }}>
                          <button
                            style={{
                              padding: '4px 10px',
                              fontSize: '11px',
                              color: '#a0a0a0',
                              backgroundColor: 'rgba(255, 255, 255, 0.05)',
                              border: '1px solid rgba(255, 255, 255, 0.1)',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                              transition: 'all 0.2s ease',
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                              e.currentTarget.style.color = '#ffffff';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                              e.currentTarget.style.color = '#a0a0a0';
                            }}
                            onClick={() => navigator.clipboard.writeText(msg.content)}
                          >
                            <Copy className="h-3 w-3" />
                            Copy
                          </button>
                          <button
                            style={{
                              padding: '4px 10px',
                              fontSize: '11px',
                              color: '#a0a0a0',
                              backgroundColor: 'rgba(255, 255, 255, 0.05)',
                              border: '1px solid rgba(255, 255, 255, 0.1)',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '4px',
                              transition: 'all 0.2s ease',
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                              e.currentTarget.style.color = '#ffffff';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                              e.currentTarget.style.color = '#a0a0a0';
                            }}
                          >
                            <RotateCcw className="h-3 w-3" />
                            Regenerate
                          </button>
                        </div>
                      )}
                    </div>
                    {msg.role === 'user' && (
                      <span style={{ fontSize: '11px', color: '#606060', marginRight: '4px' }}>
                        {msg.timestamp.toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                ))}

                {isSending && (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: '4px' }}>
                      <div style={{
                        width: '24px',
                        height: '24px',
                        borderRadius: '6px',
                        background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}>
                        <Bot className="h-3.5 w-3.5" style={{ color: '#ffffff' }} />
                      </div>
                      <span style={{ fontSize: '12px', color: '#808080', fontWeight: 500 }}>AI Assistant</span>
                    </div>
                    <div
                      style={{
                        padding: '14px 18px',
                        borderRadius: '16px 16px 16px 4px',
                        background: 'rgba(26, 26, 26, 0.8)',
                        border: '1px solid rgba(59, 130, 246, 0.2)',
                        backdropFilter: 'blur(10px)',
                        display: 'flex',
                        gap: '6px',
                        alignItems: 'center',
                      }}
                    >
                      <div
                        style={{
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          backgroundColor: '#3b82f6',
                          animation: 'bounce 1s infinite',
                        }}
                      />
                      <div
                        style={{
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          backgroundColor: '#3b82f6',
                          animation: 'bounce 1s infinite 0.15s',
                        }}
                      />
                      <div
                        style={{
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          backgroundColor: '#3b82f6',
                          animation: 'bounce 1s infinite 0.3s',
                        }}
                      />
                    </div>
                  </div>
                )}

                <div ref={chatEndRef} />
              </div>

              {/* Input - Redesigned */}
              <div
                style={{
                  padding: '20px 24px',
                  borderTop: '1px solid rgba(59, 130, 246, 0.1)',
                  background: 'linear-gradient(to top, #0f0f0f, #0a0a0a)',
                }}
              >
                <div style={{ 
                  display: 'flex', 
                  gap: '12px', 
                  maxWidth: '100%', 
                  margin: '0 auto',
                  padding: '12px',
                  backgroundColor: 'rgba(26, 26, 26, 0.6)',
                  borderRadius: '16px',
                  border: '1px solid rgba(59, 130, 246, 0.2)',
                  backdropFilter: 'blur(10px)',
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
                      color: '#e0e0e0',
                      height: '48px',
                      fontSize: '15px',
                      flex: 1,
                      outline: 'none',
                      boxShadow: 'none',
                    }}
                  />
                  <Button
                    onClick={handleSend}
                    disabled={!chatInput.trim() || isSending}
                    style={{
                      background: chatInput.trim() && !isSending 
                        ? 'linear-gradient(135deg, #3b82f6, #2563eb)' 
                        : 'rgba(42, 42, 42, 0.5)',
                      color: 'white',
                      border: 'none',
                      height: '48px',
                      width: '48px',
                      padding: 0,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: '12px',
                      flexShrink: 0,
                      cursor: chatInput.trim() && !isSending ? 'pointer' : 'not-allowed',
                      transition: 'all 0.2s ease',
                      boxShadow: chatInput.trim() && !isSending 
                        ? '0 4px 12px rgba(59, 130, 246, 0.4)' 
                        : 'none',
                    }}
                    onMouseEnter={(e) => {
                      if (chatInput.trim() && !isSending) {
                        e.currentTarget.style.transform = 'scale(1.05)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'scale(1)';
                    }}
                  >
                    <Send className="h-5 w-5" />
                  </Button>
                </div>
                <div style={{ 
                  fontSize: '13px', 
                  color: '#707070', 
                  marginTop: '12px', 
                  textAlign: 'center',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '16px',
                }}>
                  <span>⏎ Send</span>
                  <span>•</span>
                  <span>⇧ + ⏎ New line</span>
                </div>
              </div>
            </div>
          )}

          {/* Logs Tab - Redesigned */}
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
                    width: '80px',
                    height: '80px',
                    margin: '0 auto 20px',
                    background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.2))',
                    borderRadius: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <Terminal className="h-10 w-10" style={{ color: '#10b981' }} />
                  </div>
                  <p style={{ fontWeight: 600, marginBottom: '10px', fontSize: '17px', color: '#e0e0e0' }}>
                    No Execution History
                  </p>
                  <p style={{ fontSize: '14px', color: '#808080', maxWidth: '400px', margin: '0 auto' }}>
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
        </>
      )}
    </div>
  );
};
