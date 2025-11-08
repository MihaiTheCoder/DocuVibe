"""
Fix PostgreSQL enum types on Azure database

This script drops native PostgreSQL enum types and converts enum columns to VARCHAR.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text

# Get Azure PostgreSQL connection string from environment
DATABASE_URL = os.getenv("AZURE_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: AZURE_DATABASE_URL or DATABASE_URL environment variable not set")
    print("Set it with: export AZURE_DATABASE_URL=postgresql://user:password@host/db")
    sys.exit(1)

def fix_enums():
    """Convert enum columns to VARCHAR and drop enum types"""

    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        print("Starting enum migration on Azure database...")

        # 1. Convert processing_jobs columns
        print("Converting processing_jobs.job_type to VARCHAR...")
        conn.execute(text("""
            ALTER TABLE processing_jobs
            ALTER COLUMN job_type TYPE VARCHAR(50)
        """))

        print("Converting processing_jobs.status to VARCHAR...")
        conn.execute(text("""
            ALTER TABLE processing_jobs
            ALTER COLUMN status TYPE VARCHAR(50)
        """))

        # 2. Convert github_issues columns
        print("Converting github_issues.difficulty to VARCHAR...")
        conn.execute(text("""
            ALTER TABLE github_issues
            ALTER COLUMN difficulty TYPE VARCHAR(50)
        """))

        print("Converting github_issues.status to VARCHAR...")
        conn.execute(text("""
            ALTER TABLE github_issues
            ALTER COLUMN status TYPE VARCHAR(50)
        """))

        # 3. Convert conversations.status column
        print("Converting conversations.status to VARCHAR...")
        conn.execute(text("""
            ALTER TABLE conversations
            ALTER COLUMN status TYPE VARCHAR(50)
        """))

        # 4. Convert messages.role column
        print("Converting messages.role to VARCHAR...")
        conn.execute(text("""
            ALTER TABLE messages
            ALTER COLUMN role TYPE VARCHAR(50)
        """))

        # 5. Drop the enum types
        print("Dropping enum types...")

        try:
            conn.execute(text("DROP TYPE IF EXISTS jobtype CASCADE"))
            print("  - Dropped jobtype")
        except Exception as e:
            print(f"  - Error dropping jobtype: {e}")

        try:
            conn.execute(text("DROP TYPE IF EXISTS jobstatus CASCADE"))
            print("  - Dropped jobstatus")
        except Exception as e:
            print(f"  - Error dropping jobstatus: {e}")

        try:
            conn.execute(text("DROP TYPE IF EXISTS issuedifficulty CASCADE"))
            print("  - Dropped issuedifficulty")
        except Exception as e:
            print(f"  - Error dropping issuedifficulty: {e}")

        try:
            conn.execute(text("DROP TYPE IF EXISTS issuestatus CASCADE"))
            print("  - Dropped issuestatus")
        except Exception as e:
            print(f"  - Error dropping issuestatus: {e}")

        try:
            conn.execute(text("DROP TYPE IF EXISTS conversationstatus CASCADE"))
            print("  - Dropped conversationstatus")
        except Exception as e:
            print(f"  - Error dropping conversationstatus: {e}")

        try:
            conn.execute(text("DROP TYPE IF EXISTS messagerole CASCADE"))
            print("  - Dropped messagerole")
        except Exception as e:
            print(f"  - Error dropping messagerole: {e}")

        print("\n[SUCCESS] Enum migration completed successfully on Azure!")
        print("All enum columns are now VARCHAR(50)")

if __name__ == "__main__":
    try:
        fix_enums()
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
