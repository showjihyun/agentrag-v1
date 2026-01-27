"""Test Milvus connection"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pymilvus import connections, utility

def test_milvus():
    try:
        # Connect to Milvus
        connections.connect(
            alias="default",
            host="localhost",
            port="19530"
        )
        
        print("✅ Successfully connected to Milvus")
        
        # List collections
        collections = utility.list_collections()
        print(f"📚 Collections: {collections}")
        
        # Disconnect
        connections.disconnect("default")
        print("✅ Disconnected from Milvus")
        
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Milvus: {e}")
        return False

if __name__ == "__main__":
    success = test_milvus()
    sys.exit(0 if success else 1)
