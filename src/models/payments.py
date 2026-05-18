from pydantic import BaseModel, Field
from enum import Enum
import uuid
from typing import Dict, Optional

class PaymentStatus(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    DECLINED = "DECLINED"

class Currency(str, Enum):
    USD = "USD"
    GBP = "GBP"
    MYR = "MYR"

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())) # Auto-generated primary key
    card_id: str
    currency: Currency
    amount_in_units: int
    status: PaymentStatus # Probably have some index here

class PaymentRepository:
    def __init__(self):
        self._store: Dict[str, Payment] = {}

    def create(self, payment: Payment) -> bool:
        self._store[payment.id] = payment
        return True

    def get(self, payment_id: str) -> Optional[Payment]:
        return self._store.get(payment_id)

payment_repo = PaymentRepository()