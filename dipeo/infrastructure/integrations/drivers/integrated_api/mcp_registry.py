"""MCP Tool Registry for managing and discovering MCP tools."""

import asyncio
import importlib
import importlib.metadata
import json
import logging

from dipeo.config.base_logger import get_module_logger
from collections.abc import Callable
from pathlib import Path

import yaml

from dipeo.infrastructure.integrations.drivers.integrated_api.providers.mcp_provider import (
    MCPProvider,
    MCPTool,
)

logger = get_module_logger(__name__)

class MCPToolRegistry:
    """Registry for discovering, validating, and managing MCP tools.

    This registry supports:
    - Loading tools from manifest files (YAML/JSON)
    - Auto-discovery of tools from Python packages
    - Dynamic tool registration
    - Tool validation and metadata management
    """

    def __init__(self):
        self._tools: dict[str, MCPTool] = {}
        self._providers: dict[str, MCPProvider] = {}
        self._tool_metadata: dict[str, dict] = {}
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the MCP tool registry."""
        async with self._lock:
            if self._initialized:
                return

            logger.info("Initializing MCP Tool Registry")

            # Load built-in tools
            await self._load_builtin_tools()

            # Load tools from manifests
            await self._discover_manifest_tools()

            # Load tools from entry points
            await self._discover_entrypoint_tools()

            self._initialized = True
            logger.info(f"MCP Tool Registry initialized with {len(self._tools)} tools")

    async def _load_builtin_tools(self) -> None:
        """Load built-in MCP tools."""
        # Define built-in tools that are always available
        builtin_tools = [
            MCPTool(
                name="mcp_echo",
                description="Echo back the input (for testing)",
                parameters={"message": {"type": "string", "required": True}},
            ),
            MCPTool(
                name="mcp_delay",
                description="Wait for specified seconds",
                parameters={"seconds": {"type": "number", "required": True}},
            ),
        ]

        for tool in builtin_tools:
            self.register_tool(tool)

    def register_tool(self, tool: MCPTool, metadata: dict | None = None) -> None:
        """Register an MCP tool.

        Args:
            tool: The MCPTool instance to register
            metadata: Optional metadata about the tool
        """
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered, overwriting")

        self._tools[tool.name] = tool
        self._tool_metadata[tool.name] = metadata or {}
        logger.debug(f"Registered MCP tool: {tool.name}")

    def get_tool(self, tool_name: str) -> MCPTool | None:
        """Get a tool by name."""
        return self._tools.get(tool_name)

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def get_tool_info(self, tool_name: str) -> dict | None:
        """Get detailed information about a tool."""
        tool = self._tools.get(tool_name)
        if not tool:
            return None

        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "metadata": self._tool_metadata.get(tool_name, {}),
        }

    async def _discover_manifest_tools(self) -> None:
        """Discover MCP tools from manifest files."""
        # Look for MCP tool manifests in standard locations
        manifest_patterns = [
            "integrations/mcp/*.yaml",
            "integrations/mcp/*.yml",
            "integrations/mcp/*.json",
            "integrations/mcp/tools/*.yaml",
            "integrations/mcp/tools/*.yml",
            "integrations/mcp/tools/*.json",
        ]

        for pattern in manifest_patterns:
            try:
                manifest_files = list(Path.cwd().glob(pattern))
                for manifest_file in manifest_files:
                    await self._load_tool_manifest(manifest_file)
            except Exception as e:
                logger.debug(f"Error discovering tools from {pattern}: {e}")

    async def _load_tool_manifest(self, manifest_path: Path) -> None:
        """Load MCP tools from a manifest file.

        Args:
            manifest_path: Path to the manifest file
        """
        try:
            logger.debug(f"Loading MCP tool manifest: {manifest_path}")

            # Read manifest file
            content = manifest_path.read_text()

            # Parse based on extension
            if manifest_path.suffix in [".yaml", ".yml"]:
                manifest = yaml.safe_load(content)
            elif manifest_path.suffix == ".json":
                manifest = json.loads(content)
            else:
                logger.warning(f"Unknown manifest format: {manifest_path}")
                return

            # Load tools from manifest
            await self._load_tools_from_manifest(manifest, manifest_path)

        except Exception as e:
            logger.error(f"Failed to load manifest {manifest_path}: {e}")

    async def _load_tools_from_manifest(self, manifest: dict, source_path: Path) -> None:
        """Load tools from a parsed manifest.

        Args:
            manifest: Parsed manifest dictionary
            source_path: Path to the source manifest file
        """
        # Check if this is an MCP tool manifest
        if manifest.get("type") != "mcp":
            logger.debug(f"Skipping non-MCP manifest: {source_path}")
            return

        provider_name = manifest.get("name", "mcp")

        # Create or get provider
        if provider_name not in self._providers:
            provider = MCPProvider(provider_name=provider_name, manifest=manifest)
            self._providers[provider_name] = provider
            await provider.initialize()
        else:
            provider = self._providers[provider_name]

        # Load tools/operations from manifest
        tools_section = manifest.get("tools") or manifest.get("operations", {})

        for tool_name, tool_spec in tools_section.items():
            tool = MCPTool(
                name=tool_name,
                description=tool_spec.get("description", ""),
                parameters=tool_spec.get("parameters", {}),
                handler=None,  # Handler will be set based on tool type
            )

            # Set handler based on tool type or category
            tool_type = tool_spec.get("type", "generic")
            tool.handler = self._get_handler_for_type(tool_type)

            # Register the tool
            self.register_tool(
                tool,
                metadata={"source": str(source_path), "provider": provider_name, "type": tool_type},
            )

            # Also register with provider
            provider.register_tool(tool)

        logger.info(f"Loaded {len(tools_section)} tools from {source_path}")

    def _get_handler_for_type(self, tool_type: str) -> Callable | None:
        """Get the appropriate handler for a tool type.

        Args:
            tool_type: The type of tool (browser, filesystem, etc.)

        Returns:
            Handler function or None
        """
        # This would map tool types to actual handler implementations
        # For now, return None and let the provider handle it
        return None

    async def _discover_entrypoint_tools(self) -> None:
        """Discover MCP tools from Python package entry points."""
        try:
            # Look for entry points in the 'dipeo.mcp_tools' group
            entry_points = importlib.metadata.entry_points()

            # Handle different Python versions
            if hasattr(entry_points, "select"):
                # Python 3.10+
                mcp_eps = entry_points.select(group="dipeo.mcp_tools")
            else:
                # Python 3.9
                mcp_eps = entry_points.get("dipeo.mcp_tools", [])

            for ep in mcp_eps:
                try:
                    logger.debug(f"Loading MCP tool entry point: {ep.name}")

                    # Load the entry point
                    load_func = ep.load()

                    # Call the loader function to get tools
                    if asyncio.iscoroutinefunction(load_func):
                        tools = await load_func()
                    else:
                        tools = load_func()

                    # Register the tools
                    if isinstance(tools, list):
                        for tool in tools:
                            if isinstance(tool, MCPTool):
                                self.register_tool(
                                    tool, metadata={"source": f"entry_point:{ep.name}"}
                                )
                    elif isinstance(tools, MCPTool):
                        self.register_tool(tools, metadata={"source": f"entry_point:{ep.name}"})

                except Exception as e:
                    logger.error(f"Failed to load MCP tool entry point {ep.name}: {e}")

        except Exception as e:
            logger.debug(f"Error discovering MCP tools from entry points: {e}")

    def create_provider(self, provider_name: str = "mcp") -> MCPProvider:
        """Create an MCP provider with all registered tools.

        Args:
            provider_name: Name for the provider instance

        Returns:
            MCPProvider instance with all registered tools
        """
        if provider_name in self._providers:
            return self._providers[provider_name]

        # Create new provider with all tools
        provider = MCPProvider(provider_name=provider_name, tools=list(self._tools.values()))

        self._providers[provider_name] = provider
        return provider

    async def load_manifest_file(self, manifest_path: str) -> None:
        """Load a specific MCP tool manifest file.

        Args:
            manifest_path: Path to the manifest file
        """
        path = Path(manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

        await self._load_tool_manifest(path)

    def validate_tool_params(self, tool_name: str, params: dict) -> bool:
        """Validate parameters for a specific tool.

        Args:
            tool_name: Name of the tool
            params: Parameters to validate

        Returns:
            True if valid, raises ValueError if not
        """
        tool = self._tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        return tool.validate_params(params)

    def get_tools_by_category(self, category: str) -> list[MCPTool]:
        """Get all tools in a specific category.

        Args:
            category: Tool category (browser, filesystem, etc.)

        Returns:
            List of tools in that category
        """
        tools = []
        for tool_name, tool in self._tools.items():
            metadata = self._tool_metadata.get(tool_name, {})
            if metadata.get("type") == category or metadata.get("category") == category:
                tools.append(tool)
        return tools

    def export_manifest(self, provider_name: str = "mcp") -> dict:
        """Export all registered tools as a manifest.

        Args:
            provider_name: Name for the exported provider

        Returns:
            Manifest dictionary
        """
        manifest = {
            "name": provider_name,
            "type": "mcp",
            "version": "1.0.0",
            "description": "MCP Tool Provider",
            "tools": {},
        }

        for tool_name, tool in self._tools.items():
            manifest["tools"][tool_name] = {
                "description": tool.description,
                "parameters": tool.parameters,
                "metadata": self._tool_metadata.get(tool_name, {}),
            }

        return manifest

# Global registry instance
_mcp_registry: MCPToolRegistry | None = None

async def get_mcp_registry() -> MCPToolRegistry:
    """Get the global MCP tool registry instance.

    Returns:
        The initialized MCP tool registry
    """
    global _mcp_registry

    if _mcp_registry is None:
        _mcp_registry = MCPToolRegistry()
        await _mcp_registry.initialize()

    return _mcp_registry
