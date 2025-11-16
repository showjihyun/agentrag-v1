# Chat Components Integration Guide

## MessageSources Component

### Overview
The `MessageSources` component displays source documents used to generate AI responses, with special highlighting for Knowledge Base (KB) sources.

### Features
- Separates KB sources from general sources
- Visual distinction with colored badges
- Confidence score display
- Document metadata (name, KB, chunk index)

### Usage

#### Basic Integration
```typescript
import { MessageSources } from '@/components/chat/MessageSources';

// In your message rendering
<MessageSources sources={message.sources} />
```

#### Integration with ChatInterface

Add to `frontend/components/ChatInterface.tsx`:

```typescript
import { MessageSources } from '@/components/chat/MessageSources';

// In the message rendering section (around line 200-300)
{message.role === 'assistant' && message.sources && (
  <MessageSources sources={message.sources} className="mt-3" />
)}
```

#### Integration with MessageList

Add to `frontend/components/MessageList.tsx`:

```typescript
import { MessageSources } from '@/components/chat/MessageSources';

// In the assistant message rendering
{message.role === 'assistant' && (
  <div>
    <div className="message-content">{message.content}</div>
    {message.sources && message.sources.length > 0 && (
      <MessageSources sources={message.sources} />
    )}
  </div>
)}
```

### Props

```typescript
interface MessageSourcesProps {
  sources: Source[];
  className?: string;
}

interface Source {
  id: string;
  document_id?: string;
  document_name?: string;
  text: string;
  score: number;
  metadata?: {
    source?: string;      // "kb:uuid" for KB sources
    kb_id?: string;       // KB identifier
    kb_name?: string;     // KB display name
    chunk_index?: number; // Chunk position
  };
}
```

### Styling

The component uses Tailwind CSS and shadcn/ui components:
- KB sources: Blue badge, highlighted card
- General sources: Gray badge, standard card
- Confidence badges: Color-coded by score

### Example Response

```json
{
  "answer": "Based on your documents...",
  "sources": [
    {
      "id": "1",
      "document_name": "Product Manual.pdf",
      "text": "The product features include...",
      "score": 0.92,
      "metadata": {
        "source": "kb:abc-123",
        "kb_id": "abc-123",
        "kb_name": "Product Documentation",
        "chunk_index": 5
      }
    },
    {
      "id": "2",
      "document_name": "General Knowledge",
      "text": "Industry standards suggest...",
      "score": 0.78,
      "metadata": {
        "source": "general"
      }
    }
  ]
}
```

### Testing

```typescript
// Test with KB sources
const kbSources = [
  {
    id: '1',
    document_name: 'Test Doc',
    text: 'Test content',
    score: 0.9,
    metadata: {
      source: 'kb:test-123',
      kb_id: 'test-123',
      kb_name: 'Test KB'
    }
  }
];

<MessageSources sources={kbSources} />
```

### Troubleshooting

**Sources not showing:**
- Check if `message.sources` exists and is an array
- Verify source objects have required fields
- Check console for errors

**KB sources not highlighted:**
- Ensure `metadata.source` starts with "kb:" OR
- Ensure `metadata.kb_id` is present

**Styling issues:**
- Verify Tailwind CSS is configured
- Check shadcn/ui components are installed
- Ensure Card and Badge components are available
