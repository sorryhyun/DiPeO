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
            source_path = self.diagram.metadata.get('source_path')
            if not source_path:
                source_path = self.diagram.metadata.get('file_path')
        
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
        if not self.filesystem or not prompt_filename:
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
        1. Relative to diagram directory (diagram_dir/prompts/filename)
        2. Global prompts directory (DIPEO_BASE_DIR/files/prompts/filename)
        """
        if self._diagram_source_path:
            # First try relative to diagram directory
            local_path = self._diagram_source_path / 'prompts' / prompt_filename
            if self.filesystem.exists(local_path):
                return local_path
        
        # Fall back to global prompts directory
        return Path(self._base_dir) / 'files' / 'prompts' / prompt_filename