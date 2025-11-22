"""Check tools table schema."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, inspect
from config import settings

engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)

print("\n" + "="*60)
print("Tools Table Schema")
print("="*60)

columns = inspector.get_columns('tools')
for col in columns:
    print(f"{col['name']}: {col['type']}")

print("="*60)
