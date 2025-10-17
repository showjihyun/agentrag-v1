"""
Verification script for semantic chunking feature.

Tests:
1. SemanticChunker initialization
2. Sentence splitting
3. Paragraph splitting
4. Semantic chunking
5. Sentence chunking
6. Paragraph chunking
7. Heading chunking
8. Fixed-size chunking
9. Integration with DocumentProcessor
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        from services.semantic_chunker import SemanticChunker, get_semantic_chunker

        print("✓ SemanticChunker imported")

        from services.document_processor import DocumentProcessor

        print("✓ DocumentProcessor imported")

        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_semantic_chunker_init():
    """Test SemanticChunker initialization."""
    print("\nTesting SemanticChunker initialization...")

    try:
        from services.semantic_chunker import SemanticChunker, get_semantic_chunker

        # Test different strategies
        strategies = ["semantic", "sentence", "paragraph", "heading", "fixed"]

        for strategy in strategies:
            chunker = SemanticChunker(strategy=strategy, target_size=500, overlap=50)
            assert (
                chunker.strategy == strategy
            ), f"Strategy mismatch: {chunker.strategy}"
            print(f"✓ {strategy} strategy initialized")

        # Test singleton
        chunker1 = get_semantic_chunker("sentence", 500, 50)
        chunker2 = get_semantic_chunker("sentence", 500, 50)
        assert chunker1 is chunker2, "Singleton should return same instance"
        print("✓ Singleton pattern works")

        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_sentence_splitting():
    """Test sentence splitting."""
    print("\nTesting sentence splitting...")

    try:
        from services.semantic_chunker import SemanticChunker

        chunker = SemanticChunker(strategy="sentence")

        # Test English
        text_en = "This is sentence one. This is sentence two! Is this sentence three?"
        sentences = chunker._split_sentences(text_en)
        assert (
            len(sentences) >= 3
        ), f"Expected at least 3 sentences, got {len(sentences)}"
        print(f"✓ English sentence splitting: {len(sentences)} sentences")

        # Test Korean
        text_ko = "이것은 첫 번째 문장입니다. 이것은 두 번째 문장입니다! 이것은 세 번째 문장입니까?"
        sentences_ko = chunker._split_sentences(text_ko)
        assert (
            len(sentences_ko) >= 3
        ), f"Expected at least 3 sentences, got {len(sentences_ko)}"
        print(f"✓ Korean sentence splitting: {len(sentences_ko)} sentences")

        return True
    except Exception as e:
        print(f"✗ Sentence splitting failed: {e}")
        return False


def test_paragraph_splitting():
    """Test paragraph splitting."""
    print("\nTesting paragraph splitting...")

    try:
        from services.semantic_chunker import SemanticChunker

        chunker = SemanticChunker(strategy="paragraph")

        text = """This is paragraph one.
It has multiple sentences.

This is paragraph two.
It also has multiple sentences.

This is paragraph three."""

        paragraphs = chunker._split_paragraphs(text)
        assert len(paragraphs) == 3, f"Expected 3 paragraphs, got {len(paragraphs)}"
        print(f"✓ Paragraph splitting: {len(paragraphs)} paragraphs")

        return True
    except Exception as e:
        print(f"✗ Paragraph splitting failed: {e}")
        return False


def test_sentence_chunking():
    """Test sentence-based chunking."""
    print("\nTesting sentence chunking...")

    try:
        from services.semantic_chunker import SemanticChunker

        chunker = SemanticChunker(strategy="sentence", target_size=100, overlap=20)

        text = """This is the first sentence. This is the second sentence.
This is the third sentence. This is the fourth sentence.
This is the fifth sentence. This is the sixth sentence."""

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0, "Should produce at least one chunk"
        assert all(isinstance(c, str) for c in chunks), "All chunks should be strings"

        print(f"✓ Sentence chunking: {len(chunks)} chunks")
        print(f"  Chunk sizes: {[len(c) for c in chunks]}")

        return True
    except Exception as e:
        print(f"✗ Sentence chunking failed: {e}")
        return False


def test_paragraph_chunking():
    """Test paragraph-based chunking."""
    print("\nTesting paragraph chunking...")

    try:
        from services.semantic_chunker import SemanticChunker

        chunker = SemanticChunker(strategy="paragraph", target_size=200, overlap=20)

        text = """Paragraph one has some content.
It spans multiple lines.

Paragraph two also has content.
It also spans multiple lines.

Paragraph three is here too.
With more content."""

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0, "Should produce at least one chunk"
        print(f"✓ Paragraph chunking: {len(chunks)} chunks")

        return True
    except Exception as e:
        print(f"✗ Paragraph chunking failed: {e}")
        return False


def test_heading_chunking():
    """Test heading-based chunking."""
    print("\nTesting heading chunking...")

    try:
        from services.semantic_chunker import SemanticChunker

        chunker = SemanticChunker(strategy="heading", target_size=200)

        text = """# Introduction
This is the introduction section.
It has some content.

## Background
This is the background subsection.
More content here.

# Methods
This is the methods section.
Even more content."""

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0, "Should produce at least one chunk"
        print(f"✓ Heading chunking: {len(chunks)} chunks")

        return True
    except Exception as e:
        print(f"✗ Heading chunking failed: {e}")
        return False


def test_fixed_chunking():
    """Test fixed-size chunking."""
    print("\nTesting fixed-size chunking...")

    try:
        from services.semantic_chunker import SemanticChunker

        chunker = SemanticChunker(strategy="fixed", target_size=100, overlap=20)

        text = "A" * 500  # 500 characters

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0, "Should produce at least one chunk"
        print(f"✓ Fixed-size chunking: {len(chunks)} chunks from 500 chars")

        return True
    except Exception as e:
        print(f"✗ Fixed-size chunking failed: {e}")
        return False


def test_semantic_chunking():
    """Test semantic similarity-based chunking."""
    print("\nTesting semantic chunking...")

    try:
        from services.semantic_chunker import SemanticChunker

        # This may fall back to sentence chunking if embedding model not available
        chunker = SemanticChunker(strategy="semantic", target_size=200, overlap=20)

        text = """Machine learning is a subset of artificial intelligence.
It focuses on developing algorithms that can learn from data.
Deep learning uses neural networks with multiple layers.
Neural networks are inspired by the human brain.
The weather today is sunny and warm.
Tomorrow it might rain in the afternoon."""

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0, "Should produce at least one chunk"
        print(f"✓ Semantic chunking: {len(chunks)} chunks")

        if chunker.embedding_model:
            print("  ✓ Using embedding model for semantic chunking")
        else:
            print("  ⚠ Fell back to sentence chunking (embedding model not available)")

        return True
    except Exception as e:
        print(f"✗ Semantic chunking failed: {e}")
        return False


def test_document_processor_integration():
    """Test integration with DocumentProcessor."""
    print("\nTesting DocumentProcessor integration...")

    try:
        from services.document_processor import DocumentProcessor

        # Test with different strategies
        strategies = ["sentence", "paragraph", "fixed"]

        for strategy in strategies:
            processor = DocumentProcessor(
                chunk_size=200, chunk_overlap=20, chunking_strategy=strategy
            )

            assert (
                processor.chunking_strategy == strategy
            ), f"Strategy mismatch: {processor.chunking_strategy}"
            assert (
                processor.semantic_chunker is not None
            ), "SemanticChunker should be initialized"

            print(f"✓ DocumentProcessor with {strategy} strategy")

        return True
    except Exception as e:
        print(f"✗ DocumentProcessor integration failed: {e}")
        return False


def test_config():
    """Test configuration."""
    print("\nTesting configuration...")

    try:
        from config import Settings

        settings = Settings()

        # Check if CHUNKING_STRATEGY exists
        if hasattr(settings, "CHUNKING_STRATEGY"):
            print(f"✓ CHUNKING_STRATEGY in config: {settings.CHUNKING_STRATEGY}")
        else:
            print("⚠ CHUNKING_STRATEGY not in config (using default)")

        return True
    except Exception as e:
        print(f"✗ Config check failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Semantic Chunking Feature Verification")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("SemanticChunker Init", test_semantic_chunker_init),
        ("Sentence Splitting", test_sentence_splitting),
        ("Paragraph Splitting", test_paragraph_splitting),
        ("Sentence Chunking", test_sentence_chunking),
        ("Paragraph Chunking", test_paragraph_chunking),
        ("Heading Chunking", test_heading_chunking),
        ("Fixed Chunking", test_fixed_chunking),
        ("Semantic Chunking", test_semantic_chunking),
        ("DocumentProcessor Integration", test_document_processor_integration),
        ("Configuration", test_config),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All verification tests passed!")
        print("\nNext steps:")
        print("1. Test with actual documents")
        print("2. Compare chunking strategies:")
        print("   - semantic: Best quality, slower")
        print("   - sentence: Good balance")
        print("   - paragraph: Fast, for well-structured docs")
        print("   - heading: For Markdown/structured docs")
        print("   - fixed: Fallback")
        print("3. Adjust CHUNKING_STRATEGY in .env if needed")
        print("4. Monitor chunk quality in search results")
        return 0
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
