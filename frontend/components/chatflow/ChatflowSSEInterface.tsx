'use client';

/**
 * Chatflow SSE Interface Component
 * 
 * Real-time chat interface using Server-Sent Events (SSE) for streaming responses.
 * Provides better reliability and simpler implementation than WebSocket.
 * 
 * Enhanced with collapsible Thinking/Reasoning display.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Trash2, RefreshCw, Zap, Wrench, Brain, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';
import { useChatflowSSE, ChatMessage } from '@/hooks/useChatflowSSE';
import { ThinkingBlock, type ThinkingStep } from '@/components/agent-builder/chat/ThinkingBlock';

interface ChatflowSSEInterfaceProps {
  chatflowId: string;
  sessionId?: string;
  className?: string;
  placeholder?: string;
  showToolCalls?: boolean;
  showThinking?: boolean;
}

export function ChatflowSSEInterface({
  chatflowId,
  sessionId,
  className,
  placeholder = "Type your message...",
  showToolCalls = true,
  showThinking = true,
}: ChatflowSSEInterfaceProps) {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  
  const {
    state,
    sendMessage,
    clearHistory,
    reconnect,
    isReady,
  } = useChatflowSSE({
    chatflowId,
    ...(sessionId && { sessionId }),
  });
  
  // Track thinking steps
  useEffect(() => {
    if (state.thinkingStep && state.isProcessing) {
      const newStep: ThinkingStep = {
        id: `step_${Date.now()}`,
        type: 'reasoning',
        content: state.thinkingStep,
        timestamp: new Date(),
        status: 'in_progress',
      };
      
      setThinkingSteps(prev => {
        // Update last step to completed if exists
        const updated = prev.map((s, i) => 
          i === prev.length - 1 ? { ...s, status: 'completed' as const } : s
        );
        return [...updated, newStep];
      });
    }
  }, [state.thinkingStep, state.isProcessing]);
  
  // Clear thinking steps when processing completes
  useEffect(() => {
    if (!state.isProcessing && thinkingSteps.length > 0) {
      // Mark all as completed
      setThinkingSteps(prev => prev.map(s => ({ ...s, status: 'completed' as const })));
    }
  }, [state.isProcessing]);
  
  // Clear thinking steps when new message is sent
  const handleClearThinkingSteps = () => {
    setThinkingSteps([]);
  };
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages, state.currentResponse]);
  
  // Handle send message
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !isReady || state.isProcessing) {
      return;
    }
    
    const message = inputMessage.trim();
    setInputMessage('');
    handleClearThinkingSteps(); // Clear previous thinking steps
    
    await sendMessage(message);
    
    // Focus back to input
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  };
  
  // Handle key down instead of deprecated onKeyPress
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Render message
  const renderMessage = (message: ChatMessage) => {
    const isUser = message.type === 'user';
    const isSystem = message.type === 'system';
    
    return (
      <div
        key={message.id}
        className={cn(
          "flex gap-3 p-4",
          isUser ? "justify-end" : "justify-start"
        )}
      >
        {!isUser && (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
            AI
          </div>
        )}
        
        <div
          className={cn(
            "max-w-[80%] rounded-lg px-4 py-2",
            isUser
              ? "bg-primary text-primary-foreground"
              : isSystem
              ? "bg-muted text-muted-foreground border"
              : "bg-muted text-foreground border"
          )}
        >
          <div className="whitespace-pre-wrap break-words">
            {message.content}
          </div>
          
          {/* Tool calls */}
          {!isUser && message.metadata?.toolCalls && showToolCalls && (
            <div className="mt-2 space-y-1">
              {message.metadata.toolCalls.map((tool: any, index: number) => (
                <div key={index} className="text-xs">
                  <Badge variant="outline" className="mr-1">
                    <Wrench className="h-3 w-3 mr-1" />
                    {tool.name}
                  </Badge>
                  {tool.result && (
                    <span className="text-muted-foreground ml-1">
                      ✓ Done
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
          
          <div className="text-xs text-muted-foreground mt-1 opacity-70">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
        
        {isUser && (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-muted-foreground text-sm font-medium">
            You
          </div>
        )}
      </div>
    );
  };
  
  // Render current response (streaming)
  const renderCurrentResponse = () => {
    if (!state.currentResponse && !state.thinkingStep && state.toolCalls.length === 0) {
      return null;
    }
    
    return (
      <div className="flex gap-3 p-4 justify-start">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
          AI
        </div>
        
        <div className="max-w-[80%] space-y-2">
          {/* Thinking Block - Collapsible */}
          {showThinking && (state.thinkingStep || thinkingSteps.length > 0) && (
            <ThinkingBlock
              isThinking={state.isProcessing && !!state.thinkingStep}
              currentStep={state.thinkingStep}
              steps={thinkingSteps}
              defaultExpanded={false}
            />
          )}
          
          {/* Main Response */}
          <div className="rounded-lg px-4 py-2 bg-muted text-foreground border">
            {/* Tool calls */}
            {state.toolCalls.length > 0 && showToolCalls && (
              <div className="mb-2 space-y-1">
                {state.toolCalls.map((tool, index) => (
                  <div key={index} className="text-xs flex items-center gap-1">
                    <Badge variant="outline">
                      <Wrench className="h-3 w-3 mr-1" />
                      {tool.name}
                    </Badge>
                    {tool.result ? (
                      <span className="text-green-600">✓ Done</span>
                    ) : (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    )}
                  </div>
                ))}
              </div>
            )}
            
            {/* Current response */}
            <div className="whitespace-pre-wrap break-words">
              {state.currentResponse}
              {state.isProcessing && (
                <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1" />
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <Card className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Chat</CardTitle>
          <div className="flex items-center gap-2">
            {/* Connection status */}
            <Badge 
              variant={isReady ? "default" : state.error ? "destructive" : "secondary"}
              className="text-xs"
            >
              {state.isConnecting ? (
                <>
                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                  Connecting
                </>
              ) : isReady ? (
                <>
                  <Zap className="h-3 w-3 mr-1" />
                  SSE Connected
                </>
              ) : state.error ? (
                "Connection Error"
              ) : (
                "Not Connected"
              )}
            </Badge>
            
            {/* Actions */}
            <Button
              variant="ghost"
              size="sm"
              onClick={reconnect}
              disabled={state.isConnecting}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={clearHistory}
              disabled={state.messages.length === 0}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        {state.sessionId && (
          <div className="text-xs text-muted-foreground">
            Session: {state.sessionId.slice(0, 8)}...
          </div>
        )}
      </CardHeader>
      
      <Separator />
      
      {/* Messages */}
      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-full">
          <div className="min-h-full">
            {state.messages.length === 0 && !state.currentResponse ? (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <div className="text-center">
                  <div className="text-lg mb-2">💬</div>
                  <div>Start a conversation</div>
                </div>
              </div>
            ) : (
              <>
                {state.messages.map(renderMessage)}
                {renderCurrentResponse()}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </CardContent>
      
      <Separator />
      
      {/* Input */}
      <CardContent className="p-4">
        {state.error && (
          <div className="mb-3 p-2 bg-destructive/10 border border-destructive/20 rounded text-sm text-destructive">
            {state.error}
          </div>
        )}
        
        <div className="flex gap-2">
          <Input
            ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={!isReady || state.isProcessing}
            className="flex-1"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || !isReady || state.isProcessing}
            size="icon"
          >
            {state.isProcessing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        
        <div className="text-xs text-muted-foreground mt-2">
          {state.isProcessing ? (
            "AI is generating a response..."
          ) : (
            "Press Enter to send, Shift+Enter for new line"
          )}
        </div>
      </CardContent>
    </Card>
  );
}