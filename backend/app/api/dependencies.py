"""
API Dependencies

Dependency injection functions for FastAPI.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_database
from ..config import load_settings
from ..llm import LLMManager

logger = logging.getLogger(__name__)

# Global instances (initialized on startup)
_settings = None
_llm_manager = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Yields:
        Async database session
    """
    async with await get_database() as session:
        yield session


def get_settings():
    """
    Dependency to get application settings.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = load_settings("../config.yaml")
    return _settings


def get_llm_manager() -> LLMManager:
    """
    Dependency to get LLM manager.

    Returns:
        LLM Manager instance
    """
    global _llm_manager
    if _llm_manager is None:
        settings = get_settings()
        from ..config import get_llm_config_dict

        _llm_manager = LLMManager(get_llm_config_dict(settings))

    return _llm_manager


def initialize_dependencies(settings=None, init_llm=True):
    """
    Initialize global dependencies on startup.

    Args:
        settings: Optional pre-loaded settings. If not provided, will load from default path.
        init_llm: Whether to initialize LLM manager on startup (default: True)
    """
    global _settings, _llm_manager

    # Load or use provided settings
    if settings is not None:
        _settings = settings
    else:
        _settings = load_settings("../config.yaml")

    # Optionally initialize LLM manager (skip on startup for faster boot)
    if init_llm:
        from ..config import get_llm_config_dict
        _llm_manager = LLMManager(get_llm_config_dict(_settings))

    logger.info("Dependencies initialized")
