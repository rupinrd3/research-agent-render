"""
FastAPI REST API

Provides REST endpoints and WebSocket server for the research system.
"""

from .main import create_app

__all__ = ["create_app"]
