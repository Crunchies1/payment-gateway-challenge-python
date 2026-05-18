import asyncio
from unittest.mock import MagicMock, patch

from src.clients.bank import BankProcessPaymentRequest, BankProcessPaymentResponse, process_payment

VALID_REQUEST = BankProcessPaymentRequest(
    card_number="2222405343248877",
    expiry_date="4/2030",
    currency="GBP",
    amount=100,
    cvv="123",
)

class TestBankClient:
    @patch("src.clients.bank.requests.post")
    def test_process_payment_returns_authorized_response(self, mock_post):
        mock_post.return_value = MagicMock(json=lambda: {"authorized": True, "authorization_code": "test-uuid-123"})

        response = asyncio.run(process_payment(VALID_REQUEST))

        expected = BankProcessPaymentResponse(
            authorized=True,
            authorization_code="test-uuid-123"
        )
        assert response == expected

    @patch("src.clients.bank.requests.post")
    def test_process_payment_returns_declined_response(self, mock_post):
        mock_post.return_value = MagicMock(json=lambda: {"authorized": False, "authorization_code": ""})

        response = asyncio.run(process_payment(VALID_REQUEST))

        expected = BankProcessPaymentResponse(
            authorized=False,
            authorization_code=""
        )
        assert response == expected
