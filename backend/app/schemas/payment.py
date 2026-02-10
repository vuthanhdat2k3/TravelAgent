from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentCreate(BaseModel):
    booking_id: UUID
    amount: Decimal
    currency: str = "VND"
    provider: str | None = None  # VNPAY, MOMO, etc.


class PaymentResponse(BaseModel):
    id: UUID
    booking_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    provider: str | None = None
    external_id: str | None = None
    paid_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
