"""
Get user's organization info using raw SQL
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from sqlalchemy import text

USER_ID = "c9ccb230-4b1c-435e-98e3-dd17594b4643"

with engine.connect() as conn:
    # Get user
    user_result = conn.execute(
        text("SELECT email FROM users WHERE id = :user_id"),
        {"user_id": USER_ID}
    ).first()

    if not user_result:
        print(f"User {USER_ID} not found!")
        sys.exit(1)

    print(f"\nUser: {user_result[0]}")

    # Get organizations
    org_results = conn.execute(
        text("""
            SELECT o.id, o.name, uo.role
            FROM user_organizations uo
            JOIN organizations o ON o.id = uo.organization_id
            WHERE uo.user_id = :user_id
        """),
        {"user_id": USER_ID}
    ).fetchall()

    if not org_results:
        print("No organizations found for this user!")
        sys.exit(1)

    print("\nOrganizations:")
    for org_id, org_name, role in org_results:
        print(f"  - {org_name} (ID: {org_id}, Role: {role})")
        print(f"    Use: -H \"X-Organization-ID: {org_id}\"")
