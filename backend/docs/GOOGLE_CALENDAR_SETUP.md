# Google Calendar Integration Setup

## Tích hợp Google Calendar API

Hệ thống đã được tích hợp với Google Calendar API để tự động tạo event khi thêm booking vào lịch trình.

### 1. Tạo Google Cloud Project

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project có sẵn
3. Enable Google Calendar API:
   - Vào **APIs & Services** > **Library**
   - Tìm "Google Calendar API"
   - Click **Enable**

### 2. Tạo OAuth 2.0 Credentials

1. Vào **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Chọn **Application type**: Web application
4. Cấu hình:
   - **Name**: Travel Agent Backend
   - **Authorized JavaScript origins**: 
     - `http://localhost:3000` (Frontend)
     - `http://localhost:8000` (Backend)
   - **Authorized redirect URIs**:
     - `http://localhost:8000/api/google-calendar/callback`
     - (Production): `https://your-domain.com/api/google-calendar/callback`
5. Click **Create**
6. Lưu lại **Client ID** và **Client Secret**

### 3. Cấu hình Backend (.env)

Thêm vào file `.env`:

```env
# --- Google Calendar OAuth Configuration ---
# Client ID từ Google Cloud Console (OAuth 2.0 Client)
GOOGLE_CLIENT_ID=123456789-abc123xyz.apps.googleusercontent.com

# Client Secret từ Google Cloud Console
GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz_your_secret_here

# Redirect URI sau khi OAuth thành công
# Development: http://localhost:8000/api/google-calendar/callback
# Production: https://your-domain.com/api/google-calendar/callback
GOOGLE_REDIRECT_URI=http://localhost:8000/api/google-calendar/callback

# Legacy credentials file (optional, không cần cho OAuth flow)
GOOGLE_CALENDAR_CREDENTIALS_JSON=
```

**Lưu ý**: Cần thêm 3 biến môi trường mới vào file `.env` của bạn.

### 4. Luồng OAuth Flow

#### A. Kết nối Google Calendar (Frontend)

```typescript
// 1. Lấy authorization URL
const response = await fetch('/api/google-calendar/auth/url', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
const { authorization_url } = await response.json();

// 2. Redirect user đến Google OAuth
window.location.href = authorization_url;

// 3. User cấp quyền trên Google
// 4. Google redirect về callback URL
// 5. Backend lưu tokens vào user.metadata_
```

#### B. Kiểm tra trạng thái kết nối

```typescript
const response = await fetch('/api/google-calendar/status', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
const { connected } = await response.json();
```

#### C. Thêm booking vào Calendar

```typescript
const response = await fetch(`/bookings/${bookingId}/calendar`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});

// Tự động tạo event trên Google Calendar
```

### 5. API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/google-calendar/auth/url` | Lấy URL để kết nối Google |
| GET | `/api/google-calendar/callback` | OAuth callback (tự động) |
| GET | `/api/google-calendar/status` | Kiểm tra trạng thái kết nối |
| DELETE | `/api/google-calendar/disconnect` | Ngắt kết nối Google Calendar |
| POST | `/bookings/{booking_id}/calendar` | Thêm booking vào lịch |

### 6. Lưu trữ Tokens

Tokens được lưu trong `users.metadata_` (JSONB):

```json
{
  "google_calendar": {
    "access_token": "ya29.xxx",
    "refresh_token": "1//xxx",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "xxx.apps.googleusercontent.com",
    "client_secret": "xxx",
    "scopes": ["https://www.googleapis.com/auth/calendar"],
    "expiry": "2026-02-10T15:30:00"
  }
}
```

### 7. Cấu trúc Event được tạo

```
📅 Tiêu đề: ✈️ Chuyến bay VN123: HAN → SGN

📝 Mô tả:
🎫 Booking Reference: ABC123XYZ
👤 Hành khách: Nguyen Van A

🛫 Khởi hành: HAN
🛬 Đến: SGN
✈️ Chuyến bay: VN 123

⏱️ Giờ khởi hành: 10/02/2026 08:00
⏱️ Giờ đến: 10/02/2026 10:30

Được tạo bởi Travel Agent AI

🔔 Nhắc nhở:
- 1 ngày trước chuyến bay
- 3 giờ trước giờ khởi hành
```

### 8. Development Mode

Nếu chưa cấu hình Google OAuth:
- Hệ thống vẫn hoạt động bình thường
- Tạo placeholder event thay vì event thật trên Google Calendar
- Log warning: `User has no Google Calendar credentials`

### 9. Error Handling

- **401**: Chưa đăng nhập
- **404**: Booking không tồn tại
- **409**: Event đã tồn tại cho booking này
- **400**: Booking chưa có thông tin chuyến bay
- **500**: Lỗi khi gọi Google Calendar API → Tự động fallback về placeholder

### 10. Testing

```bash
# 1. Khởi động backend
cd backend
uvicorn main:app --reload

# 2. Test OAuth flow
curl http://localhost:8000/api/google-calendar/auth/url \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. Truy cập authorization_url từ response
# 4. Cấp quyền và được redirect về callback

# 5. Thêm booking vào calendar
curl -X POST http://localhost:8000/bookings/{booking_id}/calendar \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 11. Production Checklist

- [ ] Cập nhật `GOOGLE_REDIRECT_URI` với domain thật
- [ ] Thêm production domain vào Google OAuth Authorized URIs
- [ ] Set `GOOGLE_CLIENT_ID` và `GOOGLE_CLIENT_SECRET` trong production env
- [ ] Verify Google Calendar API quota (10,000 requests/day free tier)
- [ ] Setup monitoring cho OAuth token refresh failures
- [ ] Implement token refresh trước khi expire

### 12. Security Notes

- **Không bao giờ** commit credentials vào git
- Tokens được lưu encrypted trong database
- Auto-refresh tokens khi hết hạn
- User có thể ngắt kết nối bất kỳ lúc nào
- Chỉ request quyền `calendar` scope (không phải full Google account)
