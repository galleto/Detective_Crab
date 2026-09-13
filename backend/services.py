import os
from google import genai
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

# Gemini Config
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ElevenLabs Config
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

def is_suspicious_transaction(amount: float, user_avg_amount: float = 1000.0) -> bool:
    return amount > (user_avg_amount * 3)

async def evaluate_user_response(user_text: str) -> bool:
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
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    result = response.text.strip().upper()
    return "TRUE" in result

def generate_voice_alert(message: str) -> bytes:
    try:
        audio = elevenlabs_client.text_to_speech.convert(
            text=message,
            voice_id="21m00Tcm4TlvDq8ikWAM",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        audio_bytes = b"".join([chunk for chunk in audio])
        return audio_bytes
    except Exception as e:
        print(f"Error generando audio con ElevenLabs: {e}")
        return b""
