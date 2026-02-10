"""
Flight Agent – handles flight search, booking, and cancellation.

This agent has its own LLM brain and a set of flight-related tools.
It receives a task description from the Router and uses tools to fulfill it.
"""

from __future__ import annotations

import logging
import json
from uuid import UUID

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from app.agents.tools import FLIGHT_TOOLS

logger = logging.getLogger(__name__)

FLIGHT_AGENT_PROMPT = """Bạn là Flight Agent – chuyên gia tìm kiếm và đặt vé máy bay.

Nhiệm vụ của bạn:
• Tìm chuyến bay theo yêu cầu (origin, destination, date)
• Đặt vé cho hành khách
• Hủy booking khi được yêu cầu

Quy tắc:
• LUÔN sử dụng tools được cung cấp để thực hiện tác vụ
• Trả lời bằng tiếng Việt, ngắn gọn, rõ ràng
• Khi hiển thị kết quả tìm kiếm, format dạng danh sách có đánh số
• Hiển thị giá, thời gian bay, số điểm dừng cho mỗi chuyến
• Nếu không có kết quả, đề xuất thay đổi ngày hoặc điểm đến

**Khi user chọn chuyến bay theo MÃ SỐ HIỆU (VD: VJ145, VN123):**
⚠️ **QUAN TRỌNG**: Số hiệu chuyến bay KHÔNG đủ để xác định chuyến bay! VJ197 có thể bay nhiều route khác nhau.

1. Đọc origin, destination, depart_date từ task description (Router đã provide thông tin này)
2. Gọi tool với ĐẦY ĐỦ thông tin từ task:
   ```
   get_offer_by_flight_number(
       flight_number="VJ145",
       origin="HAN",           # BẮT BUỘC - Lấy từ task description
       destination="SGN",      # BẮT BUỘC - Lấy từ task description
       depart_date="2026-02-12" # Tùy chọn - Lấy từ task description nếu có
   )
   ```
3. Nếu tìm thấy (`found: true`), trích xuất `offer_id` từ `offer` trong kết quả
4. Nếu KHÔNG tìm thấy (`found: false`), thông báo user:
   "⚠️ Rất tiếc, tôi không tìm thấy chuyến bay [VJ145] cho route [HAN → SGN] ngày [12/02/2026].
   Vui lòng tìm kiếm chuyến bay trước, sau đó chọn bằng mã chuyến bay hoặc số thứ tự."
5. Tiếp tục quy trình đặt vé với offer_id đã lấy được

**Khi đặt vé (Booking)**:
  - Bạn CẦN có `passenger_id` (UUID) và `offer_id` (từ kết quả tìm kiếm hoặc từ get_offer_by_flight_number).
  - **TUYỆT ĐỐI KHÔNG tự bịa ra UUID hoặc dùng User ID làm Passenger ID.**
  - Quy trình lấy `passenger_id`:
    1. Gọi `get_user_preferences` để lấy `default_passenger_id`.
    2. Nếu không có (None), gọi `get_passengers` để xem danh sách hành khách của user.
    3. Nếu chỉ có 1 hành khách, có thể dùng ID đó. Nếu có nhiều, hãy liệt kê và hỏi user muốn đặt cho ai.
    4. Nếu không có hành khách nào, hãy thông báo user cần tạo hồ sơ hành khách trước.
  - Xác nhận lại thông tin chuyến bay (Số hiệu, hành trình, giá) và Tên hành khách trước khi gọi `create_booking`.
  - **TUYỆT ĐỐI KHÔNG tự bịa ra mã đặt chỗ (booking reference) hoặc thông báo thành công nếu tool trả về lỗi.**
  - Nếu tool trả về JSON có chứa `"error"`, bạn phải thông báo lỗi đó cho user và yêu cầu hỗ trợ hoặc sửa thông tin.
  - Chỉ xác nhận đặt vé thành công KHI VÀ CHỈ KHI tool `create_booking` trả về kết quả thành công kèm theo mã đặt chỗ thật từ hệ thống.

Format kết quả tìm chuyến bay:
✈️ **Chuyến [số]**: [airline] [flight_number]
   [origin] → [destination] | [departure] - [arrival]
   ⏱ [duration] phút | 🔄 [stops] điểm dừng | 💰 [price] [currency]



"""


async def run_flight_agent(
    llm: BaseChatModel,
    task: str,
    user_id: str,
    conversation_history: list[dict] | None = None,
    state: dict | None = None,
) -> str:
    """
    Run the Flight Agent with the given task.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM instance for this agent.
    task : str
        Task description from the Router (e.g. "search flights HAN to SGN on 2025-12-20")
    user_id : str
        Current user's UUID (passed to tools for DB queries).
    conversation_history : list[dict] | None
        Prior conversation messages for context.
    state : dict | None
        Conversation state (last_offer_ids, etc.)

    Returns
    -------
    str – Agent's response text.
    """
    # Build the LLM with tools bound
    llm_with_tools = llm.bind_tools(FLIGHT_TOOLS)

    # Build messages
    messages = [SystemMessage(content=FLIGHT_AGENT_PROMPT)]

    # Add relevant conversation history (last 6 messages for context)
    if conversation_history:
        for msg in conversation_history[-6:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

    # Add state context if available
    state_context = ""
    if state:
        if state.get("last_offer_ids"):
            state_context += f"\nCác offer ID đã tìm được trước đó: {state['last_offer_ids']}"
        if state.get("selected_offer_index"):
            state_context += f"\nUser đã chọn chuyến số: {state['selected_offer_index']}"

    # Add the task
    task_with_context = f"""User ID: {user_id}
{state_context}

Nhiệm vụ: {task}"""

    messages.append(HumanMessage(content=task_with_context))

    # Run agent loop (tool calling)
    max_iterations = 5
    for _ in range(max_iterations):
        try:
            response = await llm_with_tools.ainvoke(messages)
        except Exception as e:
            logger.error(f"Flight Agent LLM error: {e}")
            return f"⚠️ Lỗi khi xử lý yêu cầu: {str(e)}"

        # Check if the LLM wants to call tools
        if hasattr(response, "tool_calls") and response.tool_calls:
            messages.append(response)

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Find and execute the tool
                tool_func = next(
                    (t for t in FLIGHT_TOOLS if t.name == tool_name), None
                )
                if tool_func is None:
                    tool_result = f"Tool '{tool_name}' not found."
                else:
                    try:
                        tool_result = await tool_func.ainvoke(tool_args)
                    except Exception as e:
                        logger.error(f"Flight tool {tool_name} error: {e}")
                        tool_result = f"Error: {str(e)}"

                # Side-effect: Update state if tool was search_flights
                if tool_name == "search_flights" and state is not None:
                    try:
                        # tool_result is a JSON string
                        data = json.loads(str(tool_result))
                        offers = data.get("offers", [])
                        offer_ids = [offer.get("offer_id") for offer in offers if offer.get("offer_id")]
                        if offer_ids:
                            state["last_offer_ids"] = offer_ids
                            logger.info(f"FlightAgent: Updated state with {len(offer_ids)} offer IDs")
                        # Store structured flight offers for frontend card rendering
                        if offers:
                            state["_attachments"] = [{
                                "type": "flight_offers",
                                "offers": offers,
                            }]
                    except Exception as e:
                        logger.warning(f"Failed to update state from search_flights: {e}")

                # Side-effect: Capture booking success data for frontend card
                if tool_name == "create_booking" and state is not None:
                    try:
                        data = json.loads(str(tool_result))
                        if data.get("success"):
                            state["_attachments"] = [{
                                "type": "booking_success",
                                "booking_id": data.get("booking_id"),
                                "booking_reference": data.get("booking_reference"),
                                "status": data.get("status"),
                            }]
                            state["_suggested_actions"] = [
                                {
                                    "label": "📅 Lưu vào lịch trình",
                                    "payload": f"Thêm booking {data.get('booking_id')} vào lịch trình",
                                    "type": "calendar",
                                    "icon": "calendar",
                                },
                            ]
                    except Exception as e:
                        logger.warning(f"Failed to capture booking success: {e}")

                # Add tool result as a ToolMessage
                from langchain_core.messages import ToolMessage
                messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
                )
        else:
            # No more tool calls – return the final response
            return response.content if hasattr(response, "content") else str(response)

    return "⚠️ Agent đã xử lý quá nhiều bước. Vui lòng thử lại với yêu cầu đơn giản hơn."
