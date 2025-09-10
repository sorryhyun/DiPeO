"""Text format handling for structured output in PersonJob nodes."""

import logging
import os
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TextFormatHandler:
    """Handles text format configuration for structured outputs."""

    def __init__(self):
        self._base_dir = os.environ.get("DIPEO_BASE_DIR", os.getcwd())

    def get_pydantic_model(self, node: Any) -> type[BaseModel] | None:
        """Get Pydantic model from node's text_format configuration."""
        text_format_content = self._load_text_format_content(node)

        if not text_format_content:
            return None

        model = self._compile_pydantic_model(text_format_content)
        if not model:
            logger.warning(
                f"[TextFormatHandler] Failed to compile Pydantic model for node {node.id}"
            )
        return model

    def _load_text_format_content(self, node: Any) -> str | None:
        """Load text format content from file or inline configuration."""
        if hasattr(node, "text_format_file") and node.text_format_file:
            content = self._load_from_file(node.text_format_file)
            if content:
                return content

        if hasattr(node, "text_format") and node.text_format:
            return node.text_format
        return None

    def _load_from_file(self, file_path: str) -> str | None:
        """Load Pydantic models from external file."""
        if not os.path.isabs(file_path):
            file_path = os.path.join(self._base_dir, file_path)

        if os.path.exists(file_path):
            try:
                with open(file_path) as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read text_format_file {file_path}: {e}")
        else:
            logger.warning(f"text_format_file not found: {file_path}")

        return None

    def _compile_pydantic_model(self, content: str) -> type[BaseModel] | None:
        """Compile Python code string into a Pydantic BaseModel class."""
        from dipeo.infrastructure.llm.drivers.pydantic_compiler import (
            compile_pydantic_model,
            is_pydantic_code,
        )

        if isinstance(content, str) and is_pydantic_code(content):
            pydantic_model = compile_pydantic_model(content)
            if pydantic_model:
                return pydantic_model
            else:
                logger.warning("Failed to compile Pydantic model from text_format")
        else:
            logger.warning("text_format must be Python code defining Pydantic models")

        return None

    def process_structured_output(self, result: Any, has_text_format: bool) -> dict | None:
        """Process LLM result for structured output."""
        if not has_text_format:
            return None
        if hasattr(result, "text") and result.text:
            import json

            try:
                parsed = json.loads(result.text)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError) as e:
                logger.debug(f"[TextFormatHandler] Failed to parse text as JSON: {e}")

        if hasattr(result, "raw_response") and result.raw_response:
            raw_data = result.raw_response

            if hasattr(raw_data, "parsed") and raw_data.parsed:
                if hasattr(raw_data.parsed, "model_dump"):
                    return raw_data.parsed.model_dump()
                elif hasattr(raw_data.parsed, "dict"):
                    return raw_data.parsed.dict()
                elif isinstance(raw_data.parsed, dict):
                    return raw_data.parsed

            if hasattr(raw_data, "output_parsed") and raw_data.output_parsed:
                if hasattr(raw_data.output_parsed, "model_dump"):
                    return raw_data.output_parsed.model_dump()
                elif hasattr(raw_data.output_parsed, "dict"):
                    return raw_data.output_parsed.dict()
                elif isinstance(raw_data.output_parsed, dict):
                    return raw_data.output_parsed

            if hasattr(raw_data, "model_dump"):
                return raw_data.model_dump()
            elif hasattr(raw_data, "dict"):
                return raw_data.dict()

            if isinstance(raw_data, dict):
                return raw_data

        if hasattr(result, "text") and result.text:
            logger.warning("Could not extract structured data, wrapping text in response dict")
            return {"response": result.text}

        return None
