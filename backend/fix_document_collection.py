"""Fix documents with missing milvus_collection field"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/agenticrag"
engine = create_engine(DATABASE_URL)

def fix_document_collections():
    """Update documents with their knowledgebase's milvus collection"""
    
    with engine.connect() as conn:
        # Find documents without milvus_collection but in a knowledgebase
        result = conn.execute(text("""
            SELECT 
                d.id as document_id,
                d.filename,
                kb.id as kb_id,
                kb.name as kb_name,
                kb.milvus_collection_name
            FROM documents d
            JOIN knowledgebase_documents kd ON d.id = kd.document_id
            JOIN knowledge_bases kb ON kd.knowledgebase_id = kb.id
            WHERE d.milvus_collection IS NULL
            AND kd.removed_at IS NULL
            AND d.status = 'completed'
        """))
        
        docs_to_fix = result.fetchall()
        
        if not docs_to_fix:
            print("✅ No documents need fixing")
            return
        
        print(f"Found {len(docs_to_fix)} documents to fix:\n")
        
        for doc in docs_to_fix:
            doc_id, filename, kb_id, kb_name, collection_name = doc
            print(f"📄 {filename}")
            print(f"   KB: {kb_name}")
            print(f"   Collection: {collection_name}")
            
            # Update the document
            conn.execute(text("""
                UPDATE documents
                SET milvus_collection = :collection_name
                WHERE id = :doc_id
            """), {
                "collection_name": collection_name,
                "doc_id": doc_id
            })
            
            print(f"   ✅ Updated\n")
        
        conn.commit()
        print(f"✅ Fixed {len(docs_to_fix)} documents")

if __name__ == "__main__":
    fix_document_collections()
