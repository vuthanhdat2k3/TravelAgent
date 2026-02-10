# API Reference – Travel Agent (Đặt vé máy bay)

Tài liệu liệt kê toàn bộ API cần thiết để triển khai services. Mỗi API gồm: method, path, request/response và **lưu ý** khi implement.

**Quy ước chung:**
- Base URL: `https://api.example.com/v1` (hoặc `/api/v1`).
- Content-Type: `application/json` (trừ upload file).
- Auth: Bearer JWT trong header `Authorization: Bearer <access_token>` (trừ auth và webhook).
- ID: UUID (string) trừ khi ghi chú khác.
- Lỗi: HTTP 4xx/5xx, body `{ "detail": "..." }` hoặc `{ "detail": [{ "loc": [], "msg": "" }] }` (Pydantic).

---

## 1. Auth

### 1.1 Đăng ký

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/auth/register` |
| **Auth** | Không |
| **Request** | `UserCreate`: `email`, `password`, `full_name?`, `phone?` |
| **Response** | `201`: `{ "user": UserResponse, "access_token": str, "refresh_token": str, "token_type": "bearer", "expires_in": int }` |
| **Schema** | `app.schemas.user.UserCreate`, `UserResponse` |

**Lưu ý:**
- Hash password bằng bcrypt/passlib trước khi lưu (`hashed_password`).
- Trả JWT (access + refresh). Refresh token lưu DB hoặc blacklist khi logout.
- Validate email unique; 409 nếu trùng.

---

### 1.2 Đăng nhập

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/auth/login` |
| **Auth** | Không |
| **Request** | `{ "email": str, "password": str }` |
| **Response** | `200`: cùng format như register (user + access_token + refresh_token). |
| **Lỗi** | `401` sai email/password. |

**Lưu ý:**
- Verify password với `passlib.verify(plain, hashed)`.
- Kiểm tra `user.is_active`; 403 nếu bị khóa.

---

### 1.3 Refresh token

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/auth/refresh` |
| **Auth** | Không (gửi refresh token trong body) |
| **Request** | `{ "refresh_token": str }` |
| **Response** | `200`: `{ "access_token": str, "refresh_token": str, "token_type": "bearer", "expires_in": int }` |

**Lưu ý:**
- Verify refresh token (JWT secret, chưa expire, chưa bị revoke).
- Có thể rotate refresh token (trả token mới, vô hiệu hóa token cũ).

---

### 1.4 Lấy thông tin user hiện tại

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/auth/me` hoặc `GET /users/me` |
| **Auth** | Bearer (bắt buộc) |
| **Response** | `200`: `UserResponse` |

**Lưu ý:**
- JWT payload chứa `sub` (user_id). Query user theo id; 404 nếu không tồn tại hoặc bị xóa.

---

## 2. Users (Profile)

### 2.1 Cập nhật profile

| | |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/users/me` |
| **Auth** | Bearer |
| **Request** | `UserUpdate`: `full_name?`, `phone?`, `avatar_url?`, `is_active?` (admin mới cho sửa is_active) |
| **Response** | `200`: `UserResponse` |
| **Schema** | `app.schemas.user.UserUpdate` |

**Lưu ý:**
- Chỉ cho phép sửa bản thân; `user_id` lấy từ JWT.
- Không cho phép đổi `email` qua API này (tách endpoint đổi email + verify nếu cần).

---

### 2.2 (Admin) Danh sách users

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/admin/users` |
| **Auth** | Bearer (role admin/superuser) |
| **Query** | `skip=0`, `limit=20`, `is_active=?`, `q=` (search email/name) |
| **Response** | `200`: `{ "items": [UserResponse], "total": int }` |

**Lưu ý:**
- Chỉ `is_superuser == True` mới gọi được. Phân quyền rõ trong middleware/dependency.

---

### 2.3 (Admin) Chi tiết / Cập nhật / Khóa user

| | |
|---|---|
| **Method** | `GET` \| `PATCH` |
| **Path** | `/admin/users/{user_id}` |
| **Auth** | Bearer (admin) |
| **PATCH body** | Một phần UserUpdate + `is_active?` |
| **Response** | `200`: `UserResponse` |

**Lưu ý:**
- GET: trả user bất kỳ (admin). PATCH: có thể khóa `is_active=false` để chặn đăng nhập.

---

## 3. Passengers (Hành khách)

Tất cả dưới `/users/me/passengers` — passenger thuộc user đăng nhập.

### 3.1 Danh sách passengers

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/users/me/passengers` |
| **Auth** | Bearer |
| **Query** | `skip=0`, `limit=50` (optional) |
| **Response** | `200`: `[PassengerResponse]` |
| **Schema** | `app.schemas.passenger.PassengerResponse` |

**Lưu ý:**
- Filter `Passenger.user_id == current_user.id`. Dùng cho form đặt vé (chọn hành khách).

---

### 3.2 Tạo passenger

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/users/me/passengers` |
| **Auth** | Bearer |
| **Request** | `PassengerCreate`: `user_id` (có thể bỏ qua, lấy từ JWT), `first_name`, `last_name`, `gender?`, `dob?`, `passport_number?`, `passport_expiry?`, `nationality?` |
| **Response** | `201`: `PassengerResponse` |
| **Schema** | `app.schemas.passenger.PassengerCreate` |

**Lưu ý:**
- Service gán `user_id = current_user.id` (không tin client). Passport: format tùy quy định (số + chữ), `passport_expiry > today`.

---

### 3.3 Chi tiết passenger

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/users/me/passengers/{passenger_id}` |
| **Auth** | Bearer |
| **Response** | `200`: `PassengerResponse`. `404` nếu không tồn tại hoặc không thuộc user. |

**Lưu ý:**
- Luôn kiểm tra `passenger.user_id == current_user.id`.

---

### 3.4 Cập nhật passenger

| | |
|---|---|
| **Method** | `PATCH` |
| **Path** | `/users/me/passengers/{passenger_id}` |
| **Auth** | Bearer |
| **Request** | `PassengerUpdate`: các field optional |
| **Response** | `200`: `PassengerResponse` |

**Lưu ý:**
- Kiểm tra ownership. Nếu passenger đã có booking, có thể chỉ cho sửa một số field (theo policy).

---

### 3.5 Xóa passenger

| | |
|---|---|
| **Method** | `DELETE` |
| **Path** | `/users/me/passengers/{passenger_id}` |
| **Auth** | Bearer |
| **Response** | `204 No Content` hoặc `200`. `404` nếu không thuộc user. |

**Lưu ý:**
- Nếu có FK từ `bookings.passenger_id` hoặc `user_preferences.default_passenger_id`, có thể RESTRICT → trả 400 "Đã có booking, không xóa được" hoặc SET NULL cho default_passenger_id.

---

## 4. Flights (Tìm chuyến bay)

### 4.1 Tìm chuyến bay (Amadeus)

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/flights/search` |
| **Auth** | Optional (Bearer). Nếu có user thì lưu `flight_searches`. |
| **Request** | `FlightSearchRequest`: `origin`, `destination`, `depart_date`, `return_date?`, `adults=1`, `travel_class="ECONOMY"`, `currency="VND"` |
| **Response** | `200`: `{ "offers": [FlightOffer], "search_id": UUID? }` (search_id nếu đã lưu flight_searches) |
| **Schema** | `app.schemas.flight.FlightSearchRequest`, `FlightOffer` (offer_id, total_price, currency, duration_minutes, stops, segments[]) |

**Lưu ý:**
- Service: gọi Amadeus Flight Offers API; normalize response → list `FlightOffer`.
- Cache: tạo `search_key = hash(origin, destination, depart_date, adults, travel_class)`; lưu từng offer vào `flight_offer_cache` (payload JSONB, expires_at 15–30 phút). Lần sau cùng params có thể đọc từ cache trước khi gọi Amadeus.
- Nếu có user: insert `FlightSearch` (user_id, origin, destination, depart_date, return_date, adults, travel_class) để lịch sử tìm kiếm.
- Amadeus rate limit: xử lý 429, retry với backoff. Origin/destination IATA 3 ký tự.

---

### 4.2 (Optional) Lịch sử tìm kiếm

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/users/me/flight-searches` |
| **Auth** | Bearer |
| **Query** | `skip=0`, `limit=20` |
| **Response** | `200`: `[ { id, origin, destination, depart_date, return_date, adults, travel_class, created_at } ]` |

**Lưu ý:**
- Chỉ phục vụ UX (gợi ý tìm lại). Có thể bỏ qua nếu không cần.

---

## 5. Bookings (Đặt vé)

### 5.1 Tạo booking

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/bookings` |
| **Auth** | Bearer |
| **Request** | `BookingCreateRequest`: `passenger_id`, `offer_id` (Amadeus flightOfferId) |
| **Response** | `201`: `BookingResponse` (booking_id, status, provider, booking_reference?, total_price?, currency?, flights[], created_at?, confirmed_at?) |
| **Schema** | `app.schemas.booking.BookingCreateRequest`, `BookingResponse` |

**Lưu ý:**
- `offer_id` phải tồn tại trong cache hoặc validate với Amadeus (nếu API hỗ trợ). Lấy thông tin chuyến từ cache/Amadeus để tạo `Booking` + `BookingFlight`.
- Kiểm tra `passenger_id` thuộc `current_user`; validate passenger (Policy Agent): passport, DOB, v.v. trước khi gọi Amadeus Order/Booking API (nếu có).
- Sau khi Amadeus trả PNR/booking_reference: cập nhật `Booking.booking_reference`, `status=CONFIRMED`, `confirmed_at=now`. Nếu lỗi: `status=FAILED`, có thể tạo bản ghi vẫn để log.
- Idempotency: có thể nhận `idempotency_key` header để tránh tạo booking trùng khi client retry.

---

### 5.2 Danh sách booking của tôi

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/users/me/bookings` |
| **Auth** | Bearer |
| **Query** | `skip=0`, `limit=20`, `status=PENDING|CONFIRMED|CANCELLED` (optional) |
| **Response** | `200`: `[BookingListResponse]` (id, user_id, passenger_id, status, provider, booking_reference, total_price, currency, created_at, confirmed_at, flights[]) |
| **Schema** | `app.schemas.booking.BookingListResponse` |

**Lưu ý:**
- Filter `Booking.user_id == current_user.id`. Order by `created_at desc`.

---

### 5.3 Chi tiết một booking

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/users/me/bookings/{booking_id}` |
| **Auth** | Bearer |
| **Response** | `200`: `BookingListResponse` (hoặc BookingResponse đủ chi tiết). `404` nếu không thuộc user. |

**Lưu ý:**
- Dùng cho màn "Xem đặt vé" và cho Calendar Agent (lấy flight times để tạo event).

---

### 5.4 Hủy booking

| | |
|---|---|
| **Method** | `PATCH` hoặc `POST` |
| **Path** | `/users/me/bookings/{booking_id}/cancel` |
| **Auth** | Bearer |
| **Request** | (optional) `{ "reason": str }` |
| **Response** | `200`: `BookingResponse` (status = CANCELLED). `400` nếu đã cancel/refund rồi. |

**Lưu ý:**
- Chỉ cho phép khi `status` là PENDING hoặc CONFIRMED (tùy policy). Cập nhật `Booking.status = CANCELLED`. Có thể gọi Amadeus cancel API nếu có; ghi log và có thể trigger refund/notification.

---

## 6. Payments (Thanh toán)

### 6.1 Tạo thanh toán cho booking

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/bookings/{booking_id}/payments` |
| **Auth** | Bearer |
| **Request** | `PaymentCreate`: `booking_id`, `amount`, `currency="VND"`, `provider?` (VNPAY, MOMO, …) |
| **Response** | `201`: `PaymentResponse` + (tùy provider) `payment_url` để redirect user đi thanh toán. |
| **Schema** | `app.schemas.payment.PaymentCreate`, `PaymentResponse` |

**Lưu ý:**
- Kiểm tra booking thuộc user và `booking.status` cho phép thanh toán (vd PENDING). Amount thường = booking.total_price.
- Tạo bản ghi `Payment` (status=PENDING); gọi gateway (VNPAY/MOMO) tạo link thanh toán; trả `payment_url` + `PaymentResponse`. Lưu `external_id` khi gateway trả về (có thể cập nhật ở bước webhook).
- Redirect user đến payment_url; sau khi thanh toán xong gateway redirect/notify về backend (webhook).

---

### 6.2 Webhook / Callback từ cổng thanh toán

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/payments/webhook/vnpay` (hoặc `/payments/callback/momo`, v.v.) |
| **Auth** | Không (hoặc HMAC/signature verify) |
| **Request** | Query/form body do gateway gửi (vd vnp_TxnRef, vnp_ResponseCode, vnp_SecureHash). |
| **Response** | `200` với body theo tài liệu gateway (để họ biết đã nhận). |

**Lưu ý:**
- **Bắt buộc verify chữ ký** (HMAC) theo tài liệu VNPAY/MOMO; từ chối nếu sai.
- Tìm `Payment` theo external_id hoặc ref trong callback; cập nhật `status=COMPLETED` (hoặc FAILED), `paid_at`, `metadata_` (raw response). Cập nhật `Booking.status=CONFIRMED` khi payment COMPLETED (nếu business logic yêu cầu).
- Trả 200 nhanh; xử lý nặng (email, calendar) có thể đẩy queue. Tránh timeout gateway.

---

### 6.3 Danh sách thanh toán của một booking

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/bookings/{booking_id}/payments` |
| **Auth** | Bearer |
| **Response** | `200`: `[PaymentResponse]` |

**Lưu ý:**
- Chỉ khi booking thuộc current_user. Dùng để hiển thị lịch sử thanh toán/refund.

---

## 7. User Preferences (Profile Agent)

### 7.1 Lấy preference

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/users/me/preferences` |
| **Auth** | Bearer |
| **Response** | `200`: `UserPreferenceResponse` hoặc `204`/`404` nếu chưa có. |
| **Schema** | `app.schemas.user_preference.UserPreferenceResponse` |

**Lưu ý:**
- Mỗi user tối đa 1 bản ghi `UserPreference` (unique user_id). Dùng cho chatbot Profile Agent (cabin_class, preferred_airlines, default_passenger_id).

---

### 7.2 Tạo / Cập nhật preference

| | |
|---|---|
| **Method** | `PUT` hoặc `PATCH` |
| **Path** | `/users/me/preferences` |
| **Auth** | Bearer |
| **Request** | `UserPreferenceUpdate` hoặc `UserPreferenceCreate`: `cabin_class?`, `preferred_airlines?`, `seat_preference?`, `default_passenger_id?` |
| **Response** | `200`: `UserPreferenceResponse`. `201` nếu PUT và vừa tạo mới. |
| **Schema** | `app.schemas.user_preference.UserPreferenceUpdate` |

**Lưu ý:**
- PUT: upsert (nếu chưa có thì tạo). `default_passenger_id` phải thuộc user. preferred_airlines: list IATA code.

---

## 8. Calendar (Google Calendar)

### 8.1 Thêm booking vào Google Calendar

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/bookings/{booking_id}/calendar` |
| **Auth** | Bearer |
| **Request** | (optional) `{ "calendar_id": str }` (mặc định primary). |
| **Response** | `201`: `CalendarEventResponse` (id, booking_id, user_id, google_event_id, calendar_id, synced_at, created_at). `409` nếu booking đã có calendar event. |
| **Schema** | `app.schemas.calendar_event.CalendarEventResponse` |

**Lưu ý:**
- Kiểm tra booking thuộc user. Lấy thông tin flights (departure_time, arrival_time, origin, destination) từ `BookingFlight`; tạo Google Calendar event (summary, start, end); lưu `CalendarEvent` (booking_id, user_id, google_event_id, calendar_id). Cần OAuth token Google của user (lưu trong profile hoặc session) — nếu chưa có token trả 400 "Chưa kết nối Google Calendar".

---

### 8.2 Danh sách calendar events (theo user hoặc theo booking)

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/users/me/calendar-events` hoặc `GET /bookings/{booking_id}/calendar` |
| **Auth** | Bearer |
| **Query** | (me) `skip=0`, `limit=20` |
| **Response** | `200`: `[CalendarEventResponse]` (có thể kèm booking summary). |

**Lưu ý:**
- `/users/me/calendar-events`: list mọi calendar event của user. `/bookings/{booking_id}/calendar`: chỉ events của booking đó (1 booking có thể 1 event hoặc 1 event per leg tùy thiết kế).

---

## 9. Chatbot (Multi-Agent)

### 9.1 Tạo hoặc mở conversation

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/chat/conversations` |
| **Auth** | Optional (Bearer). Anonymous nếu không gửi token. |
| **Request** | `{ "channel": "web" }` (optional) |
| **Response** | `201`: `ConversationResponse` (id, user_id?, channel, state?, created_at, updated_at, message_count=0). |
| **Schema** | `app.schemas.chat.ConversationResponse` |

**Lưu ý:**
- Nếu không tạo sẵn conversation thì có thể bỏ API này và để "tạo conversation" ngầm trong "Gửi tin nhắn" (conversation_id optional).

---

### 9.2 Danh sách conversation của user

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/chat/conversations` |
| **Auth** | Bearer (nếu không gửi token trả 401 hoặc list rỗng) |
| **Query** | `skip=0`, `limit=20` |
| **Response** | `200`: `[ConversationResponse]` (có thể thêm last_message preview). |

**Lưu ý:**
- Filter `Conversation.user_id == current_user.id`. Anonymous conversations (user_id=null) không list được sau khi đăng nhập trừ khi có cơ chế "ghép" session.

---

### 9.3 Chi tiết conversation + tin nhắn

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/chat/conversations/{conversation_id}` |
| **Auth** | Bearer (hoặc cho phép anonymous nếu conversation không có user_id) |
| **Query** | `limit=50`, `before=message_id` (cursor pagination optional) |
| **Response** | `200`: `ConversationResponse` + `messages: [MessageSchema]`. |
| **Schema** | `app.schemas.chat.MessageSchema` |

**Lưu ý:**
- Kiểm tra conversation thuộc user (hoặc anonymous và session match). Order messages by created_at.

---

### 9.4 Gửi tin nhắn (Chat)

| | |
|---|---|
| **Method** | `POST` |
| **Path** | `/chat/messages` hoặc `POST /chat/conversations/{conversation_id}/messages` |
| **Auth** | Optional |
| **Request** | `ChatRequest`: `message`, `conversation_id?`, `user_id?`, `channel="web"`. Nếu không có conversation_id thì tạo conversation mới. |
| **Response** | `200`: `ChatResponse` (conversation_id, message_id, content, intent?, agent_name?, state?, suggested_actions[], attachments[], created_at). Có thể dùng SSE/stream cho reply. |
| **Schema** | `app.schemas.chat.ChatRequest`, `ChatResponse` |

**Lưu ý:**
- Service: (1) Lấy hoặc tạo Conversation. (2) Lưu message user vào `ConversationMessage` (role=user). (3) Gọi Router/Orchestrator → sub-agents (Flight, Booking, Calendar, Profile, DB, Validation, Notification). (4) Tạo message assistant, cập nhật conversation.state. (5) Trả ChatResponse. Nếu stream: dùng SSE endpoint riêng, emit từng chunk.
- Rate limit theo conversation_id hoặc IP để tránh spam.

---

## 10. (Nội bộ / Admin) Notifications

| | |
|---|---|
| **Method** | `GET` |
| **Path** | `/users/me/notifications` (optional) |
| **Auth** | Bearer |
| **Query** | `skip=0`, `limit=20`, `type=?` |
| **Response** | `200`: `[NotificationLogResponse]` (id, user_id, type, channel, subject, ref_id, status, sent_at). |

**Lưu ý:**
- Notification thường do server gửi (Notification Agent), không tạo qua API công khai. API này chỉ xem lịch sử đã gửi. Schema: `NotificationLogResponse`; model `NotificationLog` có `type_` (column "type").

---

## 11. Tóm tắt bảng API theo nhóm

| Nhóm | Method | Path | Mô tả ngắn |
|------|--------|------|------------|
| Auth | POST | /auth/register | Đăng ký |
| Auth | POST | /auth/login | Đăng nhập |
| Auth | POST | /auth/refresh | Refresh token |
| Auth | GET | /auth/me | User hiện tại |
| Users | PATCH | /users/me | Cập nhật profile |
| Admin | GET | /admin/users | List users |
| Admin | GET/PATCH | /admin/users/{id} | Chi tiết / cập nhật user |
| Passengers | GET | /users/me/passengers | List |
| Passengers | POST | /users/me/passengers | Tạo |
| Passengers | GET | /users/me/passengers/{id} | Chi tiết |
| Passengers | PATCH | /users/me/passengers/{id} | Cập nhật |
| Passengers | DELETE | /users/me/passengers/{id} | Xóa |
| Flights | POST | /flights/search | Tìm chuyến (Amadeus + cache) |
| Flights | GET | /users/me/flight-searches | Lịch sử tìm kiếm (optional) |
| Bookings | POST | /bookings | Tạo booking |
| Bookings | GET | /users/me/bookings | List |
| Bookings | GET | /users/me/bookings/{id} | Chi tiết |
| Bookings | PATCH/POST | /users/me/bookings/{id}/cancel | Hủy |
| Payments | POST | /bookings/{id}/payments | Tạo thanh toán |
| Payments | POST | /payments/webhook/vnpay (…) | Callback gateway |
| Payments | GET | /bookings/{id}/payments | List payments |
| Preferences | GET | /users/me/preferences | Lấy |
| Preferences | PUT/PATCH | /users/me/preferences | Upsert |
| Calendar | POST | /bookings/{id}/calendar | Thêm vào Google Calendar |
| Calendar | GET | /users/me/calendar-events hoặc /bookings/{id}/calendar | List events |
| Chat | POST | /chat/conversations | Tạo conversation |
| Chat | GET | /chat/conversations | List |
| Chat | GET | /chat/conversations/{id} | Chi tiết + messages |
| Chat | POST | /chat/messages hoặc /chat/conversations/{id}/messages | Gửi tin nhắn |
| Notifications | GET | /users/me/notifications | Lịch sử gửi (optional) |

---

## 12. ERD hoàn chỉnh

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                    users                                          │
│-----------------------------------------------------------------------------------│
│ id (uuid) PK                                                                      │
│ email (unique, indexed)                                                           │
│ hashed_password                                                                   │
│ full_name, phone                                                                  │
│ is_active, is_superuser                                                           │
│ avatar_url, metadata (JSONB)                                                      │
│ created_at, updated_at                                                            │
└───────┬─────────────────────────────────────────────────────────────────────────┘
        │
        │ 1
        │
        │ N
        ├──────────────────────────────────────────────────────────────────────────┐
        │                                                                            │
        ▼                                                                            ▼
┌───────────────────────────────┐                                    ┌─────────────────────────────┐
│         passengers             │                                    │      user_preferences        │
│---------------------------------|                                    |-----------------------------|
│ id (uuid) PK                    │◄──────────────────────────────────│ id (uuid) PK                 │
│ user_id (uuid) FK → users       │         default_passenger_id       │ user_id (uuid) FK → users   │
│ first_name, last_name           │         (nullable)                 │ cabin_class                 │
│ gender, dob                     │                                    │ preferred_airlines (JSONB)  │
│ passport_number, passport_expiry│                                    │ seat_preference             │
│ nationality                     │                                    │ default_passenger_id FK     │
│ created_at, updated_at          │                                    │ metadata (JSONB)            │
└───────────────┬─────────────────┘                                    │ created_at, updated_at      │
                │                                                       └─────────────────────────────┘
                │ 1                                                                     │
                │                                                                       │ N
                │ N                                                                     │ 1
                ▼                                                                       │
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                                      bookings                                          │
│-----------------------------------------------------------------------------------------│
│ id (uuid) PK                                                                            │
│ user_id (uuid) FK → users                                                               │
│ passenger_id (uuid) FK → passengers                                                     │
│ status (enum: PENDING, CONFIRMED, CANCELLED, FAILED, REFUNDED)                         │
│ provider (default AMADEUS), amadeus_offer_id, booking_reference                         │
│ total_price (numeric), currency                                                         │
│ created_at, confirmed_at, updated_at                                                    │
└───────┬─────────────────────────────┬───────────────────────────────────────────────────┘
        │                             │
        │ 1                           │ 1
        │                             │
        │ N                           │ N
        ▼                             ▼
┌─────────────────────────────┐    ┌─────────────────────────────┐    ┌─────────────────────────────┐
│      booking_flights         │    │         payments             │    │      calendar_events         │
│------------------------------|    │------------------------------|    │-----------------------------|
│ id (uuid) PK                 │    │ id (uuid) PK                 │    │ id (uuid) PK                │
│ booking_id (uuid) FK         │    │ booking_id (uuid) FK         │    │ booking_id (uuid) FK         │
│ origin, destination (IATA)   │    │ amount, currency             │    │ user_id (uuid) FK → users   │
│ departure_time, arrival_time │    │ status (enum)                │    │ google_event_id             │
│ airline_code, flight_number  │    │ provider, external_id        │    │ calendar_id                 │
│ duration_minutes, stops      │    │ metadata (text), paid_at      │    │ synced_at, created_at        │
│ cabin_class, created_at     │    │ created_at, updated_at        │    └─────────────────────────────┘
└─────────────────────────────┘    └─────────────────────────────┘

        │
        │ users 1 ── N flight_searches
        ▼
┌─────────────────────────────┐
│      flight_searches         │
│------------------------------|
│ id (uuid) PK                 │
│ user_id (uuid) FK (nullable) │
│ origin, destination (IATA)   │
│ depart_date, return_date     │
│ adults, travel_class         │
│ created_at                   │
└─────────────────────────────┘

        │
        │ users 1 ── N conversations
        ▼
┌─────────────────────────────┐        ┌─────────────────────────────┐
│      conversations           │        │   flight_offer_cache         │
│------------------------------|        │------------------------------|
│ id (uuid) PK                 │        │ id (uuid) PK                 │
│ user_id (uuid) FK (nullable) │        │ search_key (index)           │
│ channel                      │        │ offer_id (index)             │
│ state (JSONB)                │        │ payload (JSONB)              │
│ created_at, updated_at       │        │ expires_at, created_at       │
└───────────────┬──────────────┘        │ (index: search_key, expires)  │
                │ 1                      └─────────────────────────────┘
                │ N                      (no FK to users; internal cache)
                ▼
┌─────────────────────────────┐
│   conversation_messages      │
│------------------------------|
│ id (uuid) PK                 │
│ conversation_id (uuid) FK    │
│ role (user|assistant|system) │
│ content                      │
│ intent, agent_name           │
│ metadata (JSONB), created_at │
└─────────────────────────────┘

        │
        │ users 1 ── N notification_logs
        ▼
┌─────────────────────────────┐
│     notification_logs        │
│------------------------------|
│ id (uuid) PK                 │
│ user_id (uuid) FK            │
│ type                         │
│ channel, subject             │
│ ref_id (uuid, nullable)      │
│ status, sent_at              │
│ metadata (text)              │
└─────────────────────────────┘
```

**Quan hệ tóm tắt:**
- **users** → passengers (1–N), bookings (1–N), flight_searches (1–N), conversations (1–N), user_preferences (1–1), calendar_events (1–N), notification_logs (1–N).
- **passengers** → bookings (1–N); user_preferences.default_passenger_id → passengers (N–1).
- **bookings** → booking_flights (1–N), payments (1–N), calendar_events (1–N).
- **conversations** → conversation_messages (1–N).
- **flight_offer_cache**: không FK; dùng nội bộ bởi Flight Search Agent.

---

*Tài liệu này đủ để triển khai services cho từng API; khi implement nhớ bám schema trong `app.schemas` và model trong `app.models`.*
