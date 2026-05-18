from fastapi import APIRouter, HTTPException
from ..internal import payments as payment_service

router = APIRouter(
    prefix="/payments"
)

@router.post("/", response_model=payment_service.ProcessPaymentResponse)
async def process_payment(req: payment_service.ProcessPaymentRequest) -> payment_service.ProcessPaymentResponse:
    try:
        return await payment_service.process_payment(req)
    except payment_service.PaymentValidationError:
        raise HTTPException(status_code=400, detail="Payment details invalid")
    except:
        raise HTTPException(status_code=500, detail="Service error")

@router.post("/{payment_id}", response_model=payment_service.GetPaymentDetailsResponse)
def get_payment_details(payment_id: str) -> payment_service.GetPaymentDetailsResponse:
    payment = payment_service.get_payment_details(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment ID not found")
    return payment