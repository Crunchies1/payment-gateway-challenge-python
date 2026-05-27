"""Bank Client"""

import os
import requests
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

BANK_URL = f"{os.getenv('BANK_BASE_URL')}/payments"

class BankProcessPaymentRequest(BaseModel):
    """
    Sample JSON request:
    {
        "card_number": "2222405343248877",
        "expiry_date": "04/2025",
        "currency": "GBP",
        "amount": 100,
        "cvv": "123"
    }
    """
    card_number: str
    expiry_date: str
    currency: str
    amount: int
    cvv: str   

class BankProcessPaymentResponse(BaseModel):
    """
    Sample JSON response:
    {
        "authorized": true,
        "authorization_code": "0bb07405-6d44-4b50-a14f-7ae0beff13ad"
    }
    """
    authorized: bool
    authorization_code: str

async def process_payment(req: BankProcessPaymentRequest) -> BankProcessPaymentResponse:
    resp = requests.post(BANK_URL, json=req.model_dump())
    data_json = resp.json()
    payment_resp = BankProcessPaymentResponse(**data_json)
    return payment_resp