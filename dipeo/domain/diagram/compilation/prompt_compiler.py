"""Compile-time prompt file resolution for diagrams.

This module handles resolving prompt file references to their actual content
during diagram compilation, eliminating runtime filesystem I/O.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

from dipeo.diagram_generated import DomainNode, NodeID, NodeType

logger = logging.getLogger(__name__)


class PromptFileCompiler:
    """Resolves prompt file references to actual content during compilation.
    
    This is a pure domain component that resolves prompt files at compile time,
    embedding the content directly into the node data. This eliminates runtime
    filesystem operations and infrastructure dependencies.
    """
    
    def __init__(self, base_dir: Optional[str] = None, filesystem_reader: Optional[Any] = None):
        """Initialize the prompt compiler.
        
        Args:
            base_dir: Base directory for resolving relative paths
            filesystem_reader: Optional filesystem reader for testing
        """
        self._base_dir = base_dir or os.getenv('DIPEO_BASE_DIR', os.getcwd())
        self._filesystem_reader = filesystem_reader or self._default_file_reader
        self._resolved_cache: dict[str, str] = {}
    
    def _default_file_reader(self, path: Path) -> str:
        """Default file reader using standard library."""
        try:
            return path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise
    
    def resolve_prompt_files(self, nodes: list[dict[str, Any]], diagram_path: Optional[str] = None) -> list[dict[str, Any]]:
        """Resolve all prompt file references in a list of nodes.
        
        Args:
            nodes: List of node dictionaries
            diagram_path: Path to the diagram file for relative resolution
            
        Returns:
            Updated nodes with resolved prompt content
        """
        diagram_dir = None
        if diagram_path:
            if not os.path.isabs(diagram_path):
                diagram_path = os.path.join(self._base_dir, diagram_path)
            if os.path.exists(diagram_path):
                diagram_dir = Path(diagram_path).parent
        
        for node in nodes:
            # Only process PersonJob nodes
            node_type = node.get('type', '')
            if node_type not in ['person_job', 'PersonJob', NodeType.PERSON_JOB]:
                continue
            
            # Get node data
            data = node.get('data', {})
            
            # Resolve prompt_file if present
            if 'prompt_file' in data and data['prompt_file']:
                resolved_content = self._resolve_single_prompt(
                    data['prompt_file'], 
                    diagram_dir,
                    node.get('label', node.get('id', 'unknown'))
                )
                if resolved_content:
                    # Store resolved content in a special field
                    data['resolved_prompt'] = resolved_content
                    # Log that we resolved the prompt
                    logger.debug(f"[PromptCompiler] Set resolved_prompt for node {node.get('id')}")
            
            # Resolve first_prompt_file if present
            if 'first_prompt_file' in data and data['first_prompt_file']:
                resolved_content = self._resolve_single_prompt(
                    data['first_prompt_file'],
                    diagram_dir,
                    node.get('label', node.get('id', 'unknown'))
                )
                if resolved_content:
                    # Store resolved content in a special field
                    data['resolved_first_prompt'] = resolved_content
                    # Log that we resolved the prompt
                    logger.debug(f"[PromptCompiler] Set resolved_first_prompt for node {node.get('id')}")
        
        return nodes
    
    def _resolve_single_prompt(self, prompt_filename: str, diagram_dir: Optional[Path], node_label: str) -> Optional[str]:
        """Resolve a single prompt file to its content.
        
        Args:
            prompt_filename: Name or path of the prompt file
            diagram_dir: Directory of the diagram for relative resolution
            node_label: Label of the node for logging
            
        Returns:
            Content of the prompt file, or None if not found
        """
        # Check cache first
        cache_key = f"{diagram_dir}:{prompt_filename}" if diagram_dir else prompt_filename
        if cache_key in self._resolved_cache:
            logger.debug(f"[PromptCompiler] Using cached prompt for {node_label}: {prompt_filename}")
            return self._resolved_cache[cache_key]
        
        # Try to resolve the path
        prompt_path = self._resolve_prompt_path(prompt_filename, diagram_dir)
        
        if prompt_path and prompt_path.exists():
            try:
                content = self._filesystem_reader(prompt_path)
                # Cache the result
                self._resolved_cache[cache_key] = content
                logger.info(f"[PromptCompiler] Resolved prompt file for {node_label}: {prompt_filename}")
                return content
            except Exception as e:
                logger.error(f"[PromptCompiler] Error reading prompt file {prompt_path} for {node_label}: {e}")
                return None
        else:
            logger.warning(f"[PromptCompiler] Prompt file not found for {node_label}: {prompt_filename}")
            return None
    
    def _resolve_prompt_path(self, prompt_filename: str, diagram_dir: Optional[Path]) -> Optional[Path]:
        """Resolve the full path to a prompt file.
        
        Resolution order:
        1. If path starts with 'projects/' or 'files/', treat as relative to base directory
        2. Relative to diagram directory (diagram_dir/prompts/filename)
        3. Global prompts directory (DIPEO_BASE_DIR/files/prompts/filename)
        """
        base_path = Path(self._base_dir)
        
        # Check if path is already relative to base directory
        if prompt_filename.startswith(('projects/', 'files/')):
            full_path = base_path / prompt_filename
            if full_path.exists():
                return full_path
        
        # Try relative to diagram directory
        if diagram_dir:
            local_path = diagram_dir / 'prompts' / prompt_filename
            if local_path.exists():
                return local_path
        
        # Fall back to global prompts directory
        global_path = base_path / 'files' / 'prompts' / prompt_filename
        if global_path.exists():
            return global_path
        
        # Try as absolute path
        abs_path = Path(prompt_filename)
        if abs_path.is_absolute() and abs_path.exists():
            return abs_path
        
        return None
    
    def compile_domain_nodes(self, domain_nodes: list[DomainNode], diagram_path: Optional[str] = None) -> list[DomainNode]:
        """Resolve prompt files in DomainNode objects.
        
        Args:
            domain_nodes: List of DomainNode objects
            diagram_path: Path to the diagram file
            
        Returns:
            Updated DomainNode objects with resolved prompts
        """
        diagram_dir = None
        if diagram_path:
            if not os.path.isabs(diagram_path):
                diagram_path = os.path.join(self._base_dir, diagram_path)
            if os.path.exists(diagram_path):
                diagram_dir = Path(diagram_path).parent
        
        for node in domain_nodes:
            # Only process PersonJob nodes
            if node.type != NodeType.PERSON_JOB:
                continue
            
            # Access data dictionary
            if not node.data:
                continue
            
            # Resolve prompt_file if present
            if node.data.get('prompt_file'):
                resolved_content = self._resolve_single_prompt(
                    node.data['prompt_file'],
                    diagram_dir,
                    node.data.get('label', str(node.id))
                )
                if resolved_content:
                    node.data['resolved_prompt'] = resolved_content

            # Resolve first_prompt_file if present
            if node.data.get('first_prompt_file'):
                resolved_content = self._resolve_single_prompt(
                    node.data['first_prompt_file'],
                    diagram_dir,
                    node.data.get('label', str(node.id))
                )
                if resolved_content:
                    node.data['resolved_first_prompt'] = resolved_content

        return domain_nodes