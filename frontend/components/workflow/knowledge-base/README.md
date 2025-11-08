# Knowledge Base UI Components

This directory contains UI components for integrating Knowledge Base functionality into workflows.

## Components

### KnowledgeBaseSelector
Dropdown selector for choosing Milvus collections.

**Props:**
- `value?: string` - Selected collection name
- `onChange: (value: string) => void` - Callback when selection changes
- `disabled?: boolean` - Disable the selector

**Usage:**
```tsx
<KnowledgeBaseSelector
  value={selectedCollection}
  onChange={setSelectedCollection}
/>
```

### DocumentBrowser
Browse and search documents in the knowledge base.

**Props:**
- `onSelectDocument?: (documentId: string) => void` - Callback when document is selected

**Features:**
- Search documents by name or author
- Filter by file type
- View document metadata
- Expandable document details

**Usage:**
```tsx
<DocumentBrowser
  onSelectDocument={(docId) => console.log('Selected:', docId)}
/>
```

### MetadataFilterUI
Visual editor for creating metadata filters.

**Props:**
- `value?: string` - JSON string of filters
- `onChange: (value: string) => void` - Callback with updated JSON
- `disabled?: boolean` - Disable editing

**Supported Fields:**
- Author
- Language
- File Type
- Keywords
- Creation Date
- Upload Date

**Operators:**
- String fields: Equals, Contains
- Number fields: Equals, Greater than, Less than, Greater or equal, Less or equal

**Usage:**
```tsx
<MetadataFilterUI
  value={filtersJson}
  onChange={setFiltersJson}
/>
```

### SearchPreview
Preview search results before executing workflow.

**Props:**
- `query: string` - Search query
- `topK?: number` - Number of results (default: 5)
- `filters?: string` - JSON string of metadata filters

**Features:**
- Execute preview search
- Display results with scores
- Show document metadata
- Highlight keywords

**Usage:**
```tsx
<SearchPreview
  query="machine learning"
  topK={5}
  filters='{"author": "John Doe"}'
/>
```

### KnowledgeBaseInput (SubBlock)
Comprehensive configuration component for Knowledge Base blocks.

**Props:**
- `id: string` - SubBlock ID
- `title: string` - Display title
- `value?: object` - Configuration value
- `onChange: (value: any) => void` - Callback with updated config
- `required?: boolean` - Mark as required
- `disabled?: boolean` - Disable editing
- `error?: string` - Validation error message

**Configuration Object:**
```typescript
{
  collection?: string;    // Milvus collection name
  query?: string;         // Search query (supports {{variables}})
  topK?: number;          // Number of results
  filters?: string;       // JSON metadata filters
}
```

**Usage:**
```tsx
<KnowledgeBaseInput
  id="kb_config"
  title="Knowledge Base Configuration"
  value={kbConfig}
  onChange={setKbConfig}
  required
/>
```

## Integration with SubBlockRenderer

The `KnowledgeBaseInput` component is integrated into the `SubBlockRenderer` as a new sub-block type:

```typescript
// In block definition (backend)
{
  id: "kb_config",
  type: "knowledge-base",
  title: "Knowledge Base Configuration",
  required: true
}

// Automatically rendered by SubBlockRenderer
<SubBlockRenderer
  subBlocks={block.sub_blocks}
  values={values}
  onChange={handleChange}
/>
```

## API Endpoints

The components interact with these backend endpoints:

### GET /api/knowledge-base/collections
Get available Milvus collections.

**Response:**
```json
{
  "collections": [
    {
      "name": "documents",
      "num_entities": 1234,
      "loaded": true
    }
  ]
}
```

### GET /api/knowledge-base/documents
List documents in knowledge base.

**Query Parameters:**
- `limit?: number` - Max documents (default: 100)
- `offset?: number` - Pagination offset (default: 0)

**Response:**
```json
{
  "documents": [
    {
      "document_id": "uuid",
      "document_name": "example.pdf",
      "file_type": "pdf",
      "chunk_count": 42,
      "author": "John Doe",
      "language": "en",
      "upload_date": 1234567890
    }
  ],
  "total": 1
}
```

### POST /api/knowledge-base/search
Search knowledge base.

**Request:**
```json
{
  "query": "machine learning",
  "top_k": 5,
  "filters": {
    "author": "John Doe",
    "language": "en"
  },
  "ranking_method": "score",
  "include_metadata": true
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "chunk_id",
      "text": "...",
      "score": 0.95,
      "document_name": "example.pdf",
      "chunk_index": 0,
      "metadata": {
        "author": "John Doe",
        "keywords": "ML, AI",
        "language": "en"
      }
    }
  ],
  "count": 5,
  "query": "machine learning"
}
```

## Styling

Components use Tailwind CSS classes and follow the application's design system:

- Primary color: Blue (#3B82F6)
- Success color: Green (#10B981)
- Error color: Red (#EF4444)
- Gray scale for neutral elements

## Accessibility

All components include:
- Proper ARIA labels
- Keyboard navigation support
- Focus indicators
- Screen reader friendly text
- Error message announcements

## Testing

Test files are located in `frontend/__tests__/workflow/knowledge-base/`:

- `KnowledgeBaseSelector.test.tsx`
- `DocumentBrowser.test.tsx`
- `MetadataFilterUI.test.tsx`
- `SearchPreview.test.tsx`
- `KnowledgeBaseInput.test.tsx`

Run tests:
```bash
npm test -- knowledge-base
```

## Future Enhancements

- [ ] Real-time search suggestions
- [ ] Advanced filter builder with AND/OR logic
- [ ] Document preview in browser
- [ ] Bulk document operations
- [ ] Collection management UI
- [ ] Search analytics and insights
