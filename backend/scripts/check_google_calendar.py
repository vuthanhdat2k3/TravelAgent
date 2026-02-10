"""
Script kiểm tra kết nối Google Calendar API.
Kiểm tra OAuth config và trạng thái kết nối.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

load_dotenv()


def print_header(text):
    """Print colored header."""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{text:^60}")
    print(f"{Fore.CYAN}{'='*60}\n")


def print_success(text):
    """Print success message."""
    print(f"{Fore.GREEN}✅ {text}")


def print_error(text):
    """Print error message."""
    print(f"{Fore.RED}❌ {text}")


def print_warning(text):
    """Print warning message."""
    print(f"{Fore.YELLOW}⚠️  {text}")


def print_info(text):
    """Print info message."""
    print(f"{Fore.BLUE}ℹ️  {text}")


def check_env_variables():
    """Check if required environment variables are set."""
    print_header("Kiểm tra Biến Môi Trường")
    
    required_vars = {
        'GOOGLE_CLIENT_ID': os.getenv('GOOGLE_CLIENT_ID'),
        'GOOGLE_CLIENT_SECRET': os.getenv('GOOGLE_CLIENT_SECRET'),
        'GOOGLE_REDIRECT_URI': os.getenv('GOOGLE_REDIRECT_URI'),
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value and var_value.strip():
            print_success(f"{var_name}: {var_value[:20]}..." if len(var_value) > 20 else f"{var_name}: {var_value}")
        else:
            print_error(f"{var_name}: Chưa được thiết lập")
            all_set = False
    
    return all_set


def check_dependencies():
    """Check if required Python packages are installed."""
    print_header("Kiểm tra Dependencies")
    
    required_packages = {
        'google-api-python-client': 'googleapiclient',
        'google-auth-httplib2': 'google.auth.transport.requests',
        'google-auth-oauthlib': 'google_auth_oauthlib.flow',
    }
    
    all_installed = True
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print_success(f"{package_name}: Đã cài đặt")
        except ImportError:
            print_error(f"{package_name}: Chưa cài đặt")
            all_installed = False
    
    return all_installed


def test_oauth_flow():
    """Test OAuth flow configuration."""
    print_header("Kiểm tra OAuth Flow")
    
    try:
        from google_auth_oauthlib.flow import Flow
        
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        
        if not all([client_id, client_secret, redirect_uri]):
            print_error("Thiếu thông tin OAuth credentials")
            return False
        
        # Try to create Flow object
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
            include_granted_scopes='true',
            prompt='consent'
        )
        
        print_success("OAuth Flow config hợp lệ")
        print_info(f"Authorization URL: {authorization_url[:80]}...")
        
        return True
        
    except Exception as e:
        print_error(f"OAuth Flow config lỗi: {str(e)}")
        return False


def test_calendar_client():
    """Test Google Calendar client initialization."""
    print_header("Kiểm tra Calendar Client")
    
    try:
        from app.core.google_calendar_client import GoogleCalendarClient
        
        # Try to create client with dummy tokens
        # This will fail but we just want to see if the class works
        try:
            client = GoogleCalendarClient(
                access_token="dummy_token",
                refresh_token="dummy_refresh",
            )
            print_success("GoogleCalendarClient class khởi tạo thành công")
        except Exception as e:
            if "invalid_grant" in str(e).lower() or "invalid" in str(e).lower():
                print_success("GoogleCalendarClient class hoạt động (token không hợp lệ là bình thường)")
            else:
                raise
        
        return True
        
    except Exception as e:
        print_error(f"GoogleCalendarClient lỗi: {str(e)}")
        return False


def test_api_routes():
    """Check if Google Calendar routes are registered."""
    print_header("Kiểm tra API Routes")
    
    try:
        from app.routes import google_calendar_route
        
        print_success("google_calendar_route module tồn tại")
        
        # Check if router exists
        if hasattr(google_calendar_route, 'router'):
            print_success("Router được định nghĩa đúng")
        else:
            print_error("Router không tìm thấy")
            return False
        
        return True
        
    except ImportError as e:
        print_error(f"Không thể import google_calendar_route: {str(e)}")
        return False


def print_setup_instructions():
    """Print setup instructions if config is incomplete."""
    print_header("Hướng Dẫn Setup")
    
    print(f"{Fore.YELLOW}Để hoàn tất setup Google Calendar:\n")
    
    print("1️⃣  Tạo Google Cloud Project:")
    print("   • Truy cập: https://console.cloud.google.com/")
    print("   • Tạo project mới")
    print("   • Enable Google Calendar API\n")
    
    print("2️⃣  Tạo OAuth 2.0 Client:")
    print("   • Vào: APIs & Services > Credentials")
    print("   • Create Credentials > OAuth client ID")
    print("   • Application type: Web application")
    print("   • Authorized redirect URIs: http://localhost:8000/api/google-calendar/callback\n")
    
    print("3️⃣  Cập nhật file .env:")
    print(f"{Fore.CYAN}   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com")
    print(f"{Fore.CYAN}   GOOGLE_CLIENT_SECRET=your-client-secret")
    print(f"{Fore.CYAN}   GOOGLE_REDIRECT_URI=http://localhost:8000/api/google-calendar/callback\n")
    
    print("4️⃣  Restart backend và test lại:")
    print("   cd backend")
    print("   uvicorn main:app --reload\n")
    
    print("5️⃣  Test OAuth flow:")
    print("   • Truy cập: http://localhost:8000/api/google-calendar/auth/url")
    print("   • Đăng nhập Google và cấp quyền")
    print("   • Kiểm tra trạng thái: http://localhost:8000/api/google-calendar/status\n")
    
    print(f"{Fore.YELLOW}📖 Chi tiết: backend/docs/GOOGLE_CALENDAR_SETUP.md")


def main():
    """Main test function."""
    print_header("🧪 KIỂM TRA GOOGLE CALENDAR INTEGRATION")
    
    results = {
        'env': check_env_variables(),
        'dependencies': check_dependencies(),
        'oauth': False,
        'client': False,
        'routes': False,
    }
    
    # Only test OAuth if env vars are set
    if results['env']:
        results['oauth'] = test_oauth_flow()
    
    # Only test client if dependencies are installed
    if results['dependencies']:
        results['client'] = test_calendar_client()
    
    # Always test routes
    results['routes'] = test_api_routes()
    
    # Summary
    print_header("📊 Kết Quả Tổng Hợp")
    
    all_passed = all(results.values())
    
    if all_passed:
        print_success("TẤT CẢ KIỂM TRA ĐỀU PASS! 🎉")
        print_info("\nGoogle Calendar đã được cấu hình đúng.")
        print_info("Bạn có thể bắt đầu sử dụng OAuth flow để kết nối user accounts.\n")
        
        print(f"{Fore.YELLOW}Bước tiếp theo:")
        print("1. Khởi động backend: uvicorn main:app --reload")
        print("2. Test OAuth: GET http://localhost:8000/api/google-calendar/auth/url")
        print("3. Hoàn tất OAuth flow trên trình duyệt")
        print("4. Tạo booking và thêm vào calendar qua chatbot\n")
    else:
        print_error("MỘT SỐ KIỂM TRA THẤT BẠI!\n")
        
        failed_checks = [name for name, passed in results.items() if not passed]
        print(f"{Fore.RED}Các bước thất bại: {', '.join(failed_checks)}\n")
        
        print_setup_instructions()
    
    # Exit code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  Test bị hủy bởi user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Fore.RED}❌ Lỗi không mong đợi: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
