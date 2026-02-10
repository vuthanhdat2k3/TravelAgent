"""
Email service using Resend API.

Sends transactional emails (booking confirmations, etc.)
via the Resend email delivery platform.
"""

import logging
import json
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.user import User
from app.models.booking import Booking
from app.models.notification_log import NotificationLog

logger = logging.getLogger(__name__)


def _get_resend_client():
    """Lazy-load Resend client."""
    import resend

    api_key = getattr(settings, "RESEND_API_KEY", None)
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured.")
    resend.api_key = api_key
    return resend


def _resolve_recipient(user_email: str) -> str:
    """Return the actual recipient email.

    When using Resend's test domain (onboarding@resend.dev), emails can only
    be delivered to the Resend account owner.  If RESEND_TEST_TO_EMAIL is set
    we override the recipient so testing works without a custom domain.
    """
    from_email = getattr(settings, "RESEND_FROM_EMAIL", "") or ""
    test_to = getattr(settings, "RESEND_TEST_TO_EMAIL", "") or ""
    if test_to and "resend.dev" in from_email:
        if user_email != test_to:
            logger.info(
                f"Resend test mode: overriding recipient {user_email} → {test_to}"
            )
        return test_to
    return user_email


async def send_booking_confirmation_email(
    db: AsyncSession,
    booking_id: UUID,
    user_id: UUID,
) -> dict:
    """
    Send a booking confirmation email to the user.

    Args:
        db: Database session
        booking_id: UUID of the booking
        user_id: UUID of the user

    Returns:
        dict with success status and email ID
    """
    # Fetch user
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user or not user.email:
        logger.warning(f"Cannot send email: user {user_id} not found or no email")
        return {"success": False, "error": "User not found or no email"}

    # Fetch booking with flights
    booking_result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.flights))
        .where(Booking.id == booking_id, Booking.user_id == user_id)
    )
    booking = booking_result.scalar_one_or_none()
    if not booking:
        logger.warning(f"Cannot send email: booking {booking_id} not found")
        return {"success": False, "error": "Booking not found"}

    # Build email content
    flights_html = ""
    for flight in booking.flights:
        dep_time = flight.departure_time.strftime("%H:%M %d/%m/%Y") if flight.departure_time else "N/A"
        arr_time = flight.arrival_time.strftime("%H:%M %d/%m/%Y") if flight.arrival_time else "N/A"
        flights_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                <strong>{flight.airline_code}{flight.flight_number}</strong>
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                {flight.origin} → {flight.destination}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                {dep_time}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                {arr_time}
            </td>
        </tr>
        """

    price_formatted = f"{booking.total_price:,.0f}" if booking.total_price else "N/A"
    currency = booking.currency or "VND"
    user_name = user.full_name or user.email.split("@")[0]

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 24px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #2563eb, #7c3aed); border-radius: 16px 16px 0 0; padding: 32px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">✈️ Xác nhận đặt vé</h1>
                <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0;">Travel Agent AI</p>
            </div>

            <!-- Body -->
            <div style="background: white; padding: 32px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.07);">
                <p style="color: #374151; font-size: 16px; margin: 0 0 16px;">
                    Xin chào <strong>{user_name}</strong>,
                </p>
                <p style="color: #6b7280; font-size: 14px; margin: 0 0 24px;">
                    Đặt vé của bạn đã được xác nhận thành công! Dưới đây là thông tin chi tiết:
                </p>

                <!-- Booking Info -->
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 16px; margin-bottom: 24px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #6b7280; font-size: 13px;">Mã đặt chỗ</span>
                        <span style="color: #059669; font-size: 16px; font-weight: 700; font-family: monospace;">
                            {booking.booking_reference or 'N/A'}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #6b7280; font-size: 13px;">Trạng thái</span>
                        <span style="color: #059669; font-size: 13px; font-weight: 600;">
                            {booking.status}
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #6b7280; font-size: 13px;">Tổng tiền</span>
                        <span style="color: #1f2937; font-size: 16px; font-weight: 700;">
                            {price_formatted} {currency}
                        </span>
                    </div>
                </div>

                <!-- Flights Table -->
                <h3 style="color: #1f2937; font-size: 14px; margin: 0 0 12px;">Thông tin chuyến bay</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #374151;">
                    <thead>
                        <tr style="background: #f9fafb;">
                            <th style="padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #e5e7eb;">Chuyến bay</th>
                            <th style="padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #e5e7eb;">Hành trình</th>
                            <th style="padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #e5e7eb;">Khởi hành</th>
                            <th style="padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #e5e7eb;">Đến nơi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {flights_html if flights_html else '<tr><td colspan="4" style="padding: 12px; text-align: center; color: #9ca3af;">Chưa có thông tin chuyến bay</td></tr>'}
                    </tbody>
                </table>

                <!-- Footer note -->
                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #9ca3af; font-size: 12px; margin: 0; text-align: center;">
                        Email này được gửi tự động từ Travel Agent AI.<br>
                        Nếu cần hỗ trợ, vui lòng trả lời email hoặc chat với AI assistant.
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # Send via Resend
    try:
        resend = _get_resend_client()

        from_email = getattr(settings, "RESEND_FROM_EMAIL", None) or "Travel Agent <noreply@resend.dev>"

        params: dict = {
            "from": from_email,
            "to": [_resolve_recipient(user.email)],
            "subject": f"✈️ Xác nhận đặt vé - {booking.booking_reference or 'Booking'}",
            "html": html_content,
        }

        email_response = resend.Emails.send(params)
        email_id = email_response.get("id", "") if isinstance(email_response, dict) else getattr(email_response, "id", "")

        logger.info(f"Booking confirmation email sent to {user.email}, resend_id={email_id}")

        # Log notification
        notification = NotificationLog(
            user_id=user_id,
            type_="booking_confirmed",
            channel="email",
            subject=f"Xác nhận đặt vé - {booking.booking_reference}",
            ref_id=booking_id,
            status="sent",
            metadata_=json.dumps({"resend_email_id": email_id}),
        )
        db.add(notification)
        await db.commit()

        return {"success": True, "email_id": email_id}

    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {e}")

        # Log failed notification
        try:
            notification = NotificationLog(
                user_id=user_id,
                type_="booking_confirmed",
                channel="email",
                subject=f"Xác nhận đặt vé - {booking.booking_reference}",
                ref_id=booking_id,
                status="failed",
                metadata_=json.dumps({"error": str(e)}),
            )
            db.add(notification)
            await db.commit()
        except Exception:
            pass

        return {"success": False, "error": str(e)}


async def send_flight_info_email(
    db: AsyncSession,
    user_id: UUID,
    booking_id: UUID | None = None,
    flight_summary: str | None = None,
) -> dict:
    """
    Send flight information to user's email.

    Supports two modes:
    1. booking_id provided → fetch booking details from DB and send
    2. flight_summary provided → send the raw text summary (e.g. from search results)

    Args:
        db: Database session
        user_id: UUID of the user
        booking_id: Optional - UUID of a booking to send details for
        flight_summary: Optional - plain-text flight info to send

    Returns:
        dict with success status
    """
    # Fetch user email
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user or not user.email:
        return {"success": False, "error": "User not found or no email address"}

    user_name = user.full_name or user.email.split("@")[0]
    subject = "✈️ Thông tin chuyến bay - Travel Agent AI"
    flights_html = ""

    # ── Mode 1: Build from booking ──────────────────────────────────────
    if booking_id:
        booking_result = await db.execute(
            select(Booking)
            .options(selectinload(Booking.flights))
            .where(Booking.id == booking_id, Booking.user_id == user_id)
        )
        booking = booking_result.scalar_one_or_none()
        if not booking:
            return {"success": False, "error": f"Booking {booking_id} not found"}

        subject = f"✈️ Thông tin chuyến bay - {booking.booking_reference or 'Booking'}"

        rows = ""
        for f in booking.flights:
            dep = f.departure_time.strftime("%H:%M %d/%m/%Y") if f.departure_time else "N/A"
            arr = f.arrival_time.strftime("%H:%M %d/%m/%Y") if f.arrival_time else "N/A"
            cabin = f.cabin_class or ""
            rows += f"""
            <tr>
                <td style="padding:12px;border-bottom:1px solid #e5e7eb;"><strong>{f.airline_code}{f.flight_number}</strong></td>
                <td style="padding:12px;border-bottom:1px solid #e5e7eb;">{f.origin} → {f.destination}</td>
                <td style="padding:12px;border-bottom:1px solid #e5e7eb;">{dep}</td>
                <td style="padding:12px;border-bottom:1px solid #e5e7eb;">{arr}</td>
                <td style="padding:12px;border-bottom:1px solid #e5e7eb;">{cabin}</td>
            </tr>"""

        price_fmt = f"{booking.total_price:,.0f}" if booking.total_price else "N/A"
        currency = booking.currency or "VND"

        flights_html = f"""
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:16px;margin-bottom:24px;">
            <div style="margin-bottom:8px;"><span style="color:#6b7280;font-size:13px;">Mã đặt chỗ:</span>
                <strong style="color:#059669;font-family:monospace;font-size:16px;"> {booking.booking_reference or 'N/A'}</strong></div>
            <div style="margin-bottom:8px;"><span style="color:#6b7280;font-size:13px;">Trạng thái:</span>
                <strong style="color:#059669;"> {booking.status}</strong></div>
            <div><span style="color:#6b7280;font-size:13px;">Tổng tiền:</span>
                <strong style="color:#1f2937;font-size:16px;"> {price_fmt} {currency}</strong></div>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:13px;color:#374151;">
            <thead><tr style="background:#f9fafb;">
                <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #e5e7eb;">Chuyến bay</th>
                <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #e5e7eb;">Hành trình</th>
                <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #e5e7eb;">Khởi hành</th>
                <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #e5e7eb;">Đến nơi</th>
                <th style="padding:10px 12px;text-align:left;border-bottom:2px solid #e5e7eb;">Hạng</th>
            </tr></thead>
            <tbody>{rows if rows else '<tr><td colspan="5" style="padding:12px;text-align:center;color:#9ca3af;">Không có thông tin chuyến bay</td></tr>'}</tbody>
        </table>"""

    # ── Mode 2: Build from plain-text summary ───────────────────────────
    elif flight_summary:
        # Convert newlines to <br> for HTML rendering
        summary_html = flight_summary.replace("\n", "<br>")
        flights_html = f"""
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:20px;font-size:14px;color:#1e3a5f;line-height:1.7;white-space:pre-line;">
            {summary_html}
        </div>"""
    else:
        return {"success": False, "error": "Cần cung cấp booking_id hoặc flight_summary"}

    # ── Build full HTML email ───────────────────────────────────────────
    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:24px;">
    <div style="background:linear-gradient(135deg,#2563eb,#7c3aed);border-radius:16px 16px 0 0;padding:32px;text-align:center;">
        <h1 style="color:white;margin:0;font-size:24px;">✈️ Thông tin chuyến bay</h1>
        <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;">Travel Agent AI</p>
    </div>
    <div style="background:white;padding:32px;border-radius:0 0 16px 16px;box-shadow:0 4px 6px rgba(0,0,0,0.07);">
        <p style="color:#374151;font-size:16px;margin:0 0 16px;">Xin chào <strong>{user_name}</strong>,</p>
        <p style="color:#6b7280;font-size:14px;margin:0 0 24px;">
            Dưới đây là thông tin chuyến bay bạn yêu cầu:
        </p>
        {flights_html}
        <div style="margin-top:24px;padding-top:16px;border-top:1px solid #e5e7eb;">
            <p style="color:#9ca3af;font-size:12px;margin:0;text-align:center;">
                Email này được gửi tự động từ Travel Agent AI.<br>
                Nếu cần hỗ trợ, vui lòng chat với AI assistant.
            </p>
        </div>
    </div>
</div>
</body>
</html>"""

    # ── Send via Resend ─────────────────────────────────────────────────
    try:
        resend = _get_resend_client()
        from_email = getattr(settings, "RESEND_FROM_EMAIL", None) or "Travel Agent <onboarding@resend.dev>"

        params = {
            "from": from_email,
            "to": [_resolve_recipient(user.email)],
            "subject": subject,
            "html": html_content,
        }
        email_response = resend.Emails.send(params)
        email_id = email_response.get("id", "") if isinstance(email_response, dict) else getattr(email_response, "id", "")

        actual_recipient = _resolve_recipient(user.email)
        logger.info(f"Flight info email sent to {actual_recipient}, resend_id={email_id}")

        # Log notification
        notification = NotificationLog(
            user_id=user_id,
            type_="flight_info",
            channel="email",
            subject=subject,
            ref_id=booking_id,
            status="sent",
            metadata_=json.dumps({"resend_email_id": email_id}),
        )
        db.add(notification)
        await db.commit()

        return {"success": True, "email_id": email_id, "sent_to": actual_recipient}

    except Exception as e:
        logger.error(f"Failed to send flight info email: {e}")
        try:
            notification = NotificationLog(
                user_id=user_id,
                type_="flight_info",
                channel="email",
                subject=subject,
                ref_id=booking_id,
                status="failed",
                metadata_=json.dumps({"error": str(e)}),
            )
            db.add(notification)
            await db.commit()
        except Exception:
            pass
        return {"success": False, "error": str(e)}
