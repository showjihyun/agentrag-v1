'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  X, 
  ChevronLeft, 
  ChevronRight, 
  Bot,
  Send,
  Trash2,
  Maximize2,
  Minimize2
} from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
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
}: AIAgentChatPanelProps) => {
  const [chatInput, setChatInput] = useState('');
  const [panelWidth, setPanelWidth] = useState(defaultWidth);
  const [isResizing, setIsResizing] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

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
        bottom: 0,
        left: 0,
        width: isCollapsed ? '48px' : `${panelWidth}%`,
        height: '40vh',
        minWidth: isCollapsed ? '48px' : `${minWidth}%`,
        maxWidth: `${maxWidth}%`,
        backgroundColor: '#0a0a0a',
        borderTop: '1px solid #2a2a2a',
        borderRight: '1px solid #2a2a2a',
        boxShadow: '4px -4px 24px rgba(0, 0, 0, 0.5)',
        zIndex: 9995,
        display: 'flex',
        flexDirection: 'column',
        transition: isResizing ? 'none' : 'width 0.3s ease-in-out',
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

      {/* Header */}
      <div
        style={{
          padding: '10px 16px',
          borderBottom: '1px solid #2a2a2a',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#0f0f0f',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Bot className="h-4 w-4" style={{ color: '#3b82f6' }} />
          {!isCollapsed && (
            <>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#e0e0e0' }}>
                  AI Agent Chat
                </div>
                <div style={{ fontSize: '10px', color: '#707070' }}>
                  {llmProvider} • {llmModel}
                </div>
              </div>
              {chatMessages.length > 0 && (
                <Badge
                  variant="secondary"
                  style={{
                    fontSize: '10px',
                    padding: '0 6px',
                    height: '18px',
                  }}
                >
                  {chatMessages.length}
                </Badge>
              )}
            </>
          )}
        </div>

        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          {!isCollapsed && chatMessages.length > 0 && (
            <Button
              onClick={() => {
                // Clear messages - implement in parent
              }}
              variant="ghost"
              size="sm"
              style={{
                color: '#808080',
                fontSize: '11px',
                height: '26px',
                padding: '0 8px',
                gap: '4px',
              }}
            >
              <Trash2 className="h-3 w-3" />
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
              height: '26px',
              width: '26px',
            }}
          >
            {isCollapsed ? <Maximize2 className="h-3.5 w-3.5" /> : <Minimize2 className="h-3.5 w-3.5" />}
          </Button>
          <Button
            onClick={onToggle}
            variant="ghost"
            size="sm"
            style={{
              color: '#808080',
              padding: '4px',
              height: '26px',
              width: '26px',
            }}
          >
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <>
          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflow: 'auto',
              padding: '16px',
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
              padding: '12px 16px',
              borderTop: '1px solid #2a2a2a',
              backgroundColor: '#0f0f0f',
            }}
          >
            <div style={{ display: 'flex', gap: '8px' }}>
              <Input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                disabled={isSending}
                style={{
                  ...darkStyles.input,
                  height: '38px',
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
                  height: '38px',
                  width: '38px',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '6px',
                  flexShrink: 0,
                }}
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            <div style={{ fontSize: '10px', color: '#606060', marginTop: '6px', textAlign: 'center' }}>
              Press Enter to send • Shift+Enter for new line
            </div>
          </div>
        </>
      )}
    </div>
  );
};
