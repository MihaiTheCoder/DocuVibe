"""
Add test user to organization
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text
from datetime import datetime

USER_ID = "c9ccb230-4b1c-435e-98e3-dd17594b4643"
ORG_ID = "cbd50808-75e3-45a8-80fa-86f418f41c13"

with engine.connect() as conn:
    # Check if organization exists
    org_result = conn.execute(
        text("SELECT name FROM organizations WHERE id = :org_id"),
        {"org_id": ORG_ID}
    ).first()

    if not org_result:
        print(f"Organization {ORG_ID} not found!")
        sys.exit(1)

    print(f"Organization: {org_result[0]}")

    # Check if already associated
    existing = conn.execute(
        text("""
            SELECT 1 FROM user_organizations
            WHERE user_id = :user_id AND organization_id = :org_id
        """),
        {"user_id": USER_ID, "org_id": ORG_ID}
    ).first()

    if existing:
        print(f"User already associated with organization!")
    else:
        # Add association
        conn.execute(
            text("""
                INSERT INTO user_organizations (user_id, organization_id, role, invited_at, joined_at)
                VALUES (:user_id, :org_id, 'admin', :now, :now)
            """),
            {"user_id": USER_ID, "org_id": ORG_ID, "now": datetime.utcnow()}
        )
        conn.commit()
        print(f"User added to organization as admin!")

    print(f"\nYou can now use:")
    print(f'  -H "X-Organization-ID: {ORG_ID}"')
