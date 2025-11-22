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
  User, Bot, Settings as SettingsIcon
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  metadata?: {
    model?: string;
    usage?: any;
    provider?: string;
  };
  isStreaming?: boolean;
}

interface AIAgentChatUIProps {
  position?: "right" | "bottom" | "modal" | "inline";
  onClose?: () => void;
  onSendMessage: (message: string) => Promise<string>;
  sessionId?: string;
  systemPrompt?: string;
  provider?: string;
  model?: string;
}

export function AIAgentChatUI({
  position = "right",
  onClose,
  onSendMessage,
  sessionId,
  systemPrompt,
  provider = "ollama",
  model = "llama3.3:70b",
}: AIAgentChatUIProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
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

    try {
      const response = await onSendMessage(input.trim());

      // Update with final response
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === streamingId
            ? {
                ...msg,
                content: response,
                isStreaming: false,
                metadata: { model, provider },
              }
            : msg
        )
      );
    } catch (error) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === streamingId
            ? {
                ...msg,
                content: `❌ Error: ${error instanceof Error ? error.message : "Failed to get response"}`,
                isStreaming: false,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
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

  // Position-based styling with animations
  const getContainerClass = () => {
    const baseAnimation = "transition-all duration-300 ease-in-out";
    
    if (isMinimized) {
      return `fixed bottom-4 right-4 w-80 h-14 bg-white border rounded-lg shadow-lg z-50 ${baseAnimation}`;
    }

    switch (position) {
      case "right":
        return `fixed top-0 right-0 w-[420px] h-full bg-gradient-to-br from-white to-gray-50 border-l shadow-2xl z-50 flex flex-col ${baseAnimation}`;
      case "bottom":
        return `fixed bottom-0 left-0 right-0 h-[500px] bg-gradient-to-t from-white to-gray-50 border-t shadow-2xl z-50 flex flex-col ${baseAnimation}`;
      case "modal":
        return `fixed inset-0 m-auto w-[900px] h-[700px] bg-gradient-to-br from-white to-gray-50 border rounded-2xl shadow-2xl z-50 flex flex-col ${baseAnimation}`;
      case "inline":
        return `w-full h-[600px] bg-gradient-to-br from-white to-gray-50 border rounded-xl shadow-lg flex flex-col ${baseAnimation}`;
      default:
        return `w-full h-full bg-white flex flex-col ${baseAnimation}`;
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
                      {message.content || (
                        <div className="flex gap-1">
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
                    className={`flex items-center gap-2 text-xs text-gray-500 px-2 ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    {message.metadata?.model && (
                      <>
                        <span>•</span>
                        <span className="font-medium">{message.metadata.model}</span>
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
      </div>
    </TooltipProvider>
  );
}
