"""
Get user's organization info
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.organization import Organization, UserOrganization

USER_ID = "c9ccb230-4b1c-435e-98e3-dd17594b4643"

db = SessionLocal()

try:
    user = db.query(User).filter(User.id == USER_ID).first()
    if not user:
        print(f"User {USER_ID} not found!")
        sys.exit(1)

    print(f"\nUser: {user.email}")

    user_orgs = db.query(UserOrganization).filter(
        UserOrganization.user_id == user.id
    ).all()

    if not user_orgs:
        print("No organizations found for this user!")
        sys.exit(1)

    print("\nOrganizations:")
    for user_org in user_orgs:
        org = db.query(Organization).filter(
            Organization.id == user_org.organization_id
        ).first()
        if org:
            print(f"  - {org.name} (ID: {org.id}, Role: {user_org.role})")
            print(f"    Use: -H \"X-Organization-ID: {org.id}\"")

finally:
    db.close()
