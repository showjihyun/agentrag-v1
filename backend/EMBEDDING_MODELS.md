# Embedding Models Configuration

## Overview

The system now automatically detects and uses the correct embedding dimension for each model. When creating a knowledgebase, the embedding dimension is automatically determined based on the selected model.

## Supported Models

### Korean Optimized Models (Recommended)

| Model | Dimension | Description |
|-------|-----------|-------------|
| `jhgan/ko-sroberta-multitask` | 768 | **BEST** for Korean - specialized model |
| `BM-K/KoSimCSE-roberta` | 768 | Excellent for Korean semantic similarity |
| `BM-K/KoSimCSE-bert-multitask` | 768 | Korean BERT-based model |

### Multilingual Models

| Model | Dimension | Description |
|-------|-----------|-------------|
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | 768 | High quality multilingual |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 | Faster multilingual |
| `sentence-transformers/distiluse-base-multilingual-cased-v2` | 512 | Balanced speed/quality |

### OpenAI Models

| Model | Dimension | Description |
|-------|-----------|-------------|
| `text-embedding-3-small` | 1536 | OpenAI's small embedding model |
| `text-embedding-3-large` | 3072 | OpenAI's large embedding model |
| `text-embedding-ada-002` | 1536 | Legacy OpenAI model |

### English Only Models (Not Recommended for Korean)

| Model | Dimension | Description |
|-------|-----------|-------------|
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Fast but English only |
| `sentence-transformers/all-mpnet-base-v2` | 768 | High quality English only |

## How It Works

### 1. Knowledgebase Creation

When creating a knowledgebase:

```python
# The system automatically determines the dimension
kb = knowledgebase_service.create_knowledgebase(
    user_id=user_id,
    kb_data=KnowledgebaseCreate(
        name="My KB",
        embedding_model="jhgan/ko-sroberta-multitask"  # 768d auto-detected
    )
)
```

### 2. Document Processing

When uploading documents:

```python
# Uses the KB's embedding model and dimension
documents = await knowledgebase_service.add_documents(
    kb_id=kb_id,
    files=files
)
# Automatically uses jhgan/ko-sroberta-multitask with 768d
```

### 3. Search

When searching:

```python
# Uses the KB's embedding model and dimension
results = await knowledgebase_service.search_knowledgebase(
    kb_id=kb_id,
    query="search query"
)
# Automatically uses the correct model and dimension
```

## Configuration

### Adding New Models

To add support for a new model, update `backend/config/llm.py`:

```python
EMBEDDING_MODEL_DIMENSIONS = {
    # ... existing models ...
    "your-new-model": 512,  # Add your model dimension
}
```

### Default Model

Set the default model in `.env`:

```bash
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
```

## Database Schema

The `knowledge_bases` table now includes:

- `embedding_model`: Name of the embedding model (e.g., "jhgan/ko-sroberta-multitask")
- `embedding_dimension`: Dimension of the embedding vectors (e.g., 768)

## Migration

Existing knowledgebases have been automatically updated with the correct dimensions based on their embedding models.

## Best Practices

1. **Choose the right model for your language**:
   - Korean content: Use `jhgan/ko-sroberta-multitask` (768d)
   - Multilingual: Use `paraphrase-multilingual-mpnet-base-v2` (768d)
   - English only: Use `all-mpnet-base-v2` (768d)

2. **Consistency**: Once a knowledgebase is created with a model, all documents use that model

3. **Performance vs Quality**:
   - Higher dimensions (768, 1536) = Better quality, slower
   - Lower dimensions (384, 512) = Faster, lower quality

4. **Storage**: Higher dimensions require more storage in Milvus

## Troubleshooting

### Dimension Mismatch Error

If you see "Query embedding dimension X does not match expected Y":

1. Check the knowledgebase's `embedding_dimension` in the database
2. Ensure the search is using the same model as the knowledgebase
3. The system should handle this automatically now

### Adding Documents Fails

If document upload fails:

1. Check logs for embedding errors
2. Verify the embedding model is accessible
3. Ensure sufficient memory for the model

## API Response

The knowledgebase response now includes the dimension:

```json
{
  "id": "...",
  "name": "My KB",
  "embedding_model": "jhgan/ko-sroberta-multitask",
  "embedding_dimension": 768,
  ...
}
```
