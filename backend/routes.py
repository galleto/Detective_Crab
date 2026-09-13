@router.post("/transfer")
async def transfer(request: TransferRequest):
    """Ejecuta el flujo normal, de pánico o de revisión por monto inusual."""
    db = get_mongo_db()
    user = await db.usuarios.find_one({"user_id": request.user_id})
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    real_pin = user.get("pin", "")
    input_pin = request.pin

    # Definir cuál será el PIN de pánico
    es_palindromo = real_pin == real_pin[::-1]
    pin_panico = "9111" if es_palindromo else real_pin[::-1]

    # LOGICA 2: FLUJO DE PELIGRO / EXTORSION (Botón de pánico)
    if input_pin == pin_panico and len(real_pin) > 1:
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