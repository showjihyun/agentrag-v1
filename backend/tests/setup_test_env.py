"""
Script to set up and verify the test environment.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

# Load test environment
test_env_path = backend_dir / ".env.test"
if test_env_path.exists():
    load_dotenv(test_env_path, override=True)

from config import settings
from backend.services.milvus import MilvusManager
import redis.asyncio as redis


async def check_milvus():
    """Check Milvus connection."""
    print(f"Checking Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}...")

    try:
        manager = MilvusManager(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name="test_connection",
        )

        await manager.connect()
        print("✓ Milvus connection successful")
        await manager.disconnect()
        return True
    except Exception as e:
        print(f"✗ Milvus connection failed: {e}")
        return False


async def check_redis():
    """Check Redis connection."""
    print(f"Checking Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}...")

    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

        await client.ping()
        print("✓ Redis connection successful")
        await client.close()
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        return False


async def check_ollama():
    """Check Ollama connection (if using Ollama)."""
    if settings.LLM_PROVIDER != "ollama":
        print(f"Skipping Ollama check (using {settings.LLM_PROVIDER})")
        return True

    print(f"Checking Ollama at {settings.OLLAMA_BASE_URL}...")

    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5.0
            )

            if response.status_code == 200:
                models = response.json().get("models", [])
                print(
                    f"✓ Ollama connection successful ({len(models)} models available)"
                )

                # Check if configured model is available
                model_names = [m.get("name", "") for m in models]
                if settings.LLM_MODEL in model_names or any(
                    settings.LLM_MODEL in name for name in model_names
                ):
                    print(f"✓ Model '{settings.LLM_MODEL}' is available")
                else:
                    print(
                        f"⚠ Model '{settings.LLM_MODEL}' not found. Available models: {', '.join(model_names)}"
                    )
                    print(f"  Run: ollama pull {settings.LLM_MODEL}")

                return True
            else:
                print(f"✗ Ollama returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"✗ Ollama connection failed: {e}")
        print("  Make sure Ollama is running: https://ollama.ai")
        return False


async def setup_test_collections():
    """Set up test collections in Milvus."""
    print("\nSetting up test collections...")

    try:
        # Document collection
        doc_manager = MilvusManager(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_COLLECTION_NAME,
        )

        await doc_manager.connect()

        if await doc_manager.collection_exists():
            print(f"Dropping existing collection: {settings.MILVUS_COLLECTION_NAME}")
            await doc_manager.drop_collection()

        print(f"Creating collection: {settings.MILVUS_COLLECTION_NAME}")
        await doc_manager.create_collection(dimension=384)
        print("✓ Document collection created")

        await doc_manager.disconnect()

        # LTM collection
        ltm_manager = MilvusManager(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_LTM_COLLECTION_NAME,
        )

        await ltm_manager.connect()

        if await ltm_manager.collection_exists():
            print(
                f"Dropping existing collection: {settings.MILVUS_LTM_COLLECTION_NAME}"
            )
            await ltm_manager.drop_collection()

        print(f"Creating collection: {settings.MILVUS_LTM_COLLECTION_NAME}")
        await ltm_manager.create_collection(dimension=384)
        print("✓ LTM collection created")

        await ltm_manager.disconnect()

        return True
    except Exception as e:
        print(f"✗ Failed to set up collections: {e}")
        return False


async def clear_redis():
    """Clear Redis test database."""
    print("\nClearing Redis test database...")

    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

        await client.flushdb()
        print("✓ Redis test database cleared")
        await client.close()
        return True
    except Exception as e:
        print(f"✗ Failed to clear Redis: {e}")
        return False


async def main():
    """Main setup function."""
    print("=" * 60)
    print("Test Environment Setup")
    print("=" * 60)
    print()

    # Check connections
    milvus_ok = await check_milvus()
    redis_ok = await check_redis()
    ollama_ok = await check_ollama()

    if not (milvus_ok and redis_ok):
        print("\n" + "=" * 60)
        print("ERROR: Required services are not available")
        print("=" * 60)
        print("\nTo start test services, run:")
        print("  docker-compose -f docker-compose.test.yml up -d")
        sys.exit(1)

    # Set up test environment
    collections_ok = await setup_test_collections()
    redis_clear_ok = await clear_redis()

    print("\n" + "=" * 60)
    if collections_ok and redis_clear_ok:
        print("✓ Test environment is ready!")
        print("=" * 60)
        print("\nYou can now run tests with:")
        print("  pytest backend/tests/")
        print("  pytest backend/tests/e2e/  # End-to-end tests only")
        sys.exit(0)
    else:
        print("✗ Test environment setup incomplete")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
