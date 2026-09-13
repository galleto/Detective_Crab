import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import connect_mongo, close_mongo, init_snowflake
from .routes import router as api_router

app = FastAPI(title="Hacktec Banco PWA API")

# CORS setup for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await connect_mongo()
    init_snowflake()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo()

# Incluir las rutas de la API
app.include_router(api_router, prefix="/api")

# Montar los estáticos para el frontend PWA
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))

