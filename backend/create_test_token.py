"""
Generate JWT token for test user
"""
import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings

# Test user ID from test_credentials.txt
user_id = "c9ccb230-4b1c-435e-98e3-dd17594b4643"
organization_id = "cbd50808-75e3-45a8-80fa-86f418f41c13"

# Create JWT token
expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
to_encode = {
    "sub": user_id,
    "org_id": organization_id,
    "exp": expire
}

token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
print(f"JWT Token: {token}")
print(f"\nUse in curl:")
print(f'  -H "Authorization: Bearer {token}"')
