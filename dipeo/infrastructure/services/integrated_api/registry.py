"""Provider registry for managing API integrations at scale."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional
import importlib
import importlib.metadata
import yaml
import json

from dipeo.core.ports import ApiProviderPort
from dipeo.core import ServiceError

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Manages discovery, registration, and lifecycle of API providers.
    
    Supports:
    - Programmatic registration
    - Package entrypoint discovery
    - Manifest-based providers (YAML/JSON)
    """
    
    def __init__(self):
        self._providers: dict[str, ApiProviderPort] = {}
        self._provider_metadata: dict[str, dict[str, Any]] = {}
        self._initialization_lock = asyncio.Lock()
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the registry."""
        async with self._initialization_lock:
            if self._initialized:
                return
            logger.info("Initializing ProviderRegistry")
            self._initialized = True
    
    async def register(
        self, 
        name: str, 
        provider_instance: ApiProviderPort,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """Register a provider instance programmatically.
        
        Args:
            name: Provider name (e.g., 'slack', 'notion')
            provider_instance: Provider implementation
            metadata: Optional metadata (version, description, etc.)
        """
        if not self._initialized:
            await self.initialize()
            
        if name in self._providers:
            logger.warning(f"Provider '{name}' already registered, overwriting")
        
        # Initialize the provider if needed
        if hasattr(provider_instance, 'initialize'):
            await provider_instance.initialize()
        
        self._providers[name] = provider_instance
        self._provider_metadata[name] = metadata or {}
        
        logger.info(
            f"Registered provider '{name}' with operations: "
            f"{provider_instance.supported_operations}"
        )
    
    async def load_entrypoints(self, group: str = "dipeo.integrations") -> None:
        """Auto-discover and load providers from Python package entry points.
        
        Args:
            group: Entry point group name
        """
        logger.info(f"Loading providers from entry points: {group}")
        
        try:
            # Get all entry points in the group
            entry_points = importlib.metadata.entry_points()
            
            # Filter for our group (handles different Python versions)
            if hasattr(entry_points, 'select'):
                # Python 3.10+
                integration_eps = entry_points.select(group=group)
            else:
                # Python 3.9
                integration_eps = entry_points.get(group, [])
            
            for ep in integration_eps:
                try:
                    logger.debug(f"Loading entry point: {ep.name}")
                    
                    # Load the entry point
                    load_func = ep.load()
                    
                    # Call the loader function
                    if asyncio.iscoroutinefunction(load_func):
                        await load_func(self)
                    else:
                        load_func(self)
                        
                    logger.info(f"Successfully loaded provider from entry point: {ep.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to load entry point {ep.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading entry points: {e}")
    
    async def load_manifests(self, path_pattern: str) -> None:
        """Load manifest-based providers from filesystem.
        
        Args:
            path_pattern: Glob pattern for manifest files (e.g., './integrations/**/provider.yaml')
        """
        from .generic_provider import GenericHTTPProvider
        
        logger.info(f"Loading provider manifests from: {path_pattern}")
        
        # Handle both relative and absolute paths
        base_path = Path(path_pattern)
        if base_path.is_absolute():
            search_path = base_path
        else:
            # Make relative to current working directory
            search_path = Path.cwd() / base_path
        
        # Find all matching manifest files
        if '*' in str(search_path):
            # It's a glob pattern
            manifest_files = list(Path(search_path.parts[0]).glob('/'.join(search_path.parts[1:])))
        else:
            # Direct path
            manifest_files = [search_path] if search_path.exists() else []
        
        for manifest_file in manifest_files:
            try:
                await self._load_single_manifest(manifest_file)
            except Exception as e:
                logger.error(f"Failed to load manifest {manifest_file}: {e}")
    
    async def _load_single_manifest(self, manifest_path: Path) -> None:
        """Load a single provider manifest file.
        
        Args:
            manifest_path: Path to the manifest file
        """
        from .generic_provider import GenericHTTPProvider
        
        logger.debug(f"Loading manifest: {manifest_path}")
        
        # Load manifest content
        with open(manifest_path, 'r') as f:
            if manifest_path.suffix in ['.yaml', '.yml']:
                manifest = yaml.safe_load(f)
            elif manifest_path.suffix == '.json':
                manifest = json.load(f)
            else:
                raise ValueError(f"Unsupported manifest format: {manifest_path.suffix}")
        
        # Validate required fields
        if 'name' not in manifest:
            raise ValueError(f"Manifest missing required field 'name': {manifest_path}")
        
        # Create generic provider from manifest
        provider = GenericHTTPProvider(manifest, manifest_path.parent)
        
        # Register the provider
        await self.register(
            name=manifest['name'],
            provider_instance=provider,
            metadata={
                'version': manifest.get('version', '1.0.0'),
                'manifest_path': str(manifest_path),
                'type': 'manifest',
                **manifest.get('metadata', {})
            }
        )
        
        logger.info(f"Loaded manifest provider: {manifest['name']} from {manifest_path}")
    
    def get_provider(self, name: str) -> Optional[ApiProviderPort]:
        """Get a provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(name)
    
    def list_providers(self) -> list[str]:
        """List all registered provider names.
        
        Returns:
            List of provider names
        """
        return list(self._providers.keys())
    
    def get_all_providers(self) -> dict[str, ApiProviderPort]:
        """Get all registered providers.
        
        Returns:
            Dictionary of provider name to instance
        """
        return self._providers.copy()
    
    def get_provider_metadata(self, name: str) -> dict[str, Any]:
        """Get metadata for a provider.
        
        Args:
            name: Provider name
            
        Returns:
            Provider metadata or empty dict if not found
        """
        return self._provider_metadata.get(name, {})
    
    def get_provider_info(self, name: str) -> Optional[dict[str, Any]]:
        """Get detailed information about a provider.
        
        Args:
            name: Provider name
            
        Returns:
            Provider info including operations and metadata
        """
        provider = self._providers.get(name)
        if not provider:
            return None
        
        return {
            'name': name,
            'operations': provider.supported_operations,
            'metadata': self._provider_metadata.get(name, {}),
            'provider_type': provider.__class__.__name__
        }
    
    async def remove_provider(self, name: str) -> bool:
        """Remove a provider from the registry.
        
        Args:
            name: Provider name
            
        Returns:
            True if removed, False if not found
        """
        if name in self._providers:
            # Clean up provider if it has cleanup method
            provider = self._providers[name]
            if hasattr(provider, 'cleanup'):
                try:
                    await provider.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up provider {name}: {e}")
            
            del self._providers[name]
            self._provider_metadata.pop(name, None)
            logger.info(f"Removed provider: {name}")
            return True
        
        return False
    
    async def reload_provider(self, name: str) -> bool:
        """Reload a provider (useful for manifest-based providers).
        
        Args:
            name: Provider name
            
        Returns:
            True if reloaded, False if not found
        """
        metadata = self._provider_metadata.get(name)
        if not metadata or metadata.get('type') != 'manifest':
            logger.warning(f"Cannot reload provider {name}: not a manifest-based provider")
            return False
        
        manifest_path = metadata.get('manifest_path')
        if not manifest_path:
            logger.error(f"No manifest path found for provider {name}")
            return False
        
        # Remove the old provider
        await self.remove_provider(name)
        
        # Reload from manifest
        try:
            await self._load_single_manifest(Path(manifest_path))
            logger.info(f"Successfully reloaded provider: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to reload provider {name}: {e}")
            return False
    
    def get_statistics(self) -> dict[str, Any]:
        """Get registry statistics.
        
        Returns:
            Statistics about registered providers
        """
        total_operations = sum(
            len(p.supported_operations) 
            for p in self._providers.values()
        )
        
        provider_types = {}
        for metadata in self._provider_metadata.values():
            ptype = metadata.get('type', 'programmatic')
            provider_types[ptype] = provider_types.get(ptype, 0) + 1
        
        return {
            'total_providers': len(self._providers),
            'total_operations': total_operations,
            'provider_types': provider_types,
            'providers': [
                {
                    'name': name,
                    'operation_count': len(provider.supported_operations),
                    'type': self._provider_metadata.get(name, {}).get('type', 'programmatic')
                }
                for name, provider in self._providers.items()
            ]
        }