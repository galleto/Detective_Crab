# Detective Crab

Aplicacion web de demostracion para detectar transferencias inusuales y situaciones de posible coercion. El proyecto combina una interfaz bancaria, una API en FastAPI, MongoDB, Snowflake, Gemini y ElevenLabs.

> **Aviso:** es un prototipo para demostracion. No debe usarse para manejar dinero real ni datos reales de clientes.

## Que necesitas

Elige una de estas opciones:

- **Docker Desktop**, recomendado si no quieres instalar Python.
- **Python 3.11 o posterior**, si prefieres ejecutarlo directamente.

En ambos casos necesitaras acceso a estos servicios:

- MongoDB, para usuarios y saldos.
- Snowflake, para registrar transacciones.
- Google Gemini, para analizar la respuesta de seguridad.
- ElevenLabs, para generar el audio de alerta.

Las credenciales las debe proporcionar la persona responsable del proyecto. Nunca las publiques en GitHub.

## Descargar el proyecto

1. Instala Git desde [git-scm.com/downloads](https://git-scm.com/downloads).
2. Abre PowerShell o una terminal.
3. Ejecuta:

```powershell
git clone https://github.com/galleto/Detective_Crab.git
cd Detective_Crab
```

## Configurar las credenciales

1. Crea un archivo llamado `.env` en la carpeta principal del proyecto.
2. Copia en ese archivo la plantilla de `.env.example`.
3. Reemplaza cada valor de ejemplo por las credenciales reales.

El archivo debe tener esta forma:

```env
MONGODB_URI=mongodb+srv://usuario:contraseña@cluster.mongodb.net/
MONGODB_USERNAME=usuario
MONGODB_PASSWORD=contraseña

ELEVENLABS_API_KEY=tu_clave_de_elevenlabs
GEMINI_API_KEY=tu_clave_de_gemini

SNOWFLAKE_ACCOUNT=tu_cuenta
SNOWFLAKE_USER=tu_usuario
SNOWFLAKE_PASSWORD=tu_contraseña
SNOWFLAKE_WAREHOUSE=tu_warehouse
SNOWFLAKE_DATABASE=tu_base_de_datos
SNOWFLAKE_SCHEMA=tu_schema
SNOWFLAKE_ROLE=tu_rol
```

No subas `.env` al repositorio. Ya esta incluido en `.gitignore` y `.dockerignore`.

## Opcion A: ejecutar con Docker

1. Instala y abre [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Desde la carpeta del proyecto, construye la imagen:

```powershell
docker build -t detective-crab .
```

3. Inicia la aplicacion:

```powershell
docker run --env-file .env -p 8000:8000 --name detective-crab-app detective-crab
```

4. Abre [http://localhost:8000](http://localhost:8000) en el navegador.

Para detenerla, pulsa `Ctrl+C`. Si el nombre ya existe, elimina el contenedor anterior con:

```powershell
docker rm -f detective-crab-app
```

## Opcion B: ejecutar con Python

1. Instala Python 3.11 o posterior desde [python.org/downloads](https://www.python.org/downloads/). Durante la instalacion, activa **Add Python to PATH**.
2. Abre una terminal en la carpeta del proyecto.
3. Crea un entorno virtual:

```powershell
python -m venv .venv
```

4. Activalo en Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activacion, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a intentarlo.

5. Instala las dependencias:

```powershell
python -m pip install -r requirements.txt
```

6. Inicia el servidor:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

7. Abre [http://127.0.0.1:8000](http://127.0.0.1:8000).

Para detener el servidor, pulsa `Ctrl+C` en la terminal.

## Como probarlo

1. En la pantalla de inicio, escribe cualquier usuario y PIN de prueba. Si no existe, el sistema lo crea en MongoDB.
2. Completa una transferencia con un monto menor o igual a tres veces el promedio del usuario. Debe aprobarse de forma normal.
3. Para probar la alerta de transferencia inusual, usa un monto mayor a tres veces el promedio. El sistema pedira una confirmacion de seguridad.
4. Para probar la alerta silenciosa, introduce el PIN al reves durante una transferencia. El sistema mostrara un error 503 simulado.

El usuario nuevo comienza con un saldo simulado de `$50,000` y un promedio de transaccion de `$1,000`.

## Direcciones utiles

- Aplicacion: [http://localhost:8000](http://localhost:8000)
- Documentacion interactiva de la API: [http://localhost:8000/docs](http://localhost:8000/docs)
- Esquema alternativo de la API: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Problemas frecuentes

**El navegador no abre la pagina**

Confirma que la terminal muestre que Uvicorn esta ejecutandose y que estas usando el puerto `8000`.

**Aparece un error al iniciar MongoDB o Snowflake**

Revisa que `.env` exista, que no tenga espacios alrededor de `=`, y que las credenciales y permisos sigan vigentes.

**La alerta de voz no tiene audio**

Comprueba `ELEVENLABS_API_KEY`. Si la clave no funciona, la aplicacion puede continuar, pero la respuesta recibida no tendra audio.

**La confirmacion de seguridad falla**

Comprueba `GEMINI_API_KEY` y que la cuenta tenga acceso al modelo configurado.

## Estructura principal

```text
backend/       API, conexiones y reglas de seguridad
frontend/      Interfaz web y PWA
clientes.json  Datos de ejemplo
Dockerfile     Configuracion para ejecutar con Docker
requirements.txt
```
