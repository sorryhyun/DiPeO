"""System prompt handling for LLM services."""

import os
from pathlib import Path
from typing import Optional
import logging

from dipeo.diagram_generated import PersonLLMConfig, LLMService

logger = logging.getLogger(__name__)


class SystemPromptHandler:
    """Handles system prompt resolution and loading for LLM services.
    
    This class is responsible for:
    - Loading prompt content from files or inline configuration
    - Resolving prompt file paths relative to DIPEO_BASE_DIR
    - Providing fallback mechanisms for prompt resolution
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the system prompt handler.
        
        Args:
            base_dir: Base directory for resolving relative paths.
                     Falls back to DIPEO_BASE_DIR env var or cwd.
        """
        self.base_dir = base_dir or os.environ.get('DIPEO_BASE_DIR', os.getcwd())
    
    def get_system_prompt(self, llm_config: PersonLLMConfig) -> Optional[str]:
        """Get the system prompt content from LLM configuration.
        
        This method follows a priority order:
        1. If prompt_file is specified and exists, read from file
        2. If prompt_file fails to read, fall back to system_prompt
        3. If no prompt_file, use system_prompt directly
        
        Args:
            llm_config: The LLM configuration containing prompt settings
            
        Returns:
            The system prompt content, or None if no prompt is configured
        """
        # First check if prompt_file is specified
        if llm_config.prompt_file:
            prompt_content = self._load_prompt_from_file(llm_config.prompt_file)
            if prompt_content is not None:
                return prompt_content
            # Fall back to system_prompt if file loading fails
            logger.warning(
                f"Failed to load prompt file {llm_config.prompt_file}, "
                f"falling back to system_prompt"
            )
        
        # Use system_prompt if available
        return llm_config.system_prompt
    
    def _load_prompt_from_file(self, prompt_file: str) -> Optional[str]:
        """Load prompt content from a file.
        
        Args:
            prompt_file: Path to the prompt file (can be relative or absolute)
            
        Returns:
            The file content, or None if file cannot be read
        """
        # Resolve path relative to base_dir if not absolute
        prompt_path = Path(prompt_file)
        if not prompt_path.is_absolute():
            prompt_path = Path(self.base_dir) / prompt_path
        
        # Read prompt from file if it exists
        if prompt_path.exists():
            try:
                return prompt_path.read_text(encoding='utf-8')
            except Exception as e:
                logger.error(f"Error reading prompt file {prompt_path}: {e}")
                return None
        else:
            logger.warning(f"Prompt file {prompt_path} not found")
            return None
    
    def get_system_role(self, service: LLMService) -> str:
        """Get the appropriate system role name for the LLM service.
        
        Different LLM providers use different role names for system messages:
        - OpenAI uses "developer" for stronger system instructions
        - Most others use "system"
        
        Args:
            service: The LLM service type
            
        Returns:
            The role name to use for system messages
        """
        # OpenAI recommends using "developer" role for stronger adherence
        if service == LLMService.OPENAI:
            return "developer"
        else:
            return "system"