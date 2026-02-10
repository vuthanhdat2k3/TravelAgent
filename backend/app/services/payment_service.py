from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.payment import Payment
from app.models.booking import Booking
from app.schemas.payment import PaymentCreate, PaymentResponse


async def get_payment_by_id(
    db: AsyncSession,
    payment_id: UUID
) -> Payment | None:
    """Get payment by ID."""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one_or_none()


async def get_payments_by_booking(
    db: AsyncSession,
    booking_id: UUID,
    user_id: UUID
) -> list[Payment]:
    """Get all payments for a booking, ensuring booking belongs to user."""
    # First verify booking belongs to user
    booking_result = await db.execute(
        select(Booking).where(
            Booking.id == booking_id,
            Booking.user_id == user_id
        )
    )
    booking = booking_result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or does not belong to user"
        )
    
    # Get payments
    result = await db.execute(
        select(Payment)
        .where(Payment.booking_id == booking_id)
        .order_by(Payment.created_at.desc())
    )
    return list(result.scalars().all())


async def create_payment(
    db: AsyncSession,
    user_id: UUID,
    payment_create: PaymentCreate
) -> tuple[PaymentResponse, str | None]:
    """
    Create a payment for a booking.
    Returns payment response and payment_url (if applicable).
    """
    # Verify booking belongs to user and can be paid
    booking_result = await db.execute(
        select(Booking).where(
            Booking.id == payment_create.booking_id,
            Booking.user_id == user_id
        )
    )
    booking = booking_result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or does not belong to user"
        )
    
    # Check if booking status allows payment
    if booking.status not in ["PENDING", "CONFIRMED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create payment for booking with status {booking.status}"
        )
    
    # Create payment record
    db_payment = Payment(
        booking_id=payment_create.booking_id,
        amount=payment_create.amount,
        currency=payment_create.currency,
        provider=payment_create.provider or "VNPAY",
        status="PENDING",
    )
    
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    
    # TODO: Call payment gateway (VNPAY/MOMO) to get payment URL
    # For now, return None for payment_url
    payment_url = None
    
    # In production:
    # if payment_create.provider == "VNPAY":
    #     payment_url = await _create_vnpay_payment(db_payment)
    # elif payment_create.provider == "MOMO":
    #     payment_url = await _create_momo_payment(db_payment)
    
    return PaymentResponse.model_validate(db_payment), payment_url


async def handle_payment_webhook(
    db: AsyncSession,
    provider: str,
    webhook_data: dict
) -> Payment:
    """
    Handle payment webhook from payment gateway.
    Update payment status based on gateway response.
    """
    # TODO: Verify signature/HMAC based on provider
    
    # TODO: Extract payment info from webhook_data
    # This is provider-specific (VNPAY, MOMO, etc.)
    
    # Example for VNPAY:
    # external_id = webhook_data.get("vnp_TxnRef")
    # response_code = webhook_data.get("vnp_ResponseCode")
    
    # Find payment by external_id
    # payment = await get_payment_by_external_id(db, external_id)
    
    # Update payment status
    # if response_code == "00":  # Success
    #     payment.status = "COMPLETED"
    #     payment.paid_at = datetime.utcnow()
    #     
    #     # Update booking status
    #     booking = await get_booking_by_id(db, payment.booking_id)
    #     booking.status = "CONFIRMED"
    # else:
    #     payment.status = "FAILED"
    
    # await db.commit()
    
    # Placeholder - return None for now
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Payment webhook not implemented yet"
    )
