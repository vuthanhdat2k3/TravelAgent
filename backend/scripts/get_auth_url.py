"""
Generate Google Calendar authorization URL without authentication.
This simulates what frontend will do.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from google_auth_oauthlib.flow import Flow
from app.core.config import settings


def main():
    """Generate authorization URL."""
    
    print("🔐 Google Calendar OAuth Authorization\n")
    
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    
    if not client_id or not client_secret:
        print("❌ Missing Google OAuth credentials in .env")
        print("   Required: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET")
        return
    
    print(f"✅ Client ID: {client_id[:30]}...")
    print(f"✅ Redirect URI: {redirect_uri}")
    
    try:
        # Create OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": [redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri=redirect_uri
        )
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )
        
        print("\n" + "="*80)
        print("📋 AUTHORIZATION URL (Copy & Paste vào browser):")
        print("="*80)
        print(authorization_url)
        print("="*80)
        
        print("\n📝 Hướng dẫn:")
        print("   1. Copy URL trên")
        print("   2. Paste vào browser")
        print("   3. Đăng nhập Google account bạn muốn dùng")
        print("   4. Click 'Allow' để cấp quyền truy cập Calendar")
        print("   5. Sau khi authorize, bạn sẽ được redirect về callback URL")
        print("   6. Backend sẽ tự động lưu tokens vào database")
        
        print(f"\n⚠️  Lưu ý: Đảm bảo backend đang chạy tại: http://localhost:8000")
        print(f"   Và bạn đã đăng nhập (có JWT token)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
