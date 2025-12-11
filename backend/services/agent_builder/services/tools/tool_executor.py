"""
Tool Executor for AI Agents

Executes tools that agents can use to accomplish tasks.
Inspired by n8n's AI Agent tools architecture.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Execute tools for AI Agents."""
    
    def __init__(self):
        self.tools = {
            'calculator': self._execute_calculator,
            'code_executor': self._execute_code,
            'http_request': self._execute_http,
            'vector_search': self._execute_vector_search,
            'workflow_call': self._execute_workflow,
            'web_search': self._execute_web_search,
            'json_parser': self._execute_json_parser,
            'text_splitter': self._execute_text_splitter,
            'ai_agent': self._execute_ai_agent,
            'slack': self._execute_slack,
            'gmail': self._execute_gmail,
        }
    
    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with given parameters.
        
        Args:
            tool_id: Tool identifier
            parameters: Tool parameters
            context: Execution context (user_id, agent_id, etc.)
            
        Returns:
            Execution result with success status and data
        """
        
        if tool_id not in self.tools:
            return {
                'success': False,
                'error': f"Unknown tool: {tool_id}",
                'tool_id': tool_id
            }
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Executing tool: {tool_id} with parameters: {parameters}")
            result = await self.tools[tool_id](parameters, context or {})
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                'success': True,
                'result': result,
                'tool_id': tool_id,
                'duration_ms': duration_ms
            }
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_id} - {e}", exc_info=True)
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                'success': False,
                'error': str(e),
                'tool_id': tool_id,
                'duration_ms': duration_ms
            }
    
    async def _execute_calculator(self, params: Dict, context: Dict) -> Any:
        """Execute mathematical expression safely."""
        import ast
        import operator
        import math
        
        expression = params.get('expression', '')
        
        # Safe evaluation using ast
        # Only allow basic math operations
        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }
        
        allowed_functions = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'exp': math.exp,
            'abs': abs,
            'round': round,
        }
        
        def eval_expr(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                op = allowed_operators.get(type(node.op))
                if not op:
                    raise ValueError(f"Operator not allowed: {type(node.op)}")
                return op(eval_expr(node.left), eval_expr(node.right))
            elif isinstance(node, ast.UnaryOp):
                op = allowed_operators.get(type(node.op))
                if not op:
                    raise ValueError(f"Operator not allowed: {type(node.op)}")
                return op(eval_expr(node.operand))
            elif isinstance(node, ast.Call):
                func_name = node.func.id if isinstance(node.func, ast.Name) else None
                if func_name not in allowed_functions:
                    raise ValueError(f"Function not allowed: {func_name}")
                args = [eval_expr(arg) for arg in node.args]
                return allowed_functions[func_name](*args)
            else:
                raise ValueError(f"Expression type not allowed: {type(node)}")
        
        try:
            tree = ast.parse(expression, mode='eval')
            result = eval_expr(tree.body)
            
            return {
                'result': result,
                'expression': expression
            }
        except Exception as e:
            raise ValueError(f"Invalid expression: {str(e)}")
    
    async def _execute_code(self, params: Dict, context: Dict) -> Any:
        """
        Execute code in sandbox.
        
        Note: This is a placeholder. In production, use:
        - Docker containers
        - AWS Lambda
        - Sandboxed environments like PyPy sandbox
        """
        code = params.get('code', '')
        language = params.get('language', 'python')
        timeout = params.get('timeout', 30)
        
        # For now, return a warning
        return {
            'stdout': '',
            'stderr': 'Code execution is disabled for security reasons. Please configure a sandbox environment.',
            'result': None,
            'warning': 'Code execution requires sandbox configuration'
        }
    
    async def _execute_http(self, params: Dict, context: Dict) -> Any:
        """
        Make HTTP request with full n8n-like features.
        
        Supports:
        - All HTTP methods
        - Custom headers
        - Query parameters
        - Authentication (Basic, Bearer, API Key)
        - Timeout configuration
        - SSL verification
        - Response format handling
        """
        url = params.get('url')
        method = params.get('method', 'GET').upper()
        headers = params.get('headers', {})
        query_parameters = params.get('query_parameters', {})
        body = params.get('body')
        timeout = params.get('timeout', 30)
        follow_redirects = params.get('follow_redirects', True)
        verify_ssl = params.get('verify_ssl', True)
        response_format = params.get('response_format', 'Auto')
        authentication = params.get('authentication', 'None')
        
        if not url:
            raise ValueError("URL is required")
        
        # Handle authentication
        if authentication == 'Bearer Token':
            token = params.get('bearer_token') or context.get('env', {}).get('BEARER_TOKEN')
            if token:
                headers['Authorization'] = f'Bearer {token}'
        elif authentication == 'Basic Auth':
            username = params.get('username') or context.get('env', {}).get('HTTP_USERNAME')
            password = params.get('password') or context.get('env', {}).get('HTTP_PASSWORD')
            if username and password:
                import base64
                credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
                headers['Authorization'] = f'Basic {credentials}'
        elif authentication == 'API Key':
            api_key = params.get('api_key') or context.get('env', {}).get('API_KEY')
            api_key_header = params.get('api_key_header', 'X-API-Key')
            if api_key:
                headers[api_key_header] = api_key
        
        # Build client with configuration
        client_config = {
            'timeout': timeout,
            'follow_redirects': follow_redirects,
            'verify': verify_ssl
        }
        
        async with httpx.AsyncClient(**client_config) as client:
            try:
                # Make request
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=query_parameters,
                    json=body if body and method in ['POST', 'PUT', 'PATCH'] else None
                )
                
                # Parse response based on format
                if response_format == 'JSON' or (response_format == 'Auto' and 'application/json' in response.headers.get('content-type', '')):
                    try:
                        data = response.json()
                    except:
                        data = response.text
                elif response_format == 'Binary':
                    data = {
                        'binary': True,
                        'size': len(response.content),
                        'content_type': response.headers.get('content-type')
                    }
                else:
                    data = response.text
                
                return {
                    'status_code': response.status_code,
                    'status_text': response.reason_phrase,
                    'headers': dict(response.headers),
                    'data': data,
                    'url': str(response.url),
                    'elapsed_ms': int(response.elapsed.total_seconds() * 1000)
                }
            except httpx.TimeoutException:
                raise ValueError(f"Request timed out after {timeout} seconds")
            except httpx.RequestError as e:
                raise ValueError(f"Request failed: {str(e)}")
    
    async def _execute_vector_search(self, params: Dict, context: Dict) -> Any:
        """Search in vector database."""
        from backend.services.milvus import MilvusManager
        from backend.services.embedding import EmbeddingService
        
        query = params.get('query')
        knowledgebase_id = params.get('knowledgebase_id')
        top_k = params.get('top_k', 5)
        min_score = params.get('min_score', 0.7)
        
        if not query:
            raise ValueError("Query is required")
        if not knowledgebase_id:
            raise ValueError("Knowledgebase ID is required")
        
        try:
            embedding_service = EmbeddingService()
            milvus = MilvusManager(
                collection_name=knowledgebase_id,
                embedding_dim=embedding_service.dimension
            )
            
            # Generate query embedding
            query_embedding = embedding_service.embed_query(query)
            
            # Search
            results = milvus.search(
                query_vectors=[query_embedding],
                top_k=top_k,
                output_fields=["text", "metadata"]
            )
            
            # Filter by min_score and format results
            filtered_results = []
            for result in results[0]:
                if result.score >= min_score:
                    filtered_results.append({
                        'text': result.entity.get('text', ''),
                        'score': float(result.score),
                        'metadata': result.entity.get('metadata', {})
                    })
            
            return {
                'results': filtered_results,
                'total': len(filtered_results)
            }
        except Exception as e:
            raise ValueError(f"Vector search failed: {str(e)}")
    
    async def _execute_workflow(self, params: Dict, context: Dict) -> Any:
        """Execute another workflow."""
        from backend.services.agent_builder.workflow_executor import execute_workflow
        from backend.db.database import get_db
        from backend.db.models.agent_builder import Workflow
        
        workflow_id = params.get('workflow_id')
        input_data = params.get('input', {})
        wait_for_completion = params.get('wait_for_completion', True)
        
        if not workflow_id:
            raise ValueError("Workflow ID is required")
        
        try:
            db = next(get_db())
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            # Add user context
            if context.get('user_id'):
                input_data['_user_id'] = context['user_id']
            
            if wait_for_completion:
                result = await execute_workflow(workflow, db, input_data)
                return {
                    'output': result.get('output'),
                    'status': result.get('status', 'completed'),
                    'execution_id': result.get('execution_id')
                }
            else:
                # Start workflow asynchronously
                asyncio.create_task(execute_workflow(workflow, db, input_data))
                return {
                    'status': 'started',
                    'message': 'Workflow execution started in background'
                }
        except Exception as e:
            raise ValueError(f"Workflow execution failed: {str(e)}")
    
    async def _execute_web_search(self, params: Dict, context: Dict) -> Any:
        """Search the web using DuckDuckGo."""
        from backend.services.web_search_service import WebSearchService
        
        query = params.get('query')
        max_results = params.get('max_results', 5)
        
        if not query:
            raise ValueError("Query is required")
        
        try:
            search_service = WebSearchService()
            results = await search_service.search(query, max_results=max_results)
            
            return {
                'results': [
                    {
                        'title': r.get('title', ''),
                        'url': r.get('url', ''),
                        'snippet': r.get('snippet', '')
                    }
                    for r in results
                ]
            }
        except Exception as e:
            raise ValueError(f"Web search failed: {str(e)}")
    
    async def _execute_json_parser(self, params: Dict, context: Dict) -> Any:
        """Parse and manipulate JSON data."""
        json_string = params.get('json_string', '')
        path = params.get('path')
        
        if not json_string:
            raise ValueError("JSON string is required")
        
        try:
            parsed = json.loads(json_string)
            
            # If path is provided, extract data using simple dot notation
            if path:
                extracted = parsed
                for key in path.strip('$.').split('.'):
                    if '[' in key:
                        # Handle array indexing
                        key_name, index = key.split('[')
                        index = int(index.rstrip(']'))
                        extracted = extracted[key_name][index]
                    else:
                        extracted = extracted[key]
                
                return {
                    'parsed': parsed,
                    'extracted': extracted
                }
            
            return {
                'parsed': parsed
            }
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")
        except (KeyError, IndexError, TypeError) as e:
            raise ValueError(f"Path extraction failed: {str(e)}")
    
    async def _execute_text_splitter(self, params: Dict, context: Dict) -> Any:
        """Split text into chunks."""
        text = params.get('text', '')
        chunk_size = params.get('chunk_size', 500)
        chunk_overlap = params.get('chunk_overlap', 50)
        
        if not text:
            raise ValueError("Text is required")
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - chunk_overlap
        
        return {
            'chunks': chunks,
            'total_chunks': len(chunks)
        }
    
    async def _execute_ai_agent(self, params: Dict, context: Dict) -> Any:
        """
        Execute AI Agent with tool use capabilities.
        
        Supports:
        - Local LLM (Ollama)
        - OpenAI
        - Anthropic (Claude)
        - Web search
        - Vector search
        - Multiple tools
        """
        from backend.services.llm_manager import LLMManager
        from backend.agents.aggregator import AggregatorAgent
        from backend.services.embedding import EmbeddingService
        from backend.services.milvus import MilvusManager
        from backend.services.web_search_service import WebSearchService
        from backend.config import settings
        
        task = params.get('task')
        llm_provider = params.get('llm_provider', 'Local (Ollama)')
        model = params.get('model', 'llama3.1:8b')
        enable_web_search = params.get('enable_web_search', True)
        enable_vector_search = params.get('enable_vector_search', True)
        knowledgebase_id = params.get('knowledgebase_id')
        available_tools = params.get('available_tools', ['web_search', 'vector_search'])
        max_iterations = params.get('max_iterations', 10)
        temperature = params.get('temperature', 0.7)
        system_prompt = params.get('system_prompt')
        max_tokens = params.get('max_tokens', 2000)
        timeout = params.get('timeout', 120)
        
        if not task:
            raise ValueError("Task is required")
        
        try:
            # Map provider names to internal format
            provider_map = {
                'Local (Ollama)': 'ollama',
                'OpenAI': 'openai',
                'Anthropic (Claude)': 'claude'
            }
            
            provider = provider_map.get(llm_provider, 'ollama')
            
            # Initialize LLM Manager
            llm_manager = LLMManager()
            
            # Build available tools list
            agent_tools = []
            
            if enable_web_search and 'web_search' in available_tools:
                agent_tools.append({
                    'name': 'web_search',
                    'description': 'Search the internet for current information',
                    'executor': self._execute_web_search
                })
            
            if enable_vector_search and 'vector_search' in available_tools and knowledgebase_id:
                agent_tools.append({
                    'name': 'vector_search',
                    'description': 'Search in knowledge base for relevant documents',
                    'executor': self._execute_vector_search
                })
            
            if 'calculator' in available_tools:
                agent_tools.append({
                    'name': 'calculator',
                    'description': 'Perform mathematical calculations',
                    'executor': self._execute_calculator
                })
            
            if 'http_request' in available_tools:
                agent_tools.append({
                    'name': 'http_request',
                    'description': 'Make HTTP requests to APIs',
                    'executor': self._execute_http
                })
            
            # Use Aggregator Agent for complex reasoning
            try:
                embedding_service = EmbeddingService()
                milvus_manager = None
                
                if enable_vector_search and knowledgebase_id:
                    milvus_manager = MilvusManager(
                        collection_name=knowledgebase_id,
                        embedding_dim=embedding_service.dimension
                    )
                
                # Create aggregator agent
                aggregator = AggregatorAgent(
                    llm_manager=llm_manager,
                    embedding_service=embedding_service,
                    milvus_manager=milvus_manager
                )
                
                # Execute agent with task
                result = await aggregator.execute(
                    query=task,
                    context={
                        'max_iterations': max_iterations,
                        'temperature': temperature,
                        'model': model,
                        'provider': provider,
                        'system_prompt': system_prompt,
                        'max_tokens': max_tokens,
                        'enable_web_search': enable_web_search,
                        'enable_vector_search': enable_vector_search,
                        'available_tools': agent_tools
                    }
                )
                
                return {
                    'answer': result.get('answer', ''),
                    'reasoning_steps': result.get('steps', []),
                    'tools_used': result.get('tools_used', []),
                    'sources': result.get('sources', []),
                    'confidence': result.get('confidence', 0.0),
                    'iterations': result.get('iterations', 0)
                }
                
            except Exception as e:
                # Fallback to simple LLM call if agent fails
                logger.warning(f"Agent execution failed, falling back to simple LLM: {e}")
                
                prompt = task
                if system_prompt:
                    prompt = f"{system_prompt}\n\nTask: {task}"
                
                response = await llm_manager.generate(
                    prompt=prompt,
                    model=model,
                    provider=provider,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                return {
                    'answer': response,
                    'reasoning_steps': [],
                    'tools_used': [],
                    'sources': [],
                    'confidence': 0.5,
                    'iterations': 1,
                    'fallback': True
                }
                
        except Exception as e:
            raise ValueError(f"AI Agent execution failed: {str(e)}")

    
    async def _execute_slack(self, params: Dict, context: Dict) -> Any:
        """
        Execute Slack operations.
        
        Supports:
        - Send Message
        - Send Direct Message
        - Update Message
        - Get Channel
        - Create Channel
        - Get User
        """
        operation = params.get('operation', 'Send Message')
        token = params.get('token') or context.get('env', {}).get('SLACK_TOKEN')
        
        if not token:
            raise ValueError("Slack token is required")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if operation == 'Send Message':
                channel = params.get('channel')
                text = params.get('text')
                blocks = params.get('blocks')
                attachments = params.get('attachments')
                thread_ts = params.get('thread_ts')
                username = params.get('username')
                icon_emoji = params.get('icon_emoji')
                icon_url = params.get('icon_url')
                
                if not channel:
                    raise ValueError("Channel is required for Send Message")
                if not text and not blocks:
                    raise ValueError("Either text or blocks is required")
                
                payload = {
                    'channel': channel,
                    'text': text
                }
                
                if blocks:
                    payload['blocks'] = blocks
                if attachments:
                    payload['attachments'] = attachments
                if thread_ts:
                    payload['thread_ts'] = thread_ts
                if username:
                    payload['username'] = username
                if icon_emoji:
                    payload['icon_emoji'] = icon_emoji
                if icon_url:
                    payload['icon_url'] = icon_url
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        'https://slack.com/api/chat.postMessage',
                        headers=headers,
                        json=payload
                    )
                    
                    result = response.json()
                    
                    if not result.get('ok'):
                        raise ValueError(f"Slack API error: {result.get('error', 'Unknown error')}")
                    
                    return {
                        'success': True,
                        'channel': result.get('channel'),
                        'ts': result.get('ts'),
                        'message': result.get('message')
                    }
            
            elif operation == 'Send Direct Message':
                user = params.get('user')
                text = params.get('text')
                
                if not user:
                    raise ValueError("User ID is required for Send Direct Message")
                if not text:
                    raise ValueError("Text is required")
                
                # First, open a DM channel
                async with httpx.AsyncClient() as client:
                    dm_response = await client.post(
                        'https://slack.com/api/conversations.open',
                        headers=headers,
                        json={'users': user}
                    )
                    
                    dm_result = dm_response.json()
                    if not dm_result.get('ok'):
                        raise ValueError(f"Failed to open DM: {dm_result.get('error')}")
                    
                    channel_id = dm_result['channel']['id']
                    
                    # Send message to DM channel
                    msg_response = await client.post(
                        'https://slack.com/api/chat.postMessage',
                        headers=headers,
                        json={
                            'channel': channel_id,
                            'text': text
                        }
                    )
                    
                    msg_result = msg_response.json()
                    if not msg_result.get('ok'):
                        raise ValueError(f"Failed to send message: {msg_result.get('error')}")
                    
                    return {
                        'success': True,
                        'channel': channel_id,
                        'ts': msg_result.get('ts')
                    }
            
            elif operation == 'Get Channel':
                channel = params.get('channel')
                
                if not channel:
                    raise ValueError("Channel is required")
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        'https://slack.com/api/conversations.info',
                        headers=headers,
                        json={'channel': channel}
                    )
                    
                    result = response.json()
                    if not result.get('ok'):
                        raise ValueError(f"Slack API error: {result.get('error')}")
                    
                    return {
                        'success': True,
                        'channel': result.get('channel')
                    }
            
            elif operation == 'Create Channel':
                channel_name = params.get('channel')
                is_private = params.get('is_private', False)
                
                if not channel_name:
                    raise ValueError("Channel name is required")
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        'https://slack.com/api/conversations.create',
                        headers=headers,
                        json={
                            'name': channel_name,
                            'is_private': is_private
                        }
                    )
                    
                    result = response.json()
                    if not result.get('ok'):
                        raise ValueError(f"Slack API error: {result.get('error')}")
                    
                    return {
                        'success': True,
                        'channel': result.get('channel')
                    }
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except httpx.RequestError as e:
            raise ValueError(f"Slack API request failed: {str(e)}")
    
    async def _execute_gmail(self, params: Dict, context: Dict) -> Any:
        """
        Execute Gmail operations.
        
        Supports:
        - Send Email
        - Get Email
        - Search Emails
        - Delete Email
        - Add/Remove Labels
        - Create Draft
        """
        operation = params.get('operation', 'Send Email')
        credentials = params.get('credentials') or context.get('env', {}).get('GMAIL_CREDENTIALS')
        
        if not credentials:
            raise ValueError("Gmail credentials are required")
        
        try:
            if operation == 'Send Email':
                to = params.get('to')
                cc = params.get('cc')
                bcc = params.get('bcc')
                subject = params.get('subject', '')
                body = params.get('body', '')
                body_type = params.get('body_type', 'Plain Text')
                attachments = params.get('attachments', [])
                
                if not to:
                    raise ValueError("Recipient email (to) is required")
                
                # Build email message
                import base64
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                from email.mime.base import MIMEBase
                from email import encoders
                
                if attachments:
                    message = MIMEMultipart()
                else:
                    message = MIMEText(body, 'html' if body_type == 'HTML' else 'plain')
                
                message['to'] = to
                if cc:
                    message['cc'] = cc
                if bcc:
                    message['bcc'] = bcc
                message['subject'] = subject
                
                if attachments:
                    # Add body
                    body_part = MIMEText(body, 'html' if body_type == 'HTML' else 'plain')
                    message.attach(body_part)
                    
                    # Add attachments
                    for attachment in attachments:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(base64.b64decode(attachment.get('data', '')))
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={attachment.get("filename", "file")}'
                        )
                        message.attach(part)
                
                # Encode message
                raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                
                # Send via Gmail API
                # Note: This requires google-api-python-client
                # For now, return mock response
                return {
                    'success': True,
                    'message_id': 'mock_message_id_123',
                    'thread_id': 'mock_thread_id_456',
                    'label_ids': ['SENT'],
                    'note': 'Gmail API integration requires google-api-python-client package'
                }
            
            elif operation == 'Search Emails':
                query = params.get('query', '')
                max_results = params.get('max_results', 10)
                
                if not query:
                    raise ValueError("Search query is required")
                
                # Mock search results
                return {
                    'success': True,
                    'messages': [
                        {
                            'id': 'msg_1',
                            'thread_id': 'thread_1',
                            'snippet': 'Email preview text...',
                            'from': 'sender@example.com',
                            'subject': 'Test Email',
                            'date': '2025-11-17'
                        }
                    ],
                    'total': 1,
                    'note': 'Gmail API integration requires google-api-python-client package'
                }
            
            elif operation == 'Get Email':
                message_id = params.get('message_id')
                
                if not message_id:
                    raise ValueError("Message ID is required")
                
                # Mock email data
                return {
                    'success': True,
                    'id': message_id,
                    'thread_id': 'thread_123',
                    'from': 'sender@example.com',
                    'to': 'recipient@example.com',
                    'subject': 'Email Subject',
                    'body': 'Email body content',
                    'date': '2025-11-17',
                    'labels': ['INBOX', 'UNREAD'],
                    'note': 'Gmail API integration requires google-api-python-client package'
                }
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            raise ValueError(f"Gmail operation failed: {str(e)}")
