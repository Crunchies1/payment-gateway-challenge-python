from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.app import app
from src.internal.payments import (
    ProcessPaymentResponse,
    GetPaymentDetailsResponse,
    PaymentValidationError,
    DatabaseError
)
from src.models.payments import PaymentStatus, Currency

client = TestClient(app)

VALID_REQUEST = {
    "card_details": {
        "number": "2222405343248877",
        "expiry_month": 4,
        "expiry_year": 2030,
        "cvv": "123",
    },
    "currency": "GBP",
    "amount": 100,
}

AUTHORIZED_RESPONSE = ProcessPaymentResponse(
    id="test-uuid",
    status=PaymentStatus.AUTHORIZED,
    last_four_card_digits="8877",
    expiry_month=4,
    expiry_year=2030,
    currency=Currency.GBP,
    amount=100,
)

DECLINED_RESPONSE = ProcessPaymentResponse(
    id="test-uuid",
    status=PaymentStatus.DECLINED,
    last_four_card_digits="8877",
    expiry_month=4,
    expiry_year=2030,
    currency=Currency.GBP,
    amount=100,
)

PAYMENT_DETAILS_RESPONSE = GetPaymentDetailsResponse(
    id="test-uuid",
    status=PaymentStatus.AUTHORIZED,
    last_four_card_digits="8877",
    expiry_month=4,
    expiry_year=2030,
    currency=Currency.GBP,
    amount=100,
)

class TestProcessPayment:
    @patch("src.handlers.payments.payment_service.process_payment", new_callable=AsyncMock)
    def test_process_payment_returns_authorized_response(self, mock_process):
        mock_process.return_value = AUTHORIZED_RESPONSE

        response = client.post("/payments", json=VALID_REQUEST)

        assert response.status_code == 200
        assert response.json() == AUTHORIZED_RESPONSE

    @patch("src.handlers.payments.payment_service.process_payment", new_callable=AsyncMock)
    def test_process_payment_returns_declined_response(self, mock_process):
        mock_process.return_value = DECLINED_RESPONSE

        response = client.post("/payments", json=VALID_REQUEST)

        assert response.status_code == 200
        assert response.json() == DECLINED_RESPONSE

    @patch("src.handlers.payments.payment_service.process_payment", new_callable=AsyncMock)
    def test_process_payment_returns_400_on_validation_error(self, mock_process):
        mock_process.side_effect = PaymentValidationError("test")

        response = client.post("/payments", json=VALID_REQUEST)

        assert response.status_code == 400

    @patch("src.handlers.payments.payment_service.process_payment", new_callable=AsyncMock)
    def test_process_payment_returns_500_on_internal_error(self, mock_process):
        mock_process.side_effect = DatabaseError("test")

        response = client.post("/payments", json=VALID_REQUEST)

        assert response.status_code == 500

class TestGetPaymentDetails:
    @patch("src.handlers.payments.payment_service.get_payment_details")
    def test_get_payment_details_success_found(self, mock_get):
        mock_get.return_value = PAYMENT_DETAILS_RESPONSE

        response = client.post("/payments/test-uuid")

        assert response.status_code == 200
        assert response.json() == PAYMENT_DETAILS_RESPONSE

    @patch("src.handlers.payments.payment_service.get_payment_details")
    def test_get_payment_details_returns_404_not_found(self, mock_get):
        mock_get.return_value = None

        response = client.post("/payments/nonexistent-id")

        assert response.status_code == 404
