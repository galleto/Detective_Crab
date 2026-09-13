"""Clientes y operaciones de inicialización de los almacenes externos."""

import os
from motor.motor_asyncio import AsyncIOMotorClient
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

# MongoDB Config
MONGO_URI = os.getenv("MONGODB_URI")
mongo_client = None
db = None

def get_mongo_db():
    """Devuelve la base de datos MongoDB abierta durante el arranque."""
    return db


async def connect_mongo():
    """Crea el cliente asíncrono y selecciona la base `banco_db`."""
    global mongo_client, db
    print("Conectando a MongoDB...")
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client.banco_db # Nombre de la base de datos
    print("Conexión a MongoDB establecida.")

async def close_mongo():
    """Libera el cliente MongoDB cuando la aplicación se apaga."""
    global mongo_client
    if mongo_client:
        mongo_client.close()

# Snowflake Config
def get_snowflake_conn():
    """Abre una conexión Snowflake usando las variables del archivo `.env`."""
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        role=os.getenv("SNOWFLAKE_ROLE")
    )
    return conn

def init_snowflake():
    """Garantiza que exista la tabla usada para auditar transacciones."""
    print("Iniciando conexión a Snowflake...")
    try:
        conn = get_snowflake_conn()
        cursor = conn.cursor()
        # Crear tabla de transacciones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TRANSACTIONS (
                ID VARCHAR,
                USER_ID VARCHAR,
                AMOUNT FLOAT,
                DESTINATION VARCHAR,
                STATUS VARCHAR,
                TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
            )
        """)
        conn.close()
        print("Snowflake inicializado correctamente.")
    except Exception as e:
        print(f"Error conectando a Snowflake: {e}")

