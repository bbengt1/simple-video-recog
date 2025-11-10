# FastAPI application for video recognition system

import logging
import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import events, health, metrics, stream
from core.config import load_config

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    # Load configuration (used implicitly by dependencies)
    load_config("config/config.yaml")

    # Create FastAPI app
    app = FastAPI(
        title="Local Video Recognition System API",
        version="1.0.0",
        description="REST API and WebSocket for event access and real-time monitoring",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(events.router, prefix="/api", tags=["events"])
    app.include_router(metrics.router, prefix="/api", tags=["metrics"])
    app.include_router(stream.router, prefix="", tags=["websocket"])  # No prefix for /ws

    # Mount static files
    web_dir = Path(__file__).parent.parent / "web"
    if web_dir.exists():
        app.mount("/css", StaticFiles(directory=web_dir / "css"), name="css")
        app.mount("/js", StaticFiles(directory=web_dir / "js"), name="js")

        # Serve index.html at root
        from fastapi.responses import FileResponse

        @app.get("/")
        async def read_root():
            return FileResponse(web_dir / "index.html")

    # Mount event images
    events_dir = Path("data/events")
    if events_dir.exists():
        app.mount("/images", StaticFiles(directory=events_dir), name="images")

    # Startup event to start WebSocket heartbeat
    @app.on_event("startup")
    async def startup_event():
        ws_manager = stream.get_websocket_manager()
        asyncio.create_task(ws_manager.start_heartbeat(interval=30))
        logger.info("WebSocket heartbeat task started")

    # Shutdown event to close all WebSocket connections
    @app.on_event("shutdown")
    async def shutdown_event():
        ws_manager = stream.get_websocket_manager()
        await ws_manager.close_all()
        logger.info("All WebSocket connections closed")

    logger.info("FastAPI application created with WebSocket support")
    return app

app = create_app()
