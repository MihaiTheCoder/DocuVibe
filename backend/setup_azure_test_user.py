"""
Setup test user and organization on Azure database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from datetime import datetime
import uuid

# Get Azure PostgreSQL connection string from environment
DATABASE_URL = os.getenv("AZURE_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: AZURE_DATABASE_URL or DATABASE_URL environment variable not set")
    print("Set it with: export AZURE_DATABASE_URL=postgresql://user:password@host/db")
    sys.exit(1)

USER_ID = "c9ccb230-4b1c-435e-98e3-dd17594b4643"
ORG_ID = "cbd50808-75e3-45a8-80fa-86f418f41c13"

def setup_test_user():
    """Ensure test user and organization exist"""

    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:
        print("Setting up test user on Azure database...")

        # Check if user exists
        user_result = conn.execute(
            text("SELECT email FROM users WHERE id = :user_id"),
            {"user_id": USER_ID}
        ).first()

        if not user_result:
            print("Creating test user...")
            conn.execute(
                text("""
                    INSERT INTO users (id, email, name, created_at, updated_at)
                    VALUES (:user_id, :email, :name, :now, :now)
                """),
                {
                    "user_id": USER_ID,
                    "email": "test@example.com",
                    "name": "Test User",
                    "now": datetime.utcnow()
                }
            )
            print(f"  - Created user: test@example.com")
        else:
            print(f"  - User already exists: {user_result[0]}")

        # Check if organization exists
        org_result = conn.execute(
            text("SELECT name FROM organizations WHERE id = :org_id"),
            {"org_id": ORG_ID}
        ).first()

        if not org_result:
            print("Creating test organization...")
            conn.execute(
                text("""
                    INSERT INTO organizations (id, name, created_at)
                    VALUES (:org_id, :name, :now)
                """),
                {
                    "org_id": ORG_ID,
                    "name": "Test Organization",
                    "now": datetime.utcnow()
                }
            )
            print(f"  - Created organization: Test Organization")
        else:
            print(f"  - Organization already exists: {org_result[0]}")

        # Check if user is associated with organization
        existing = conn.execute(
            text("""
                SELECT 1 FROM user_organizations
                WHERE user_id = :user_id AND organization_id = :org_id
            """),
            {"user_id": USER_ID, "org_id": ORG_ID}
        ).first()

        if not existing:
            print("Adding user to organization...")
            conn.execute(
                text("""
                    INSERT INTO user_organizations (user_id, organization_id, role, invited_at, joined_at)
                    VALUES (:user_id, :org_id, 'admin', :now, :now)
                """),
                {"user_id": USER_ID, "org_id": ORG_ID, "now": datetime.utcnow()}
            )
            print(f"  - User added to organization as admin")
        else:
            print("  - User already associated with organization")

        print("\n[SUCCESS] Test user setup complete on Azure!")
        print(f"\nYou can now use:")
        print(f'  -H "X-Organization-ID: {ORG_ID}"')

if __name__ == "__main__":
    try:
        setup_test_user()
    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
