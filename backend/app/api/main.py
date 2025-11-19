"""
FastAPI Application

Main FastAPI application with REST API and WebSocket support.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routes import (
    research_router,
    export_router,
    history_router,
    config_router,
    metrics_router,
)
from .websocket import router as websocket_router
from .dependencies import initialize_dependencies
from ..database import init_database, close_database
from ..config import load_settings

logger = logging.getLogger(__name__)


class WebSocketAccessFilter(logging.Filter):
    """Suppress noisy WebSocket accepted/open logs from Uvicorn/websockets."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if "WebSocket" in message and "[accepted]" in message:
            return False
        if message.startswith("connection open") or message.startswith("connection closed"):
            return False
        return True


def _install_ws_log_filter():
    filter_instance = WebSocketAccessFilter()
    target_loggers = (
        "uvicorn.access",
        "uvicorn.asgi",
        "uvicorn.error",
        "websockets.server",
    )
    for logger_name in target_loggers:
        target_logger = logging.getLogger(logger_name)
        # Lower verbosity for noisy WebSocket internals
        if logger_name.startswith("websockets."):
            target_logger.setLevel(logging.WARNING)
        target_logger.addFilter(filter_instance)
        for handler in target_logger.handlers:
            handler.addFilter(filter_instance)
    # Attach to root logger as a final safeguard so reloader-created handlers
    # also drop the noisy WebSocket accepted/open/closed lines.
    root_logger = logging.getLogger()
    root_logger.addFilter(filter_instance)
    for handler in root_logger.handlers:
        handler.addFilter(filter_instance)


_install_ws_log_filter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info("Starting FastAPI application...")
    _install_ws_log_filter()

    # Load settings (config.yaml is in parent directory when run from backend/)
    settings = load_settings("../config.yaml")

    # Initialize database (with async driver transformation)
    await init_database(settings.database.get_async_url(), echo=settings.database.echo)

    # Initialize dependencies (without LLM manager - will be lazy loaded)
    initialize_dependencies(settings, init_llm=False)

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI application...")

    # Close database
    await close_database()

    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="Agentic AI Research System",
        description="REST API and WebSocket server for autonomous research",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify actual origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(research_router)
    app.include_router(export_router)
    app.include_router(history_router)
    app.include_router(config_router)
    app.include_router(metrics_router)
    app.include_router(websocket_router)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "research-api"}

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Agentic AI Research System API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    logger.info("FastAPI application created")

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
