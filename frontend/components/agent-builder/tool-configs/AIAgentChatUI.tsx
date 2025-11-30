"use client";

/**
 * AI Agent Chat UI Component - Professional Edition
 * 
 * Enhanced real-time chat interface with:
 * - Modern gradient design
 * - Smooth animations
 * - Markdown rendering
 * - Code syntax highlighting
 * - Typing indicators
 * - Message reactions
 * - Quick actions
 */

import React, { useState, useRef, useEffect } from "react";
import { 
  Send, X, Minimize2, Maximize2, Trash2, Download, 
  Copy, Check, RotateCcw, Sparkles, Zap, Clock,
  User, Bot, AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useAIAgentStreaming } from "@/hooks/useAIAgentStreaming";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  metadata?: {
    model?: string;
    usage?: any;
    provider?: string;
    temperature?: number;
    max_tokens?: number;
    execution_time_ms?: number;
    memory_type?: string;
    success?: boolean;
    error?: string;
    canRetry?: boolean;
  };
  isStreaming?: boolean;
}

interface AIAgentChatUIProps {
  position?: "right" | "bottom" | "modal" | "inline";
  onClose?: () => void;
  onSendMessage?: (message: string) => Promise<string>;
  sessionId?: string;
  systemPrompt?: string;
  provider?: string;
  model?: string;
  externalMessages?: Message[]; // Allow external messages to be injected
  onMessagesChange?: (messages: Message[]) => void; // Notify parent of message changes
  readOnly?: boolean; // Read-only mode for workflow execution results
}

export function AIAgentChatUI({
  position = "right",
  onClose,
  onSendMessage,
  sessionId,
  systemPrompt,
  provider = "ollama",
  model = "llama3.3:70b",
  externalMessages = [],
  onMessagesChange,
  readOnly = false,
}: AIAgentChatUIProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  
  // Streaming hook
  const { streamMessage, isStreaming } = useAIAgentStreaming();

  // Smooth auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add system prompt as first message if provided
  useEffect(() => {
    if (systemPrompt && messages.length === 0) {
      setMessages([
        {
          id: "system-0",
          role: "system",
          content: systemPrompt,
          timestamp: new Date(),
        },
      ]);
    }
  }, [systemPrompt]);

  // Sync external messages (from workflow execution)
  useEffect(() => {
    if (externalMessages.length > 0) {
      setMessages(prev => {
        // Merge external messages with existing ones, avoiding duplicates
        const existingIds = new Set(prev.map(m => m.id));
        const newMessages = externalMessages.filter(m => !existingIds.has(m.id));
        
        if (newMessages.length > 0) {
          const updated = [...prev, ...newMessages];
          return updated;
        }
        return prev;
      });
    }
  }, [externalMessages]);

  // Notify parent when messages change
  useEffect(() => {
    if (onMessagesChange) {
      onMessagesChange(messages);
    }
  }, [messages, onMessagesChange]);

  const handleSend = async () => {
    if (!input.trim() || isLoading || isStreaming || readOnly) return;
    
    // If no onSendMessage provided, show error
    if (!onSendMessage) {
      toast({
        title: 'Chat Disabled',
        description: 'This chat is read-only. You can only view workflow execution results.',
      });
      return;
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const userInput = input.trim();
    setInput("");
    setIsLoading(true);

    // Add streaming placeholder
    const streamingId = `assistant-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: streamingId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        isStreaming: true,
      },
    ]);

    // Try streaming first
    let accumulatedContent = "";
    
    await streamMessage(
      userInput,
      {
        provider,
        model,
        systemPrompt,
        sessionId,
        temperature: 0.7,
        maxTokens: 1000,
      },
      // onChunk: Update message with each chunk
      (chunk: string) => {
        accumulatedContent += chunk;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === streamingId
              ? { ...msg, content: accumulatedContent }
              : msg
          )
        );
      },
      // onComplete: Mark as complete
      () => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === streamingId
              ? {
                  ...msg,
                  isStreaming: false,
                  metadata: { model, provider },
                }
              : msg
          )
        );
        setIsLoading(false);
        inputRef.current?.focus();
      },
      // onError: Handle error with retry option
      (error: string) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === streamingId
              ? {
                  ...msg,
                  content: '',
                  isStreaming: false,
                  metadata: {
                    ...msg.metadata,
                    error: error,
                    canRetry: true,
                  },
                }
              : msg
          )
        );
        setIsLoading(false);
        inputRef.current?.focus();
        
        // Show error toast
        toast({
          title: 'Message Failed',
          description: error,
        });
      }
    );
  };

  const copyToClipboard = async (text: string, messageId: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(messageId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const regenerateResponse = async (messageIndex: number) => {
    const userMessage = messages[messageIndex - 1];
    if (userMessage?.role === "user") {
      setInput(userMessage.content);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    if (confirm("Clear all messages?")) {
      setMessages(systemPrompt ? [messages[0]] : []);
    }
  };

  const exportChat = () => {
    const chatData = {
      sessionId,
      provider,
      model,
      messages: messages.map((m) => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp.toISOString(),
      })),
    };

    const blob = new Blob([JSON.stringify(chatData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `chat-${sessionId || Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Position-based styling with animations and responsive design
  const getContainerClass = () => {
    const baseAnimation = "transition-all duration-300 ease-in-out";
    const darkMode = "dark:from-zinc-900 dark:to-zinc-950 dark:border-zinc-800";
    
    if (isMinimized) {
      return `fixed bottom-4 right-4 w-72 sm:w-80 h-14 bg-white dark:bg-zinc-900 border dark:border-zinc-800 rounded-lg shadow-lg z-50 ${baseAnimation}`;
    }

    switch (position) {
      case "right":
        // Responsive: full width on mobile, fixed width on desktop
        return `fixed top-0 right-0 w-full sm:w-[380px] md:w-[420px] h-full bg-gradient-to-br from-white to-gray-50 ${darkMode} border-l shadow-2xl z-50 flex flex-col ${baseAnimation}`;
      case "bottom":
        // Responsive height
        return `fixed bottom-0 left-0 right-0 h-[70vh] sm:h-[500px] bg-gradient-to-t from-white to-gray-50 ${darkMode} border-t shadow-2xl z-50 flex flex-col ${baseAnimation}`;
      case "modal":
        // Responsive modal
        return `fixed inset-4 sm:inset-auto sm:left-1/2 sm:top-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2 sm:w-[90vw] sm:max-w-[900px] sm:h-[80vh] sm:max-h-[700px] bg-gradient-to-br from-white to-gray-50 ${darkMode} border rounded-2xl shadow-2xl z-50 flex flex-col ${baseAnimation}`;
      case "inline":
        return `w-full h-[400px] sm:h-[600px] bg-gradient-to-br from-white to-gray-50 ${darkMode} border rounded-xl shadow-lg flex flex-col ${baseAnimation}`;
      default:
        return `w-full h-full bg-white dark:bg-zinc-900 flex flex-col ${baseAnimation}`;
    }
  };

  const getProviderColor = () => {
    switch (provider) {
      case "ollama": return "from-orange-500 to-red-500";
      case "openai": return "from-green-500 to-emerald-500";
      case "claude": return "from-purple-500 to-pink-500";
      case "gemini": return "from-blue-500 to-cyan-500";
      case "grok": return "from-yellow-500 to-orange-500";
      default: return "from-gray-500 to-gray-600";
    }
  };

  if (isMinimized) {
    return (
      <TooltipProvider>
        <div className={getContainerClass()}>
          <div className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 rounded-lg transition-colors">
            <div className="flex items-center gap-2" onClick={() => setIsMinimized(false)}>
              <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${getProviderColor()} flex items-center justify-center text-white shadow-md`}>
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <div className="font-semibold text-sm">AI Agent</div>
                <div className="text-xs text-gray-500">{messages.length} messages</div>
              </div>
            </div>
            <div className="flex gap-1">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setIsMinimized(false)}
                  >
                    <Maximize2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Expand</TooltipContent>
              </Tooltip>
              {onClose && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="ghost" onClick={onClose}>
                      <X className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Close</TooltipContent>
                </Tooltip>
              )}
            </div>
          </div>
        </div>
      </TooltipProvider>
    );
  }

  return (
    <TooltipProvider>
      <div className={getContainerClass()}>
        {/* Enhanced Header with Gradient */}
        <div className={`relative overflow-hidden border-b backdrop-blur-sm`}>
          {/* Animated Background */}
          <div className={`absolute inset-0 bg-gradient-to-r ${getProviderColor()} opacity-10`} />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent to-white/50" />
          
          <div className="relative flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              {/* Provider Avatar */}
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${getProviderColor()} flex items-center justify-center text-white shadow-lg transform hover:scale-105 transition-transform`}>
                <Bot className="h-6 w-6" />
              </div>
              
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-lg">AI Agent Chat</h3>
                  <Badge variant="secondary" className="text-xs">
                    <Sparkles className="h-3 w-3 mr-1" />
                    Live
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <span className="font-medium">{provider}</span>
                  <span>•</span>
                  <span>{model}</span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {messages.filter(m => m.role !== "system").length} msgs
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex gap-1">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button size="sm" variant="ghost" onClick={exportChat}>
                    <Download className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Export Chat</TooltipContent>
              </Tooltip>
              
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button size="sm" variant="ghost" onClick={clearChat}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Clear Chat</TooltipContent>
              </Tooltip>
              
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button size="sm" variant="ghost" onClick={() => setIsMinimized(true)}>
                    <Minimize2 className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Minimize</TooltipContent>
              </Tooltip>
              
              {onClose && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button size="sm" variant="ghost" onClick={onClose}>
                      <X className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Close</TooltipContent>
                </Tooltip>
              )}
            </div>
          </div>
        </div>

        {/* Enhanced Messages */}
        <ScrollArea className="flex-1 p-4 bg-gradient-to-b from-transparent to-gray-50/30">
          <div className="space-y-6 pb-4">
            {messages.map((message, index) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === "user" ? "flex-row-reverse" : "flex-row"
                } animate-in fade-in slide-in-from-bottom-4 duration-300`}
              >
                {/* Avatar */}
                {message.role !== "system" && (
                  <div
                    className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-md ${
                      message.role === "user"
                        ? "bg-gradient-to-br from-blue-500 to-blue-600"
                        : `bg-gradient-to-br ${getProviderColor()}`
                    }`}
                  >
                    {message.role === "user" ? (
                      <User className="h-5 w-5 text-white" />
                    ) : (
                      <Bot className="h-5 w-5 text-white" />
                    )}
                  </div>
                )}

                {/* Message Content */}
                <div
                  className={`flex-1 ${
                    message.role === "user" ? "items-end" : "items-start"
                  } flex flex-col gap-1`}
                >
                  {/* Message Bubble */}
                  <div
                    className={`group relative max-w-[85%] rounded-2xl p-4 shadow-sm transition-all hover:shadow-md ${
                      message.role === "user"
                        ? "bg-gradient-to-br from-blue-600 to-blue-700 text-white ml-auto"
                        : message.role === "system"
                        ? "bg-amber-50 border border-amber-200 text-amber-900 text-sm italic"
                        : "bg-white border border-gray-200 text-gray-900"
                    }`}
                  >
                    {/* Streaming Indicator */}
                    {message.isStreaming && (
                      <div className="flex items-center gap-2 mb-2 text-sm text-gray-500">
                        <Zap className="h-3 w-3 animate-pulse" />
                        <span>Thinking...</span>
                      </div>
                    )}

                    {/* Content */}
                    <div className="whitespace-pre-wrap break-words leading-relaxed">
                      {message.metadata?.error ? (
                        // Error state with retry option
                        <div className="space-y-3">
                          <div className="flex items-start gap-2 text-red-600 dark:text-red-400">
                            <span className="text-lg">⚠️</span>
                            <div>
                              <p className="font-medium text-sm">Failed to get response</p>
                              <p className="text-xs opacity-80 mt-1">{message.metadata.error}</p>
                            </div>
                          </div>
                          {message.metadata.canRetry && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="gap-2 text-xs"
                              onClick={() => {
                                // Find the user message before this one and retry
                                const msgIndex = messages.findIndex(m => m.id === message.id);
                                if (msgIndex > 0) {
                                  const userMsg = messages[msgIndex - 1];
                                  if (userMsg?.role === 'user') {
                                    setInput(userMsg.content);
                                    // Remove the error message
                                    setMessages(prev => prev.filter(m => m.id !== message.id));
                                  }
                                }
                              }}
                            >
                              <RotateCcw className="h-3 w-3" />
                              Retry
                            </Button>
                          )}
                        </div>
                      ) : message.content ? (
                        message.content
                      ) : (
                        // Loading dots
                        <div className="flex gap-1" role="status" aria-label="Loading response">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                          <div
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0.1s" }}
                          />
                          <div
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0.2s" }}
                          />
                        </div>
                      )}
                    </div>

                    {/* Quick Actions */}
                    {message.role === "assistant" && !message.isStreaming && message.content && (
                      <div className="absolute -bottom-8 right-0 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              size="sm"
                              variant="secondary"
                              className="h-7 px-2 shadow-sm"
                              onClick={() => copyToClipboard(message.content, message.id)}
                            >
                              {copiedId === message.id ? (
                                <Check className="h-3 w-3 text-green-600" />
                              ) : (
                                <Copy className="h-3 w-3" />
                              )}
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Copy</TooltipContent>
                        </Tooltip>

                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              size="sm"
                              variant="secondary"
                              className="h-7 px-2 shadow-sm"
                              onClick={() => regenerateResponse(index)}
                            >
                              <RotateCcw className="h-3 w-3" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Regenerate</TooltipContent>
                        </Tooltip>
                      </div>
                    )}
                  </div>

                  {/* Metadata */}
                  <div
                    className={`flex flex-wrap items-center gap-2 text-xs text-gray-500 px-2 ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    {message.metadata?.provider && (
                      <>
                        <span>•</span>
                        <span className="font-medium capitalize">{message.metadata.provider}</span>
                      </>
                    )}
                    {message.metadata?.model && (
                      <>
                        <span>•</span>
                        <span className="font-medium">{message.metadata.model}</span>
                      </>
                    )}
                    {message.metadata?.execution_time_ms && (
                      <>
                        <span>•</span>
                        <span className="text-green-600">{message.metadata.execution_time_ms}ms</span>
                      </>
                    )}
                    {message.metadata?.temperature !== undefined && (
                      <>
                        <span>•</span>
                        <span>temp: {message.metadata.temperature}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Enhanced Input Area */}
        {!readOnly && (
          <div className="border-t bg-white/80 backdrop-blur-sm">
            <div className="p-4">
              {/* Quick Suggestions (optional) */}
              {messages.length === 1 && messages[0].role === "system" && (
                <div className="mb-3 flex flex-wrap gap-2">
                  {["Hello!", "Help me with...", "Explain..."].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setInput(suggestion)}
                      className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}

              {/* Input Container */}
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <Textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type your message... (Shift+Enter for new line)"
                    className="min-h-[60px] max-h-[120px] resize-none pr-12 rounded-xl border-2 focus:border-blue-500 transition-colors"
                    disabled={isLoading}
                  />
                  
                  {/* Character Count */}
                  {input.length > 0 && (
                    <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                      {input.length}
                    </div>
                  )}
                </div>

                {/* Send Button */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      onClick={handleSend}
                      disabled={!input.trim() || isLoading}
                      className={`self-end h-[60px] w-[60px] rounded-xl shadow-lg transition-all ${
                        input.trim() && !isLoading
                          ? `bg-gradient-to-br ${getProviderColor()} hover:scale-105`
                          : ""
                      }`}
                    >
                      {isLoading ? (
                        <div className="animate-spin">
                          <Sparkles className="h-5 w-5" />
                        </div>
                      ) : (
                        <Send className="h-5 w-5" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {isLoading ? "Sending..." : "Send message (Enter)"}
                  </TooltipContent>
                </Tooltip>
              </div>

              {/* Footer Info */}
              <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                <div className="flex items-center gap-2">
                  <span>Session: {sessionId?.slice(0, 8) || "auto"}</span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Zap className="h-3 w-3" />
                    {provider}
                  </span>
                </div>
                <div className="text-gray-400">
                  Press Enter to send, Shift+Enter for new line
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Read-only footer */}
        {readOnly && (
          <div className="border-t bg-amber-50/80 backdrop-blur-sm p-4">
            <div className="flex items-center justify-center gap-2 text-sm text-amber-800">
              <Bot className="h-4 w-4" />
              <span className="font-medium">Workflow Execution Results</span>
              <span>•</span>
              <span className="text-xs text-amber-600">Read-only mode</span>
            </div>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
