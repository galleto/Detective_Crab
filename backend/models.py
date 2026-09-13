"""Esquemas de entrada que validan los cuerpos de la API."""

from pydantic import BaseModel


class TransferRequest(BaseModel):
    """Datos necesarios para solicitar una transferencia."""

    user_id: str
    pin: str
    amount: float
    destination_account: str
    concept: str

class VoiceConfirmRequest(BaseModel):
    """Respuesta del usuario para revisar una transferencia retenida."""

    transaction_id: str
    user_response_text: str

class LoginRequest(BaseModel):
    """Credenciales usadas por el endpoint de inicio de sesión."""

    username: str
    password: str

