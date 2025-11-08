"""
Generate a test JWT token for API testing
"""
from datetime import datetime, timedelta
from jose import jwt
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings

# Test user from test_credentials.txt
USER_ID = "c9ccb230-4b1c-435e-98e3-dd17594b4643"
EMAIL = "test@example.com"

def create_test_token():
    """Create a test JWT token"""
    data = {
        "sub": USER_ID,
        "email": EMAIL,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }

    token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

if __name__ == "__main__":
    token = create_test_token()
    print("\n" + "="*80)
    print("TEST JWT TOKEN")
    print("="*80)
    print(f"\nToken: {token}\n")
    print("Use this token in your API calls:")
    print(f'  -H "Authorization: Bearer {token}"')
    print("\n" + "="*80)
