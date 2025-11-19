"""
API Request Models
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class StartResearchRequest(BaseModel):
    """Request to start a new research session."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Research query",
        examples=["What are the latest advances in multimodal LLMs?"],
    )

    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional research configuration override",
    )

    # Legacy/top-level overrides kept for backward compatibility with older clients
    llm_provider: Optional[str] = Field(
        default=None,
        description="Preferred LLM provider (legacy)",
    )
    llm_model: Optional[str] = Field(
        default=None,
        description="Preferred LLM model (legacy)",
    )
    temperature: Optional[float] = Field(
        default=None,
        description="LLM temperature override (legacy)",
    )
    max_iterations: Optional[int] = Field(
        default=None,
        description="Max iteration override (legacy)",
    )


class UpdateConfigRequest(BaseModel):
    """Request to update system configuration."""

    llm_settings: Optional[Dict[str, Any]] = Field(
        default=None, description="LLM configuration"
    )

    research_settings: Optional[Dict[str, Any]] = Field(
        default=None, description="Research settings"
    )

    tool_settings: Optional[Dict[str, Any]] = Field(
        default=None, description="Tool settings"
    )

    evaluation_settings: Optional[Dict[str, Any]] = Field(
        default=None, description="Evaluation settings"
    )
