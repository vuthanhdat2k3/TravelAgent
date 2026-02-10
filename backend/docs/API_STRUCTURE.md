# Travel Agent API - Complete Structure

## Project Structure

```
TravelAgent/
├── app/
│   ├── core/
│   │   ├── auth.py              # JWT & password hashing
│   │   ├── config.py            # Settings
│   │   └── dependencies.py      # Auth dependencies ✅ UPDATED
│   ├── db/
│   │   └── database.py          # Database connection
│   ├── models/                  # SQLAlchemy models (đã có sẵn)
│   │   ├── user.py
│   │   ├── passenger.py
│   │   ├── booking.py
│   │   ├── booking_flight.py
│   │   ├── payment.py
│   │   ├── flight_search.py
│   │   ├── flight_offer_cache.py
│   │   ├── user_preference.py
│   │   ├── calendar_event.py
│   │   ├── conversation.py
│   │   ├── conversation_message.py
│   │   └── notification_log.py
│   ├── schemas/                 # Pydantic schemas (đã có sẵn)
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── passenger.py
│   │   ├── booking.py
│   │   ├── payment.py
│   │   ├── flight.py
│   │   ├── user_preference.py
│   │   ├── calendar_event.py
│   │   ├── chat.py
│   │   ├── intent.py
│   │   ├── notification.py
│   │   └── offer_cache.py
│   ├── services/                # Business logic ✅ NEW
│   │   ├── user_service.py      # (đã có)
│   │   ├── passenger_service.py ✅
│   │   ├── flight_service.py    ✅
│   │   ├── booking_service.py   ✅
│   │   ├── payment_service.py   ✅
│   │   ├── user_preference_service.py ✅
│   │   ├── calendar_service.py  ✅
│   │   ├── chat_service.py      ✅
│   │   ├── notification_service.py ✅
│   │   └── admin_service.py     ✅
│   └── routes/                  # API endpoints ✅ NEW
│       ├── auth_route.py        # (đã có)
│       ├── user_route.py        # (đã có)
│       ├── passenger_route.py   ✅
│       ├── flight_route.py      ✅
│       ├── booking_route.py     ✅
│       ├── payment_route.py     ✅
│       ├── preference_route.py  ✅
│       ├── calendar_route.py    ✅
│       ├── chat_route.py        ✅
│       ├── notification_route.py ✅
│       └── admin_route.py       ✅
├── docs/
│   ├── API_REFERENCE.md         # Tài liệu gốc
│   ├── IMPLEMENTATION_SUMMARY.md ✅ NEW
│   └── CHECKLIST.md             ✅ NEW
├── alembic/                     # Database migrations
├── main.py                      # FastAPI app ✅ UPDATED
└── requirements.txt
```

## API Endpoints Overview

### 🔐 Authentication & Authorization
```
POST   /auth/register          # Đăng ký
POST   /auth/login             # Đăng nhập
POST   /auth/refresh           # Refresh token
GET    /auth/me                # Thông tin user hiện tại
```

### 👤 User Management
```
GET    /users/me               # Profile của tôi
PATCH  /users/me               # Cập nhật profile
```

### 👥 Admin
```
GET    /admin/users            # Danh sách users (superuser)
GET    /admin/users/{id}       # Chi tiết user (superuser)
PATCH  /admin/users/{id}       # Cập nhật user (superuser)
```

### 🧳 Passengers
```
GET    /users/me/passengers              # Danh sách hành khách
POST   /users/me/passengers              # Tạo hành khách
GET    /users/me/passengers/{id}         # Chi tiết hành khách
PATCH  /users/me/passengers/{id}         # Cập nhật hành khách
DELETE /users/me/passengers/{id}         # Xóa hành khách
```

### ✈️ Flights
```
POST   /flights/search                   # Tìm chuyến bay (auth optional)
GET    /flights/searches                 # Lịch sử tìm kiếm
```

### 📋 Bookings
```
POST   /bookings                         # Tạo booking
GET    /bookings                         # Danh sách bookings
GET    /bookings/{id}                    # Chi tiết booking
POST   /bookings/{id}/cancel             # Hủy booking
```

### 💳 Payments
```
POST   /bookings/{id}/payments           # Tạo thanh toán
GET    /bookings/{id}/payments           # Danh sách thanh toán
POST   /payments/webhook/vnpay           # VNPAY webhook
POST   /payments/webhook/momo            # MOMO webhook
```

### ⚙️ User Preferences
```
GET    /users/me/preferences             # Lấy preferences
PUT    /users/me/preferences             # Tạo/cập nhật (upsert)
PATCH  /users/me/preferences             # Cập nhật một phần
```

### 📅 Calendar
```
POST   /bookings/{id}/calendar           # Thêm vào Google Calendar
GET    /users/me/calendar-events         # Danh sách events
GET    /bookings/{id}/calendar           # Events của booking
```

### 💬 Chat (Multi-Agent)
```
POST   /chat/conversations               # Tạo conversation (auth optional)
GET    /chat/conversations               # Danh sách conversations
GET    /chat/conversations/{id}          # Chi tiết + messages
POST   /chat/messages                    # Gửi message (auth optional)
POST   /chat/conversations/{id}/messages # Gửi message vào conversation
```

### 🔔 Notifications
```
GET    /users/me/notifications           # Lịch sử notifications
```

## Authentication Flow

### 1. Đăng ký
```
POST /auth/register
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "phone": "+84123456789"
}

Response:
{
  "user": { ... },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2. Đăng nhập
```
POST /auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

Response: (same as register)
```

### 3. Sử dụng API
```
Authorization: Bearer eyJ...
```

## Typical User Flow

### 1. Tìm chuyến bay
```
POST /flights/search
{
  "origin": "HAN",
  "destination": "SGN",
  "depart_date": "2024-03-15",
  "return_date": "2024-03-20",
  "adults": 2,
  "travel_class": "ECONOMY",
  "currency": "VND"
}
```

### 2. Tạo hành khách (nếu chưa có)
```
POST /users/me/passengers
{
  "first_name": "John",
  "last_name": "Doe",
  "gender": "MALE",
  "dob": "1990-01-01",
  "passport_number": "A12345678",
  "passport_expiry": "2030-01-01",
  "nationality": "VNM"
}
```

### 3. Tạo booking
```
POST /bookings
{
  "passenger_id": "uuid-of-passenger",
  "offer_id": "amadeus-offer-id"
}
```

### 4. Thanh toán
```
POST /bookings/{booking_id}/payments
{
  "booking_id": "uuid-of-booking",
  "amount": 5000000,
  "currency": "VND",
  "provider": "VNPAY"
}

Response:
{
  "payment": { ... },
  "payment_url": "https://vnpay.vn/..."
}
```

### 5. Thêm vào Calendar
```
POST /bookings/{booking_id}/calendar
{
  "calendar_id": "primary"
}
```

## Chat Flow

### 1. Tạo conversation (optional)
```
POST /chat/conversations
{
  "channel": "web"
}
```

### 2. Gửi message
```
POST /chat/messages
{
  "message": "Tôi muốn đặt vé từ Hà Nội đi Sài Gòn",
  "conversation_id": "uuid-of-conversation",
  "channel": "web"
}

Response:
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "content": "Tôi có thể giúp bạn tìm chuyến bay...",
  "intent": "SEARCH_FLIGHT",
  "agent_name": "flight_agent",
  "suggested_actions": [
    {
      "type": "date_picker",
      "label": "Chọn ngày đi"
    }
  ]
}
```

## Error Handling

Tất cả API đều trả về error theo format:

```json
{
  "detail": "Error message"
}
```

Hoặc với validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error"
    }
  ]
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `204` - No Content (delete success)
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (no permission)
- `404` - Not Found
- `409` - Conflict (duplicate email, etc.)
- `500` - Internal Server Error

## Security Features

### ✅ Implemented
- JWT authentication (access + refresh tokens)
- Password hashing (bcrypt)
- User ownership validation (users can only access their own data)
- Admin/superuser role checking
- Optional authentication for public endpoints

### 🔧 To Implement
- Rate limiting
- CORS configuration
- Request validation
- SQL injection prevention (using SQLAlchemy ORM)
- XSS prevention
- CSRF protection for webhooks

## Performance Optimizations

### ✅ Implemented
- Flight offer caching (30 minutes)
- Database indexing on foreign keys
- Async database operations

### 🔧 To Implement
- Redis caching
- Database query optimization
- Pagination for all list endpoints
- Background tasks with Celery
- CDN for static assets

## Next Steps

1. **Set up development environment**
   ```bash
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn main:app --reload
   ```

2. **Test endpoints**
   - Visit http://localhost:8000/docs
   - Test authentication flow
   - Test each endpoint group

3. **Implement external integrations**
   - Amadeus API
   - Payment gateways
   - Google Calendar
   - Multi-agent chatbot

4. **Write tests**
   - Unit tests for services
   - Integration tests for routes
   - E2E tests for critical flows

5. **Deploy to production**
   - Set up production database
   - Configure environment variables
   - Set up monitoring
   - Deploy to cloud (AWS/GCP/Azure)
