import random

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="TraceNet API")

RISK_THRESHOLD = 0.7


class Transaction(BaseModel):
    transaction_id: str
    sender_account: str
    receiver_account: str
    amount: float
    currency: str = "USD"


@app.get("/")
def root():
    return {"status": "ok", "service": "TraceNet AML API"}


@app.post("/score_transaction")
def score_transaction(transaction: Transaction):
    risk_score = round(random.uniform(0.0, 1.0), 4)
    action = "BLOCK" if risk_score >= RISK_THRESHOLD else "ALLOW"
    return {
        "transaction_id": transaction.transaction_id,
        "risk_score": risk_score,
        "action": action,
    }
