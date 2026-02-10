# Kế hoạch Chatbot Multi-Agent – Đặt vé máy bay

## 1. Tổng quan kiến trúc

```
                    ┌─────────────────────────┐
    User ──────────►│  Router / Orchestrator  │
                    │  (intent, state, flow)  │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────┐
│ Flight Search   │   │ Booking Agent   │   │ Itinerary/Calendar   │
│ Agent           │   │                 │   │ Agent                │
└────────┬────────┘   └────────┬────────┘   └──────────┬──────────┘
         │                     │                        │
         ▼                     ▼                        ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────┐
│ Amadeus API     │   │ Amadeus Booking  │   │ Google Calendar API  │
│ + Offer Cache   │   │ + Validation     │   │                      │
└────────┬────────┘   └────────┬────────┘   └──────────┬──────────┘
         │                     │                        │
         └─────────────────────┼────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │     DB Agent        │
                    │ (read/write guard)  │
                    └────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────┐
│ User Profile    │   │ Policy/         │   │ Notification        │
│ Agent           │   │ Validation      │   │ Agent (optional)    │
└─────────────────┘   └─────────────────┘   └─────────────────────┘
```

---

## 2. Core Agents (bắt buộc)

### 2.1 Router / Orchestrator Agent

| Trách nhiệm | Chi tiết |
|-------------|----------|
| **Intent detection** | Phân loại câu user: `flight_search`, `book_flight`, `view_booking`, `cancel_booking`, `add_to_calendar`, `ask_itinerary`, `profile_update`, `general_question`, `unknown` |
| **State management** | Lưu context: `conversation_id`, `current_intent`, `last_offer_id`, `selected_passenger_id`, `step`, `pending_slots` (origin, destination, date...) |
| **Flow control** | Quyết định gọi agent nào, xử lý multi-step (thu thập origin/destination/date trước khi gọi Flight Agent) |
| **Response shaping** | Gộp kết quả từ sub-agents, trả reply thân thiện + suggested_actions (quick replies) |

**Intent enum (gợi ý):**  
`flight_search` \| `book_flight` \| `view_booking` \| `cancel_booking` \| `add_to_calendar` \| `ask_itinerary` \| `profile_update` \| `general_question` \| `unknown`

### 2.2 Flight Search Agent

| Trách nhiệm | Chi tiết |
|-------------|----------|
| **Gọi Amadeus** | Flight Offers API (origin, destination, date, adults, class) |
| **Normalize** | Chuẩn hóa segments, price, duration; filter/sort theo preference nếu có |
| **Cache** | Lưu offers vào `flight_offer_cache` với TTL (vd 15–30 phút), key = hash(search params) |
| **Output** | Danh sách `FlightOffer` (offer_id, price, segments) để user chọn |

### 2.3 Booking Agent

| Trách nhiệm | Chi tiết |
|-------------|----------|
| **Input** | `offer_id` (từ cache/Amadeus), `passenger_id` (hoặc thông tin từ Profile Agent) |
| **Validation** | Gọi Policy/Validation Agent trước khi book |
| **Amadeus** | Gọi Order/Booking API (nếu có), nhận PNR/booking_reference |
| **DB** | Tạo `Booking` + `BookingFlight`, cập nhật status |
| **Hậu xử lý** | Gọi Calendar Agent (add event), có thể trigger Notification Agent |

### 2.4 Itinerary / Calendar Agent

| Trách nhiệm | Chi tiết |
|-------------|----------|
| **Tạo event** | Từ booking (flights, times, origin/destination) |
| **Google Calendar** | Create event, lấy `google_event_id` |
| **DB** | Lưu `calendar_events` (booking_id, google_event_id, user_id) |

### 2.5 User Profile Agent

| Trách nhiệm | Chi tiết |
|-------------|----------|
| **CRUD passenger** | Tên, passport, quốc tịch, ngày sinh (bảng `passengers`) |
| **Preferences** | Cabin class, airline yêu thích, seat preference (bảng `user_preferences`) |
| **Fill missing** | Khi Booking Agent cần passenger info → Profile Agent trả về default passenger hoặc gợi ý điền |

---

## 3. Support Agents

### 3.1 DB Agent (SQL Tool Agent)

| Trách nhiệm | Chi tiết |
|-------------|----------|
| **Read** | Query bookings, passengers, flight_searches, calendar_events (theo user_id/session) |
| **Write** | Chỉ qua tool có sẵn: “create_booking”, “update_booking_status”, “save_offer_cache”, “save_calendar_event” — **không** cho LLM viết raw SQL tùy ý |
| **Guardrails** | Chỉ truy vấn đúng tenant (user_id từ session); whitelist bảng; không DROP/ALTER; rate limit |

### 3.2 Policy / Validation Agent

| Trách nhiệm | Chi tiết |
|-------------|----------|
| **Data validation** | Passport format, expiry > today; DOB hợp lý; origin ≠ destination; date >= today |
| **Compliance** | Không book khi thiếu passenger bắt buộc; không confirm khi chưa thanh toán (nếu áp dụng) |
| **Output** | `valid: bool`, `errors: list[str]` để Booking Agent quyết định tiếp hay hỏi lại user |

### 3.3 Notification Agent (optional)

| Trách nhiệm | Chi tiết |
|-------------|----------|
| **Channels** | Email (Resend), Telegram (optional) |
| **Events** | Booking confirmed, nhắc check-in trước giờ bay, cancel/refund |
| **Log** | Ghi `notification_log` (user_id, type, channel, sent_at, ref_id) |

---

## 4. Luồng use case chi tiết

### Use case A: Tìm chuyến bay

1. User gửi: "Tìm vé Hà Nội Sài Gòn ngày 20/12"
2. Router: intent = `flight_search`, extract slots (origin=HAN, destination=SGN, date=20/12) hoặc hỏi thiếu.
3. Router → **Flight Search Agent** với params.
4. Flight Agent: gọi Amadeus → normalize → **DB Agent** save cache → trả list offers.
5. Router lưu state: `last_search_offers = [offer_ids]`, `conversation_id`.
6. Reply user: danh sách chuyến + "Bạn muốn đặt chuyến nào? (số 1, 2, 3...)"

### Use case B: Đặt vé

1. User: "Đặt giúp tôi chuyến số 2"
2. Router: intent = `book_flight`, state có `last_search_offers` → offer_id = offers[1].
3. Router → **User Profile Agent**: lấy default passenger (hoặc list để chọn).
4. Router → **Policy/Validation Agent**: check passenger + offer hợp lệ.
5. Nếu invalid → reply lỗi / hỏi sửa. Nếu valid → **Booking Agent**.
6. Booking Agent: Amadeus Booking API → tạo `Booking` + `BookingFlight` (DB Agent).
7. Booking Agent → **Calendar Agent**: tạo event → lưu `calendar_events`.
8. (Optional) **Notification Agent**: gửi email xác nhận.
9. Reply: booking_reference + "Đã thêm vào lịch của bạn."

### Use case C: Xem lịch trình

1. User: "Lịch bay của tôi tuần này?"
2. Router: intent = `ask_itinerary`.
3. Router → **DB Agent**: query bookings (+ booking_flights) của user, filter theo khoảng ngày.
4. Reply: danh sách booking với chuyến, giờ, trạng thái; có thể kèm "Thêm vào Google Calendar?" (add_to_calendar).

### Use case D: Thêm vào Calendar (sau khi đã book)

1. User: "Thêm booking ABC123 vào lịch"
2. Router: intent = `add_to_calendar`, extract booking_reference hoặc booking_id.
3. DB Agent: lấy booking + flights.
4. Calendar Agent: tạo event Google → lưu `calendar_events`.
5. Reply: "Đã thêm vào Google Calendar."

---

## 5. State & persistence

- **Conversation**: mỗi session (web/telegram) = 1 `conversation`, có `state` (JSONB): intent, slots, last_offer_ids, selected_passenger_id, step.
- **Messages**: từng tin nhắn user/assistant lưu `conversation_messages` (role, content, intent, agent_name, metadata).
- **Offer cache**: `flight_offer_cache` (search_key, offer_id, payload, expires_at) để không gọi Amadeus lặp lại và để booking reference đúng offer.

---

## 6. Models & Schemas bổ sung (tóm tắt)

| Mục đích | Model | Schema chính |
|----------|--------|---------------|
| Chat session | Conversation, ConversationMessage | ChatRequest, ChatResponse, ConversationState |
| Intent / router | (enum trong code) | IntentResult, AgentContext |
| Cache offers | FlightOfferCache | (nội bộ agent) |
| Preference | UserPreference | UserPreferenceCreate, UserPreferenceResponse |
| Calendar | CalendarEvent | CalendarEventResponse |
| Notification | NotificationLog | NotificationLogResponse (optional) |

---

## 7. Thứ tự triển khai gợi ý

1. **Phase 1 – Nền tảng**  
   Models + schemas (conversation, message, offer_cache, user_preference, calendar_event, notification_log). API chat: nhận message, trả reply (có thể mock router).

2. **Phase 2 – Router + Flight**  
   Intent classification (LLM hoặc classifier). Flight Search Agent + Amadeus + cache. End-to-end "tìm chuyến bay".

3. **Phase 3 – Booking + Validation**  
   Profile Agent (đọc passenger/preference). Policy/Validation Agent. Booking Agent + DB. End-to-end "đặt vé".

4. **Phase 4 – Calendar + Notify**  
   Calendar Agent (Google). Notification Agent (email). DB Agent với guardrails.

5. **Phase 5 – Tối ưu**  
   Multi-turn slot filling, suggested_actions, error handling, logging.

---

*Tài liệu này dùng làm baseline; khi implement có thể chỉnh lại cho đúng stack (LangGraph/LangChain, FastAPI, DB đang dùng).*
