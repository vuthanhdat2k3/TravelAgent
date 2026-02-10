"""
Router Agent – the central orchestrator of the multi-agent system.

Responsibilities:
  1. Intent detection (via LLM structured output)
  2. Slot extraction (origin, destination, date, etc.)
  3. Multi-turn slot filling (ask for missing info)
  4. Delegation to Flight Agent or Assistant Agent
  5. State management (update conversation.state)
  6. Response shaping (combine agent results with suggestions)
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.flight_agent import run_flight_agent
from app.agents.assistant_agent import run_assistant_agent

logger = logging.getLogger(__name__)

# ── Intent definitions ──────────────────────────────────────────────────────

INTENTS = [
    "flight_search",       # Tìm chuyến bay
    "book_flight",         # Đặt vé
    "cancel_booking",      # Hủy booking
    "view_booking",        # Xem booking
    "add_to_calendar",     # Thêm booking vào lịch
    "send_email",          # Gửi thông tin chuyến bay qua email
    "view_passengers",     # Xem hành khách
    "view_preferences",    # Xem sở thích
    "view_calendar",       # Xem lịch bay
    "general_question",    # Câu hỏi chung / tư vấn du lịch
    "greeting",            # Chào hỏi
]

# Intent → Agent mapping
FLIGHT_INTENTS = {"flight_search", "book_flight", "cancel_booking"}
ASSISTANT_INTENTS = {"view_booking", "view_passengers", "view_preferences", "view_calendar", "add_to_calendar", "send_email"}
ROUTER_ONLY_INTENTS = {"greeting", "general_question"}

# ── Slot definitions per intent ─────────────────────────────────────────────

REQUIRED_SLOTS = {
    "flight_search": ["origin", "destination", "depart_date"],
    "book_flight": ["offer_index", "offer_id", "flight_number"],  # offer_index OR offer_id OR flight_number
    "cancel_booking": ["booking_id"],
    "view_booking": [],
    "add_to_calendar": ["booking_id"],  # Cần booking_id để thêm vào lịch
    "send_email": [],  # booking_id optional – nếu không có sẽ gửi từ conversation context
    "view_passengers": [],
    "view_preferences": [],
    "view_calendar": [],
    "general_question": [],
    "greeting": [],
}

# ── Router System Prompt ────────────────────────────────────────────────────

ROUTER_SYSTEM_PROMPT = """Bạn là Router Agent – bộ não trung tâm của Travel Agent AI.

Nhiệm vụ: Phân tích tin nhắn của user, trích xuất intent và slots, rồi trả về JSON.

## Danh sách Intent:
- `flight_search`: User muốn tìm chuyến bay (VD: "Tìm vé HN đi SG ngày 20/12")
- `book_flight`: User muốn đặt vé MỚI (VD: "Đặt chuyến số 2", "Book chuyến đầu tiên", "Đặt chuyến VJ145")
- `cancel_booking`: User muốn hủy booking (VD: "Hủy booking ABC123")
- `view_booking`: User muốn xem bookings (VD: "Booking của tôi?", "Xem đơn đặt vé")
- `add_to_calendar`: User muốn THÊM booking ĐÃ CÓ vào lịch Google Calendar (VD: "Thêm booking này vào lịch", "Sync vào calendar", "Thêm vào lịch trình")
- `send_email`: User muốn gửi thông tin chuyến bay qua email (VD: "Gửi thông tin chuyến bay tới email", "Email booking cho tôi", "Gửi vé qua mail")
- `view_passengers`: User hỏi về hành khách (VD: "Danh sách hành khách", "Ai là hành khách?")
- `view_preferences`: User hỏi sở thích (VD: "Sở thích bay của tôi?")
- `view_calendar`: User hỏi lịch bay (VD: "Lịch bay tuần này?")
- `general_question`: Câu hỏi chung về du lịch (VD: "Thời tiết Nhật tháng 12?", "Visa đi Hàn?")
- `greeting`: Chào hỏi (VD: "Xin chào", "Hi")

## Slots cần trích xuất:
- `origin`: Mã sân bay IATA (3 ký tự) hoặc tên thành phố. Chuyển đổi: Hà Nội/HN → HAN, Sài Gòn/SG/TP HCM → SGN, Đà Nẵng → DAD, Nha Trang → CXR, Phú Quốc → PQC, Huế → HUI, Hải Phòng → HPH, Cần Thơ → VCA
- `destination`: Tương tự origin
- `depart_date`: Ngày khởi hành (YYYY-MM-DD). Nếu user nói "ngày 20/12" thì dùng năm hiện tại hoặc năm tới. Nếu nói "tuần sau" thì tính từ hôm nay.
- `adults`: Số người lớn (default 1)
- `travel_class`: ECONOMY hoặc BUSINESS (default ECONOMY)
- `offer_index`: Số thứ tự chuyến bay user chọn (1-based)
- `offer_id`: UUID của chuyến bay (nếu user cung cấp trực tiếp)
- `flight_number`: Mã số hiệu chuyến bay (VD: "VJ145", "VN123", "VJ 145") - format có thể có space hoặc không
- `booking_id`: UUID hoặc mã booking
- `booking_reference`: Mã tham chiếu booking

## Quy tắc:
1. Trả về DUY NHẤT một JSON object, KHÔNG kèm text nào khác
2. Nếu thiếu slot bắt buộc, set `missing_slots` kèm câu hỏi tiếng Việt
3. Xem xét context từ conversation history để điền slots:
   - Với `book_flight`: Nếu user nói "đặt chuyến số X", lấy offer_index từ X. Nếu nói "đặt chuyến VJ145", lấy flight_number="VJ145"
   - Với `add_to_calendar`: Nếu user nói "thêm booking này", tìm booking_id trong lịch sử chat gần nhất (tìm pattern về booking_id, booking_reference)
   - Với `cancel_booking`: Tìm booking_id/booking_reference từ context
4. Với `book_flight`: Cần `offer_index` HOẶC `offer_id` HOẶC `flight_number` (1 trong 3)
5. Với `add_to_calendar`: Cần `booking_id` - có thể lấy từ state hoặc conversation history
6. Phân biệt rõ: `book_flight` = đặt vé MỚI, `add_to_calendar` = thêm booking ĐÃ TẠO vào lịch
7. Năm hiện tại: 2026

## Format output (JSON):
{
  "intent": "<intent_name>",
  "confidence": <0.0-1.0>,
  "slots": {
    "origin": "HAN",
    "destination": "SGN",
    "depart_date": "2026-12-20",
    "adults": 1,
    "travel_class": "ECONOMY",
    "offer_index": null,
    "offer_id": null,
    "flight_number": null,
    "booking_id": null
  },
  "missing_slots": [],
  "follow_up_question": null
}

Nếu thiếu slots bắt buộc, ví dụ:
{
  "intent": "flight_search",
  "confidence": 0.8,
  "slots": {"origin": "HAN", "destination": null, "depart_date": null},
  "missing_slots": ["destination", "depart_date"],
  "follow_up_question": "Bạn muốn bay đến đâu và vào ngày nào? ✈️"
}
"""

# ── Greeting / general response prompt ──────────────────────────────────────

RESPONSE_SHAPING_PROMPT = """Bạn là Travel Agent AI – trợ lý du lịch thân thiện.

Dựa trên kết quả từ sub-agent, hãy tạo phản hồi hoàn chỉnh cho user.

Quy tắc:
• Trả lời bằng tiếng Việt, thân thiện, ngắn gọn
• Sử dụng emoji phù hợp
• Nếu có danh sách kết quả, giữ nguyên format
• Thêm gợi ý hành động tiếp theo (suggested actions) nếu phù hợp
• Với greeting: chào đón, giới thiệu khả năng
"""


# ── Main Router ─────────────────────────────────────────────────────────────


async def route_message(
    router_llm: BaseChatModel,
    flight_llm: BaseChatModel,
    assistant_llm: BaseChatModel,
    user_message: str,
    user_id: str,
    conversation_history: list[dict],
    state: dict,
) -> tuple[str, dict, str | None]:
    """
    Route a user message through the multi-agent system.

    Parameters
    ----------
    router_llm : BaseChatModel – LLM for intent detection
    flight_llm : BaseChatModel – LLM for Flight Agent
    assistant_llm : BaseChatModel – LLM for Assistant Agent
    user_message : str – The user's message
    user_id : str – User UUID
    conversation_history : list[dict] – Prior messages
    state : dict – Conversation state (mutable, will be updated)

    Returns
    -------
    tuple[str, dict, str | None]
        (response_text, updated_state, detected_intent)
    """

    # ── Step 1: Intent Detection + Slot Extraction ──────────────────────
    intent_result = await _detect_intent(router_llm, user_message, conversation_history, state)

    intent = intent_result.get("intent", "general_question")
    slots = intent_result.get("slots", {})
    missing_slots = intent_result.get("missing_slots", [])
    follow_up = intent_result.get("follow_up_question")

    logger.info(f"Router: intent={intent}, slots={slots}, missing={missing_slots}")

    # Update state with detected info
    state["current_intent"] = intent
    if slots:
        state["slots"] = {**state.get("slots", {}), **{k: v for k, v in slots.items() if v is not None}}

    # Special handling: auto-fill booking_id from last booking if needed
    if intent in ("add_to_calendar", "send_email") and not slots.get("booking_id"):
        last_booking_id = state.get("last_booking_id")
        if last_booking_id:
            slots["booking_id"] = last_booking_id
            state["slots"]["booking_id"] = last_booking_id
            logger.info(f"Auto-filled booking_id from state: {last_booking_id}")
            # Remove from missing_slots if it was there
            if "booking_id" in missing_slots:
                missing_slots.remove("booking_id")

    # ── Step 2: Check for missing slots → ask follow-up ─────────────────
    if missing_slots and follow_up:
        state["pending_slots"] = missing_slots
        return follow_up, state, intent

    # ── Step 3: Delegate to appropriate agent ───────────────────────────
    response_text = ""
    detected_intent = intent

    if intent in FLIGHT_INTENTS:
        task = _build_flight_task(intent, state.get("slots", {}), state)
        response_text = await run_flight_agent(
            llm=flight_llm,
            task=task,
            user_id=user_id,
            conversation_history=conversation_history,
            state=state,
        )

        # Save offer IDs to state if flight search
        if intent == "flight_search":
            _extract_offer_ids(response_text, state)
        
        # Save booking ID to state if booking created
        elif intent == "book_flight":
            _extract_booking_id(response_text, state)

    elif intent in ASSISTANT_INTENTS:
        task = _build_assistant_task(intent, state.get("slots", {}))
        response_text = await run_assistant_agent(
            llm=assistant_llm,
            task=task,
            user_id=user_id,
            conversation_history=conversation_history,
            state=state,
        )

    elif intent == "greeting":
        response_text = await _handle_greeting(router_llm, user_message)

    elif intent == "general_question":
        # For general questions, use Assistant Agent (it can answer without tools)
        response_text = await run_assistant_agent(
            llm=assistant_llm,
            task=f"Trả lời câu hỏi du lịch: {user_message}",
            user_id=user_id,
            conversation_history=conversation_history,
            state=state,
        )

    else:
        response_text = await _handle_greeting(router_llm, user_message)

    return response_text, state, detected_intent


# ── Private helpers ─────────────────────────────────────────────────────────


async def _detect_intent(
    llm: BaseChatModel,
    user_message: str,
    conversation_history: list[dict],
    state: dict,
) -> dict:
    """Use the Router LLM to detect intent and extract slots."""
    messages = [SystemMessage(content=ROUTER_SYSTEM_PROMPT)]

    # Add recent history for context (last 4 messages)
    for msg in conversation_history[-4:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    # Add current state context
    state_info = ""
    if state.get("current_intent"):
        state_info += f"\nIntent trước đó: {state['current_intent']}"
    if state.get("slots"):
        state_info += f"\nSlots đã có: {json.dumps(state['slots'], ensure_ascii=False)}"
    if state.get("last_offer_ids"):
        state_info += f"\nCó {len(state['last_offer_ids'])} chuyến bay đã tìm được trước đó"
    if state.get("pending_slots"):
        state_info += f"\nĐang chờ user cung cấp: {state['pending_slots']}"

    prompt = f"State hiện tại: {state_info}\n\nTin nhắn mới của user: {user_message}"
    messages.append(HumanMessage(content=prompt))

    try:
        response = await llm.ainvoke(messages)
        content = response.content if hasattr(response, "content") else str(response)

        # Parse JSON from response
        # Try to extract JSON from the response (handle markdown code blocks)
        json_str = content.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        result = json.loads(json_str)
        return result

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Router intent detection failed: {e}, raw: {content if 'content' in dir() else 'N/A'}")
        # Fallback: treat as general question
        return {
            "intent": "general_question",
            "confidence": 0.5,
            "slots": {},
            "missing_slots": [],
            "follow_up_question": None,
        }


def _build_flight_task(intent: str, slots: dict, state: dict) -> str:
    """Build a task description for the Flight Agent."""
    if intent == "flight_search":
        origin = slots.get("origin", "?")
        destination = slots.get("destination", "?")
        depart_date = slots.get("depart_date", "?")
        adults = slots.get("adults", 1)
        travel_class = slots.get("travel_class", "ECONOMY")
        return (
            f"Tìm chuyến bay từ {origin} đến {destination} "
            f"ngày {depart_date}, {adults} hành khách, hạng {travel_class}."
        )

    elif intent == "book_flight":
        offer_id_manual = slots.get("offer_id")
        offer_index = slots.get("offer_index")
        flight_number = slots.get("flight_number")
        last_offers = state.get("last_offer_ids", [])

        if offer_id_manual:
             return f"Đặt vé cho offer_id: {offer_id_manual}. Lấy passenger mặc định của user."
        elif flight_number:
            # User chọn theo mã chuyến bay (VD: VJ145)
            # QUAN TRỌNG: Cần truyền origin/destination/depart_date từ search context
            origin = slots.get("origin", "?")
            destination = slots.get("destination", "?")
            depart_date = slots.get("depart_date", "")
            return (
                f"Tìm offer_id của chuyến bay {flight_number} bằng tool get_offer_by_flight_number với:\n"
                f"- flight_number: {flight_number}\n"
                f"- origin: {origin}\n"
                f"- destination: {destination}\n"
                f"- depart_date: {depart_date}\n"
                f"Sau đó đặt vé. Lấy passenger mặc định của user."
            )
        elif offer_index and last_offers:
            idx = int(offer_index) - 1  # Convert 1-based to 0-based
            if 0 <= idx < len(last_offers):
                offer_id = last_offers[idx]
                return f"Đặt vé cho offer_id: {offer_id}. Lấy passenger mặc định của user."
            else:
                return f"User chọn chuyến số {offer_index} nhưng chỉ có {len(last_offers)} chuyến. Thông báo lỗi."
        else:
            return "User muốn đặt vé nhưng chưa có kết quả tìm kiếm trước đó. Yêu cầu tìm chuyến bay trước."

    elif intent == "cancel_booking":
        booking_id = slots.get("booking_id", "")
        return f"Hủy booking với ID: {booking_id}"

    return f"Xử lý yêu cầu: {intent} với slots: {json.dumps(slots, ensure_ascii=False)}"


def _build_assistant_task(intent: str, slots: dict) -> str:
    """Build a task description for the Assistant Agent."""
    if intent == "view_booking":
        status_filter = slots.get("status_filter", "")
        return f"Xem danh sách bookings của user.{f' Lọc theo trạng thái: {status_filter}' if status_filter else ''}"
    elif intent == "view_passengers":
        return "Xem danh sách hành khách đã đăng ký của user."
    elif intent == "view_preferences":
        return "Xem sở thích chuyến bay của user."
    elif intent == "view_calendar":
        return "Xem lịch bay / calendar events của user."
    elif intent == "add_to_calendar":
        booking_id = slots.get("booking_id", "")
        return f"CALL TOOL: add_booking_to_calendar với booking_id={booking_id}. Thêm booking này vào Google Calendar của user. BẮT BUỘC phải gọi tool add_booking_to_calendar, không được trả lời text trực tiếp."
    elif intent == "send_email":
        booking_id = slots.get("booking_id", "")
        return (
            f"CALL TOOL: send_flight_info_email để gửi thông tin chuyến bay tới email của user.\n"
            f"- Nếu có booking_id ({booking_id or 'không có'}), truyền booking_id vào tool.\n"
            f"- Nếu không có booking_id, hãy dùng get_bookings để lấy booking gần nhất rồi gửi.\n"
            f"BẮT BUỘC phải gọi tool send_flight_info_email."
        )

    return f"Xử lý: {intent}"


async def _handle_greeting(llm: BaseChatModel, user_message: str) -> str:
    """Handle greeting messages directly."""
    messages = [
        SystemMessage(content=RESPONSE_SHAPING_PROMPT),
        HumanMessage(content=f"User chào: \"{user_message}\". Hãy chào lại và giới thiệu khả năng."),
    ]
    try:
        response = await llm.ainvoke(messages)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        logger.error(f"Greeting handler error: {e}")
        return (
            "Xin chào! 👋 Tôi là Travel Agent AI, sẵn sàng hỗ trợ bạn:\n\n"
            "✈️ Tìm kiếm chuyến bay\n"
            "🎫 Đặt vé & quản lý booking\n"
            "📋 Xem thông tin hành khách\n"
            "📅 Xem lịch bay\n"
            "💡 Tư vấn du lịch\n\n"
            "Bạn cần giúp gì hôm nay?"
        )


def _extract_offer_ids(response_text: str, state: dict) -> None:
    """Try to extract offer IDs from flight search response and save to state."""
    # The Flight Agent's tool returns JSON with offer_id fields.
    # We try to find them in the response for state tracking.
    try:
        # Look for offer IDs in a simple pattern
        import re
        # Match patterns like "offer_id": "some-id" or offer IDs in the text
        ids = re.findall(r'"offer_id"\s*:\s*"([^"]+)"', response_text)
        if ids:
            state["last_offer_ids"] = ids
            logger.info(f"Extracted {len(ids)} offer IDs to state")
    except Exception:
        pass


def _extract_booking_id(response_text: str, state: dict) -> None:
    """Try to extract booking ID from booking creation response and save to state."""
    try:
        import re
        # Match patterns like "booking_id": "uuid" in JSON response
        match = re.search(r'"booking_id"\s*:\s*"([0-9a-f-]{36})"', response_text)
        if match:
            booking_id = match.group(1)
            state["last_booking_id"] = booking_id
            logger.info(f"Extracted booking_id to state: {booking_id}")
    except Exception:
        pass
