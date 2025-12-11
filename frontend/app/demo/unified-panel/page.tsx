'use client';

import { useState } from 'react';
import { AIAgentChatPanel } from '@/components/agent-builder/workflow/AIAgentChatPanel';
import { SimplifiedPropertiesPanel } from '@/components/agent-builder/workflow/SimplifiedPropertiesPanel';
import { Button } from '@/components/ui/button';
import { Node } from 'reactflow';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function UnifiedPanelDemo() {
  const [chatPanelOpen, setChatPanelOpen] = useState(false);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [hasAIAgentTool, setHasAIAgentTool] = useState(false);

  // Mock AI Agent node
  const mockAIAgentNode: Node = {
    id: 'ai-agent-1',
    type: 'tool',
    position: { x: 0, y: 0 },
    data: {
      type: 'tool_ai_agent',
      tool_id: 'ai_agent',
      tool_name: 'AI Agent',
      label: 'AI Agent Test',
      description: 'Test AI Agent with LLM capabilities',
      parameters: {
        provider: 'ollama',
        model: 'llama3.3:70b',
        system_prompt: 'You are a helpful AI assistant.',
        temperature: 0.7,
        max_tokens: 1000,
        enable_memory: true,
        memory_type: 'long_term',
      },
    },
  };

  const handleSendMessage = async (message: string) => {
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date(),
    };

    setChatMessages((prev) => [...prev, userMessage]);
    setIsSending(true);

    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: `This is a demo response to: "${message}". In production, this would call the actual AI Agent API.`,
        timestamp: new Date(),
      };

      setChatMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to get response'}`,
        timestamp: new Date(),
      };

      setChatMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div style={{ height: '100vh', backgroundColor: '#0a0a0a', color: '#e0e0e0', overflow: 'hidden' }}>
      {/* Header */}
      <div
        style={{
          padding: '16px 24px',
          borderBottom: '1px solid #2a2a2a',
          backgroundColor: '#0f0f0f',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '4px' }}>
            AI Agent Chat Panel Demo
          </h1>
          <p style={{ fontSize: '13px', color: '#707070' }}>
            AI Chat Panel (Left 30%, conditional on AI Agent Tool)
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <Button
            onClick={() => setHasAIAgentTool(!hasAIAgentTool)}
            style={{
              backgroundColor: hasAIAgentTool ? '#10b981' : '#1a1a1a',
              color: hasAIAgentTool ? '#ffffff' : '#a0a0a0',
              border: '1px solid #3a3a3a',
              height: '36px',
              fontSize: '12px',
            }}
          >
            {hasAIAgentTool ? '✓' : '○'} AI Agent Tool
          </Button>
          <Button
            onClick={() => setChatPanelOpen(!chatPanelOpen)}
            style={{
              backgroundColor: chatPanelOpen ? '#3b82f6' : '#1a1a1a',
              color: chatPanelOpen ? '#ffffff' : '#a0a0a0',
              border: '1px solid #3a3a3a',
              height: '36px',
              fontSize: '12px',
            }}
          >
            {chatPanelOpen ? 'Hide' : 'Show'} Chat Panel
          </Button>
          <Button
            onClick={() => setRightPanelOpen(!rightPanelOpen)}
            style={{
              backgroundColor: rightPanelOpen ? '#3b82f6' : '#1a1a1a',
              color: rightPanelOpen ? '#ffffff' : '#a0a0a0',
              border: '1px solid #3a3a3a',
              height: '36px',
              fontSize: '12px',
            }}
          >
            {rightPanelOpen ? 'Hide' : 'Show'} Properties
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div
        style={{
          padding: '24px',
          height: 'calc(100vh - 73px)',
          overflow: 'auto',
        }}
      >
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div
            style={{
              backgroundColor: '#0f0f0f',
              border: '1px solid #2a2a2a',
              borderRadius: '12px',
              padding: '24px',
              marginBottom: '24px',
            }}
          >
            <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>
              Demo Controls
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <p style={{ fontSize: '13px', color: '#b0b0b0', marginBottom: '8px' }}>
                  Panel Configuration:
                </p>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
                  <Button
                    onClick={() => {
                      setHasAIAgentTool(true);
                      setChatPanelOpen(true);
                    }}
                    style={{
                      backgroundColor: '#1a1a1a',
                      border: '1px solid #10b981',
                      color: '#10b981',
                      height: '32px',
                      fontSize: '12px',
                    }}
                  >
                    Enable AI Agent Mode
                  </Button>
                  <Button
                    onClick={() => {
                      setHasAIAgentTool(false);
                      setChatPanelOpen(false);
                    }}
                    style={{
                      backgroundColor: '#1a1a1a',
                      border: '1px solid #3a3a3a',
                      color: '#e0e0e0',
                      height: '32px',
                      fontSize: '12px',
                    }}
                  >
                    Disable AI Agent Mode
                  </Button>
                </div>
              </div>

              <div>
                <p style={{ fontSize: '13px', color: '#b0b0b0', marginBottom: '8px' }}>
                  Test Chat Messages:
                </p>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <Button
                    onClick={() => handleSendMessage('Hello, how are you?')}
                    disabled={isSending}
                    style={{
                      backgroundColor: '#1a1a1a',
                      border: '1px solid #3a3a3a',
                      color: '#e0e0e0',
                      height: '32px',
                      fontSize: '12px',
                    }}
                  >
                    Send Test Message 1
                  </Button>
                  <Button
                    onClick={() => handleSendMessage('What can you help me with?')}
                    disabled={isSending}
                    style={{
                      backgroundColor: '#1a1a1a',
                      border: '1px solid #3a3a3a',
                      color: '#e0e0e0',
                      height: '32px',
                      fontSize: '12px',
                    }}
                  >
                    Send Test Message 2
                  </Button>
                  <Button
                    onClick={() => setChatMessages([])}
                    style={{
                      backgroundColor: '#1a1a1a',
                      border: '1px solid #dc2626',
                      color: '#dc2626',
                      height: '32px',
                      fontSize: '12px',
                    }}
                  >
                    Clear Messages
                  </Button>
                </div>
              </div>
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#0f0f0f',
              border: '1px solid #2a2a2a',
              borderRadius: '12px',
              padding: '24px',
            }}
          >
            <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
              Features
            </h2>
            <ul style={{ fontSize: '13px', color: '#b0b0b0', lineHeight: '1.8', paddingLeft: '20px' }}>
              <li><strong>AI Agent Chat Panel</strong>: Left bottom (30% width, only when AI Agent Tool exists)</li>
              <li>Resizable panel width (drag the right border)</li>
              <li>Collapsible panel (minimize/maximize)</li>
              <li>Independent panel control</li>
              <li>Real-time message updates with smooth animations</li>
              <li>Badge counter showing message count</li>
              <li>Keyboard shortcuts (Enter: send, Shift+Enter: new line)</li>
              <li>Clean, modern dark theme UI</li>
            </ul>
          </div>
        </div>
      </div>

      {/* AI Agent Chat Panel (Left Bottom - only when AI Agent Tool exists) */}
      {hasAIAgentTool && (
        <AIAgentChatPanel
          isOpen={chatPanelOpen}
          onToggle={() => setChatPanelOpen(!chatPanelOpen)}
          chatMessages={chatMessages}
          onSendMessage={handleSendMessage}
          isSending={isSending}
          llmProvider="ollama"
          llmModel="llama3.3:70b"
          defaultWidth={30}
          minWidth={20}
          maxWidth={50}
        />
      )}

      {/* Right Properties Panel */}
      {rightPanelOpen && (
        <SimplifiedPropertiesPanel
          node={selectedNode || mockAIAgentNode}
          isOpen={rightPanelOpen}
          onClose={() => setRightPanelOpen(false)}
          onUpdate={(nodeId, updates) => {
            console.log('Node updated:', nodeId, updates);
          }}
        />
      )}
    </div>
  );
}
