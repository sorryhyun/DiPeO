"""MCP tool registry with group-based organization."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from dipeo.config.base_logger import get_module_logger

from .base import ToolDefinition

logger = get_module_logger(__name__)


class ToolGroup(str, Enum):
    """Tool groups for MCP organization."""

    MEMORY = "memory"
    DECISION = "decision"
    SUBAGENT = "subagent"
    EXECUTION = "execution"


# Default groups that are always enabled unless explicitly disabled
DEFAULT_ENABLED_GROUPS = {ToolGroup.MEMORY, ToolGroup.DECISION}


@dataclass
class MCPServerConfig:
    """Configuration for MCP servers."""

    mcp_servers: dict[str, Any] = field(default_factory=dict)
    allowed_tool_names: list[str] = field(default_factory=list)
    enabled_groups: set[ToolGroup] = field(default_factory=set)
    config_hash: str = ""


class MCPRegistry:
    """Registry for MCP tools organized by groups.

    Manages tool definitions and creates MCP servers based on
    enabled groups for a given execution context.
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._tools_by_group: dict[ToolGroup, list[ToolDefinition]] = {
            group: [] for group in ToolGroup
        }
        self._config_cache: dict[str, MCPServerConfig] = {}

    def register(self, tool_def: ToolDefinition) -> None:
        """Register a tool definition.

        Args:
            tool_def: Tool definition to register
        """
        self._tools[tool_def.name] = tool_def
        try:
            group = ToolGroup(tool_def.group)
            self._tools_by_group[group].append(tool_def)
        except ValueError:
            logger.warning(f"Unknown tool group '{tool_def.group}' for tool '{tool_def.name}'")
            # Add to default group
            self._tools_by_group[ToolGroup.MEMORY].append(tool_def)

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_tools_by_group(self, group: ToolGroup) -> list[ToolDefinition]:
        """Get all tools in a group."""
        return self._tools_by_group.get(group, [])

    def build_mcp_config(
        self,
        enabled_groups: set[ToolGroup] | None = None,
        extra_tools: list[str] | None = None,
    ) -> MCPServerConfig:
        """Build MCP server configuration for enabled groups.

        Args:
            enabled_groups: Set of tool groups to enable (defaults to DEFAULT_ENABLED_GROUPS)
            extra_tools: Additional tool names to allow (e.g., "Task", "TaskOutput")

        Returns:
            MCPServerConfig with servers and allowed tools
        """
        groups = enabled_groups or DEFAULT_ENABLED_GROUPS

        # Compute config hash for caching
        config_hash = self._compute_hash(groups, extra_tools)
        if config_hash in self._config_cache:
            return self._config_cache[config_hash]

        # Collect enabled tools
        enabled_tools: list[ToolDefinition] = []
        for group in groups:
            enabled_tools.extend(self._tools_by_group.get(group, []))

        # Filter to only enabled tools
        enabled_tools = [t for t in enabled_tools if t.enabled]

        # Create MCP server with tools
        mcp_servers = {}
        allowed_tool_names = []

        if enabled_tools:
            # Convert ToolDefinitions to SDK tool functions
            sdk_tools = []
            for tool_def in enabled_tools:
                sdk_tool = self._create_sdk_tool(tool_def)
                sdk_tools.append(sdk_tool)
                allowed_tool_names.append(f"mcp__dipeo_structured_output__{tool_def.name}")

            mcp_servers["dipeo_structured_output"] = create_sdk_mcp_server(
                name="dipeo_structured_output",
                version="1.0.0",
                tools=sdk_tools,
            )

        # Add extra tools
        if extra_tools:
            allowed_tool_names.extend(extra_tools)

        config = MCPServerConfig(
            mcp_servers=mcp_servers,
            allowed_tool_names=allowed_tool_names,
            enabled_groups=groups,
            config_hash=config_hash,
        )

        self._config_cache[config_hash] = config
        return config

    def _create_sdk_tool(self, tool_def: ToolDefinition):
        """Create an SDK tool function from a ToolDefinition."""
        name, description, schema = tool_def.to_sdk_tool_args()

        @tool(name, description, schema)
        async def tool_handler(args: dict[str, Any]) -> dict[str, Any]:
            return await tool_def.execute(args)

        return tool_handler

    def _compute_hash(
        self,
        groups: set[ToolGroup],
        extra_tools: list[str] | None,
    ) -> str:
        """Compute hash for caching."""
        group_str = ",".join(sorted(g.value for g in groups))
        extra_str = ",".join(sorted(extra_tools or []))
        return f"{group_str}|{extra_str}"

    def invalidate_cache(self, config_hash: str | None = None) -> int:
        """Invalidate cached configurations.

        Args:
            config_hash: Specific hash to invalidate, or None to clear all

        Returns:
            Number of entries invalidated
        """
        if config_hash:
            if config_hash in self._config_cache:
                del self._config_cache[config_hash]
                return 1
            return 0

        count = len(self._config_cache)
        self._config_cache.clear()
        return count


# Global registry instance
_registry: MCPRegistry | None = None


def get_registry() -> MCPRegistry:
    """Get or create the global MCP registry."""
    global _registry
    if _registry is None:
        _registry = MCPRegistry()
        _register_default_tools(_registry)
    return _registry


def _register_default_tools(registry: MCPRegistry) -> None:
    """Register default DiPeO tools."""
    from .input_models import DecisionInput, MemorySelectionInput

    # Memory selection tool
    async def select_memory_handler(args: dict[str, Any]) -> dict[str, Any]:
        message_ids = args.get("message_ids", [])
        return {
            "content": [{"type": "text", "text": f"Selected {len(message_ids)} messages"}],
            "data": {"message_ids": message_ids},
        }

    registry.register(ToolDefinition(
        name="select_memory_messages",
        description="Select relevant messages from memory for context",
        input_model=MemorySelectionInput,
        handler=select_memory_handler,
        group=ToolGroup.MEMORY.value,
    ))

    # Decision tool
    async def make_decision_handler(args: dict[str, Any]) -> dict[str, Any]:
        decision = args.get("decision", False)
        return {
            "content": [{"type": "text", "text": "YES" if decision else "NO"}],
            "data": {"decision": decision},
        }

    registry.register(ToolDefinition(
        name="make_decision",
        description="Make a binary YES/NO decision based on evaluation criteria",
        input_model=DecisionInput,
        handler=make_decision_handler,
        group=ToolGroup.DECISION.value,
    ))
