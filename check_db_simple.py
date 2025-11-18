"""Simple check for executions in database"""
import sys
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text
from backend.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # Count executions
    result = conn.execute(text('SELECT COUNT(*) FROM agent_executions'))
    count = result.scalar()
    print(f'📊 Total executions in DB: {count}')
    
    if count > 0:
        # Get latest 5
        result = conn.execute(text('''
            SELECT id, agent_id, status, started_at 
            FROM agent_executions 
            ORDER BY started_at DESC 
            LIMIT 5
        '''))
        
        print('\n🔍 Latest executions:')
        for row in result:
            print(f'  - ID: {row[0]}')
            print(f'    Agent: {row[1]}')
            print(f'    Status: {row[2]}')
            print(f'    Started: {row[3]}')
            print()
    else:
        print('\n⚠️  No executions found!')
        print('Possible reasons:')
        print('1. Agent execute endpoint is not being called')
        print('2. Execution is not being saved to DB')
        print('3. Commit is not happening')
