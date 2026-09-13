from pydantic import BaseModel
from typing import Optional, Dict, Any

class TransferRequest(BaseModel):
    user_id: str
    pin: str
    amount: float
    destination_account: str
    concept: str

class VoiceConfirmRequest(BaseModel):
    transaction_id: str
    user_response_text: str

class LoginRequest(BaseModel):
    username: str
    password: str

