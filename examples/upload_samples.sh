#!/bin/bash
# Upload sample documents to the Agentic RAG system

BASE_URL="http://localhost:8000"
DOCS_DIR="sample_documents"

echo "=========================================="
echo "Uploading Sample Documents"
echo "=========================================="
echo ""

# Check if API is available
echo "Checking API health..."
if ! curl -s -f "${BASE_URL}/api/health" > /dev/null; then
    echo "✗ Error: API is not available at ${BASE_URL}"
    echo "  Please start the backend server first:"
    echo "  cd backend && uvicorn main:app --reload"
    exit 1
fi

echo "✓ API is healthy"
echo ""

# Change to docs directory
cd "${DOCS_DIR}" || exit 1

# Upload each document
for file in *.txt; do
    if [ -f "$file" ]; then
        echo "Uploading: $file"
        response=$(curl -s -X POST "${BASE_URL}/api/documents/upload" \
            -F "file=@${file}")
        
        # Check if upload was successful
        if echo "$response" | grep -q "document_id"; then
            doc_id=$(echo "$response" | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)
            chunk_count=$(echo "$response" | grep -o '"chunk_count":[0-9]*' | cut -d':' -f2)
            echo "  ✓ Uploaded successfully"
            echo "    Document ID: $doc_id"
            echo "    Chunks: $chunk_count"
        else
            echo "  ✗ Upload failed"
            echo "    Response: $response"
        fi
        echo ""
    fi
done

# List all documents
echo "=========================================="
echo "Uploaded Documents"
echo "=========================================="
curl -s "${BASE_URL}/api/documents" | python3 -m json.tool

echo ""
echo "=========================================="
echo "Upload Complete!"
echo "=========================================="
echo ""
echo "You can now test queries:"
echo "  cd .."
echo "  python3 test_queries.py interactive"
echo ""
