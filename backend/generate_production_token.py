"""
Generate a production JWT token for Azure API
"""
import jwt
from datetime import datetime, timedelta
import os
import sys

# Get SECRET_KEY from environment variable
SECRET_KEY = os.getenv("AZURE_SECRET_KEY") or os.getenv("SECRET_KEY")
if not SECRET_KEY:
    print("ERROR: AZURE_SECRET_KEY or SECRET_KEY environment variable not set")
    print("Set it with: export AZURE_SECRET_KEY=your-secret-key")
    sys.exit(1)

ALGORITHM = "HS256"

# Test user ID (same as local)
USER_ID = "c9ccb230-4b1c-435e-98e3-dd17594b4643"

# Create token with 1 year expiration
expiration = datetime.utcnow() + timedelta(days=365)

payload = {
    "sub": USER_ID,
    "email": "test@example.com",
    "exp": expiration
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

print("=" * 80)
print("PRODUCTION JWT TOKEN (Azure)")
print("=" * 80)
print()
print(f"Token: {token}")
print()
print("Use this token in your API calls to Azure:")
print(f'  -H "Authorization: Bearer {token}"')
print()
print("=" * 80)
