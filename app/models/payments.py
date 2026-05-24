from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Float, DateTime, func
from typing import Optional
from app.core.database import Base
from app.models.base import BaseMixin
from sqlalchemy.dialects.postgresql import JSONB
import uuid
from datetime import datetime

class Subscription(Base, BaseMixin):
    __tablename__ = "subscriptions"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    plan: Mapped[str] = mapped_column(String) # monthly, yearly
    status: Mapped[str] = mapped_column(String) # active, cancelled, past_due
    paystack_subscription_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class PaymentEvent(Base, BaseMixin):
    __tablename__ = "payment_events"
    
    entity_type: Mapped[str] = mapped_column(String) # subscription, invoice, transfer
    entity_id: Mapped[uuid.UUID] = mapped_column(String) 
    event_type: Mapped[str] = mapped_column(String)
    paystack_event_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB)
