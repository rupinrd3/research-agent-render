"""
Application Settings

Centralized configuration management using Pydantic.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from pathlib import Path


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    api_key: Optional[str] = None
    model: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000
    max_completion_tokens: Optional[int] = None
    reasoning_effort: Optional[str] = None
    alternate_models: List[str] = Field(default_factory=list)


class LLMSettings(BaseModel):
    """LLM settings for all providers."""

    primary: str = "openai"
    fallback_order: List[str] = ["gemini", "openrouter"]
    openai: Optional[LLMConfig] = None
    gemini: Optional[LLMConfig] = None
    openrouter: Optional[LLMConfig] = None


class ResearchSettings(BaseModel):
    """Research execution settings."""

    max_iterations: int = 6
    timeout_minutes: int = 15
    parallel_tool_execution: bool = False
    # Agent policy knobs
    finish_guard_enabled: bool = True
    finish_guard_retry_on_auto_finish: bool = True
    sparse_result_threshold: int = 2
    sufficient_result_count: int = 5
    ascii_prompts: bool = True


class ToolsSettings(BaseModel):
    """Tool configuration settings."""

    # Web search settings (automatic provider failover)
    web_search_max_results: int = 10
    web_search_timeout_seconds: int = 90  # Total timeout for all providers
    tool_execution_timeout_seconds: int = 60  # Generic safety timeout per tool call

    # Search provider API keys (all optional, system tries in order)
    tavily_api_key: Optional[str] = None
    serper_api_key: Optional[str] = None
    serpapi_api_key: Optional[str] = None

    # Content pipeline
    use_content_pipeline: bool = True  # Enable content pipeline processing

    # Other tool settings
    arxiv_max_results: int = 20
    github_max_results: int = 10
    pdf_max_pages: int = 50


class EvaluationSettings(BaseModel):
    """Evaluation settings."""

    run_per_step: bool = True
    run_end_to_end: bool = True
    llm_as_judge: bool = True


class TracingSettings(BaseModel):
    """Tracing and observability settings."""

    enabled: bool = True
    provider: str = "custom"  # 'langsmith' or 'custom'
    langsmith_api_key: Optional[str] = None
    log_tool_outputs: bool = True
    log_llm_calls: bool = True


class DatabaseSettings(BaseModel):
    """Database configuration."""

    url: str = "sqlite+aiosqlite:///./research.db"
    echo: bool = False

    def get_async_url(self) -> str:
        """
        Get database URL with async driver.

        Transforms postgres:// or postgresql:// URLs to use asyncpg driver.
        Leaves other URLs (like SQLite) unchanged.

        Returns:
            Database URL with appropriate async driver
        """
        url = self.url

        # Transform PostgreSQL URLs to use asyncpg driver
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return url


class APISettings(BaseModel):
    """API server settings."""

    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_origins: List[str] = ["http://localhost:3000"]


class Settings(BaseModel):
    """
    Main application settings.

    Loads configuration from config.yaml and environment variables.
    """

    llm: LLMSettings
    research: ResearchSettings = Field(default_factory=ResearchSettings)
    tools: ToolsSettings = Field(default_factory=ToolsSettings)
    evaluation: EvaluationSettings = Field(
        default_factory=EvaluationSettings
    )
    tracing: TracingSettings = Field(default_factory=TracingSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)


def load_settings(config_path: str = "config.yaml") -> Settings:
    """
    Load settings from YAML file and environment variables.

    Environment variables take precedence over config file values.

    Args:
        config_path: Path to config YAML file

    Returns:
        Settings instance

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If configuration is invalid
    """
    # Load .env file if it exists (check multiple locations)
    from dotenv import load_dotenv
    config_file = Path(config_path)

    # Try to find .env file in same directory as config.yaml or parent directories
    env_locations = [
        config_file.parent / ".env",  # Same dir as config.yaml
        config_file.parent.parent / ".env",  # Parent dir (for backend/config case)
        Path(".env"),  # Current directory
        Path("../.env"),  # Parent directory
    ]

    for env_path in env_locations:
        if env_path.exists():
            load_dotenv(env_path, override=False)
            break

    # Load from YAML file
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    # Replace environment variable placeholders
    config = _replace_env_vars(config)

    # Create and validate settings
    return Settings(**config)


def _replace_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace ${ENV_VAR} or ${ENV_VAR:default} placeholders with environment variable values.

    Supports syntax:
    - ${ENV_VAR} - Returns env var value or None if not set
    - ${ENV_VAR:default_value} - Returns env var value or default_value if not set

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with environment variables replaced
    """
    if isinstance(config, dict):
        return {
            key: _replace_env_vars(value) for key, value in config.items()
        }
    elif isinstance(config, list):
        return [_replace_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        # Extract variable name and default value
        content = config[2:-1]  # Remove ${ and }

        # Check if default value is specified (syntax: ${VAR:default})
        if ":" in content:
            env_var, default_value = content.split(":", 1)
            value = os.getenv(env_var)
            return value if value is not None else default_value
        else:
            # No default value specified
            env_var = content
            value = os.getenv(env_var)
            if value is None:
                # Return None for missing env vars - allows optional API keys
                return None
            return value
    else:
        return config


def get_llm_config_dict(settings: Settings) -> Dict[str, Any]:
    """
    Convert Settings to LLM Manager configuration dict.

    Args:
        settings: Application settings

    Returns:
        Dict suitable for LLMManager initialization
    """
    llm_config = {
        "primary": settings.llm.primary,
        "fallback_order": settings.llm.fallback_order,
    }

    # Include all providers with API keys (no filtering)
    if settings.llm.openai and settings.llm.openai.api_key:
        llm_config["openai"] = {
            "api_key": settings.llm.openai.api_key,
            "model": settings.llm.openai.model,
        }
        if settings.llm.openai.temperature is not None:
            llm_config["openai"]["temperature"] = settings.llm.openai.temperature
        if settings.llm.openai.max_tokens is not None:
            llm_config["openai"]["max_tokens"] = settings.llm.openai.max_tokens
        if settings.llm.openai.max_completion_tokens is not None:
            llm_config["openai"]["max_completion_tokens"] = (
                settings.llm.openai.max_completion_tokens
            )
        if settings.llm.openai.reasoning_effort:
            llm_config["openai"]["reasoning_effort"] = (
                settings.llm.openai.reasoning_effort
            )
        if settings.llm.openai.alternate_models:
            llm_config["openai"]["alternate_models"] = settings.llm.openai.alternate_models

    if settings.llm.gemini and settings.llm.gemini.api_key:
        llm_config["gemini"] = {
            "api_key": settings.llm.gemini.api_key,
            "model": settings.llm.gemini.model,
        }
        if settings.llm.gemini.temperature is not None:
            llm_config["gemini"]["temperature"] = settings.llm.gemini.temperature
        if settings.llm.gemini.alternate_models:
            llm_config["gemini"]["alternate_models"] = settings.llm.gemini.alternate_models

    if settings.llm.openrouter and settings.llm.openrouter.api_key:
        llm_config["openrouter"] = {
            "api_key": settings.llm.openrouter.api_key,
            "model": settings.llm.openrouter.model,
        }
        if settings.llm.openrouter.temperature is not None:
            llm_config["openrouter"]["temperature"] = settings.llm.openrouter.temperature
        if settings.llm.openrouter.alternate_models:
            llm_config["openrouter"]["alternate_models"] = settings.llm.openrouter.alternate_models

    return llm_config
