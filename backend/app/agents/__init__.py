"""
Multi-Agent System for Travel Agent chatbot.

Architecture:
  - Router Agent: Intent detection, slot filling, delegation
  - Flight Agent: Search flights, book, cancel (with tools)
  - Assistant Agent: View bookings/passengers/preferences, general Q&A (with tools)

Each agent has its own LLM brain and operates independently.
The Router coordinates them based on detected user intent.
"""

from app.agents.router_agent import route_message
from app.agents.tools import set_db_session_factory

__all__ = ["route_message", "set_db_session_factory"]
