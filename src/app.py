from typing import Dict
from fastapi import FastAPI
from .handlers import payments

app = FastAPI()

app.include_router(payments.router)

@app.get("/")
async def ping() -> Dict[str, str]:
    return {"app": "payment-gateway-api"}
