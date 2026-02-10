"""
LangChain Tools – wrap existing async services as sync tool functions.

Each tool receives primitive args (str, int) so the LLM can call them
directly via structured output.  Internally they obtain a DB session
and delegate to the corresponding service layer.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# ── Helpers ─────────────────────────────────────────────────────────────────

_DB_SESSION_FACTORY = None  # Will be set at startup


def set_db_session_factory(factory):
    """Set the async session factory (called once at app startup)."""
    global _DB_SESSION_FACTORY
    _DB_SESSION_FACTORY = factory


async def _get_db():
    """Get a fresh async DB session."""
    if _DB_SESSION_FACTORY is None:
        raise RuntimeError("DB session factory not configured. Call set_db_session_factory() first.")
    async with _DB_SESSION_FACTORY() as session:
        yield session


def _db_session():
    """Return an async context manager for a DB session.

    Usage:
        async with _db_session() as db:
            ...
    """
    if _DB_SESSION_FACTORY is None:
        raise RuntimeError("DB session factory not configured.")
    return _DB_SESSION_FACTORY()



# ── Flight Tools ────────────────────────────────────────────────────────────


@tool
async def search_flights(
    origin: str,
    destination: str,
    depart_date: str,
    adults: int = 1,
    travel_class: str = "ECONOMY",
    currency: str = "VND",
) -> str:
    """Search for flights between two airports on a given date.

    Args:
        origin: IATA airport code for departure (e.g. HAN, SGN, DAD)
        destination: IATA airport code for arrival (e.g. SGN, HAN, NRT)
        depart_date: Departure date in YYYY-MM-DD format
        adults: Number of adult passengers (1-9)
        travel_class: Cabin class – ECONOMY or BUSINESS
        currency: Currency code (default VND)

    Returns:
        JSON string with list of flight offers including price, duration, stops, segments.
    """
    logger.info(f"TOOL CALL: search_flights(origin={origin}, destination={destination}, date={depart_date}, "
                f"adults={adults}, class={travel_class})")
    from app.services.flight_service import search_flights as _search
    from app.schemas.flight import FlightSearchRequest

    try:
        search_req = FlightSearchRequest(
            origin=origin.upper(),
            destination=destination.upper(),
            depart_date=date.fromisoformat(depart_date),
            adults=adults,
            travel_class=travel_class,
            currency=currency,
        )

        async with _db_session() as db:
            search_result = await _search(db, search_req)

        offers = search_result.get("offers", [])

        if not offers:
            return json.dumps({"offers": [], "message": "Không tìm thấy chuyến bay nào."})

        # Serialize offers
        result = []
        for i, offer in enumerate(offers[:5], 1):  # Max 5 offers (match card count)
            offer_dict = offer if isinstance(offer, dict) else offer.model_dump() if hasattr(offer, 'model_dump') else vars(offer)
            offer_dict["index"] = i
            # Convert datetime objects to strings
            for key, val in offer_dict.items():
                if isinstance(val, (datetime, date)):
                    offer_dict[key] = val.isoformat()
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                if isinstance(v, (datetime, date)):
                                    item[k] = v.isoformat()
            result.append(offer_dict)

        return json.dumps({"offers": result, "count": len(result)}, default=str, ensure_ascii=False)

    except Exception as e:
        logger.error(f"search_flights tool error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_offer_by_flight_number(
    flight_number: str,
    origin: str = "",
    destination: str = "",
    depart_date: str = "",
) -> str:
    """Get flight offer by flight number + route.

    Args:
        flight_number: Flight number like "VJ145" or "VJ 145"
        origin: Departure airport code (e.g., HAN) - REQUIRED for accurate match
        destination: Arrival airport code (e.g., SGN) - REQUIRED for accurate match
        depart_date: Departure date (YYYY-MM-DD) - Optional

    Returns:
        JSON string with flight offer details if found.
        
    Important:
        Flight number alone is NOT unique! VJ197 can fly HAN→SGN and SGN→HAN.
        Always provide origin and destination from search context.
    """
    logger.info(f"TOOL CALL: get_offer_by_flight_number(flight_number={flight_number}, origin={origin}, dest={destination}, date={depart_date})")
    from app.services.flight_service import get_offer_by_flight_number as _get_offer

    try:
        async with _db_session() as db:
            offer = await _get_offer(
                db, 
                flight_number,
                origin=origin if origin else None,
                destination=destination if destination else None,
                depart_date=depart_date if depart_date else None
            )

        if not offer:
            return json.dumps({
                "found": False,
                "message": f"Không tìm thấy chuyến bay {flight_number} trong kết quả tìm kiếm gần đây."
            }, ensure_ascii=False)

        # Convert datetime objects to strings
        offer_dict = dict(offer)
        for key, val in offer_dict.items():
            if isinstance(val, (datetime, date)):
                offer_dict[key] = val.isoformat()
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            if isinstance(v, (datetime, date)):
                                item[k] = v.isoformat()

        return json.dumps({
            "found": True,
            "offer": offer_dict
        }, default=str, ensure_ascii=False)

    except Exception as e:
        logger.error(f"get_offer_by_flight_number tool error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def create_booking(
    offer_id: str,
    passenger_id: str,
    user_id: str,
) -> str:
    """Create a flight booking for a specific offer and passenger.

    Args:
        offer_id: The flight offer ID from search results
        passenger_id: UUID of the passenger
        user_id: UUID of the user

    Returns:
        JSON string with booking confirmation details.
    """
    logger.info(f"TOOL CALL: create_booking(offer_id={offer_id}, passenger_id={passenger_id})")
    from app.services.booking_service import create_booking as _create
    from app.schemas.booking import BookingCreateRequest

    try:
        req = BookingCreateRequest(
            passenger_id=UUID(passenger_id),
            offer_id=offer_id,
        )

        async with _db_session() as db:
            booking = await _create(db, UUID(user_id), req)

        result = {
            "success": True,
            "booking_id": str(booking.booking_id),
            "status": booking.status,
            "booking_reference": booking.booking_reference,
        }

        # Send booking confirmation email asynchronously (fire-and-forget)
        try:
            from app.services.email_service import send_booking_confirmation_email
            async with _db_session() as db:
                email_result = await send_booking_confirmation_email(
                    db, UUID(result["booking_id"]), UUID(user_id)
                )
                if email_result.get("success"):
                    result["email_sent"] = True
                    logger.info(f"Booking confirmation email sent for booking {result['booking_id']}")
                else:
                    result["email_sent"] = False
                    logger.warning(f"Failed to send booking email: {email_result.get('error')}")
        except Exception as email_err:
            logger.warning(f"Email sending failed (non-critical): {email_err}")
            result["email_sent"] = False

        return json.dumps(result, default=str, ensure_ascii=False)

    except Exception as e:
        logger.error(f"create_booking tool error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def cancel_booking(
    booking_id: str,
    user_id: str,
    reason: str = "",
) -> str:
    """Cancel an existing booking.

    Args:
        booking_id: UUID of the booking to cancel
        user_id: UUID of the user
        reason: Optional reason for cancellation

    Returns:
        JSON string with cancellation result.
    """
    logger.info(f"TOOL CALL: cancel_booking(booking_id={booking_id}, reason={reason})")
    from app.services.booking_service import cancel_booking as _cancel

    try:
        async with _db_session() as db:
            result = await _cancel(db, UUID(booking_id), UUID(user_id), reason or None)

        return json.dumps({
            "success": True,
            "booking_id": str(result.booking_id),
            "status": result.status,
        }, default=str, ensure_ascii=False)

    except Exception as e:
        logger.error(f"cancel_booking tool error: {e}")
        return json.dumps({"error": str(e)})


# ── Assistant Tools ─────────────────────────────────────────────────────────


@tool
async def get_passengers(user_id: str) -> str:
    """Get list of passengers registered by the user.

    Args:
        user_id: UUID of the user

    Returns:
        JSON string with list of passengers (name, passport, DOB, etc.)
    """
    logger.info(f"TOOL CALL: get_passengers(user_id={user_id})")
    from app.services.passenger_service import get_passengers as _get

    try:
        async with _db_session() as db:
            passengers = await _get(db, UUID(user_id))

        result = []
        for p in passengers:
            result.append({
                "id": str(p.id),
                "first_name": p.first_name,
                "last_name": p.last_name,
                "gender": p.gender,
                "dob": str(p.dob) if p.dob else None,
                "passport_number": p.passport_number,
                "nationality": p.nationality,
            })

        return json.dumps({"passengers": result, "count": len(result)}, ensure_ascii=False)

    except Exception as e:
        logger.error(f"get_passengers tool error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_bookings(
    user_id: str,
    status_filter: str = "",
) -> str:
    """Get list of bookings for the user.

    Args:
        user_id: UUID of the user
        status_filter: Optional filter by status (PENDING, CONFIRMED, CANCELLED)

    Returns:
        JSON string with list of bookings.
    """
    logger.info(f"TOOL CALL: get_bookings(user_id={user_id}, status_filter={status_filter})")
    from app.services.booking_service import get_bookings as _get

    try:
        async with _db_session() as db:
            bookings = await _get(
                db, UUID(user_id),
                status_filter=status_filter or None,
            )

        result = []
        for b in bookings:
            result.append({
                "id": str(b.id),
                "status": b.status,
                "provider": b.provider,
                "booking_reference": b.booking_reference,
                "total_price": b.total_price,
                "currency": b.currency,
                "created_at": str(b.created_at) if b.created_at else None,
            })

        return json.dumps({"bookings": result, "count": len(result)}, ensure_ascii=False)

    except Exception as e:
        logger.error(f"get_bookings tool error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_user_preferences(user_id: str) -> str:
    """Get user's flight preferences (cabin class, airlines, seat preference).

    Args:
        user_id: UUID of the user

    Returns:
        JSON string with user preferences.
    """
    logger.info(f"TOOL CALL: get_user_preferences(user_id={user_id})")
    from app.services.user_preference_service import get_user_preference as _get

    try:
        async with _db_session() as db:
            pref = await _get(db, UUID(user_id))

        if not pref:
            return json.dumps({"preferences": None, "message": "Chưa cài đặt sở thích."})

        return json.dumps({
            "preferences": {
                "cabin_class": pref.cabin_class,
                "preferred_airlines": pref.preferred_airlines,
                "seat_preference": pref.seat_preference,
                "default_passenger_id": str(pref.default_passenger_id) if pref.default_passenger_id else None,
            }
        }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"get_user_preferences tool error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def get_calendar_events(user_id: str) -> str:
    """Get calendar events (flight schedule) for the user.

    Args:
        user_id: UUID of the user

    Returns:
        JSON string with list of calendar events.
    """
    logger.info(f"TOOL CALL: get_calendar_events(user_id={user_id})")
    from app.services.calendar_service import get_calendar_events_by_user as _get

    try:
        async with _db_session() as db:
            events = await _get(db, UUID(user_id))

        result = []
        for ev in events:
            result.append({
                "id": str(ev.id),
                "booking_id": str(ev.booking_id),
                "google_event_id": ev.google_event_id,
                "synced_at": str(ev.synced_at) if ev.synced_at else None,
            })

        return json.dumps({"events": result, "count": len(result)}, ensure_ascii=False)

    except Exception as e:
        logger.error(f"get_calendar_events tool error: {e}")
        return json.dumps({"error": str(e)})


@tool
async def add_booking_to_calendar(
    booking_id: str,
    user_id: str,
    calendar_id: str = "primary",
) -> str:
    """Add a booking to Google Calendar.

    Args:
        booking_id: UUID of the booking to add to calendar
        user_id: UUID of the user
        calendar_id: Google Calendar ID (default: primary)

    Returns:
        JSON string with calendar event details or error.
    """
    logger.info(f"TOOL CALL: add_booking_to_calendar(booking_id={booking_id}, user_id={user_id})")
    from app.services.calendar_service import create_calendar_event as _create
    from app.models.user import User
    from sqlalchemy import select

    try:
        async with _db_session() as db:
            # Check if user has Google Calendar credentials
            result = await db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return json.dumps({
                    "success": False,
                    "error": "User not found"
                }, ensure_ascii=False)
            
            # Check if user has Google Calendar connected
            google_tokens = user.metadata_.get('google_calendar', {}) if user.metadata_ else {}
            has_tokens = google_tokens.get('access_token') and google_tokens.get('refresh_token')
            
            if not has_tokens:
                # Generate OAuth URL for user to authorize
                from google_auth_oauthlib.flow import Flow
                from app.core.config import settings
                
                GOOGLE_CLIENT_ID = getattr(settings, 'GOOGLE_CLIENT_ID', None)
                GOOGLE_CLIENT_SECRET = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
                GOOGLE_REDIRECT_URI = getattr(settings, 'GOOGLE_REDIRECT_URI', 'http://localhost:8000/api/google-calendar/callback')
                
                if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
                    return json.dumps({
                        "success": False,
                        "error": "Google Calendar không được cấu hình. Vui lòng liên hệ admin."
                    }, ensure_ascii=False)
                
                try:
                    flow = Flow.from_client_config(
                        {
                            "web": {
                                "client_id": GOOGLE_CLIENT_ID,
                                "client_secret": GOOGLE_CLIENT_SECRET,
                                "redirect_uris": [GOOGLE_REDIRECT_URI],
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                            }
                        },
                        scopes=['https://www.googleapis.com/auth/calendar'],
                        redirect_uri=GOOGLE_REDIRECT_URI
                    )
                    
                    authorization_url, state = flow.authorization_url(
                        access_type='offline',
                        prompt='consent',
                        state=str(user_id)
                    )
                    
                    return json.dumps({
                        "success": False,
                        "needs_authorization": True,
                        "authorization_url": authorization_url,
                        "message": "Bạn cần kết nối Google Calendar trước. Vui lòng click vào link bên dưới để authorize."
                    }, ensure_ascii=False)
                    
                except Exception as auth_error:
                    logger.error(f"Failed to generate OAuth URL: {auth_error}")
                    return json.dumps({
                        "success": False,
                        "error": f"Không thể tạo OAuth URL: {str(auth_error)}"
                    }, ensure_ascii=False)
            
            # User has tokens, proceed with calendar event creation
            calendar_event = await _create(db, UUID(booking_id), UUID(user_id), calendar_id)

        return json.dumps({
            "success": True,
            "event_id": str(calendar_event.id),
            "booking_id": str(calendar_event.booking_id),
            "google_event_id": calendar_event.google_event_id,
            "synced_at": str(calendar_event.synced_at) if calendar_event.synced_at else None,
        }, default=str, ensure_ascii=False)

    except Exception as e:
        logger.error(f"add_booking_to_calendar tool error: {e}")
        return json.dumps({"error": str(e), "success": False}, ensure_ascii=False)


@tool
async def send_flight_info_email(
    user_id: str,
    booking_id: str = "",
    flight_summary: str = "",
) -> str:
    """Send flight information to the user's email.

    Use this tool when the user asks to send/email flight details.
    Two modes:
    - Provide booking_id to send booking details
    - Provide flight_summary (text) to send recent search results or any flight info

    At least one of booking_id or flight_summary must be provided.

    Args:
        user_id: UUID of the user
        booking_id: Optional UUID of the booking to send
        flight_summary: Optional plain-text flight information to send

    Returns:
        JSON string with send result.
    """
    logger.info(f"TOOL CALL: send_flight_info_email(user_id={user_id}, booking_id={booking_id or 'N/A'})")
    from app.services.email_service import send_flight_info_email as _send

    try:
        async with _db_session() as db:
            result = await _send(
                db,
                user_id=UUID(user_id),
                booking_id=UUID(booking_id) if booking_id else None,
                flight_summary=flight_summary if flight_summary else None,
            )

        if result.get("success"):
            return json.dumps({
                "success": True,
                "message": f"Đã gửi thông tin chuyến bay tới email {result.get('sent_to', '')} thành công!",
                "email_id": result.get("email_id", ""),
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "success": False,
                "error": result.get("error", "Unknown error"),
            }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"send_flight_info_email tool error: {e}")
        return json.dumps({"error": str(e)})


# ── Tool registries (for agents) ───────────────────────────────────────────

FLIGHT_TOOLS = [search_flights, get_offer_by_flight_number, create_booking, cancel_booking, get_passengers, get_user_preferences]
ASSISTANT_TOOLS = [get_passengers, get_bookings, get_user_preferences, get_calendar_events, add_booking_to_calendar, send_flight_info_email]
ALL_TOOLS = FLIGHT_TOOLS + ASSISTANT_TOOLS
