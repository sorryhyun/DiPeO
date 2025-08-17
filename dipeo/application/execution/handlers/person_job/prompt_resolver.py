"""Prompt file resolution utility for PersonJob handler."""

import os
import logging
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)


class PromptFileResolver:
    """Resolves prompt file paths and loads prompt content."""
    
    def __init__(self, filesystem_adapter: Any, diagram: Any = None):
        self.filesystem = filesystem_adapter
        self.diagram = diagram
        self._base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
        self._diagram_source_path = self._resolve_diagram_source_path()
    
    def _resolve_diagram_source_path(self) -> Optional[Path]:
        """Resolve the source path of the diagram for relative prompt paths."""
        source_path = None
        
        # Try to get from diagram metadata
        if self.diagram and hasattr(self.diagram, 'metadata') and self.diagram.metadata:
            # Use diagram_id which contains the file path
            source_path = self.diagram.metadata.get('diagram_id')
        
        if source_path:
            # Convert to absolute path if relative
            if not os.path.isabs(source_path):
                source_path = os.path.join(self._base_dir, source_path)
            
            if os.path.exists(source_path):
                return Path(source_path).parent
        return None
    
    def load_prompt_file(self, prompt_filename: str, node_label: str = None) -> Optional[str]:
        """Load prompt content from file.
        
        Args:
            prompt_filename: Name of the prompt file
            node_label: Optional node label for logging
            
        Returns:
            Prompt content as string, or None if file not found
        """
        if not self.filesystem:
            logger.error(f"[PromptResolver] No filesystem adapter available! Cannot load prompt file: {prompt_filename}")
            return None
        if not prompt_filename:
            logger.warning(f"[PromptResolver] No prompt filename provided")
            return None
        
        try:
            prompt_path = self._resolve_prompt_path(prompt_filename)
            
            if self.filesystem.exists(prompt_path):
                with self.filesystem.open(prompt_path, 'rb') as f:
                    return f.read().decode('utf-8')
            else:
                logger.warning(f"[PersonJob {node_label or 'unknown'}] Prompt file not found: {prompt_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading prompt file {prompt_filename}: {e}")
            return None
    
    def _resolve_prompt_path(self, prompt_filename: str) -> Path:
        """Resolve the full path to a prompt file.
        
        Tries in order:
        1. If path starts with 'projects/' or 'files/', treat as relative to base directory
        2. Relative to diagram directory (diagram_dir/prompts/filename)
        3. Global prompts directory (DIPEO_BASE_DIR/files/prompts/filename)
        """
        # Check if path is already relative to base directory
        if prompt_filename.startswith(('projects/', 'files/')):
            base_relative_path = Path(self._base_dir) / prompt_filename
            if self.filesystem.exists(base_relative_path):
                return base_relative_path
        
        if self._diagram_source_path:
            # Try relative to diagram directory
            local_path = self._diagram_source_path / 'prompts' / prompt_filename
            if self.filesystem.exists(local_path):
                return local_path
        
        # Fall back to global prompts directory
        return Path(self._base_dir) / 'files' / 'prompts' / prompt_filename