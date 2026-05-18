"""
Payments Service
"""

import logging
from datetime import date
from typing import Optional
from pydantic import BaseModel
from ..models import payments
from ..clients import bank
from . import cards as card_service 

logger = logging.getLogger(__name__)

### Error Definitions

class PaymentValidationError(Exception):
    pass

class BankError(Exception):
    pass

class DatabaseError(Exception):
    pass

class CardNotFoundError(Exception):
    pass

### -----------------

class CardDetails(BaseModel):
    number: str
    expiry_month: int
    expiry_year: int
    cvv: str

class ProcessPaymentRequest(BaseModel):
    card_details: CardDetails
    currency: str
    amount: int

    # To be honest there's a lot I can do here to make this better like adding
    # error messages to each fail case so that the merchant can get the right
    # error :^)
    def _is_valid(self) -> bool:
        # Card number length
        if len(self.card_details.number) < 14 or len(self.card_details.number) > 19:
            return False

        # make sure card number only contains digits
        if not self.card_details.number.isdigit():
            return False

        # Expiry month valid
        if self.card_details.expiry_month < 1 or self.card_details.expiry_month > 12:
            return False
    
        # Ensure expiry date not passed on card
        today = date.today()
        if (self.card_details.expiry_year, self.card_details.expiry_month) < (today.year, today.month):
            return False

        # CVV length
        if len(self.card_details.cvv) < 3 or len(self.card_details.cvv) > 4:
            return False

        # make sure CVV only contains digits
        if not self.card_details.cvv.isdigit():
            return False
        
        # Validate the currency is within the currency enum we defined
        try:
            payments.Currency(self.currency)
        except ValueError:
            return False
        
        # Make sure amount is not negative, lets assume we can have 0 dollar txns
        if self.amount < 0:
            return False

        return True

class ProcessPaymentResponse(BaseModel):
    id: str
    status: payments.PaymentStatus
    last_four_card_digits: str
    expiry_month: int
    expiry_year: int
    currency: payments.Currency
    amount: int

async def process_payment(req: ProcessPaymentRequest) -> ProcessPaymentResponse:
    if not req._is_valid():
        logger.warning("Payment rejected due to invalid request fields: %s", req)
        raise PaymentValidationError("invalid request fields")

    bank_req = bank.BankProcessPaymentRequest(
        card_number=req.card_details.number,
        expiry_date=f"{req.card_details.expiry_month}/{req.card_details.expiry_year}",
        currency=req.currency,
        amount=req.amount,
        cvv=req.card_details.cvv
    )
    try:
        response: bank.BankProcessPaymentResponse = await bank.process_payment(bank_req)
    except Exception as e:
        logger.error("Bank request failed: %s", e)
        raise BankError("did not receive response from bank")

    # 1. Save Card details to DB (only if new)
    # 2. Save Payment details to DB (always)
    # In reality, these would probably be wrapped in some atomic transaction
    # We'd probably also want some level of isolation if two payments for the same
    # card were attempted in the same instant, maybe might create duplicated cards
    # Fastest thing is probably SELECT FOR UPDATE, could also use DB unique constraint
    # as another method

    try:
        card = card_service.get_or_create_card(card_service.CardRequest(
            number=req.card_details.number,
            expiry_month=req.card_details.expiry_month,
            expiry_year=req.card_details.expiry_year
        ))
        new_payment: payments.Payment = payments.Payment(
            card_id=card.id,
            currency=payments.Currency(req.currency),
            amount_in_units=req.amount,
            status=payments.PaymentStatus.AUTHORIZED if response.authorized else payments.PaymentStatus.DECLINED
        )
        payments.payment_repo.create(new_payment)
    except Exception as e:
        logger.error("Database transaction failed: %s", e)
        raise DatabaseError("transaction failed")

    return ProcessPaymentResponse(
        id=new_payment.id,
        status=new_payment.status,
        last_four_card_digits=card.last_four_digits(),
        expiry_month=card.expiry_month,
        expiry_year=card.expiry_year,
        currency=new_payment.currency,
        amount=new_payment.amount_in_units,
    )

class GetPaymentDetailsResponse(BaseModel):
    id: str
    status: payments.PaymentStatus
    last_four_card_digits: str
    expiry_month: int
    expiry_year: int
    currency: payments.Currency
    amount: int

def get_payment_details(payment_id: str) -> Optional[GetPaymentDetailsResponse]:
    try:
        payment = payments.payment_repo.get(payment_id)
        if not payment:
            logger.info("Payment not found for id: %s", payment_id)
            return None
    except Exception as e:
        logger.error("Failed to retrieve payment with id %s: %s", payment_id, e)
        raise DatabaseError(f"could not get payment with id {payment_id}")

    try:
        card = card_service.get_by_id(payment.card_id)
        if not card:
            raise CardNotFoundError(f"could not find card with id {payment.card_id}")
    except Exception as e:
        logger.error("Failed to retrieve card with id %s: %s", payment.card_id, e)
        raise DatabaseError(f"could not get card with id {payment.card_id}")

    return GetPaymentDetailsResponse(
        id=payment.id,
        status=payment.status,
        last_four_card_digits=card.last_four_digits(),
        expiry_month=card.expiry_month,
        expiry_year=card.expiry_year,
        currency=payment.currency,
        amount=payment.amount_in_units,
    )