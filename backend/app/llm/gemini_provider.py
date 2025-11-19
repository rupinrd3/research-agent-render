"""
Google Gemini Provider

Implements the BaseLLMProvider interface for Google's Gemini API.
"""

import logging
import json
from collections.abc import Mapping, Sequence
from typing import Dict, Any, List, Optional
import google.generativeai as genai

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini API provider.

    Supports Gemini 2.5 Flash and other Gemini models with conversion
    between OpenAI and Gemini formats for compatibility.
    """

    # Pricing per 1M tokens (as of 2025)
    PRICING = {
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    }

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key
            model: Model name (default: gemini-2.5-flash)
        """
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = None  # Initialized per request

        logger.info(f"Initialized Gemini provider with model: {model}")

    async def complete(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tool_choice: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Generate completion using Gemini API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions for function calling
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Dict containing completion result and metadata

        Raises:
            Exception: If API call fails
        """
        try:
            # Convert full conversation to Gemini format
            gemini_contents = self._convert_full_conversation(messages)

            # Log conversation structure for debugging
            logger.info(f"Gemini conversation has {len(gemini_contents)} turns")
            for idx, content in enumerate(gemini_contents):
                role = content.get("role")
                parts = content.get("parts", [])
                parts_summary = []
                for part in parts:
                    if "text" in part:
                        text_preview = part['text'][:50] + "..." if len(part['text']) > 50 else part['text']
                        parts_summary.append(f"text({len(part['text'])} chars: '{text_preview}')")
                    elif "function_call" in part:
                        parts_summary.append(f"function_call({part['function_call']['name']})")
                    elif "function_response" in part:
                        parts_summary.append(f"function_response({part['function_response']['name']})")
                logger.info(f"  Turn {idx}: {role} with parts: {parts_summary}")

            # Validate conversation structure
            if not gemini_contents:
                raise ValueError("Empty conversation - no messages to send to Gemini")

            # Convert tools to Gemini format with cleaned schemas
            gemini_tools = None
            if tools:
                gemini_tools = [self._simplify_tool_def(tool) for tool in tools]

            # Initialize model
            model_kwargs = {"model_name": self.model_name}
            if gemini_tools:
                model_kwargs["tools"] = gemini_tools

            self.model = genai.GenerativeModel(**model_kwargs)

            # For multi-turn conversations with function calling, use generate_content
            # instead of start_chat to avoid history validation issues
            #
            # CRITICAL: Gemini's start_chat() validates that history is complete.
            # If history ends with a model turn containing function_call, it MUST
            # be followed by a user turn with function_response IN THE HISTORY.
            # Using generate_content() with full contents bypasses this limitation.

            response = await self.model.generate_content_async(
                contents=gemini_contents,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                ),
            )

            # Safety / block checks
            prompt_feedback = getattr(response, "prompt_feedback", None)
            if prompt_feedback:
                block_reason = getattr(prompt_feedback, "block_reason", None)
                if block_reason and str(block_reason) != "BLOCK_REASON_UNSPECIFIED":
                    raise Exception(f"Gemini safety block: {block_reason}")

            # Extract response
            tool_calls: List[Dict[str, Any]] = []
            content_chunks: List[str] = []

            candidates = getattr(response, "candidates", None)
            if not candidates:
                raise Exception("Gemini returned no candidates")

            for candidate in candidates:
                finish_reason = str(getattr(candidate, "finish_reason", "") or "").upper()
                if finish_reason == "SAFETY":
                    raise Exception("Gemini blocked output for safety")

                candidate_content = getattr(candidate, "content", None)
                parts = getattr(candidate_content, "parts", []) if candidate_content else []

                for part in parts:
                    if hasattr(part, "function_call") and part.function_call:
                        tool_calls.append(self._convert_function_call(part.function_call))
                    text_value = getattr(part, "text", None)
                    if text_value:
                        content_chunks.append(text_value)

            content = "\n".join(
                chunk.strip() for chunk in content_chunks if chunk and chunk.strip()
            )
            tool_calls = tool_calls or None

            if not content and not tool_calls:
                reasons = {
                    str(getattr(candidate, "finish_reason", "") or "").upper()
                    for candidate in candidates
                }
                reason_str = ", ".join(sorted(reasons)) or "UNKNOWN"
                raise Exception(
                    f"Gemini returned no content or tool calls (finish_reason={reason_str})"
                )

            # Get token usage
            usage_metadata = response.usage_metadata
            input_tokens = usage_metadata.prompt_token_count if usage_metadata else 0
            output_tokens = usage_metadata.candidates_token_count if usage_metadata else 0
            total_tokens = input_tokens + output_tokens

            return {
                "content": content,
                "tool_calls": tool_calls,
                "finish_reason": ",".join(
                    {
                        str(getattr(candidate, "finish_reason", "") or "").lower()
                        for candidate in candidates
                    }
                ),
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                },
                "model": self.model_name,
                "provider": "gemini",
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini API error: {error_msg}", exc_info=True)

            # Provide helpful error messages for common issues
            if "function call turn" in error_msg.lower():
                logger.error(
                    "Gemini function calling error - this usually indicates a conversation "
                    "history formatting issue. Check that function calls and responses are "
                    "properly paired in the conversation."
                )
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                logger.error(
                    "Gemini authentication failed. Verify GOOGLE_API_KEY in .env file."
                )

            raise Exception(f"Gemini API call failed: {error_msg}")

    def count_tokens(self, text: str) -> int:
        """
        Approximate token count for Gemini.

        Gemini uses a different tokenizer, so this is an approximation.

        Args:
            text: Text to count tokens for

        Returns:
            Approximate number of tokens
        """
        # Approximate: ~4 characters per token
        return len(text) // 4

    def get_model_name(self) -> str:
        """
        Get current model name.

        Returns:
            Model identifier string
        """
        return self.model_name

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost in USD for given token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        pricing = self.PRICING.get(
            self.model_name, self.PRICING["gemini-2.5-flash"]
        )
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def _clean_schema_for_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively remove unsupported fields from schema.

        Gemini ONLY supports: type, nullable, required, format,
        description, properties, items, enum, anyOf, $ref, $defs

        Args:
            schema: OpenAPI schema dictionary

        Returns:
            Cleaned schema compatible with Gemini
        """
        if not isinstance(schema, dict):
            return schema

        # Allowed fields per Gemini docs
        allowed_fields = {
            "type", "nullable", "required", "format",
            "description", "properties", "items", "enum",
            "anyOf", "$ref", "$defs"
        }

        cleaned = {}

        for key, value in schema.items():
            if key not in allowed_fields:
                continue  # Skip unsupported fields like default, minimum, maximum

            # Recursively clean nested objects
            if key == "properties" and isinstance(value, dict):
                cleaned[key] = {
                    k: self._clean_schema_for_gemini(v)
                    for k, v in value.items()
                }
            elif key == "items" and isinstance(value, dict):
                cleaned[key] = self._clean_schema_for_gemini(value)
            elif key == "anyOf" and isinstance(value, list):
                cleaned[key] = [
                    self._clean_schema_for_gemini(item)
                    for item in value
                ]
            elif key == "enum" and isinstance(value, list):
                # Filter out None from enum lists
                cleaned[key] = [v for v in value if v is not None]
            else:
                cleaned[key] = value

        return cleaned

    def _get_function_name_from_tool_call_id(
        self, messages: List[Dict[str, Any]], tool_call_id: str
    ) -> str:
        """
        Extract function name from previous assistant message's tool_calls.

        Args:
            messages: Full message history
            tool_call_id: ID of the tool call to find

        Returns:
            Function name or "unknown_function"
        """
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    if tc.get("id") == tool_call_id:
                        return tc["function"]["name"]
        return "unknown_function"

    def _convert_full_conversation(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert OpenAI message format to Gemini content format.

        Handles:
        - System messages (merge into first user message)
        - User messages
        - Assistant messages (with/without tool_calls)
        - Tool messages (convert to function responses)

        Args:
            messages: OpenAI format messages

        Returns:
            List of Gemini format content dicts
        """
        gemini_contents = []
        system_msg = ""
        pending_function_responses = []

        for i, msg in enumerate(messages):
            role = msg.get("role")

            if role == "system":
                # Store system message to prepend to first user message
                system_msg = msg.get("content", "")

            elif role == "user":
                # Build user message parts
                content = msg.get("content", "")

                # Prepend system message to first user message
                if system_msg and (i == 1 or (i > 0 and messages[i-1].get("role") == "system")):
                    content = f"{system_msg}\n\n{content}"
                    system_msg = ""  # Only use once

                # Combine pending function responses with user text in ONE message
                # This is critical: Gemini requires function_response and text in same user turn
                parts = []

                if pending_function_responses:
                    parts.extend(pending_function_responses)
                    pending_function_responses = []

                if content:
                    parts.append({"text": content})

                if parts:
                    gemini_contents.append({
                        "role": "user",
                        "parts": parts
                    })

            elif role == "assistant":
                parts = []

                # Add text content if present (even if empty string, add it when there's no tool_call)
                content = msg.get("content")
                if content:
                    parts.append({"text": content})

                # Add function calls if present
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        try:
                            args = json.loads(tc["function"]["arguments"])
                        except (json.JSONDecodeError, KeyError):
                            args = {}

                        parts.append({
                            "function_call": {
                                "name": tc["function"]["name"],
                                "args": args
                            }
                        })
                else:
                    # If no tool_calls and no content, add empty text to avoid empty parts
                    if not content:
                        parts.append({"text": ""})

                if parts:
                    gemini_contents.append({
                        "role": "model",
                        "parts": parts
                    })

            elif role == "tool":
                # Collect function responses to send together
                func_name = self._get_function_name_from_tool_call_id(
                    messages, msg.get("tool_call_id", "")
                )

                pending_function_responses.append({
                    "function_response": {
                        "name": func_name,
                        "response": {"result": msg.get("content", "")}
                    }
                })

        # Flush any remaining function responses
        if pending_function_responses:
            gemini_contents.append({
                "role": "user",
                "parts": pending_function_responses
            })

        return gemini_contents

    def _simplify_tool_def(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert OpenAI tool definition to Gemini-compatible format.

        Gemini's GenerativeModel accepts tool dicts in this format:
        {
            "function_declarations": [{
                "name": "...",
                "description": "...",
                "parameters": {...}  # Cleaned OpenAPI schema
            }]
        }

        Args:
            tool: OpenAI format tool definition

        Returns:
            Gemini format tool definition with cleaned schema
        """
        func = tool.get("function", {})

        # Clean the parameters schema to remove unsupported fields
        original_params = func.get("parameters", {})
        cleaned_params = self._clean_schema_for_gemini(original_params)

        return {
            "function_declarations": [{
                "name": func.get("name"),
                "description": func.get("description"),
                "parameters": cleaned_params,
            }]
        }

    def _convert_function_call(self, function_call) -> Dict[str, Any]:
        """
        Convert a single Gemini function call to OpenAI format.
        """
        # Extract args
        args = {}
        if hasattr(function_call, "args") and function_call.args:
            try:
                args = self._proto_to_builtin(function_call.args)
            except Exception as convert_error:
                logger.warning(f"Could not convert function args: {convert_error}")
                args = {}

        # Generate unique ID
        import time
        call_id = f"call_{function_call.name}_{int(time.time()*1000)}"

        return {
            "id": call_id,
            "type": "function",
            "function": {
                "name": function_call.name,
                "arguments": json.dumps(args),
            },
        }

    def _proto_to_builtin(self, value: Any) -> Any:
        """
        Recursively convert protobuf/GenAI collection types into plain Python data.
        """
        if value is None:
            return None

        if isinstance(value, Mapping):
            return {k: self._proto_to_builtin(v) for k, v in value.items()}

        if (
            isinstance(value, Sequence)
            and not isinstance(value, (str, bytes, bytearray))
        ):
            return [self._proto_to_builtin(v) for v in value]

        if hasattr(value, "to_dict"):
            try:
                return self._proto_to_builtin(value.to_dict())
            except Exception:
                pass

        if hasattr(value, "to_json"):
            try:
                return json.loads(value.to_json())
            except Exception:
                pass

        return value
