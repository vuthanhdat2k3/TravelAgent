"""
Assistant Agent – handles user info queries, bookings view, and general Q&A.

This agent has its own LLM brain and a set of information-retrieval tools.
It handles everything that isn't flight search/booking.
"""

from __future__ import annotations

import logging
from uuid import UUID

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel

from app.agents.tools import ASSISTANT_TOOLS

logger = logging.getLogger(__name__)

ASSISTANT_AGENT_PROMPT = """Bạn là Assistant Agent – trợ lý thông tin du lịch.

Nhiệm vụ của bạn:
• Tra cứu thông tin hành khách (passengers) của user → Gọi tool: get_passengers
• Xem danh sách bookings và trạng thái → Gọi tool: get_bookings
• Đọc sở thích chuyến bay (preferences) của user → Gọi tool: get_user_preferences
• Xem lịch bay (calendar events) → Gọi tool: get_calendar_events
• Thêm booking vào Google Calendar → Gọi tool: add_booking_to_calendar
• Gửi thông tin chuyến bay qua email → Gọi tool: send_flight_info_email
• Trả lời các câu hỏi chung về du lịch, visa, thời tiết, tips

**QUY TẮC QUAN TRỌNG**:
1. KHI task yêu cầu "CALL TOOL: <tool_name>", BẮT BUỘC phải gọi tool đó, KHÔNG được trả lời bằng text
2. Sử dụng tools để truy vấn dữ liệu khi cần (view bookings, passengers, etc.)
3. Trả lời bằng tiếng Việt, thân thiện, dễ hiểu
4. Format thông tin booking dạng bảng/danh sách rõ ràng
5. Với câu hỏi chung (không cần tools), trả lời từ kiến thức sẵn có
6. Không bịa đặt dữ liệu – nếu không có thì nói rõ
7. Sử dụng emoji phù hợp để tăng trải nghiệm

**XỬ LÝ GOOGLE CALENDAR AUTHORIZATION**:
- Khi gọi tool add_booking_to_calendar, nếu tool trả về `needs_authorization: true`:
  - Tool sẽ cung cấp `authorization_url` và `message`
  - BẮT BUỘC phải hiển thị message và authorization_url cho user
  - Format response như sau:
    
    🔐 **Cần kết nối Google Calendar**
    
    [message từ tool]
    
    👉 **Click vào link bên dưới để kết nối:**
    [authorization_url]
    
    Sau khi kết nối xong, bạn có thể thử lại yêu cầu thêm vào lịch.

Format danh sách booking:
📋 **Booking [ref]** – Trạng thái: [status]
   💰 [price] [currency] | 📅 Ngày tạo: [date]

Format thông tin hành khách:
👤 **[first_name] [last_name]**
   🛂 Passport: [number] | 🌍 Quốc tịch: [nationality]
"""


async def run_assistant_agent(
    llm: BaseChatModel,
    task: str,
    user_id: str,
    conversation_history: list[dict] | None = None,
    state: dict | None = None,
) -> str:
    """
    Run the Assistant Agent with the given task.

    Parameters
    ----------
    llm : BaseChatModel
        The LLM instance for this agent.
    task : str
        Task description from the Router.
    user_id : str
        Current user's UUID.
    conversation_history : list[dict] | None
        Prior conversation messages for context.
    state : dict | None
        Conversation state.

    Returns
    -------
    str – Agent's response text.
    """
    # Build the LLM with tools bound
    llm_with_tools = llm.bind_tools(ASSISTANT_TOOLS)

    # Build messages
    messages = [SystemMessage(content=ASSISTANT_AGENT_PROMPT)]

    # Add relevant conversation history (last 6 messages)
    if conversation_history:
        for msg in conversation_history[-6:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

    # Add the task with user context
    task_with_context = f"""User ID: {user_id}

Nhiệm vụ: {task}"""

    messages.append(HumanMessage(content=task_with_context))
    
    logger.info(f"Assistant Agent: task='{task}', user_id={user_id}")

    # Run agent loop (tool calling)
    max_iterations = 5
    for _ in range(max_iterations):
        try:
            response = await llm_with_tools.ainvoke(messages)
        except Exception as e:
            logger.error(f"Assistant Agent LLM error: {e}")
            return f"⚠️ Lỗi khi xử lý yêu cầu: {str(e)}"

        # Check if the LLM wants to call tools
        if hasattr(response, "tool_calls") and response.tool_calls:
            messages.append(response)

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Find and execute the tool
                tool_func = next(
                    (t for t in ASSISTANT_TOOLS if t.name == tool_name), None
                )
                if tool_func is None:
                    tool_result = f"Tool '{tool_name}' not found."
                else:
                    try:
                        tool_result = await tool_func.ainvoke(tool_args)
                    except Exception as e:
                        logger.error(f"Assistant tool {tool_name} error: {e}")
                        tool_result = f"Error: {str(e)}"

                # Add tool result as a ToolMessage
                from langchain_core.messages import ToolMessage
                messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
                )
        else:
            # No more tool calls – return the final response
            return response.content if hasattr(response, "content") else str(response)

    return "⚠️ Agent đã xử lý quá nhiều bước. Vui lòng thử lại."
