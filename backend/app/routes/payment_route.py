from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.payment import PaymentCreate, PaymentResponse
from app.models.user import User
from app.db.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.payment_service import (
    get_payments_by_booking,
    create_payment,
    handle_payment_webhook
)

router = APIRouter(tags=["payments"])


@router.post("/bookings/{booking_id}/payments", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_booking_payment(
    booking_id: UUID,
    payment_create: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a payment for a booking."""
    # Ensure booking_id matches
    payment_create.booking_id = booking_id
    
    payment_response, payment_url = await create_payment(db, current_user.id, payment_create)
    
    return {
        "payment": payment_response,
        "payment_url": payment_url
    }


@router.get("/bookings/{booking_id}/payments", response_model=list[PaymentResponse])
async def list_booking_payments(
    booking_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all payments for a booking."""
    payments = await get_payments_by_booking(db, booking_id, current_user.id)
    return [PaymentResponse.model_validate(p) for p in payments]


@router.post("/payments/webhook/vnpay")
async def vnpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle VNPAY payment webhook.
    No authentication required, but signature must be verified.
    """
    # Get webhook data from query params or form data
    webhook_data = dict(request.query_params)
    
    # TODO: Verify VNPAY signature
    # TODO: Process payment update
    
    # For now, return success response
    return {"RspCode": "00", "Message": "Confirm Success"}


@router.post("/payments/webhook/momo")
async def momo_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle MOMO payment webhook.
    No authentication required, but signature must be verified.
    """
    # Get webhook data from request body
    webhook_data = await request.json()
    
    # TODO: Verify MOMO signature
    # TODO: Process payment update
    
    # For now, return success response
    return {"resultCode": 0, "message": "Success"}
