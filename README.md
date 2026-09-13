# Detective Crab / SecureBank

Prototipo de banca segura para detectar transferencias inusuales y señales de posible coercion. La aplicacion combina una interfaz PWA, una API en FastAPI, MongoDB para el estado operativo, Snowflake para auditoria y servicios de Gemini y ElevenLabs para revisar y comunicar alertas.

> **Importante:** este proyecto es una demostracion tecnica. No debe manejar dinero real, credenciales reales ni datos personales de clientes.

## Arquitectura

El navegador carga la PWA desde FastAPI. `frontend/js/app.js` envia solicitudes HTTP a `/api`; `backend/routes.py` valida los datos, aplica las reglas de seguridad y coordina las bases de datos y servicios externos.

```mermaid
flowchart LR
    UI[Frontend PWA] -->|JSON /api| API[FastAPI]
    API --> MODELS[Modelos Pydantic]
    API --> RULES[Servicios de riesgo e IA]
    API --> MONGO[(MongoDB)]
    API --> SNOW[(Snowflake: auditoria)]
    RULES --> GEMINI[Google Gemini]
    RULES --> ELEVEN[ElevenLabs]
```

### Flujo de una transferencia

1. El frontend envia usuario, PIN, monto, cuenta destino y concepto a `POST /api/transfer`.
2. La API obtiene el usuario desde MongoDB.
3. Si el PIN coincide con el PIN invertido, se registra `PANIC_ALERT` en Snowflake y se responde con `503`.
4. Si el monto supera tres veces el promedio del usuario, se genera un audio de alerta y la operacion queda en estado `held`.
5. Si el monto es normal, se descuenta el saldo en MongoDB y se registra `APPROVED` en Snowflake.
6. Una operacion retenida se confirma con `POST /api/confirm_transfer`; Gemini clasifica la respuesta como segura o riesgosa y se registra el resultado.

## Estructura del proyecto

```text
.
|-- backend/
|   |-- __init__.py       Marca backend como paquete Python.
|   |-- main.py           Crea FastAPI, configura CORS, ciclo de vida y archivos estaticos.
|   |-- models.py         Define los esquemas Pydantic de entrada.
|   |-- routes.py         Implementa login, transferencias y confirmacion de seguridad.
|   |-- services.py       Contiene la regla de monto, Gemini y ElevenLabs.
|   `-- database.py       Abre MongoDB, conecta Snowflake y crea la tabla de auditoria.
|-- frontend/
|   |-- index.html        Estructura las vistas de login, transferencia, alerta y error.
|   |-- css/style.css     Define layout, formularios, botones y estados visuales.
|   |-- js/app.js         Maneja eventos, fetch, sesiones y cambios de pantalla.
|   |-- manifest.json     Declara nombre, iconos y modo instalable de la PWA.
|   `-- sw.js             Cachea recursos estaticos para carga con conectividad limitada.
|-- clientes.json         Datos de referencia; no se importa automaticamente en MongoDB.
|-- requirements.txt      Dependencias Python del backend.
|-- Dockerfile            Imagen y comando de arranque para produccion/demo.
`-- README.md             Documentacion tecnica y pasos de ejecucion.
```

## Responsabilidades por modulo

### Backend

- **`backend/main.py`**: crea la instancia `app`, permite CORS para desarrollo, inicializa MongoDB y Snowflake al arrancar, cierra MongoDB al detenerse y monta `frontend/` en `/static`.
- **`backend/models.py`**: define `LoginRequest`, `TransferRequest` y `VoiceConfirmRequest`. FastAPI usa estos modelos para validar automaticamente los cuerpos JSON.
- **`backend/routes.py`**: contiene la logica HTTP. El login busca o crea usuarios en `banco_db.usuarios`; la transferencia selecciona el flujo normal, de alerta silenciosa o de revision; la confirmacion consulta Gemini.
- **`backend/services.py`**: aisla integraciones externas. La regla local considera sospechoso un monto mayor que `3 * promedio`; Gemini analiza texto y ElevenLabs genera el MP3.
- **`backend/database.py`**: carga variables de entorno, conserva el cliente global de MongoDB y crea conexiones de Snowflake bajo demanda. La tabla `TRANSACTIONS` guarda estados de auditoria.

### Frontend

- **`frontend/index.html`**: contiene cuatro pantallas ocultables mediante la clase `active`: login, formulario de transferencia, confirmacion de voz y error 503.
- **`frontend/js/app.js`**: conserva `currentUserId` y `currentTransactionId`, envia las tres solicitudes de la API y decide que pantalla mostrar segun la respuesta.
- **`frontend/css/style.css`**: presenta la aplicacion en un contenedor movil y define los estilos de formularios, alertas, reproductor y error.
- **`frontend/manifest.json`**: configura la instalacion como aplicacion independiente. Sus iconos apuntan actualmente a recursos remotos de demostracion.
- **`frontend/sw.js`**: instala un cache estatico y responde primero desde cache. Las solicitudes de API no se precargan.

## API

| Metodo | Ruta | Funcion |
| --- | --- | --- |
| `POST` | `/api/login` | Busca el usuario o crea uno nuevo con saldo inicial simulado. |
| `POST` | `/api/transfer` | Valida PIN y monto; aprueba, retiene o activa alerta silenciosa. |
| `POST` | `/api/confirm_transfer` | Analiza la respuesta del usuario y resuelve una operacion retenida. |

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

La documentacion interactiva queda disponible en `/docs` y `/redoc` cuando el servidor esta activo.

## Configuracion

Crea un archivo `.env` en la raiz. No existe una plantilla automatica en el repositorio; usa estas variables como referencia:

```env
MONGODB_URI=mongodb+srv://usuario:contrasena@cluster.mongodb.net/
GEMINI_API_KEY=tu_clave_de_gemini
ELEVENLABS_API_KEY=tu_clave_de_elevenlabs
SNOWFLAKE_ACCOUNT=tu_cuenta
SNOWFLAKE_USER=tu_usuario
SNOWFLAKE_PASSWORD=tu_contrasena
SNOWFLAKE_WAREHOUSE=tu_warehouse
SNOWFLAKE_DATABASE=tu_base_de_datos
SNOWFLAKE_SCHEMA=tu_schema
SNOWFLAKE_ROLE=tu_rol
```

MongoDB debe aceptar la conexion indicada y Snowflake debe permitir crear `TRANSACTIONS`. El backend no lee `MONGODB_USERNAME` ni `MONGODB_PASSWORD` por separado: la autenticacion se obtiene de `MONGODB_URI`.

## Ejecucion local

Requisitos: Python 3.11 o posterior, acceso a MongoDB, Snowflake y las claves de Gemini y ElevenLabs.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000`. Para probar la interfaz, usa cualquier usuario nuevo y un PIN de prueba. Un usuario creado por el prototipo comienza con saldo `50000.0` y promedio de transaccion `1000.0`.

## Ejecucion con Docker

```powershell
docker build -t detective-crab .
docker run --env-file .env -p 8000:8000 --name detective-crab-app detective-crab
```

El `Dockerfile` instala `requirements.txt`, copia el backend y frontend, expone el puerto `8000` y arranca `uvicorn` escuchando en `0.0.0.0`.

## Pruebas manuales

1. **Flujo normal:** usa un monto menor o igual a `3 * avg_transaction`; debe descontar el saldo y registrar `APPROVED`.
2. **Flujo sospechoso:** usa un monto mayor a tres veces el promedio; debe devolver `held`, un identificador de transaccion y, si ElevenLabs responde, audio Base64.
3. **Flujo de panico:** introduce el PIN al reves; debe registrar `PANIC_ALERT` y devolver `503` sin revelar al atacante que la señal fue detectada.
4. **Confirmacion:** responde una frase segura o una frase que indique presion; Gemini determina si se registra `APPROVED_AFTER_REVIEW` o `BLOCKED_FRAUD_DETECTED`.

## Limitaciones conocidas

- El PIN se guarda en texto plano y el login crea usuarios automaticamente; esto solo es valido para una demo.
- La transferencia retenida no conserva todos sus datos para ejecutarla despues: la confirmacion registra la revision, pero no descuenta el saldo.
- Las consultas SQL se construyen con interpolacion de strings; una implementacion real debe usar parametros y validacion estricta.
- CORS permite cualquier origen y el frontend usa iconos remotos; ambos valores deben restringirse antes de desplegar.
- No hay suite automatizada de pruebas ni importador para `clientes.json`.
