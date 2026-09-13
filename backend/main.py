"""Punto de entrada de FastAPI y servidor de archivos del frontend."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import connect_mongo, close_mongo, init_snowflake
from .routes import router as api_router

app = FastAPI(title="Hacktec Banco PWA API")

# Permite que el frontend local consuma la API durante el prototipado.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    """Abre MongoDB y prepara la tabla de auditoría antes de recibir tráfico."""
    await connect_mongo()
    init_snowflake()

@app.on_event("shutdown")
async def shutdown_db_client():
    """Cierra las conexiones administradas por el backend."""
    await close_mongo()

# Todas las rutas de negocio quedan agrupadas bajo `/api`.
app.include_router(api_router, prefix="/api")

# Sirve los recursos de la PWA desde el mismo proceso que la API.
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))

