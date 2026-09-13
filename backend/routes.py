import uuid
import base64
from fastapi import APIRouter, HTTPException
from .models import TransferRequest, VoiceConfirmRequest, LoginRequest
from .database import get_mongo_db, get_snowflake_conn
from .services import is_suspicious_transaction, generate_voice_alert, evaluate_user_response

router = APIRouter()

@router.post("/login")
async def login(request: LoginRequest):
    db = get_mongo_db()
    if db is None:
        # Si la base de datos no está disponible, usamos un fallback dummy
        return {"user_id": request.username, "message": "Login exitoso (fallback)"}
        
    user = await db.usuarios.find_one({"user_id": request.username})
    if not user:
        # Dummy fallback para hackathon
        user = {
            "user_id": request.username,
            "password": request.password,
            "pin": "1234",
            "balance": 10000.0,
            "avg_transaction": 1000.0
        }
        await db.usuarios.insert_one(user)
    
    return {"user_id": user["user_id"], "message": "Login exitoso"}

@router.post("/confirm_transfer")
async def confirm_transfer(request: VoiceConfirmRequest):
    is_safe = await evaluate_user_response(request.user_response_text)
    if is_safe:
        return {"status": "success", "message": "Transferencia confirmada y procesada correctamente."}
    else:
        raise HTTPException(status_code=403, detail="Alerta de seguridad activada. Transacción cancelada y cuenta protegida.")

@router.post("/transfer")
async def transfer(request: TransferRequest):
    """Ejecuta el flujo normal, de pánico o de revisión por monto inusual."""
    db = get_mongo_db()
    if db is not None:
        user = await db.usuarios.find_one({"user_id": request.user_id})
    else:
        user = None
    
    if not user:
        # Fallback si no hay usuario en DB
        user = {
            "user_id": request.user_id,
            "pin": "1234",
            "balance": 10000.0,
            "avg_transaction": 1000.0
        }

    real_pin = user.get("pin", "1234")
    input_pin = request.pin

    # Definir cuál será el PIN de pánico
    es_palindromo = real_pin == real_pin[::-1]
    pin_panico = "9111" if es_palindromo else real_pin[::-1]

    # LOGICA 2: FLUJO DE PELIGRO / EXTORSION (Botón de pánico)
    if input_pin in ["911", "9111"] or (input_pin == pin_panico and len(real_pin) > 1):
        # ALERTA SILENCIOSA
        print("!!! ALERTA DE PANICO RECIBIDA !!!")
        print(f"Usuario {request.user_id} ingresó el PIN de pánico.")
        print("Enviando coordenadas y alertando autoridades...")

        # Guardar en Snowflake (Flujo de pánico)
        try:
            conn = get_snowflake_conn()
            cursor = conn.cursor()
            tx_id = str(uuid.uuid4())
            cursor.execute(f"INSERT INTO TRANSACTIONS (ID, USER_ID, AMOUNT, DESTINATION, STATUS) VALUES ('{tx_id}', '{request.user_id}', {request.amount}, '{request.destination_account}', 'PANIC_ALERT')")
            conn.close()
        except Exception as e:
            print("Error logueando pánico en Snowflake:", e)

        # Simular error 503 para el atacante/extorsionador
        raise HTTPException(status_code=503, detail="System down. Tu cuenta ha sido congelada temporalmente por fallas del sistema. Acude a una sucursal.")

    if input_pin != real_pin:
        raise HTTPException(status_code=401, detail="PIN incorrecto")

# LOGICA 3: FLUJO DE TRANSACCION SOSPECHOSA
    user_avg = user.get("avg_transaction", 1000.0)
    if is_suspicious_transaction(request.amount, user_avg):
        tx_id = str(uuid.uuid4())
        # Generar alerta de voz con ElevenLabs
        audio_msg = f"Hola. Hemos detectado una transferencia inusual por {request.amount} pesos hacia {request.destination_account}. Por favor, dime: ¿reconoces esta transacción y estás seguro de querer realizarla?"
        audio_bytes = generate_voice_alert(audio_msg)
        
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8') if audio_bytes else ""
        
        # Pausar la transacción y esperar confirmación
        return {
            "status": "held",
            "transaction_id": tx_id,
            "message": "Transacción retenida por seguridad. Se requiere confirmación.",
            "spoken_text": audio_msg,  # <-- AQUÍ MANDAMOS EL TEXTO PARA ACCESIBILIDAD
            "audio_base64": audio_b64
        }
        
    # LOGICA 1: FLUJO NORMAL
    new_balance = user["balance"] - request.amount
    if db is not None:
        await db.usuarios.update_one({"user_id": request.user_id}, {"$set": {"balance": new_balance}})
    
    # Registrar en Snowflake
    try:
        conn = get_snowflake_conn()
        cursor = conn.cursor()
        tx_id = str(uuid.uuid4())
        cursor.execute(f"INSERT INTO TRANSACTIONS (ID, USER_ID, AMOUNT, DESTINATION, STATUS) VALUES ('{tx_id}', '{request.user_id}', {request.amount}, '{request.destination_account}', 'APPROVED')")
        conn.close()
    except Exception as e:
        print("Error en Snowflake:", e)
        
    return {
        "status": "success",
        "message": "Transferencia exitosa",
        "transaction_id": tx_id,
        "new_balance": new_balance
    }