'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
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
  Trash2
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

      {/* Header */}
      <div
        style={{
          padding: '10px 20px',
          borderBottom: isCollapsed ? 'none' : '1px solid #2a2a2a',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#0f0f0f',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'chat' | 'logs')}>
            <TabsList
              style={{
                backgroundColor: '#000000',
                border: '1px solid #2a2a2a',
                padding: '2px',
                height: '32px',
              }}
            >
              <TabsTrigger
                value="chat"
                style={{
                  color: activeTab === 'chat' ? '#ffffff' : '#606060',
                  backgroundColor: activeTab === 'chat' ? '#1a1a1a' : 'transparent',
                  fontSize: '12px',
                  fontWeight: 500,
                  padding: '4px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <MessageSquare className="h-3.5 w-3.5" />
                AI Chat
                {chatMessages.length > 0 && (
                  <Badge
                    variant="secondary"
                    style={{
                      fontSize: '10px',
                      padding: '0 4px',
                      height: '16px',
                      marginLeft: '4px',
                    }}
                  >
                    {chatMessages.length}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger
                value="logs"
                style={{
                  color: activeTab === 'logs' ? '#ffffff' : '#606060',
                  backgroundColor: activeTab === 'logs' ? '#1a1a1a' : 'transparent',
                  fontSize: '12px',
                  fontWeight: 500,
                  padding: '4px 12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Terminal className="h-3.5 w-3.5" />
                Execution Logs
                {executionLogs.length > 0 && (
                  <Badge
                    variant="secondary"
                    style={{
                      fontSize: '10px',
                      padding: '0 4px',
                      height: '16px',
                      marginLeft: '4px',
                    }}
                  >
                    {executionLogs.length}
                  </Badge>
                )}
              </TabsTrigger>
            </TabsList>
          </Tabs>

          {activeTab === 'chat' && !isCollapsed && (
            <div style={{ fontSize: '11px', color: '#707070' }}>
              {llmProvider} • {llmModel}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {activeTab === 'logs' && executionLogs.length > 0 && onClearLogs && (
            <Button
              onClick={onClearLogs}
              variant="ghost"
              size="sm"
              style={{
                color: '#808080',
                fontSize: '11px',
                height: '28px',
                padding: '0 10px',
                gap: '4px',
              }}
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear
            </Button>
          )}
          <Button
            onClick={() => setIsCollapsed(!isCollapsed)}
            variant="ghost"
            size="sm"
            style={{
              color: '#808080',
              padding: '4px',
              height: '28px',
              width: '28px',
            }}
          >
            {isCollapsed ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
          <Button
            onClick={onToggle}
            variant="ghost"
            size="sm"
            style={{
              color: '#808080',
              padding: '4px',
              height: '28px',
              width: '28px',
            }}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <>
          {/* Chat Tab */}
          {activeTab === 'chat' && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              {/* Messages */}
              <div
                style={{
                  flex: 1,
                  overflow: 'auto',
                  padding: '16px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  backgroundColor: '#0a0a0a',
                  scrollBehavior: 'smooth',
                }}
              >
                {chatMessages.length === 0 && (
                  <div
                    style={{
                      textAlign: 'center',
                      padding: '60px 20px',
                      color: '#606060',
                      fontSize: '13px',
                    }}
                  >
                    <Bot className="h-12 w-12 mx-auto mb-4" style={{ opacity: 0.3 }} />
                    <p style={{ fontWeight: 500, marginBottom: '8px' }}>
                      Start a conversation with your AI agent
                    </p>
                    <p style={{ fontSize: '12px' }}>Messages are sent using your configured LLM settings</p>
                  </div>
                )}

                {chatMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                      animation: 'fadeIn 0.3s ease-in-out',
                    }}
                  >
                    <div
                      style={{
                        maxWidth: '75%',
                        padding: '10px 14px',
                        borderRadius: '12px',
                        backgroundColor: msg.role === 'user' ? '#3b82f6' : '#1a1a1a',
                        color: msg.role === 'user' ? '#ffffff' : '#e0e0e0',
                        fontSize: '13px',
                        lineHeight: '1.6',
                        wordBreak: 'break-word',
                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
                        border: msg.role === 'assistant' ? '1px solid #2a2a2a' : 'none',
                      }}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}

                {isSending && (
                  <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                    <div
                      style={{
                        padding: '10px 14px',
                        borderRadius: '12px',
                        backgroundColor: '#1a1a1a',
                        display: 'flex',
                        gap: '5px',
                        alignItems: 'center',
                      }}
                    >
                      <div
                        style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: '#606060',
                          animation: 'bounce 1s infinite',
                        }}
                      />
                      <div
                        style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: '#606060',
                          animation: 'bounce 1s infinite 0.1s',
                        }}
                      />
                      <div
                        style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: '#606060',
                          animation: 'bounce 1s infinite 0.2s',
                        }}
                      />
                    </div>
                  </div>
                )}

                <div ref={chatEndRef} />
              </div>

              {/* Input */}
              <div
                style={{
                  padding: '16px 20px',
                  borderTop: '1px solid #2a2a2a',
                  backgroundColor: '#0f0f0f',
                }}
              >
                <div style={{ display: 'flex', gap: '10px', maxWidth: '100%', margin: '0 auto' }}>
                  <Input
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type your message..."
                    disabled={isSending}
                    style={{
                      ...darkStyles.input,
                      height: '42px',
                      fontSize: '13px',
                      flex: 1,
                    }}
                  />
                  <Button
                    onClick={handleSend}
                    disabled={!chatInput.trim() || isSending}
                    style={{
                      backgroundColor: chatInput.trim() && !isSending ? '#3b82f6' : '#2a2a2a',
                      color: 'white',
                      border: 'none',
                      height: '42px',
                      width: '42px',
                      padding: 0,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      borderRadius: '8px',
                      flexShrink: 0,
                    }}
                  >
                    <Send className="h-5 w-5" />
                  </Button>
                </div>
                <div style={{ fontSize: '11px', color: '#606060', marginTop: '8px', textAlign: 'center' }}>
                  Press Enter to send • Shift+Enter for new line
                </div>
              </div>
            </div>
          )}

          {/* Logs Tab */}
          {activeTab === 'logs' && (
            <div
              style={{
                flex: 1,
                overflow: 'auto',
                padding: '12px 20px',
                backgroundColor: '#0a0a0a',
                scrollBehavior: 'smooth',
              }}
            >
              {executionLogs.length === 0 && (
                <div
                  style={{
                    textAlign: 'center',
                    padding: '60px 20px',
                    color: '#606060',
                    fontSize: '13px',
                  }}
                >
                  <Terminal className="h-12 w-12 mx-auto mb-4" style={{ opacity: 0.3 }} />
                  <p style={{ fontWeight: 500, marginBottom: '8px' }}>No execution logs yet</p>
                  <p style={{ fontSize: '12px' }}>Click Execute to run the workflow</p>
                </div>
              )}

              {executionLogs.map((log) => (
                <div
                  key={log.id}
                  style={{
                    padding: '10px 14px',
                    marginBottom: '8px',
                    backgroundColor: '#0f0f0f',
                    border: `1px solid ${getStatusColor(log.status)}20`,
                    borderLeft: `3px solid ${getStatusColor(log.status)}`,
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '10px',
                    animation: 'slideIn 0.2s ease-out',
                  }}
                >
                  {getStatusIcon(log.status)}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#e0e0e0' }}>
                        {log.nodeName}
                      </span>
                      <Badge
                        variant="outline"
                        style={{
                          fontSize: '10px',
                          padding: '0 6px',
                          height: '18px',
                          borderColor: getStatusColor(log.status),
                          color: getStatusColor(log.status),
                        }}
                      >
                        {log.status}
                      </Badge>
                      {log.duration && (
                        <span style={{ fontSize: '10px', color: '#707070' }}>{log.duration}ms</span>
                      )}
                    </div>
                    <div style={{ fontSize: '12px', color: '#b0b0b0', lineHeight: '1.5' }}>
                      {log.message}
                    </div>
                    <div style={{ fontSize: '10px', color: '#606060', marginTop: '4px' }}>
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
