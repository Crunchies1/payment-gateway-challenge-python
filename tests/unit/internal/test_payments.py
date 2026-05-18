import pytest
from unittest.mock import AsyncMock, patch
import asyncio

from src.internal.payments import (
    CardDetails,
    PaymentValidationError,
    BankError,
    DatabaseError,
    CardNotFoundError,
    ProcessPaymentRequest,
    ProcessPaymentResponse,
    GetPaymentDetailsResponse,
    get_payment_details,
    process_payment,
)
from src.models.cards import Card
from src.models.payments import Payment, PaymentStatus, Currency
from src.clients.bank import BankProcessPaymentResponse

# --- Shared fixtures ---

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

MOCK_CARD = Card(
    id="card-uuid-123",
    number="2222405343248877",
    expiry_month=4,
    expiry_year=2030,
)

MOCK_PAYMENT = Payment(
    id="payment-uuid-123",
    card_id="card-uuid-123",
    currency=Currency.GBP,
    amount_in_units=100,
    status=PaymentStatus.AUTHORIZED,
)

class TestProcessPayment:
    @patch("src.internal.payments.card_service.get_or_create_card")
    @patch("src.internal.payments.payments.payment_repo.create")
    @patch("src.internal.payments.bank.process_payment", new_callable=AsyncMock)
    def test_process_payment_authorized(self, mock_bank, mock_repo, mock_card_service):
        mock_bank.return_value = BankProcessPaymentResponse(authorized=True, authorization_code="test-uuid-123")
        mock_card_service.return_value = MOCK_CARD

        response = asyncio.run(process_payment(VALID_REQUEST))

        expected = ProcessPaymentResponse(
            id=response.id,
            status=PaymentStatus.AUTHORIZED,
            last_four_card_digits="8877",
            expiry_month=4,
            expiry_year=2030,
            currency=Currency.GBP,
            amount=100,
        )
        assert response == expected
        mock_repo.assert_called_once()

    @patch("src.internal.payments.card_service.get_or_create_card")
    @patch("src.internal.payments.payments.payment_repo.create")
    @patch("src.internal.payments.bank.process_payment", new_callable=AsyncMock)
    def test_process_payment_declined(self, mock_bank, mock_repo, mock_card_service):
        mock_bank.return_value = BankProcessPaymentResponse(authorized=False, authorization_code="")
        mock_card_service.return_value = MOCK_CARD

        response = asyncio.run(process_payment(VALID_REQUEST))

        expected = ProcessPaymentResponse(
            id=response.id,
            status=PaymentStatus.DECLINED,
            last_four_card_digits="8877",
            expiry_month=4,
            expiry_year=2030,
            currency=Currency.GBP,
            amount=100,
        )
        assert response == expected
        mock_repo.assert_called_once()

    @pytest.mark.parametrize("invalid_request", [
        {"number": "123", "exp_month": 4, "exp_year": 2030, "cvv": "123", "cur": "GBP", "amount": 100}, # Number too short
        {"number": "12345678901234567890", "exp_month": 4, "exp_year": 2030, "cvv": "123", "cur": "GBP", "amount": 100}, # Number too long
        {"number": "123456789a123456", "exp_month": 4, "exp_year": 2030, "cvv": "123", "cur": "GBP", "amount": 100}, # Number contains alpha chars
        {"number": "1234567890123456", "exp_month": 13, "exp_year": 2030, "cvv": "123", "cur": "GBP", "amount": 100}, # Month too large
        {"number": "1234567890123456", "exp_month": 0, "exp_year": 2030, "cvv": "123", "cur": "GBP", "amount": 100}, # Month too small
        {"number": "1234567890123456", "exp_month": 4, "exp_year": 2025, "cvv": "123", "cur": "GBP", "amount": 100}, # Expiry date in past
        {"number": "1234567890123456", "exp_month": 4, "exp_year": 2030, "cvv": "12", "cur": "GBP", "amount": 100}, # CVV too short
        {"number": "1234567890123456", "exp_month": 4, "exp_year": 2030, "cvv": "12345", "cur": "GBP", "amount": 100}, # CVV too long
        {"number": "1234567890123456", "exp_month": 4, "exp_year": 2030, "cvv": "12a", "cur": "GBP", "amount": 100}, # CVV contains alpha chars
        {"number": "1234567890123456", "exp_month": 4, "exp_year": 2030, "cvv": "123", "cur": "SGD", "amount": 100}, # Currency not supported
        {"number": "1234567890123456", "exp_month": 4, "exp_year": 2030, "cvv": "123", "cur": "GBP", "amount": -1}, # Amount negative
    ])
    def test_process_payment_validation_error(self, invalid_request):
        req = ProcessPaymentRequest(
            card_details=CardDetails(
                number=invalid_request["number"],
                expiry_month=invalid_request["exp_month"],
                expiry_year=invalid_request["exp_year"],
                cvv=invalid_request["cvv"],
            ),
            currency=invalid_request["cur"],
            amount=invalid_request["amount"]
        )
        with pytest.raises(PaymentValidationError):
            asyncio.run(process_payment(req))

    @patch("src.internal.payments.bank.process_payment", new_callable=AsyncMock)
    def test_process_payment_bank_error(self, mock_bank):
        mock_bank.side_effect = BankError("test")

        with pytest.raises(BankError):
            asyncio.run(process_payment(VALID_REQUEST))
    
    @patch("src.internal.payments.card_service.get_or_create_card")
    @patch("src.internal.payments.bank.process_payment", new_callable=AsyncMock)
    def test_process_payment_card_service_error(self, mock_bank, mock_card_service):
        mock_bank.return_value = BankProcessPaymentResponse(authorized=True, authorization_code="test-uuid-123")
        mock_card_service.side_effect = DatabaseError("test")

        with pytest.raises(DatabaseError):
            asyncio.run(process_payment(VALID_REQUEST))

    @patch("src.internal.payments.card_service.get_or_create_card")
    @patch("src.internal.payments.payments.payment_repo.create")
    @patch("src.internal.payments.bank.process_payment", new_callable=AsyncMock)
    def test_process_payment_repo_error(self, mock_bank, mock_repo, mock_card_service):
        mock_bank.return_value = BankProcessPaymentResponse(authorized=True, authorization_code="test-uuid-123")
        mock_card_service.return_value = MOCK_CARD
        mock_repo.side_effect = DatabaseError("test")

        with pytest.raises(DatabaseError):
            asyncio.run(process_payment(VALID_REQUEST))


class TestGetPaymentDetails:
    @patch("src.internal.payments.card_service.get_by_id")
    @patch("src.internal.payments.payments.payment_repo")
    def test_get_payment_details_found(self, mock_repo, mock_card_service):
        mock_repo.get.return_value = MOCK_PAYMENT
        mock_card_service.return_value = MOCK_CARD

        result = get_payment_details("payment-uuid-123")

        expected = GetPaymentDetailsResponse(
            id="payment-uuid-123",
            status=PaymentStatus.AUTHORIZED,
            last_four_card_digits="8877",
            expiry_month=4,
            expiry_year=2030,
            currency=Currency.GBP,
            amount=100,
        )
        assert result == expected

    @patch("src.internal.payments.payments.payment_repo")
    def test_get_payment_details_payment_not_found(self, mock_repo):
        mock_repo.get.return_value = None

        result = get_payment_details("nonexistent-uuid")

        assert result is None

    @patch("src.internal.payments.card_service.get_by_id")
    @patch("src.internal.payments.payments.payment_repo")
    def test_get_payment_details_card_not_found(self, mock_repo, mock_card_service):
        mock_repo.get.return_value = MOCK_PAYMENT
        mock_card_service.side_effect = CardNotFoundError("test")

        with pytest.raises(DatabaseError):
            get_payment_details("payment-uuid-123")
        
    @patch("src.internal.payments.payments.payment_repo")
    def test_get_payment_details_repo_error(self, mock_repo):
        mock_repo.get.side_effect = DatabaseError("test")

        with pytest.raises(DatabaseError):
            get_payment_details("payment-uuid-123")

