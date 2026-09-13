# 🦀 Detective Crab —

> **Track 3 · Real-Time Anomaly & Security Sentinel (Risk & Security Focus)**
>
> Motores de detección de anomalías conductuales que analizan libros de transacciones en tiempo real para señalar velocidad de transferencia inesperada, saltos sospechosos de categoría de comerciante o comportamientos anormales de cuenta.

Prototipo de banca segura que detecta transferencias inusuales y señales de posible coerción. La aplicación combina una interfaz PWA, una API en FastAPI, Capital One Nessie para datos bancarios simulados, MongoDB para el estado operativo, Snowflake para auditoría, y Gemini y ElevenLabs para revisar y comunicar alertas. Desplegado en Vultr bajo el dominio **[uncangrejocontrolamisfinanzas.tech](https://uncangrejocontrolamisfinanzas.tech/)**.

> **Importante:** este proyecto es una demostración técnica. No debe manejar dinero real, credenciales reales ni datos personales de clientes.

---

## 🏆 Retos

| Premio | Cómo lo usamos |
|---|---|
| **Best Use of Vultr** | La aplicación corre en un VPS de Vultr; Docker despliega el contenedor de FastAPI expuesto en el dominio `.tech`. Vultr provee la infraestructura de cómputo y red de todo el sistema. |
| **Best Use of Snowflake API** | Cada transacción (aprobada, retenida, pánico, fraude detectado) se registra en la tabla `TRANSACTIONS` de Snowflake. Funciona como capa de auditoría inmutable e independiente de MongoDB. |
| **Best Use of ElevenLabs** | Cuando un monto supera el umbral de riesgo, ElevenLabs genera un audio MP3 en voz natural que le pide al usuario una confirmación verbal de seguridad. El audio viaja como Base64 al frontend y se reproduce automáticamente. |
| **Best Use of Gemini API** | En el flujo de confirmación, Gemini analiza la respuesta en lenguaje natural del usuario y clasifica si es una respuesta libre (aprueba) o si contiene señales de presión o coerción (bloquea y registra fraude). |
| **Best Use of MongoDB Atlas** | MongoDB Atlas almacena el perfil de cada usuario: saldo, PIN, historial de montos y promedio de transacción. Es la fuente de verdad operativa que alimenta las reglas de riesgo en tiempo real. |
| **Best .Tech Domain Name** | El dominio **uncangrejocontrolamisfinanzas.tech** comunica con humor y claridad el concepto: un cangrejo detective vigilando tus finanzas. |

---

## 🏗️ Arquitectura

```mermaid
flowchart LR
    UI[Frontend PWA\nuncangrejocontrolamisfinanzas.tech]
    UI -->|JSON /api| API[FastAPI\nVultr VPS]

    API --> MODELS[Modelos Pydantic]
    API --> RULES[Servicios de riesgo e IA]

    API --> NESSIE[Capital One Nessie API\nDatos bancarios simulados]
    API --> MONGO[(MongoDB Atlas\nUsuarios y saldos)]
    API --> SNOW[(Snowflake\nAuditoría de transacciones)]

    RULES --> GEMINI[Google Gemini\nAnálisis de texto]
    RULES --> ELEVEN[ElevenLabs\nAudio de alerta]
```

### Stack tecnológico

| Capa | Tecnología |
|---|---|
| **Hosting / Infra** | Vultr VPS + Docker |
| **Dominio** | uncangrejocontrolamisfinanzas.tech |
| **Backend** | Python 3.11 · FastAPI · Uvicorn |
| **Datos bancarios simulados** | Capital One Nessie API (nessieisreal.com) |
| **Base de datos operativa** | MongoDB Atlas |
| **Auditoría** | Snowflake |
| **IA — análisis de texto** | Google Gemini |
| **IA — audio de alerta** | ElevenLabs |
| **Frontend** | PWA (HTML · CSS · JS vanilla) |

### Flujo de una transferencia

1. El frontend envía usuario, PIN, monto, cuenta destino y concepto a `POST /api/transfer`.
2. La API obtiene el perfil del usuario desde MongoDB Atlas.
3. Nessie provee los datos de cuentas y clientes bancarios simulados para el entorno de prueba.
4. Si el PIN coincide con el PIN invertido → se registra `PANIC_ALERT` en Snowflake y se responde con `503` (alerta silenciosa: el atacante no sabe que fue detectado).
5. Si el monto supera tres veces el promedio del usuario → ElevenLabs genera audio de alerta y la operación queda en estado `held`.
6. Si el monto es normal → se descuenta el saldo en MongoDB y se registra `APPROVED` en Snowflake.
7. Una operación retenida se confirma con `POST /api/confirm_transfer`; Gemini clasifica la respuesta como segura o riesgosa y se registra el resultado final.

---

## 📁 Estructura del proyecto

```text
.
├── backend/
│   ├── __init__.py       Marca backend como paquete Python.
│   ├── main.py           Crea FastAPI, configura CORS, ciclo de vida y archivos estáticos.
│   ├── models.py         Define los esquemas Pydantic de entrada.
│   ├── routes.py         Implementa login, transferencias y confirmación de seguridad.
│   ├── services.py       Contiene la regla de monto, Nessie, Gemini y ElevenLabs.
│   └── database.py       Abre MongoDB Atlas, conecta Snowflake y crea la tabla de auditoría.
├── frontend/
│   ├── index.html        Estructura las vistas de login, transferencia, alerta y error.
│   ├── css/style.css     Define layout, formularios, botones y estados visuales.
│   ├── js/app.js         Maneja eventos, fetch, sesiones y cambios de pantalla.
│   ├── manifest.json     Declara nombre, íconos y modo instalable de la PWA.
│   └── sw.js             Cachea recursos estáticos para carga con conectividad limitada.
├── clientes.json         Datos de referencia de Nessie; no se importa automáticamente.
├── requirements.txt      Dependencias Python del backend.
├── Dockerfile            Imagen y comando de arranque para Vultr.
└── README.md             Documentación técnica y pasos de ejecución.
```

---

## 📦 Responsabilidades por módulo

### Backend

- **`backend/main.py`**: crea la instancia `app`, permite CORS para desarrollo, inicializa MongoDB Atlas y Snowflake al arrancar, cierra MongoDB al detenerse y monta `frontend/` en `/static`.
- **`backend/models.py`**: define `LoginRequest`, `TransferRequest` y `VoiceConfirmRequest`. FastAPI usa estos modelos para validar automáticamente los cuerpos JSON.
- **`backend/routes.py`**: contiene la lógica HTTP. El login busca o crea usuarios en `banco_db.usuarios`; la transferencia selecciona el flujo normal, de alerta silenciosa o de revisión; la confirmación consulta Gemini.
- **`backend/services.py`**: aísla integraciones externas. La regla local considera sospechoso un monto mayor que `3 × promedio`; Nessie provee cuentas y transacciones simuladas; Gemini analiza texto y ElevenLabs genera el MP3.
- **`backend/database.py`**: carga variables de entorno, conserva el cliente global de MongoDB Atlas y crea conexiones de Snowflake bajo demanda. La tabla `TRANSACTIONS` guarda estados de auditoría.

### Frontend

- **`frontend/index.html`**: contiene cuatro pantallas ocultables mediante la clase `active`: login, formulario de transferencia, confirmación de voz y error 503.
- **`frontend/js/app.js`**: conserva `currentUserId` y `currentTransactionId`, envía las tres solicitudes de la API y decide qué pantalla mostrar según la respuesta.
- **`frontend/css/style.css`**: presenta la aplicación en un contenedor móvil y define los estilos de formularios, alertas, reproductor y error.
- **`frontend/manifest.json`**: configura la instalación como aplicación independiente.
- **`frontend/sw.js`**: instala un caché estático y responde primero desde caché. Las solicitudes de API no se precargan.

---

## 🌐 API

| Método | Ruta | Función |
|---|---|---|
| `POST` | `/api/login` | Busca el usuario en MongoDB o crea uno nuevo con saldo inicial simulado. |
| `POST` | `/api/transfer` | Valida PIN y monto; aprueba, retiene o activa alerta silenciosa. Consulta Nessie para datos de cuentas. |
| `POST` | `/api/confirm_transfer` | Analiza la respuesta del usuario con Gemini y resuelve una operación retenida. |

Ejemplo de transferencia:

```json
{
  "user_id": "id-obtenido-en-login",
  "pin": "1234",
  "amount": 2500,
  "destination_account": "0000000000000000",
  "concept": "Pago de prueba"
}
```

La documentación interactiva queda disponible en `/docs` y `/redoc` cuando el servidor está activo.

---

## ⚙️ Configuración

Crea un archivo `.env` en la raíz:

```env
# MongoDB Atlas
MONGODB_URI=mongodb+srv://usuario:contraseña@cluster.mongodb.net/
MONGODB_USERNAME=usuario
MONGODB_PASSWORD=contraseña

# Capital One Nessie
NESSIE_API_KEY=tu_clave_de_nessie

# IA
ELEVENLABS_API_KEY=tu_clave_de_elevenlabs
GEMINI_API_KEY=tu_clave_de_gemini

# Snowflake
SNOWFLAKE_ACCOUNT=tu_cuenta
SNOWFLAKE_USER=tu_usuario
SNOWFLAKE_PASSWORD=tu_contraseña
SNOWFLAKE_WAREHOUSE=tu_warehouse
SNOWFLAKE_DATABASE=tu_base_de_datos
SNOWFLAKE_SCHEMA=tu_schema
SNOWFLAKE_ROLE=tu_rol
```

---

## 🚀 Ejecución local

Requisitos: Python 3.11 o posterior, acceso a MongoDB Atlas, Snowflake, Nessie API y las claves de Gemini y ElevenLabs.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000`. Un usuario creado por el prototipo comienza con saldo `50000.0` y promedio de transacción `1000.0`.

## 🐳 Ejecución con Docker (Vultr)

```powershell
docker build -t detective-crab .
docker run --env-file .env -p 8000:8000 --name detective-crab-app detective-crab
```

El `Dockerfile` instala `requirements.txt`, copia el backend y frontend, expone el puerto `8000` y arranca `uvicorn` escuchando en `0.0.0.0`. En Vultr, el servidor corre este contenedor de forma continua.

---

## 🧪 Pruebas manuales

1. **Flujo normal:** usa un monto ≤ `3 × avg_transaction`; debe descontar el saldo y registrar `APPROVED` en Snowflake.
2. **Flujo sospechoso:** usa un monto > tres veces el promedio; debe devolver `held`, un identificador de transacción y, si ElevenLabs responde, audio Base64.
3. **Flujo de pánico:** introduce el PIN al revés; debe registrar `PANIC_ALERT` y devolver `503` sin revelar al atacante que la señal fue detectada.
4. **Confirmación:** responde una frase segura o una frase que indique presión; Gemini determina si se registra `APPROVED_AFTER_REVIEW` o `BLOCKED_FRAUD_DETECTED`.

---

## ⚠️ Limitaciones conocidas

- El PIN se guarda en texto plano y el login crea usuarios automáticamente; esto solo es válido para una demo.
- La transferencia retenida no descuenta el saldo al confirmarse: registra la revisión pero no ejecuta el movimiento.
- Las consultas SQL se construyen con interpolación de strings; una implementación real debe usar parámetros y validación estricta.
- CORS permite cualquier origen; debe restringirse antes de desplegar en producción.
- No hay suite automatizada de pruebas ni importador automático para `clientes.json`.
