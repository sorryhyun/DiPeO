"""Options and configuration building for Claude Code SDK.

Handles creation of tool configurations, hooks formatting, and SDK options.
"""

from typing import Any

from dipeo.diagram_generated.enums import ExecutionPhase

from .prompt_builder import build_system_prompt


def create_tool_options(
    execution_phase: ExecutionPhase | None = None,
    tools_enabled: bool = True,
) -> dict[str, Any]:
    """Create phase-specific tool configuration."""
    options = {}

    if not tools_enabled or not execution_phase:
        return options

    if execution_phase in [ExecutionPhase.MEMORY_SELECTION, ExecutionPhase.DECISION_EVALUATION]:
        from .tools import create_dipeo_mcp_server

        mcp_server = create_dipeo_mcp_server()

        options["mcp_servers"] = {"dipeo_structured_output": mcp_server}
        options["allowed_tools"] = [
            "mcp__dipeo_structured_output__select_memory_messages",
            "mcp__dipeo_structured_output__make_decision",
        ]

    return options


def format_hooks_config(hooks_config: dict[str, list[dict]] | None) -> dict[str, Any]:
    """Format hooks configuration for SDK."""
    if not hooks_config:
        return {}

    from claude_agent_sdk.types import HookMatcher

    hooks_dict = {}
    for event_type, matchers_list in hooks_config.items():
        event_matchers = []
        for matcher_config in matchers_list:
            hook_matcher = HookMatcher(
                matcher=matcher_config.get("matcher"), hooks=matcher_config.get("hooks", [])
            )
            event_matchers.append(hook_matcher)

        hooks_dict[event_type] = event_matchers

    return {"hooks": hooks_dict}


def build_claude_options(
    system_prompt: str | None,
    tool_options: dict,
    hooks_config: dict | None,
    stream: bool = False,
    subagent_definitions: dict[str, Any] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """Build options dictionary for ClaudeAgentOptions.

    Args:
        system_prompt: System prompt for the agent
        tool_options: MCP tool configuration
        hooks_config: Hook configuration for SDK events
        stream: Whether to enable streaming
        subagent_definitions: Dict mapping subagent names to AgentDefinition objects
        **kwargs: Additional options passed to SDK

    Returns:
        Options dictionary for ClaudeAgentOptions
    """
    options_dict = {"system_prompt": system_prompt, "model": "claude-sonnet-4-5-20250929"}

    if stream:
        options_dict["stream"] = True

    # Tool configuration
    allowed_tools = tool_options.get("allowed_tools", [])

    if "mcp_servers" in tool_options:
        options_dict["mcp_servers"] = tool_options["mcp_servers"]

    # Subagent configuration
    if subagent_definitions:
        options_dict["agents"] = subagent_definitions
        # Add Task and TaskOutput to allowed tools for subagent invocation
        if "Task" not in allowed_tools:
            allowed_tools = list(allowed_tools) + ["Task", "TaskOutput"]

    if allowed_tools:
        options_dict["allowed_tools"] = allowed_tools

    if hooks_config:
        hooks_dict = format_hooks_config(hooks_config)
        options_dict.update(hooks_dict)

    kwargs.pop("text_format", None)
    kwargs.pop("person_name", None)
    options_dict.update(kwargs)

    if "setting_sources" not in options_dict:
        options_dict["setting_sources"] = []

    return options_dict
