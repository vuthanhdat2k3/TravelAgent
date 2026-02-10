"""
Test Google Calendar OAuth flow.
Gets authorization URL for user to complete OAuth.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


async def main():
    """Test OAuth flow."""
    
    print("🧪 Testing Google Calendar OAuth Flow\n")
    
    base_url = "http://localhost:8000"
    
    # Step 1: Get authorization URL
    print("📋 Step 1: Getting authorization URL...")
    print(f"   Calling: GET {base_url}/api/google-calendar/auth/url")
    
    try:
        async with httpx.AsyncClient() as client:
            # Note: This endpoint requires authentication
            # You need to pass a valid JWT token
            print("\n⚠️  Endpoint này yêu cầu authentication")
            print("   Bạn cần:")
            print("   1. Login qua frontend hoặc call /auth/login")
            print("   2. Lấy access_token")
            print("   3. Gọi endpoint với header: Authorization: Bearer <token>")
            print("\n   Hoặc test trực tiếp từ browser/Postman:")
            print(f"   1. Login để lấy token")
            print(f"   2. GET {base_url}/api/google-calendar/auth/url")
            print(f"   3. Copy authorization_url từ response")
            print(f"   4. Paste vào browser → Authorize")
            print(f"   5. Sau khi authorize, tokens sẽ được lưu vào database")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
