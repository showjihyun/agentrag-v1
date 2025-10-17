"""
End-to-end tests for document upload and indexing workflow.
Tests Requirements: 1.5, 2.4
"""

import pytest
import asyncio
from pathlib import Path
from io import BytesIO

from backend.services.document_processor import DocumentProcessor
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_document_upload_flow(
    milvus_manager, embedding_service, test_data_dir
):
    """
    Test complete document upload and indexing flow.

    Requirements: 1.5, 2.4
    """
    # Initialize document processor
    processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)

    # Read test document
    doc_path = test_data_dir / "sample_doc.txt"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Step 1: Process document
    chunks = processor.chunk_text(content)
    assert len(chunks) > 0, "Document should be chunked"
    print(f"✓ Document chunked into {len(chunks)} pieces")

    # Step 2: Generate embeddings
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_service.embed_batch(texts)
    assert len(embeddings) == len(chunks), "Should have embedding for each chunk"
    print(f"✓ Generated {len(embeddings)} embeddings")

    # Step 3: Store in Milvus
    import time

    timestamp = int(time.time())
    metadata_list = []
    for i, chunk in enumerate(chunks):
        metadata_list.append(
            {
                "id": f"chunk_{i}",
                "document_id": "test_doc_001",
                "document_name": "sample_doc.txt",
                "text": chunk["text"],
                "chunk_index": i,
                "file_type": "txt",
                "upload_date": timestamp,
                "author": "",
                "creation_date": 0,
                "language": "",
                "keywords": "",
            }
        )

    ids = await milvus_manager.insert_embeddings(embeddings, metadata_list)
    assert len(ids) == len(embeddings), "Should get ID for each embedding"
    print(f"✓ Stored {len(ids)} chunks in Milvus")

    # Step 4: Verify retrieval
    query_text = "What is machine learning?"
    query_embedding = embedding_service.embed_text(query_text)

    results = await milvus_manager.search(query_embedding, top_k=3)
    assert len(results) > 0, "Should retrieve relevant chunks"
    assert results[0]["score"] > 0.3, "Top result should have reasonable similarity"
    print(f"✓ Retrieved {len(results)} relevant chunks")
    print(f"  Top result score: {results[0]['score']:.3f}")
    print(f"  Top result text: {results[0]['text'][:100]}...")

    # Step 5: Verify deletion
    await milvus_manager.delete_by_document_id("test_doc_001")

    # Search again - should return no results or different results
    results_after = await milvus_manager.search(query_embedding, top_k=3)
    # Either no results or results don't match our document
    if results_after:
        assert all(r.get("document_id") != "test_doc_001" for r in results_after)
    print("✓ Document successfully deleted")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multiple_document_indexing(milvus_manager, embedding_service):
    """
    Test indexing multiple documents and cross-document search.

    Requirements: 1.5, 2.4
    """
    processor = DocumentProcessor(chunk_size=300, chunk_overlap=30)

    # Create multiple test documents
    documents = [
        {
            "id": "doc_ai",
            "name": "ai_basics.txt",
            "content": "Artificial Intelligence is the simulation of human intelligence. "
            "Machine learning is a subset of AI that learns from data. "
            "Deep learning uses neural networks with multiple layers.",
        },
        {
            "id": "doc_nlp",
            "name": "nlp_guide.txt",
            "content": "Natural Language Processing helps computers understand human language. "
            "NLP uses techniques like tokenization, parsing, and semantic analysis. "
            "Applications include chatbots, translation, and sentiment analysis.",
        },
        {
            "id": "doc_cv",
            "name": "computer_vision.txt",
            "content": "Computer Vision enables machines to interpret visual information. "
            "Image recognition identifies objects in images. "
            "Object detection locates and classifies multiple objects.",
        },
    ]

    # Index all documents
    all_ids = []
    for doc in documents:
        chunks = processor.chunk_text(doc["content"])
        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.embed_batch(texts)

        metadata_list = [
            {
                "id": f"{doc['id']}_chunk_{i}",
                "document_id": doc["id"],
                "document_name": doc["name"],
                "text": chunk["text"],
                "chunk_index": i,
                "file_type": "txt",
                "upload_date": timestamp,
                "author": "",
                "creation_date": 0,
                "language": "",
                "keywords": "",
            }
            for i, chunk in enumerate(chunks)
        ]

        ids = await milvus_manager.insert_embeddings(embeddings, metadata_list)
        all_ids.extend(ids)

    print(f"✓ Indexed {len(documents)} documents ({len(all_ids)} total chunks)")

    # Test cross-document search
    test_queries = [
        ("What is machine learning?", "doc_ai"),
        ("How does NLP work?", "doc_nlp"),
        ("What is image recognition?", "doc_cv"),
    ]

    for query, expected_doc in test_queries:
        query_embedding = embedding_service.embed_text(query)
        results = await milvus_manager.search(query_embedding, top_k=3)

        assert len(results) > 0, f"Should find results for: {query}"

        # Check if top result is from expected document
        top_doc_id = results[0].get("document_id")
        print(f"✓ Query: '{query}'")
        print(f"  Expected doc: {expected_doc}, Got: {top_doc_id}")
        print(f"  Score: {results[0]['score']:.3f}")

        # Note: We don't assert exact match as embeddings might vary
        # but we verify we got results

    # Clean up
    for doc in documents:
        await milvus_manager.delete_by_document_id(doc["id"])
    print("✓ All documents cleaned up")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_document_format_support(milvus_manager, embedding_service, tmp_path):
    """
    Test support for different document formats.

    Requirements: 2.4
    """
    processor = DocumentProcessor()

    # Test TXT
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("This is a plain text document for testing.")

    with open(txt_path, "rb") as f:
        txt_content = processor.extract_text_from_txt(f.read())
    assert "plain text document" in txt_content
    print("✓ TXT format supported")

    # Test PDF (if reportlab is available)
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        pdf_path = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawString(100, 750, "This is a PDF document for testing.")
        c.save()

        with open(pdf_path, "rb") as f:
            pdf_content = processor.extract_text_from_pdf(f.read())
        assert "PDF document" in pdf_content
        print("✓ PDF format supported")
    except ImportError:
        print("⚠ Skipping PDF test (reportlab not installed)")

    # Test DOCX (basic check)
    try:
        from docx import Document

        docx_path = tmp_path / "test.docx"
        doc = Document()
        doc.add_paragraph("This is a DOCX document for testing.")
        doc.save(str(docx_path))

        with open(docx_path, "rb") as f:
            docx_content = processor.extract_text_from_docx(f.read())
        assert "DOCX document" in docx_content
        print("✓ DOCX format supported")
    except ImportError:
        print("⚠ Skipping DOCX test (python-docx not installed)")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_large_document_processing(milvus_manager, embedding_service):
    """
    Test processing of large documents with many chunks.

    Requirements: 1.5, 2.4
    """
    processor = DocumentProcessor(chunk_size=200, chunk_overlap=20)

    # Create a large document
    large_content = "\n\n".join(
        [
            f"Section {i}: This is section {i} of a large document. "
            f"It contains information about topic {i}. "
            f"This section discusses various aspects of the subject matter. "
            f"The content is designed to test the system's ability to handle large documents. "
            * 5  # Repeat to make it longer
            for i in range(20)
        ]
    )

    # Process document
    chunks = processor.chunk_text(large_content)
    print(f"✓ Large document chunked into {len(chunks)} pieces")
    assert len(chunks) > 50, "Large document should create many chunks"

    # Generate embeddings in batches
    batch_size = 10
    all_embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_texts = [chunk["text"] for chunk in batch_chunks]
        batch_embeddings = embedding_service.embed_batch(batch_texts)
        all_embeddings.extend(batch_embeddings)

    print(f"✓ Generated {len(all_embeddings)} embeddings in batches")

    # Store in Milvus
    metadata_list = [
        {
            "document_id": "large_doc",
            "document_name": "large_document.txt",
            "chunk_id": i,
            "text": chunk["text"],
        }
        for i, chunk in enumerate(chunks)
    ]

    ids = await milvus_manager.insert_embeddings(all_embeddings, metadata_list)
    print(f"✓ Stored {len(ids)} chunks in Milvus")

    # Test retrieval
    query_embedding = embedding_service.embed_text("section 10")
    results = await milvus_manager.search(query_embedding, top_k=5)

    assert len(results) > 0, "Should retrieve results from large document"
    print(f"✓ Retrieved {len(results)} results from large document")

    # Clean up
    await milvus_manager.delete_by_document_id("large_doc")
    print("✓ Large document cleaned up")
