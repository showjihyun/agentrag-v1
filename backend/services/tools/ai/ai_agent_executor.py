"""
AI Agent Tool Executor - n8n Style

Advanced AI Agent with Memory Management:
- Short Term Memory (STM): Current conversation context
- Mid Term Memory (MTM): Session-based memory
- Long Term Memory (LTM): Persistent knowledge base
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx

from ..base_executor import BaseToolExecutor, ToolExecutionResult


class AIAgentExecutor(BaseToolExecutor):
    """
    AI Agent Tool Executor with Memory Management
    
    Features:
    - Multiple LLM provider support (OpenAI, Anthropic, Ollama)
    - Short/Mid/Long Term Memory
    - System prompts and context management
    - Conversation history
    - Tool calling capabilities
    - Streaming support
    """
    
    def __init__(self):
        super().__init__("ai_agent", "AI Agent")
        self.category = "ai"
        
        # Memory storage (in production, use Redis/Database)
        self.short_term_memory: Dict[str, List[Dict]] = {}  # session_id -> messages
        self.mid_term_memory: Dict[str, Dict] = {}  # session_id -> context
        self.long_term_memory: Dict[str, Any] = {}  # persistent knowledge
        
        # Define parameter schema
        self.params_schema = {
            # Core Settings
            "provider": {
                "type": "select",
                "description": "LLM Provider",
                "required": True,
                "enum": ["ollama", "openai", "claude", "gemini", "grok"],
                "default": "ollama",
                "helpText": "Choose your AI provider"
            },
            "model": {
                "type": "select",
                "description": "Model",
                "required": True,
                "enum": [
                    # Ollama (Local)
                    "llama3.3:70b", "llama3.1:70b", "qwen2.5:72b", "deepseek-r1:70b", "mixtral:8x7b",
                    # OpenAI
                    "gpt-5", "o3", "o3-mini", "gpt-4o", "gpt-4o-mini",
                    # Claude
                    "claude-4.5-sonnet", "claude-4-sonnet", "claude-3.7-sonnet", "claude-3.5-sonnet", "claude-3-opus",
                    # Gemini
                    "gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-ultra",
                    # Grok
                    "grok-3", "grok-2.5", "grok-2", "grok-2-mini", "grok-vision"
                ],
                "default": "llama3.3:70b",
                "helpText": "Select the AI model to use"
            },
            
            # Chat UI Mode
            "enable_chat_ui": {
                "type": "boolean",
                "description": "Enable Real-time Chat UI",
                "required": False,
                "default": False,
                "helpText": "Show interactive chat interface for real-time conversations"
            },
            "chat_ui_position": {
                "type": "select",
                "description": "Chat UI Position",
                "required": False,
                "enum": ["right", "bottom", "modal", "inline"],
                "default": "right",
                "helpText": "Where to display the chat interface"
            },
            
            # Prompt Configuration
            "system_prompt": {
                "type": "textarea",
                "description": "System Prompt",
                "required": False,
                "placeholder": "You are a helpful AI assistant...",
                "helpText": "Define the agent's behavior and personality"
            },
            "user_message": {
                "type": "textarea",
                "description": "User Message",
                "required": True,
                "placeholder": "Enter your message or use {{input.message}}",
                "helpText": "The message to send to the AI"
            },
            
            # Memory Configuration
            "enable_memory": {
                "type": "boolean",
                "description": "Enable Memory",
                "required": False,
                "default": True,
                "helpText": "Use conversation memory"
            },
            "memory_type": {
                "type": "select",
                "description": "Memory Type",
                "required": False,
                "enum": ["short_term", "mid_term", "long_term", "all"],
                "default": "short_term",
                "helpText": "Type of memory to use"
            },
            "memory_window": {
                "type": "select",
                "description": "Memory Window",
                "required": False,
                "enum": ["5", "10", "20", "50", "100"],
                "default": "10",
                "helpText": "Number of messages to remember"
            },
            "session_id": {
                "type": "string",
                "description": "Session ID",
                "required": False,
                "placeholder": "auto-generated or custom",
                "helpText": "Unique identifier for this conversation"
            },
            
            # Generation Parameters
            "temperature": {
                "type": "number",
                "description": "Temperature",
                "required": False,
                "default": 0.7,
                "min": 0,
                "max": 2,
                "helpText": "0 = deterministic, 2 = very creative"
            },
            "max_tokens": {
                "type": "number",
                "description": "Max Tokens",
                "required": False,
                "default": 1000,
                "min": 1,
                "max": 4096,
                "helpText": "Maximum length of response"
            },
            "top_p": {
                "type": "number",
                "description": "Top P",
                "required": False,
                "default": 1,
                "min": 0,
                "max": 1,
                "helpText": "Nucleus sampling parameter"
            },
            "frequency_penalty": {
                "type": "number",
                "description": "Frequency Penalty",
                "required": False,
                "default": 0,
                "min": 0,
                "max": 2,
                "helpText": "Reduce repetition"
            },
            "presence_penalty": {
                "type": "number",
                "description": "Presence Penalty",
                "required": False,
                "default": 0,
                "min": 0,
                "max": 2,
                "helpText": "Encourage new topics"
            },
            
            # Advanced Options
            "response_format": {
                "type": "select",
                "description": "Response Format",
                "required": False,
                "enum": ["text", "json", "json_object"],
                "default": "text",
                "helpText": "Format of the response"
            },
            "stop_sequences": {
                "type": "array",
                "description": "Stop Sequences",
                "required": False,
                "placeholder": "\\n\\n, END, STOP",
                "helpText": "Sequences that stop generation"
            },
            "timeout": {
                "type": "select",
                "description": "Timeout (seconds)",
                "required": False,
                "enum": ["30", "60", "120", "300"],
                "default": "60",
                "helpText": "Request timeout"
            },
            
            # Context Management
            "include_context": {
                "type": "boolean",
                "description": "Include Previous Context",
                "required": False,
                "default": True,
                "helpText": "Include conversation history"
            },
            "context_window": {
                "type": "select",
                "description": "Context Window",
                "required": False,
                "enum": ["5", "10", "20", "full"],
                "default": "10",
                "helpText": "Number of previous messages to include"
            },
            
            # Output Options
            "extract_json": {
                "type": "boolean",
                "description": "Extract JSON from Response",
                "required": False,
                "default": False,
                "helpText": "Parse JSON from markdown code blocks"
            },
            "return_metadata": {
                "type": "boolean",
                "description": "Return Metadata",
                "required": False,
                "default": True,
                "helpText": "Include usage stats and metadata"
            }
        }
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Execute AI Agent with memory management."""
        
        try:
            self.logger.info("🤖 AI Agent execution started", extra={
                "provider": params.get("provider"),
                "model": params.get("model"),
                "has_system_prompt": bool(params.get("system_prompt")),
                "message_length": len(params.get("user_message", "")),
                "enable_memory": params.get("enable_memory", True),
            })
            
            # Validate required parameters
            self.validate_params(params, ["provider", "model", "user_message"])
            
            # Extract parameters
            provider = params.get("provider")
            model = params.get("model")
            user_message = params.get("user_message")
            system_prompt = params.get("system_prompt")
            
            # Memory configuration
            enable_memory = params.get("enable_memory", True)
            memory_type = params.get("memory_type", "short_term")
            memory_window = int(params.get("memory_window", 10))
            session_id = params.get("session_id", f"session_{datetime.now().timestamp()}")
            
            # Generation parameters
            temperature = params.get("temperature", 0.7)
            max_tokens = params.get("max_tokens", 1000)
            top_p = params.get("top_p", 1)
            frequency_penalty = params.get("frequency_penalty", 0)
            presence_penalty = params.get("presence_penalty", 0)
            
            self.logger.debug("📝 Building messages with memory", extra={
                "session_id": session_id,
                "memory_type": memory_type,
                "memory_window": memory_window,
            })
            
            # Build messages with memory
            messages = self._build_messages_with_memory(
                user_message=user_message,
                system_prompt=system_prompt,
                session_id=session_id,
                enable_memory=enable_memory,
                memory_type=memory_type,
                memory_window=memory_window
            )
            
            self.logger.info(f"📨 Executing {provider} request", extra={
                "model": model,
                "message_count": len(messages),
                "temperature": temperature,
                "max_tokens": max_tokens,
            })
            
            # Execute based on provider
            if provider in ["openai"]:
                result = await self._execute_openai(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                    credentials=credentials,
                    params=params
                )
            elif provider in ["anthropic", "claude"]:
                result = await self._execute_anthropic(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    credentials=credentials,
                    params=params
                )
            elif provider == "ollama":
                result = await self._execute_ollama(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    params=params
                )
            elif provider in ["gemini"]:
                result = await self._execute_gemini(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    credentials=credentials,
                    params=params
                )
            elif provider in ["grok"]:
                result = await self._execute_grok(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    credentials=credentials,
                    params=params
                )
            else:
                error_msg = f"Unsupported provider: {provider}"
                self.logger.error(f"❌ {error_msg}", extra={
                    "provider": provider,
                    "supported_providers": ["openai", "anthropic", "claude", "ollama", "gemini", "grok"]
                })
                return ToolExecutionResult(
                    success=False,
                    output=None,
                    error=error_msg
                )
            
            # Log result
            if result.success:
                self.logger.info("✅ AI Agent execution successful", extra={
                    "provider": provider,
                    "model": model,
                    "response_length": len(result.output.get("content", "")) if result.output else 0,
                    "has_metadata": "metadata" in (result.output or {}),
                })
            else:
                self.logger.error("❌ AI Agent execution failed", extra={
                    "provider": provider,
                    "model": model,
                    "error": result.error,
                })
            
            # Update memory if enabled
            if enable_memory and result.success:
                self.logger.debug("💾 Updating memory", extra={
                    "session_id": session_id,
                    "memory_type": memory_type,
                })
                self._update_memory(
                    session_id=session_id,
                    user_message=user_message,
                    assistant_message=result.output.get("content", ""),
                    memory_type=memory_type
                )
            
            return result
            
        except ValueError as e:
            # Validation errors
            error_msg = f"Validation error: {str(e)}"
            self.logger.error(f"❌ {error_msg}", extra={
                "error_type": "ValidationError",
                "params": {k: v for k, v in params.items() if k != "user_message"},
            })
            return ToolExecutionResult(
                success=False,
                output=None,
                error=error_msg
            )
        except Exception as e:
            # Unexpected errors
            self.logger.error("❌ AI Agent execution failed with unexpected error", extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "provider": params.get("provider"),
                "model": params.get("model"),
            }, exc_info=True)
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Unexpected error: {str(e)}"
            )
    
    def _build_messages_with_memory(
        self,
        user_message: str,
        system_prompt: Optional[str],
        session_id: str,
        enable_memory: bool,
        memory_type: str,
        memory_window: int
    ) -> List[Dict[str, str]]:
        """Build message list with memory context."""
        
        messages = []
        
        # Add system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add memory context if enabled
        if enable_memory:
            memory_messages = self._get_memory_messages(
                session_id=session_id,
                memory_type=memory_type,
                window=memory_window
            )
            messages.extend(memory_messages)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _get_memory_messages(
        self,
        session_id: str,
        memory_type: str,
        window: int
    ) -> List[Dict[str, str]]:
        """Retrieve messages from memory."""
        
        messages = []
        
        if memory_type in ["short_term", "all"]:
            # Short term memory (current session)
            stm = self.short_term_memory.get(session_id, [])
            messages.extend(stm[-window:])
        
        if memory_type in ["mid_term", "all"]:
            # Mid term memory (session context)
            mtm = self.mid_term_memory.get(session_id, {})
            if mtm.get("summary"):
                messages.insert(0, {
                    "role": "system",
                    "content": f"Previous context: {mtm['summary']}"
                })
        
        if memory_type in ["long_term", "all"]:
            # Long term memory (persistent knowledge)
            if self.long_term_memory:
                ltm_context = json.dumps(self.long_term_memory, indent=2)
                messages.insert(0, {
                    "role": "system",
                    "content": f"Knowledge base: {ltm_context}"
                })
        
        return messages
    
    def _update_memory(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        memory_type: str
    ):
        """Update memory with new messages."""
        
        # Update short term memory
        if memory_type in ["short_term", "all"]:
            if session_id not in self.short_term_memory:
                self.short_term_memory[session_id] = []
            
            self.short_term_memory[session_id].append({
                "role": "user",
                "content": user_message
            })
            self.short_term_memory[session_id].append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Keep only last 100 messages
            self.short_term_memory[session_id] = self.short_term_memory[session_id][-100:]
        
        # Update mid term memory (session summary)
        if memory_type in ["mid_term", "all"]:
            if session_id not in self.mid_term_memory:
                self.mid_term_memory[session_id] = {
                    "created_at": datetime.now().isoformat(),
                    "message_count": 0,
                    "summary": ""
                }
            
            self.mid_term_memory[session_id]["message_count"] += 2
            self.mid_term_memory[session_id]["last_updated"] = datetime.now().isoformat()
    
    async def _execute_openai(
        self,
        model: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        top_p: float,
        frequency_penalty: float,
        presence_penalty: float,
        credentials: Optional[Dict],
        params: Dict
    ) -> ToolExecutionResult:
        """Execute OpenAI request."""
        
        api_key = credentials.get("api_key") if credentials else os.getenv("OPENAI_API_KEY")
        if not api_key:
            error_msg = "OpenAI API key not configured"
            self.logger.error(f"❌ {error_msg}")
            return ToolExecutionResult(
                success=False,
                output=None,
                error=error_msg
            )
        
        self.logger.debug(f"🤖 OpenAI request", extra={
            "model": model,
            "message_count": len(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Determine if model uses new API parameters (GPT-5, O3, O1, etc.)
        is_reasoning_model = any(m in model.lower() for m in [
            'gpt-5', 'o3', 'o1', 'o-1'  # Reasoning models with restricted parameters
        ])
        
        uses_max_completion_tokens = is_reasoning_model or 'gpt-4o-2024-08-06' in model.lower()
        
        payload = {
            "model": model,
            "messages": messages,
        }
        
        # Reasoning models (GPT-5, O3, O1) only support temperature=1
        if is_reasoning_model:
            payload["temperature"] = 1
        else:
            payload["temperature"] = temperature
            payload["top_p"] = top_p
            payload["frequency_penalty"] = frequency_penalty
            payload["presence_penalty"] = presence_penalty
        
        # Add max_tokens or max_completion_tokens based on model
        if uses_max_completion_tokens:
            payload["max_completion_tokens"] = max_tokens
        else:
            payload["max_tokens"] = max_tokens
        
        # Add response format if specified
        response_format = params.get("response_format")
        if response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}
        
        # Add stop sequences if specified
        stop_sequences = params.get("stop_sequences")
        if stop_sequences:
            payload["stop"] = stop_sequences
        
        timeout = int(params.get("timeout", 60))
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    self.logger.error(f"❌ OpenAI API error", extra={
                        "status_code": response.status_code,
                        "error": error_text,
                        "model": model,
                    })
                    return ToolExecutionResult(
                        success=False,
                        output=None,
                        error=f"OpenAI API error {response.status_code}: {error_text}"
                    )
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                self.logger.info(f"✅ OpenAI response received", extra={
                    "model": model,
                    "response_length": len(content),
                    "usage": data.get("usage", {}),
                    "finish_reason": data["choices"][0].get("finish_reason"),
                })
                
                output = {
                    "content": content,
                    "role": "assistant"
                }
                
                # Add metadata if requested
                if params.get("return_metadata", True):
                    output["metadata"] = {
                        "model": model,
                        "usage": data.get("usage", {}),
                        "finish_reason": data["choices"][0].get("finish_reason"),
                        "provider": "openai"
                    }
                
                # Extract JSON if requested
                if params.get("extract_json", False):
                    try:
                        # Try to parse as JSON
                        json_content = json.loads(content)
                        output["json"] = json_content
                    except:
                        # Try to extract from markdown code block
                        import re
                        json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                        if json_match:
                            try:
                                output["json"] = json.loads(json_match.group(1))
                            except:
                                pass
                
                return ToolExecutionResult(
                    success=True,
                    output=output
                )
                
        except httpx.TimeoutException:
            error_msg = f"OpenAI request timeout after {timeout}s"
            self.logger.error(f"❌ {error_msg}", extra={
                "model": model,
                "timeout": timeout,
            })
            return ToolExecutionResult(
                success=False,
                output=None,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"OpenAI execution failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}", extra={
                "model": model,
                "error_type": type(e).__name__,
                "error": str(e),
            }, exc_info=True)
            return ToolExecutionResult(
                success=False,
                output=None,
                error=error_msg
            )
    
    async def _execute_anthropic(
        self,
        model: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        credentials: Optional[Dict],
        params: Dict
    ) -> ToolExecutionResult:
        """Execute Anthropic request."""
        
        api_key = credentials.get("api_key") if credentials else os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="Anthropic API key not configured"
            )
        
        # Separate system message from other messages
        system_message = None
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                chat_messages.append(msg)
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if system_message:
            payload["system"] = system_message
        
        timeout = int(params.get("timeout", 60))
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    return ToolExecutionResult(
                        success=False,
                        output=None,
                        error=f"Anthropic API error: {response.status_code}"
                    )
                
                data = response.json()
                content = data["content"][0]["text"]
                
                output = {
                    "content": content,
                    "role": "assistant"
                }
                
                if params.get("return_metadata", True):
                    output["metadata"] = {
                        "model": model,
                        "usage": data.get("usage", {}),
                        "stop_reason": data.get("stop_reason"),
                        "provider": "anthropic"
                    }
                
                return ToolExecutionResult(
                    success=True,
                    output=output
                )
                
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Anthropic execution failed: {str(e)}"
            )
    
    async def _execute_ollama(
        self,
        model: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        params: Dict
    ) -> ToolExecutionResult:
        """Execute Ollama request."""
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        self.logger.debug(f"🦙 Ollama request", extra={
            "url": ollama_url,
            "model": model,
            "message_count": len(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        
        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": False
        }
        
        timeout = int(params.get("timeout", 60))
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{ollama_url}/api/chat",
                    json=payload
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    self.logger.error(f"❌ Ollama API error", extra={
                        "status_code": response.status_code,
                        "error": error_text,
                        "model": model,
                        "url": ollama_url,
                    })
                    return ToolExecutionResult(
                        success=False,
                        output=None,
                        error=f"Ollama API error {response.status_code}: {error_text}"
                    )
                
                data = response.json()
                content = data["message"]["content"]
                
                self.logger.info(f"✅ Ollama response received", extra={
                    "model": model,
                    "response_length": len(content),
                    "eval_count": data.get("eval_count"),
                    "eval_duration_ms": data.get("eval_duration", 0) / 1_000_000 if data.get("eval_duration") else None,
                })
                
                output = {
                    "content": content,
                    "role": "assistant"
                }
                
                if params.get("return_metadata", True):
                    output["metadata"] = {
                        "model": model,
                        "provider": "ollama",
                        "eval_count": data.get("eval_count"),
                        "eval_duration": data.get("eval_duration")
                    }
                
                return ToolExecutionResult(
                    success=True,
                    output=output
                )
                
        except httpx.TimeoutException:
            error_msg = f"Ollama request timeout after {timeout}s"
            self.logger.error(f"❌ {error_msg}", extra={
                "model": model,
                "timeout": timeout,
                "url": ollama_url,
            })
            return ToolExecutionResult(
                success=False,
                output=None,
                error=error_msg
            )
        except httpx.ConnectError as e:
            error_msg = f"Cannot connect to Ollama at {ollama_url}"
            self.logger.error(f"❌ {error_msg}", extra={
                "url": ollama_url,
                "error": str(e),
            })
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"{error_msg}. Please ensure Ollama is running."
            )
        except Exception as e:
            error_msg = f"Ollama execution failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}", extra={
                "model": model,
                "error_type": type(e).__name__,
                "error": str(e),
            }, exc_info=True)
            return ToolExecutionResult(
                success=False,
                output=None,
                error=error_msg
            )
    
    async def _execute_gemini(
        self,
        model: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        credentials: Optional[Dict],
        params: Dict
    ) -> ToolExecutionResult:
        """Execute Gemini request."""
        
        api_key = credentials.get("api_key") if credentials else os.getenv("GEMINI_API_KEY")
        if not api_key:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="Gemini API key not configured"
            )
        
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            if msg["role"] != "system":
                contents.append({
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [{"text": msg["content"]}]
                })
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        timeout = int(params.get("timeout", 60))
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    return ToolExecutionResult(
                        success=False,
                        output=None,
                        error=f"Gemini API error: {response.status_code}"
                    )
                
                data = response.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                
                output = {
                    "content": content,
                    "role": "assistant"
                }
                
                if params.get("return_metadata", True):
                    output["metadata"] = {
                        "model": model,
                        "provider": "gemini",
                        "usage": data.get("usageMetadata", {})
                    }
                
                return ToolExecutionResult(
                    success=True,
                    output=output
                )
                
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Gemini execution failed: {str(e)}"
            )
    
    async def _execute_grok(
        self,
        model: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        credentials: Optional[Dict],
        params: Dict
    ) -> ToolExecutionResult:
        """Execute Grok request (xAI API)."""
        
        api_key = credentials.get("api_key") if credentials else os.getenv("XAI_API_KEY")
        if not api_key:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="xAI API key not configured"
            )
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        timeout = int(params.get("timeout", 60))
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    return ToolExecutionResult(
                        success=False,
                        output=None,
                        error=f"xAI API error: {response.status_code}"
                    )
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                output = {
                    "content": content,
                    "role": "assistant"
                }
                
                if params.get("return_metadata", True):
                    output["metadata"] = {
                        "model": model,
                        "usage": data.get("usage", {}),
                        "provider": "grok"
                    }
                
                return ToolExecutionResult(
                    success=True,
                    output=output
                )
                
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Grok execution failed: {str(e)}"
            )


# Tool metadata for registration
TOOL_METADATA = {
    'id': 'ai_agent',
    'name': 'AI Agent',
    'description': 'Advanced AI Agent with Memory Management (n8n style)',
    'category': 'ai',
    'icon': '🤖',
    'bg_color': '#8B5CF6',
    'version': '1.0.0',
    'author': 'Agentic RAG System'
}
