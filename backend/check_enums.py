"""
Check enum values in database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Get all enum types
    result = conn.execute(text("""
        SELECT t.typname, e.enumlabel
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname IN ('conversationstatus', 'issuestatus', 'jobstatus', 'issuedifficulty')
        ORDER BY t.typname, e.enumsortorder
    """))

    current_type = None
    for typname, enumlabel in result:
        if typname != current_type:
            print(f"\n{typname}:")
            current_type = typname
        print(f"  - {enumlabel}")
