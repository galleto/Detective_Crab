"""Endpoints HTTP que coordinan validación, reglas de riesgo y persistencia."""

from fastapi import APIRouter, HTTPException
import uuid
import base64

from .models import TransferRequest, VoiceConfirmRequest, LoginRequest
from .database import get_mongo_db, get_snowflake_conn
from .services import is_suspicious_transaction, evaluate_user_response, generate_voice_alert

router = APIRouter()

@router.post("/login")
async def login(request: LoginRequest):
    """Busca al usuario y crea un perfil de demostración si aún no existe."""
    # Simulación de login con MongoDB
    db = get_mongo_db()
    user = await db.usuarios.find_one({"username": request.username})
    
    if not user:
        # Modo prototipo: si no existe, lo creamos
        user_id = str(uuid.uuid4())
        await db.usuarios.insert_one({
            "user_id": user_id,
            "username": request.username,
            "pin": request.password, # en un entorno real, iría hasheado
            "balance": 500000.0,
            "avg_transaction": 1000.0
        })
        return {"status": "success", "user_id": user_id, "message": "Usuario creado"}
        
    if request.password != user["pin"]:
        raise HTTPException(status_code=401, detail="PIN incorrecto")
        
    return {"status": "success", "user_id": user["user_id"]}


@router.post("/transfer")
async def transfer(request: TransferRequest):
    """Ejecuta el flujo normal, de pánico o de revisión por monto inusual."""
    db = get_mongo_db()
    user = await db.usuarios.find_one({"user_id": request.user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    real_pin = user.get("pin", "")
    input_pin = request.pin

    # LOGICA 2: FLUJO DE PELIGRO / EXTORSION (PIN al revés)
    if input_pin == real_pin[::-1] and len(real_pin) > 1:
        # ALERTA SILENCIOSA
        print("!!! ALERTA DE PANICO RECIBIDA !!!")
        print(f"Usuario {request.user_id} ingresó el PIN al revés.")
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
            "message": "Transacción retenida por seguridad. Se requiere confirmación por voz.",
            "audio_base64": audio_b64
        }
        
    # LOGICA 1: FLUJO NORMAL
    new_balance = user["balance"] - request.amount
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
        
    return {"status": "success", "message": "Transferencia exitosa", "new_balance": new_balance}


@router.post("/confirm_transfer")
async def confirm_transfer(request: VoiceConfirmRequest):
    """Resuelve una transferencia retenida a partir del análisis de Gemini."""
    """
    Endpoint llamado después de que el usuario escucha el audio de ElevenLabs
    y responde por texto/voz (simulado por texto).
    """
    # Usar Gemini para evaluar la respuesta
    is_safe = await evaluate_user_response(request.user_response_text)
    
    if is_safe:
        # En un flujo real, aquí ejecutaríamos la transferencia que estaba en hold
        # Actualizando saldos en Mongo y logs en Snowflake
        try:
            conn = get_snowflake_conn()
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO TRANSACTIONS (ID, USER_ID, AMOUNT, DESTINATION, STATUS) VALUES ('{request.transaction_id}', 'N/A', 0, 'N/A', 'APPROVED_AFTER_REVIEW')")
            conn.close()
        except Exception:
            pass
            
        return {"status": "success", "message": "Transacción confirmada y aprobada por seguridad."}
    else:
        # Bloquear y alertar
        try:
            conn = get_snowflake_conn()
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO TRANSACTIONS (ID, USER_ID, AMOUNT, DESTINATION, STATUS) VALUES ('{request.transaction_id}', 'N/A', 0, 'N/A', 'BLOCKED_FRAUD_DETECTED')")
            conn.close()
        except Exception:
            pass
            
        raise HTTPException(status_code=403, detail="Transacción cancelada por posible riesgo o coerción. Comuníquese con el banco.")

