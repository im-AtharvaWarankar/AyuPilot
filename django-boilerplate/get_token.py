#!/usr/bin/env python
"""
Get a fresh authentication token for AyuPilot frontend
This generates a new JWT token that you can use in the frontend
"""
import requests
import json

# API endpoint
# NOTE: user login URLs are mounted at the project root (see `src/urls.py`).
# The correct login path is `/login/` (not `/api/users/login/`).
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/login/"

# Default admin credentials from setup_admin.py
CREDENTIALS = {
    "email": "admin@gmail.com",
    "password": "admin"
}

def get_token():
    """Get a fresh JWT token from the backend"""
    print("🔐 Getting fresh authentication token...\n")
    
    try:
        response = requests.post(LOGIN_URL, json=CREDENTIALS)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access')
            refresh_token = data.get('refresh')
            
            print("✅ Token obtained successfully!\n")
            print("=" * 70)
            print("ACCESS TOKEN (copy this to frontend/src/services/api.ts):")
            print("=" * 70)
            print(access_token)
            print("\n" + "=" * 70)
            print("REFRESH TOKEN:")
            print("=" * 70)
            print(refresh_token)
            print("\n")
            
            print("📝 To update the frontend:")
            print("1. Open: frontend/src/services/api.ts")
            print("2. Find the getAuthToken() function (around line 125)")
            print("3. Replace the token string with the ACCESS TOKEN above")
            print("\nOr run this command:")
            print("=" * 70)
            print(f"Update-Content: Replace old token with:\n{access_token}")
            
            return access_token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend")
        print("Make sure Django is running on http://localhost:8000")
        print("\nStart with: python manage.py runserver")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    get_token()
