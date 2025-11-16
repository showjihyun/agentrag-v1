"""
Test script to check workflow structure in database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
import json

def check_workflow_structure():
    engine = create_engine(str(settings.DATABASE_URL))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        from backend.db.models import Workflow
        
        # Get the latest workflow
        workflow = session.query(Workflow).order_by(Workflow.created_at.desc()).first()
        
        if not workflow:
            print("❌ No workflows found in database")
            return
        
        print(f"✅ Found workflow: {workflow.name} (ID: {workflow.id})")
        print(f"\nGraph Definition:")
        print(json.dumps(workflow.graph_definition, indent=2))
        
        # Analyze nodes
        nodes = workflow.graph_definition.get('nodes', [])
        print(f"\n📊 Node Analysis ({len(nodes)} nodes):")
        
        for i, node in enumerate(nodes, 1):
            node_type = node.get('type') or node.get('node_type')
            config_type = node.get('configuration', {}).get('type')
            
            print(f"\nNode {i}:")
            print(f"  ID: {node.get('id')}")
            print(f"  node_type: {node_type}")
            print(f"  configuration.type: {config_type}")
            
            # Determine effective type
            if node_type == "control" and config_type:
                effective_type = config_type
            else:
                effective_type = node_type or config_type
            
            print(f"  → Effective type: {effective_type}")
            
            # Check if it's a start node
            is_start = effective_type == "start" or (effective_type and effective_type.startswith("trigger"))
            print(f"  → Is start/trigger: {is_start}")
        
    finally:
        session.close()

if __name__ == "__main__":
    check_workflow_structure()
