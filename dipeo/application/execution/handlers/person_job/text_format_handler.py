"""Text format handling for structured output in PersonJob nodes."""

import os
import logging
from typing import Optional, Any, Type
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TextFormatHandler:
    """Handles text format configuration for structured outputs."""
    
    def __init__(self):
        self._base_dir = os.environ.get('DIPEO_BASE_DIR', os.getcwd())
    
    def get_pydantic_model(self, node: Any) -> Optional[Type[BaseModel]]:
        """Get Pydantic model from node's text_format configuration.
        
        Args:
            node: PersonJobNode with potential text_format or text_format_file
            
        Returns:
            Compiled Pydantic BaseModel class or None
        """
        text_format_content = self._load_text_format_content(node)
        
        if not text_format_content:
            return None
        
        return self._compile_pydantic_model(text_format_content)
    
    def _load_text_format_content(self, node: Any) -> Optional[str]:
        """Load text format content from file or inline configuration.
        
        Args:
            node: PersonJobNode with text_format configuration
            
        Returns:
            Text format content as string
        """
        # First check for text_format_file (external file takes precedence)
        if hasattr(node, 'text_format_file') and node.text_format_file:
            content = self._load_from_file(node.text_format_file)
            if content:
                return content
            
        # Fall back to inline text_format
        if hasattr(node, 'text_format') and node.text_format:
            return node.text_format
        
        return None
    
    def _load_from_file(self, file_path: str) -> Optional[str]:
        """Load Pydantic models from external file.
        
        Args:
            file_path: Path to the text format file
            
        Returns:
            File content as string or None if failed
        """
        # Handle relative paths from project root
        if not os.path.isabs(file_path):
            file_path = os.path.join(self._base_dir, file_path)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read text_format_file {file_path}: {e}")
        else:
            logger.warning(f"text_format_file not found: {file_path}")
        
        return None
    
    def _compile_pydantic_model(self, content: str) -> Optional[Type[BaseModel]]:
        """Compile Python code string into a Pydantic BaseModel class.
        
        Args:
            content: Python code defining Pydantic models
            
        Returns:
            Compiled Pydantic BaseModel class or None if compilation fails
        """
        from dipeo.application.utils.pydantic_compiler import (
            compile_pydantic_model, 
            is_pydantic_code
        )
        
        # Check if it's Python code that defines Pydantic models
        if isinstance(content, str) and is_pydantic_code(content):
            pydantic_model = compile_pydantic_model(content)
            if pydantic_model:
                return pydantic_model
            else:
                logger.warning("Failed to compile Pydantic model from text_format")
        else:
            # If it's not Python code, log a warning
            logger.warning("text_format must be Python code defining Pydantic models")
        
        return None
    
    def process_structured_output(self, result: Any, has_text_format: bool) -> Optional[dict]:
        """Process LLM result for structured output.
        
        Args:
            result: LLM completion result
            has_text_format: Whether node has text_format configuration
            
        Returns:
            Structured data as dict or None if not applicable
        """
        if not has_text_format:
            return None
        
        # First try to parse from the text field if it contains JSON
        # This is because the OpenAI adapter converts Pydantic models to JSON strings
        if hasattr(result, 'text') and result.text:
            import json
            try:
                # Try to parse the text as JSON first
                parsed = json.loads(result.text)
                if isinstance(parsed, dict):
                    logger.debug(f"Successfully parsed structured output from text field")
                    return parsed
            except (json.JSONDecodeError, TypeError):
                # Not valid JSON, continue to other methods
                pass
        
        # Check raw_response for parsed output
        if hasattr(result, 'raw_response') and result.raw_response:
            raw_data = result.raw_response
            
            # Check if raw_response has parsed or output_parsed attributes (OpenAI response)
            if hasattr(raw_data, 'parsed') and raw_data.parsed:
                # This is a parsed Pydantic model from OpenAI
                if hasattr(raw_data.parsed, 'model_dump'):
                    return raw_data.parsed.model_dump()
                elif hasattr(raw_data.parsed, 'dict'):
                    return raw_data.parsed.dict()
                elif isinstance(raw_data.parsed, dict):
                    return raw_data.parsed
                    
            if hasattr(raw_data, 'output_parsed') and raw_data.output_parsed:
                # Alternative attribute name for parsed output
                if hasattr(raw_data.output_parsed, 'model_dump'):
                    return raw_data.output_parsed.model_dump()
                elif hasattr(raw_data.output_parsed, 'dict'):
                    return raw_data.output_parsed.dict()
                elif isinstance(raw_data.output_parsed, dict):
                    return raw_data.output_parsed
            
            # Check if raw_data itself is a Pydantic model
            if hasattr(raw_data, 'model_dump'):
                return raw_data.model_dump()
            elif hasattr(raw_data, 'dict'):
                return raw_data.dict()
            
            # If raw_data is already a dict
            if isinstance(raw_data, dict):
                return raw_data
        
        # Fall back to wrapping text in dict if nothing else worked
        if hasattr(result, 'text') and result.text:
            logger.warning("Could not extract structured data, wrapping text in response dict")
            return {"response": result.text}
        
        return None