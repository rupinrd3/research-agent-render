"""
Configuration API Routes

Endpoints for viewing and updating system configuration.
"""

import logging
from fastapi import APIRouter, Depends

from ..models.requests import UpdateConfigRequest
from ..models.responses import ConfigResponse
from ..exceptions import InvalidConfigException
from ..dependencies import get_settings
from ...config import Settings, get_llm_config_dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("", response_model=ConfigResponse)
async def get_config(settings: Settings = Depends(get_settings)):
    """
    Get current system configuration.

    Returns LLM settings, research settings, tool settings, and evaluation settings.
    """
    return ConfigResponse(
        llm=get_llm_config_dict(settings),
        research={
            "max_iterations": settings.research.max_iterations,
            "timeout_minutes": settings.research.timeout_minutes,
        },
        tools={
            "web_search": {
                "max_results": settings.tools.web_search.max_results,
                "providers": settings.tools.web_search.providers,
            },
            "arxiv_search": {
                "max_results": settings.tools.arxiv_search.max_results,
            },
            "github_search": {
                "max_results": settings.tools.github_search.max_results,
            },
            "pdf_parser": {
                "max_pages": settings.tools.pdf_parser.max_pages,
            },
        },
        evaluation={
            "enabled": settings.evaluation.enabled,
            "per_step_evaluation": settings.evaluation.per_step_evaluation,
            "end_to_end_evaluation": settings.evaluation.end_to_end_evaluation,
            "llm_as_judge": settings.evaluation.llm_as_judge,
        },
    )


@router.put("", response_model=ConfigResponse)
async def update_config(
    request: UpdateConfigRequest,
    settings: Settings = Depends(get_settings),
):
    """
    Update system configuration.

    Note: This updates the in-memory configuration only.
    To persist changes, edit config.yaml directly.
    """
    try:
        # Update LLM settings
        if request.llm_settings:
            # TODO: Validate and update LLM settings
            logger.warning("LLM settings update not fully implemented")

        # Update research settings
        if request.research_settings:
            if "max_iterations" in request.research_settings:
                settings.research.max_iterations = request.research_settings[
                    "max_iterations"
                ]
            if "timeout_minutes" in request.research_settings:
                settings.research.timeout_minutes = request.research_settings[
                    "timeout_minutes"
                ]

        # Update tool settings
        if request.tool_settings:
            # TODO: Update tool settings
            logger.warning("Tool settings update not fully implemented")

        # Update evaluation settings
        if request.evaluation_settings:
            if "enabled" in request.evaluation_settings:
                settings.evaluation.enabled = request.evaluation_settings["enabled"]
            if "per_step_evaluation" in request.evaluation_settings:
                settings.evaluation.per_step_evaluation = request.evaluation_settings[
                    "per_step_evaluation"
                ]
            if "end_to_end_evaluation" in request.evaluation_settings:
                settings.evaluation.end_to_end_evaluation = request.evaluation_settings[
                    "end_to_end_evaluation"
                ]

        # Return updated config
        return await get_config(settings)

    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise InvalidConfigException(str(e))
