"""
Setup Test Data for VibeDocs
Creates test organization and user for end-to-end testing

Uses raw SQL to avoid ORM relationship resolution issues
"""

import sys
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


def setup_test_data():
    """Create test organization and user using raw SQL"""

    print("========================================")
    print("Setting Up Test Data")
    print("========================================")
    print()

    # Create engine directly
    engine = create_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Generate UUIDs
            org_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())

            # Check if test org already exists
            result = conn.execute(text(
                "SELECT id, name FROM organizations WHERE name = 'test-org'"
            ))
            existing_org = result.fetchone()

            if existing_org:
                print(f"[INFO] Test organization already exists")
                org_id = str(existing_org[0])
            else:
                # Create test organization
                conn.execute(text(
                    "INSERT INTO organizations (id, name, display_name, created_at) "
                    "VALUES (:id, :name, :display_name, NOW())"
                ), {
                    "id": org_id,
                    "name": "test-org",
                    "display_name": "Test Organization"
                })
                conn.commit()
                print(f"[OK] Created test organization")

            # Check if test user already exists
            result = conn.execute(text(
                "SELECT id, email FROM users WHERE email = 'test@example.com'"
            ))
            existing_user = result.fetchone()

            if existing_user:
                print(f"[INFO] Test user already exists")
                user_id = str(existing_user[0])
            else:
                # Create test user
                conn.execute(text(
                    "INSERT INTO users (id, email, full_name, is_active, created_at) "
                    "VALUES (:id, :email, :full_name, TRUE, NOW())"
                ), {
                    "id": user_id,
                    "email": "test@example.com",
                    "full_name": "Test User"
                })
                conn.commit()
                print(f"[OK] Created test user")

            print()
            print("========================================")
            print("Test Data Ready")
            print("========================================")
            print()
            print(f"Organization ID: {org_id}")
            print(f"Organization Name: test-org")
            print()
            print(f"User ID: {user_id}")
            print(f"User Email: test@example.com")
            print()
            print("Use these IDs for testing:")
            print(f"  X-Organization-ID: {org_id}")
            print()
            print("Save these values - you'll need them for API calls!")
            print()

            # Save to file for easy access
            with open('test_credentials.txt', 'w') as f:
                f.write(f"Organization ID: {org_id}\n")
                f.write(f"User ID: {user_id}\n")
                f.write(f"\n")
                f.write(f"Use in curl commands:\n")
                f.write(f'  -H "X-Organization-ID: {org_id}"\n')

            print("[OK] Credentials saved to: backend/test_credentials.txt")
            print()

            return True, org_id, user_id

    except IntegrityError as e:
        print(f"[ERROR] Database integrity error: {e}")
        return False, None, None
    except Exception as e:
        print(f"[ERROR] Failed to create test data: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None
    finally:
        engine.dispose()


if __name__ == "__main__":
    success, org_id, user_id = setup_test_data()
    sys.exit(0 if success else 1)
