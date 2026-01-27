"""Check document processing status and Milvus data"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from pymilvus import connections, Collection, utility
import json

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/agenticrag"
engine = create_engine(DATABASE_URL)

def check_documents():
    """Check documents in database"""
    print("\n" + "="*80)
    print("📄 CHECKING DOCUMENTS IN DATABASE")
    print("="*80)
    
    with engine.connect() as conn:
        # Get recent documents
        result = conn.execute(text("""
            SELECT id, filename, status, chunk_count, uploaded_at, 
                   milvus_collection, processing_completed_at, error_message
            FROM documents 
            ORDER BY uploaded_at DESC 
            LIMIT 5
        """))
        
        documents = result.fetchall()
        
        if not documents:
            print("❌ No documents found in database")
            return []
        
        print(f"\n✅ Found {len(documents)} recent documents:\n")
        
        doc_list = []
        for doc in documents:
            doc_dict = {
                'id': str(doc[0]),
                'filename': doc[1],
                'status': doc[2],
                'chunk_count': doc[3],
                'uploaded_at': str(doc[4]),
                'milvus_collection': doc[5],
                'processing_completed_at': str(doc[6]) if doc[6] else None,
                'error_message': doc[7]
            }
            doc_list.append(doc_dict)
            
            print(f"📄 {doc_dict['filename']}")
            print(f"   ID: {doc_dict['id']}")
            print(f"   Status: {doc_dict['status']}")
            print(f"   Chunks: {doc_dict['chunk_count']}")
            print(f"   Collection: {doc_dict['milvus_collection']}")
            print(f"   Uploaded: {doc_dict['uploaded_at']}")
            if doc_dict['error_message']:
                print(f"   ❌ Error: {doc_dict['error_message']}")
            print()
        
        return doc_list

def check_milvus_collections():
    """Check Milvus collections and data"""
    print("\n" + "="*80)
    print("🔍 CHECKING MILVUS COLLECTIONS")
    print("="*80)
    
    try:
        # Connect to Milvus
        connections.connect(alias="default", host="localhost", port="19530")
        print("✅ Connected to Milvus\n")
        
        # List all collections
        collections = utility.list_collections()
        print(f"📚 Collections found: {len(collections)}")
        
        for coll_name in collections:
            print(f"\n📦 Collection: {coll_name}")
            
            try:
                collection = Collection(coll_name)
                collection.load()
                
                # Get collection stats
                num_entities = collection.num_entities
                print(f"   Entities: {num_entities}")
                
                # Get schema
                schema = collection.schema
                print(f"   Fields: {[field.name for field in schema.fields]}")
                
                # Sample some data
                if num_entities > 0:
                    results = collection.query(
                        expr="",
                        output_fields=["document_id", "text"],
                        limit=3
                    )
                    
                    print(f"   Sample data ({len(results)} items):")
                    for i, result in enumerate(results, 1):
                        text_preview = result.get('text', '')[:100] + '...' if result.get('text') else 'N/A'
                        print(f"      {i}. Doc ID: {result.get('document_id', 'N/A')}")
                        print(f"         Text: {text_preview}")
                
            except Exception as e:
                print(f"   ❌ Error loading collection: {e}")
        
        connections.disconnect("default")
        return collections
        
    except Exception as e:
        print(f"❌ Failed to connect to Milvus: {e}")
        return []

def check_knowledgebase_documents(kb_id="008dba88-5b3a-45f7-9b9e-b9af54bd7637"):
    """Check documents in specific knowledgebase"""
    print("\n" + "="*80)
    print(f"📚 CHECKING KNOWLEDGEBASE: {kb_id}")
    print("="*80)
    
    with engine.connect() as conn:
        # Check if knowledgebase exists
        kb_result = conn.execute(text("""
            SELECT id, name, milvus_collection_name, chunk_size, chunk_overlap
            FROM knowledge_bases
            WHERE id = :kb_id
        """), {"kb_id": kb_id})
        
        kb = kb_result.fetchone()
        
        if not kb:
            print(f"❌ Knowledgebase {kb_id} not found")
            return
        
        print(f"\n✅ Knowledgebase: {kb[1]}")
        print(f"   Collection: {kb[2]}")
        print(f"   Chunk size: {kb[3]}")
        print(f"   Chunk overlap: {kb[4]}\n")
        
        # Check documents in this knowledgebase
        doc_result = conn.execute(text("""
            SELECT d.id, d.filename, d.status, d.chunk_count, d.milvus_collection
            FROM knowledgebase_documents kd
            JOIN documents d ON kd.document_id = d.id
            WHERE kd.knowledgebase_id = :kb_id
            AND kd.removed_at IS NULL
            ORDER BY kd.added_at DESC
        """), {"kb_id": kb_id})
        
        docs = doc_result.fetchall()
        
        if not docs:
            print("❌ No documents found in this knowledgebase")
            return
        
        print(f"📄 Documents in knowledgebase: {len(docs)}\n")
        
        for doc in docs:
            print(f"   • {doc[1]}")
            print(f"     Status: {doc[2]}, Chunks: {doc[3]}, Collection: {doc[4]}")

def main():
    print("\n" + "="*80)
    print("🔍 DOCUMENT PROCESSING DIAGNOSTIC TOOL")
    print("="*80)
    
    # 1. Check documents in database
    documents = check_documents()
    
    # 2. Check Milvus collections
    collections = check_milvus_collections()
    
    # 3. Check specific knowledgebase
    check_knowledgebase_documents()
    
    print("\n" + "="*80)
    print("✅ DIAGNOSTIC COMPLETE")
    print("="*80)
    
    # Summary
    print("\n📊 SUMMARY:")
    print(f"   Documents in DB: {len(documents)}")
    print(f"   Milvus collections: {len(collections)}")
    
    # Check for issues
    issues = []
    
    for doc in documents:
        if doc['status'] != 'completed':
            issues.append(f"Document '{doc['filename']}' status is '{doc['status']}'")
        if doc['chunk_count'] == 0:
            issues.append(f"Document '{doc['filename']}' has 0 chunks")
        if not doc['milvus_collection']:
            issues.append(f"Document '{doc['filename']}' has no Milvus collection")
    
    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("\n✅ No obvious issues found")
    
    print()

if __name__ == "__main__":
    main()
