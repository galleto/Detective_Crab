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
    return db

async def connect_mongo():
    global mongo_client, db
    print("Conectando a MongoDB...")
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client.banco_db # Nombre de la base de datos
    print("Conexión a MongoDB establecida.")

async def close_mongo():
    global mongo_client
    if mongo_client:
        mongo_client.close()

# Snowflake Config
def get_snowflake_conn():
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

