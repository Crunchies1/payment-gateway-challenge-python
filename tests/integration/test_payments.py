"""
Integration tests
"""
import asyncio
from unittest.mock import AsyncMock, patch

from src.internal.payments import (
    CardDetails,
    ProcessPaymentRequest,
    ProcessPaymentResponse,
    GetPaymentDetailsResponse,
    get_payment_details,
    process_payment,
)
from src.models import payments, cards
from src.models.payments import PaymentStatus, Currency
from src.clients.bank import BankProcessPaymentResponse

VALID_REQUEST = ProcessPaymentRequest(
    card_details=CardDetails(
        number="2222405343248877",
        expiry_month=4,
        expiry_year=2030,
        cvv="123",
    ),
    currency="GBP",
    amount=100,
)


class TestPaymentFlow:
    def setup_method(self):
        """Reset in-memory stores before each test to ensure isolation."""
        payments.payment_repo._store.clear()
        cards.card_repo._store.clear()

    @patch("src.internal.payments.bank.process_payment", new_callable=AsyncMock)
    def test_process_payments_then_get_details_authorized(self, mock_bank):
        mock_bank.return_value = BankProcessPaymentResponse(authorized=True, authorization_code="test-uuid-123")

        process_response = asyncio.run(process_payment(VALID_REQUEST))

        expected_process_response = ProcessPaymentResponse(
            id=process_response.id,
            status=PaymentStatus.AUTHORIZED,
            last_four_card_digits="8877",
            expiry_month=4,
            expiry_year=2030,
            currency=Currency.GBP,
            amount=100,
        )
        expected_details_response = GetPaymentDetailsResponse(
            id=process_response.id,
            status=PaymentStatus.AUTHORIZED,
            last_four_card_digits="8877",
            expiry_month=4,
            expiry_year=2030,
            currency=Currency.GBP,
            amount=100,
        )

        assert process_response == expected_process_response
        assert get_payment_details(process_response.id) == expected_details_response

    @patch("src.internal.payments.bank.process_payment", new_callable=AsyncMock)
    def test_process_payments_then_get_details_declined(self, mock_bank):
        mock_bank.return_value = BankProcessPaymentResponse(authorized=False, authorization_code="")

        process_response = asyncio.run(process_payment(VALID_REQUEST))

        expected_process_response = ProcessPaymentResponse(
            id=process_response.id,
            status=PaymentStatus.DECLINED,
            last_four_card_digits="8877",
            expiry_month=4,
            expiry_year=2030,
            currency=Currency.GBP,
            amount=100,
        )
        expected_details_response = GetPaymentDetailsResponse(
            id=process_response.id,
            status=PaymentStatus.DECLINED,
            last_four_card_digits="8877",
            expiry_month=4,
            expiry_year=2030,
            currency=Currency.GBP,
            amount=100,
        )

        assert process_response == expected_process_response
        assert get_payment_details(process_response.id) == expected_details_response
