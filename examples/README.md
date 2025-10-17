# Examples

This directory contains sample documents, test scripts, and usage examples for the Agentic RAG system.

## Contents

- **sample_documents/** - Sample documents for testing (research paper, API guide, business report)
- **upload_samples.sh** - Script to upload all sample documents
- **test_queries.py** - Python script to test queries and demonstrate capabilities

## Quick Start

### 1. Start the System

Make sure the backend and frontend are running:

```bash
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### 2. Upload Sample Documents

```bash
cd examples
chmod +x upload_samples.sh
./upload_samples.sh
```

This will upload three sample documents:
- research_paper.txt (ML/NLP research)
- api_guide.txt (API documentation)
- quarterly_report.txt (Business metrics)

### 3. Test Queries

Run the test suite:

```bash
# Non-streaming mode (faster, shows final results)
python3 test_queries.py test

# Streaming mode (shows reasoning steps in real-time)
python3 test_queries.py streaming

# Interactive mode (ask your own questions)
python3 test_queries.py interactive
```

## Test Script Usage

### Test Mode

Runs a predefined set of queries across different categories:

```bash
python3 test_queries.py test
```

Output includes:
- Health check
- Document listing
- Query results with sources
- Processing metadata

### Streaming Mode

Same as test mode but shows real-time reasoning steps:

```bash
python3 test_queries.py streaming
```

You'll see:
- [PLAN] Chain of Thought planning
- [THINK] ReAct reasoning thoughts
- [ACT] Actions being executed
- [OBS] Observations from actions
- [REFLECT] Agent's self-assessment
- [RESPONSE] Final answer with sources

### Interactive Mode

Ask your own questions:

```bash
python3 test_queries.py interactive
```

Commands:
- Type any question to get an answer
- `stream` - Toggle streaming on/off
- `quit` or `exit` - Exit interactive mode

Example session:
```
> What accuracy did the model achieve?
[RESPONSE] The machine learning model achieved an accuracy of 95.2%...

> What about the F1 score?
[RESPONSE] The F1 score is 0.94, compared to a baseline of 0.85...

> stream
Streaming mode: OFF

> What was the Q3 revenue?
Response: The Q3 2025 revenue was $45.2 million...
```

## Example Queries by Category

### Simple Fact Retrieval
- "What accuracy did the model achieve?"
- "What was the Q3 revenue?"
- "What is the F1 score?"

### Comparison Queries
- "How does the new model compare to the baseline?"
- "Compare the revenue growth to customer acquisition growth"

### List Extraction
- "What are the future work directions mentioned in the research?"
- "What challenges did the company face in Q3?"
- "List the API endpoints available"

### Procedural Queries
- "How do I authenticate with the API?"
- "What should I do if I get a rate limit error?"

### Cross-Document Analysis
- "What was the Q3 revenue and how many customers were acquired?"
- "Compare the technical improvements with business results"

### Synthesis Queries
- "Summarize the main findings from the research paper"
- "What are the key takeaways from the quarterly report?"

## Creating Your Own Test Documents

1. Create a text file with your content
2. Upload it:
   ```bash
   curl -X POST http://localhost:8000/api/documents/upload \
     -F "file=@your_document.txt"
   ```
3. Query it using the test script or web interface

## Troubleshooting

### "API is not available"

Make sure the backend is running:
```bash
cd backend
uvicorn main:app --reload
```

### "No documents found"

Upload the sample documents:
```bash
cd examples
./upload_samples.sh
```

### "Connection refused"

Check that services are running:
```bash
# Check backend
curl http://localhost:8000/api/health

# Check Milvus
docker-compose ps milvus

# Check Redis
docker-compose ps redis
```

### Slow responses

- Use a smaller LLM model (e.g., llama3.2 instead of mixtral)
- Reduce `top_k` in query options
- Check system resources (RAM, CPU)

## Advanced Usage

### Custom Query Options

```python
import requests

response = requests.post(
    'http://localhost:8000/api/query',
    json={
        'query': 'Your question here',
        'session_id': 'my_session',
        'stream': True,
        'options': {
            'max_iterations': 5,      # Limit ReAct iterations
            'top_k': 5,               # Number of documents to retrieve
            'include_reasoning': True, # Include reasoning steps
            'temperature': 0.7        # LLM temperature
        }
    }
)
```

### Batch Testing

Create a file with queries (one per line) and test them:

```python
with open('queries.txt', 'r') as f:
    queries = [line.strip() for line in f if line.strip()]

for query in queries:
    result = requests.post(
        'http://localhost:8000/api/query',
        json={'query': query, 'stream': False}
    ).json()
    print(f"Q: {query}")
    print(f"A: {result['response'][:200]}...")
    print()
```

### Performance Testing

```python
import time

start = time.time()
response = requests.post(
    'http://localhost:8000/api/query',
    json={'query': 'What accuracy did the model achieve?', 'stream': False}
)
end = time.time()

print(f"Response time: {(end - start) * 1000:.0f}ms")
```

## See Also

- [EXAMPLES.md](../EXAMPLES.md) - Detailed examples and use cases
- [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) - Complete API reference
- [README.md](../README.md) - Main project documentation
