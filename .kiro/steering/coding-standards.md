---
inclusion: manual
---

# Coding Standards

## Python (Backend)

### Style
- PEP 8 compliant
- 120 character line length
- Type hints required for all functions
- Docstrings for public functions (Google style)

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

### Import Order
```python
# Standard library
import os
from typing import Optional

# Third-party
from fastapi import FastAPI
from pydantic import BaseModel

# Local
from backend.config import settings
from backend.services.embedding import EmbeddingService
```

### Error Handling
```python
from backend.exceptions import APIException

# Raise with context
raise APIException(
    status_code=400,
    error_code="INVALID_QUERY",
    message="Query cannot be empty"
)

# Use specific exceptions
from backend.services.agent_builder.shared.errors import (
    WorkflowNotFoundError,
    ExecutionFailedError,
)
```

### Async Patterns
```python
# Prefer async/await
async def get_document(document_id: str) -> Document:
    return await repository.get(document_id)

# Use asyncio.gather for parallel operations
results = await asyncio.gather(
    fetch_documents(),
    fetch_embeddings(),
)
```

### Caching
```python
from backend.core.cache_decorators import cached_medium, invalidate_cache

@cached_medium(namespace="documents")
async def get_document(document_id: str):
    ...

@invalidate_cache(namespace="documents")
async def update_document(document_id: str, data: dict):
    ...
```

## TypeScript (Frontend)

### Style
- Strict mode enabled
- 100 character line length
- Functional components with hooks
- Named exports preferred

### Naming
- Components: `PascalCase.tsx`
- Utilities: `camelCase.ts`
- Hooks: `use*.ts`
- Types/Interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

### Import Order
```typescript
// React/Next
import { useState, useEffect } from 'react';
import Link from 'next/link';

// Third-party
import { useQuery } from '@tanstack/react-query';

// Local components
import { Button } from '@/components/ui/button';

// Local utilities
import { api } from '@/lib/api-client';
import { queryKeys } from '@/lib/queryClient';
```

### Component Structure
```typescript
// Props interface
interface MyComponentProps {
  title: string;
  onSubmit: (data: FormData) => void;
}

// Component
export function MyComponent({ title, onSubmit }: MyComponentProps) {
  // Hooks first
  const [state, setState] = useState('');
  const { data, isLoading } = useQuery(...);
  
  // Handlers
  const handleSubmit = useCallback(() => {
    onSubmit(data);
  }, [data, onSubmit]);
  
  // Early returns
  if (isLoading) return <Loading />;
  
  // Render
  return (
    <div>
      <h1>{title}</h1>
      ...
    </div>
  );
}
```

### Error Handling
```typescript
import { APIError, getErrorMessage, ErrorHandler } from '@/lib/errors';

try {
  await api.uploadDocument(file);
} catch (error) {
  const errorInfo = ErrorHandler.handle(error);
  toast({
    title: errorInfo.title,
    description: errorInfo.description,
    variant: errorInfo.variant,
  });
}
```

### React Query Usage
```typescript
import { queryKeys, queryOptions, STALE_TIMES } from '@/lib/queryClient';

// Use query keys factory
const { data } = useQuery({
  queryKey: queryKeys.documents.list(),
  queryFn: fetchDocuments,
  ...queryOptions.list,
});

// Prefetch on hover
const prefetchProps = prefetchOnHover(() => 
  routePrefetchers.workflowDetail(id, fetchWorkflow)
);
```

## Testing

### Backend Tests
```python
# Use fixtures
def test_create_document(client, sample_document_data, auth_client):
    response = auth_client.post("/api/documents", json=sample_document_data)
    assert_valid_response(response, 201)

# Use assertion helpers
from backend.tests.utils.assertion_helpers import (
    assert_valid_response,
    assert_contains_keys,
)
```

### Frontend Tests
```typescript
// Use custom render with providers
import { render, screen } from '@/__tests__/utils/test-utils';
import { mockDocument } from '@/__tests__/utils/mock-data';

test('renders document', () => {
  render(<DocumentCard document={mockDocument} />);
  expect(screen.getByText(mockDocument.filename)).toBeInTheDocument();
});
```

## Git Commits

### Format
```
type(scope): description

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Examples
```
feat(agent-builder): add workflow execution streaming
fix(documents): handle large file uploads correctly
refactor(api): organize endpoints by domain
```
