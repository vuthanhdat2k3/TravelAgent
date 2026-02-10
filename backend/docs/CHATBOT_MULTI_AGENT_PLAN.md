# Kế hoạch Chatbot Multi-Agent – Travel Agent (Simplified)

## 1. Tổng quan kiến trúc (3 Agents)

```
                        ┌──────────────────────────────┐
      User ────────────►│  [1] Router Agent             │
      (message)         │  - Intent detection (LLM)     │
                        │  - Slot extraction             │
                        │  - State management            │
                        │  - Multi-turn slot filling     │
                        │  - Response shaping            │
                        └──────────┬───────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
    ┌──────────────────────────┐   ┌──────────────────────────┐
    │ [2] Flight Agent          │   │ [3] Assistant Agent       │
    │ (LLM + Tools)             │   │ (LLM + Tools)             │
    │                           │   │                           │
    │ Tools:                    │   │ Tools:                    │
    │ • search_flights          │   │ • get_passengers          │
    │ • get_cached_offers       │   │ • get_bookings            │
    │ • create_booking          │   │ • get_preferences         │
    │ • cancel_booking          │   │ • get_calendar_events     │
    │                           │   │ • general_knowledge       │
    └──────────────────────────┘   └──────────────────────────┘
              │                             │
              ▼                             ▼
    ┌──────────────────┐         ┌──────────────────┐
    │ Amadeus API +    │         │ Database (via     │
    │ Flight Service   │         │ existing services)│
    │ + Offer Cache    │         │                   │
    └──────────────────┘         └──────────────────┘
```

---

## 2. Chi tiết từng Agent

### 2.1 Router Agent (Orchestrator)

| Trách nhiệm | Chi tiết |
|-------------|----------|
| **Intent detection** | Phân loại: `flight_search`, `book_flight`, `view_booking`, `cancel_booking`, `view_passengers`, `view_preferences`, `general_question` |
| **Slot extraction** | Trích xuất: origin, destination, date, passenger_id, booking_id... |
| **State management** | Lưu context conversation: intent, slots, last_offer_ids, step |
| **Multi-turn** | Thu thập đủ slots trước khi gọi sub-agent |
| **Delegation** | Gọi Flight Agent hoặc Assistant Agent tùy intent |
| **Response shaping** | Gộp kết quả, trả reply thân thiện + suggested_actions |

**LLM**: Gemini (hoặc user-configured) – dùng structured output (JSON) cho intent + slots.

### 2.2 Flight Agent

| Trách nhiệm | Chi tiết |
|-------------|----------|
| **Search flights** | Gọi `flight_service.search_flights()` → trả list offers |
| **Get cached offers** | Lấy offers đã cache theo search key |
| **Book flight** | Validate + gọi `booking_service.create_booking()` |
| **Cancel booking** | Gọi `booking_service.cancel_booking()` |
| **Response** | Format kết quả thành text dễ đọc cho user |

**LLM riêng**: Dùng để hiểu context và quyết định tool nào cần gọi.
**Tools**: Wrapped từ existing services (flight_service, booking_service).

### 2.3 Assistant Agent

| Trách nhiệm | Chi tiết |
|-------------|----------|
| **Passengers** | Liệt kê, tìm passenger info |
| **Bookings** | Xem danh sách booking, chi tiết booking |
| **Preferences** | Đọc preferences của user |
| **Calendar** | Xem lịch bay |
| **General QA** | Trả lời câu hỏi du lịch, visa, thời tiết... |

**LLM riêng**: Dùng để trả lời tự nhiên và chọn tool phù hợp.
**Tools**: Wrapped từ existing services.

---

## 3. Luồng hoạt động

### Use case A: Tìm chuyến bay
1. User: "Tìm vé HN đi SG ngày 20/12"
2. **Router**: intent=`flight_search`, slots={origin:"HAN", destination:"SGN", date:"2025-12-20"} → đủ slots
3. Router → **Flight Agent**.search_flights(origin, destination, date)
4. Flight Agent gọi Amadeus → cache → trả list offers
5. Router lưu state `last_offer_ids`, trả reply danh sách chuyến

### Use case B: Đặt vé
1. User: "Đặt chuyến số 2"
2. **Router**: intent=`book_flight`, state có `last_offer_ids` → offer_id = offers[1]
3. Router → **Assistant Agent**: get_passengers → lấy default passenger
4. Router → **Flight Agent**: create_booking(offer_id, passenger_id)
5. Flight Agent validate + tạo booking, trả booking_reference
6. Router trả reply xác nhận

### Use case C: Xem lịch trình / Câu hỏi chung
1. User: "Booking của tôi?"
2. **Router**: intent=`view_booking` → **Assistant Agent**
3. Assistant Agent: get_bookings(user_id) → format reply

---

## 4. Memory

- **Conversation history**: Lưu trong DB (`conversation_messages`)
- **Working memory**: `conversation.state` (JSONB) – lưu slots, last_offer_ids, current step
- **Mỗi agent call**: Nhận conversation history + state → có đầy đủ context

---

## 5. Thứ tự triển khai

1. **Agent tools** – wrap existing services thành LangChain tools
2. **Flight Agent** – LLM + tools (search, book, cancel)
3. **Assistant Agent** – LLM + tools (passengers, bookings, preferences, general)
4. **Router Agent** – Intent detection + delegation + state management
5. **Tích hợp** – Replace `chat_service.send_message_stream()` để sử dụng Router Agent

---

*Giảm từ 7-8 agents xuống 3 agents, mỗi agent có LLM riêng, tận dụng existing services làm tools.*

---

## 6. Cấu trúc file đã triển khai

- **`app/agents/`**:
  - `orchestrator.py`: Main entry point, khởi tạo 3 LLM và chạy pipeline.
  - `router_agent.py`: Logic phân loại intent và điều phối.
  - `flight_agent.py`: Agent chuyên trách tìm kiếm/đặt vé.
  - `assistant_agent.py`: Agent hỗ trợ thông tin (bookings, passengers, general QA).
  - `tools.py`: Các hàm tool wrap lại service logic (search_flights, create_booking, etc.).

- **Integration**:
  - `app/services/chat_service.py`: Đã cập nhật `send_message` và `send_message_stream` để gọi `orchestrator`.
  - `main.py`: Đã thêm hook startup (`startup_event`) để inject DB session factory vào tools.

## 7. Hướng dẫn mở rộng

Để thêm tính năng mới:
1. Viết service logic trong `app/services/`.
2. Wrap service function thành tool trong `app/agents/tools.py`.
3. Đăng ký tool vào list `FLIGHT_TOOLS` hoặc `ASSISTANT_TOOLS`.
4. (Optional) Cập nhật prompt của Router Agent (`app/agents/router_agent.py`) nếu có intent mới.

