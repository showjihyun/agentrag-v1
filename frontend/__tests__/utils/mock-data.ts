/**
 * Mock data for testing
 */

// User mocks
export const mockUser = {
  id: 'user-1',
  email: 'test@example.com',
  username: 'testuser',
  full_name: 'Test User',
  created_at: '2024-01-01T00:00:00Z',
};

export const mockAuthToken = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
};

// Document mocks
export const mockDocument = {
  document_id: 'doc-1',
  filename: 'test.pdf',
  file_size: 1024,
  mime_type: 'application/pdf',
  processing_status: 'completed',
  created_at: '2024-01-01T00:00:00Z',
};

export const mockDocuments = [
  mockDocument,
  { ...mockDocument, document_id: 'doc-2', filename: 'test2.pdf' },
  { ...mockDocument, document_id: 'doc-3', filename: 'test3.pdf' },
];

// Message mocks
export const mockMessage = {
  id: 'msg-1',
  role: 'user' as const,
  content: 'What is machine learning?',
  timestamp: '2024-01-01T00:00:00Z',
};

export const mockAssistantMessage = {
  id: 'msg-2',
  role: 'assistant' as const,
  content: 'Machine learning is a subset of artificial intelligence...',
  timestamp: '2024-01-01T00:00:01Z',
  sources: [
    {
      chunk_id: 'chunk-1',
      content: 'Source content...',
      score: 0.95,
      document_id: 'doc-1',
    },
  ],
};

export const mockConversation = {
  session_id: 'session-1',
  title: 'Test Conversation',
  messages: [mockMessage, mockAssistantMessage],
  created_at: '2024-01-01T00:00:00Z',
};

// Agent Builder mocks
export const mockAgent = {
  id: 'agent-1',
  name: 'Test Agent',
  description: 'A test agent',
  status: 'active',
  created_at: '2024-01-01T00:00:00Z',
};

export const mockWorkflow = {
  id: 'workflow-1',
  name: 'Test Workflow',
  description: 'A test workflow',
  nodes: [],
  edges: [],
  created_at: '2024-01-01T00:00:00Z',
};

export const mockBlock = {
  id: 'block-1',
  type: 'llm',
  name: 'LLM Block',
  config: {
    model: 'gpt-4',
    temperature: 0.7,
  },
};

// Search result mocks
export const mockSearchResult = {
  chunk_id: 'chunk-1',
  content: 'This is a sample search result content.',
  score: 0.95,
  document_id: 'doc-1',
  metadata: {
    page: 1,
    filename: 'test.pdf',
  },
};

export const mockSearchResults = [
  mockSearchResult,
  { ...mockSearchResult, chunk_id: 'chunk-2', score: 0.87 },
  { ...mockSearchResult, chunk_id: 'chunk-3', score: 0.82 },
];

// Query response mock
export const mockQueryResponse = {
  answer: 'This is the answer to your question.',
  sources: mockSearchResults,
  mode: 'balanced',
  confidence: 0.92,
  reasoning_steps: [
    'Analyzing query complexity',
    'Searching knowledge base',
    'Generating response',
  ],
};
