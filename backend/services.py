import os
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

# Gemini Config
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ElevenLabs Config
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

def is_suspicious_transaction(amount: float, user_avg_amount: float = 1000.0) -> bool:
    # Lógica de detección de fraude simulada (podría ser un modelo en Snowflake)
    # Si el monto es mucho mayor al promedio (ej. > 3x), es sospechosa
    return amount > (user_avg_amount * 3)

async def evaluate_user_response(user_text: str) -> bool:
    """
    Usa Gemini para evaluar si el usuario está bajo presión o extorsión 
    basado en su respuesta.
    Retorna True si es seguro proceder, False si hay peligro/duda.
    """
    model = genai.GenerativeModel('gemini-1.5-pro')
    prompt = f"""
    Eres un asistente de seguridad bancaria experto en detectar coerción, 
    estrés o engaño en las respuestas de los usuarios.
    
    El usuario fue contactado para confirmar una transacción inusual y respondió:
    "{user_text}"
    
    Evalúa si la respuesta suena segura, natural y sin presión externa. 
    Si notas confusión, miedo, presión ("me dijeron que lo haga", "rápido por favor", "no sé pero debo hacerlo"), 
    o si dice que lo llamaron del banco pidiendo transferir, clasifícalo como PELIGRO (False).
    Si suena como una confirmación normal ("sí, soy yo", "todo bien, yo lo estoy haciendo"), clasifícalo como SEGURO (True).
    
    Responde ÚNICAMENTE con TRUE o FALSE.
    """
    response = model.generate_content(prompt)
    result = response.text.strip().upper()
    return "TRUE" in result

def generate_voice_alert(message: str) -> bytes:
    """
    Genera un audio con ElevenLabs preguntando al usuario sobre la transacción.
    Retorna los bytes del audio de forma sincrónica.
    """
    try:
        audio = elevenlabs_client.generate(
            text=message,
            voice="Rachel",
            model="eleven_multilingual_v2"
        )
        # audio is a generator, we need to consume it to bytes
        audio_bytes = b"".join([chunk for chunk in audio])
        return audio_bytes
    except Exception as e:
        print(f"Error generando audio con ElevenLabs: {e}")
        return b""

