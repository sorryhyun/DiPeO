"""Build ClaudeAgentOptions and tool configurations."""

import os
from pathlib import Path
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.config.paths import BASE_DIR
from dipeo.infrastructure.llm.drivers.types import ExecutionPhase

from ..claude_code.prompt_builder import (
    DIRECT_EXECUTION_PROMPT,
    LLM_DECISION_PROMPT,
    MEMORY_SELECTION_PROMPT,
)

logger = get_module_logger(__name__)


class OptionsBuilder:
    """Build options for Claude Code Custom client."""

    @staticmethod
    def get_system_prompt(
        execution_phase: ExecutionPhase | None = None, use_tools: bool = False, **kwargs
    ) -> str | None:
        """Get system prompt based on execution phase.

        CUSTOM BEHAVIOR: This method completely overrides the system prompt
        rather than appending to it. If a system_prompt is provided in messages,
        it takes precedence over all phase-specific prompts.
        """
        system_message = kwargs.get("system_message", "")
        if system_message:
            logger.debug("[ClaudeCodeCustom] Using custom system prompt (overriding defaults)")
            return system_message

        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            person_name = kwargs.get("person_name")
            if person_name:
                base_prompt = MEMORY_SELECTION_PROMPT.format(assistant_name=person_name)
            else:
                base_prompt = MEMORY_SELECTION_PROMPT.replace("{assistant_name}", "Assistant")
            if use_tools:
                base_prompt += "\n\nIMPORTANT: Use the select_memory_messages tool to return your selection. Pass the list of message IDs as the message_ids parameter."
            return base_prompt
        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            base_prompt = LLM_DECISION_PROMPT
            if use_tools:
                base_prompt += "\n\nIMPORTANT: Use the make_decision tool to return your decision. Pass true for YES or false for NO as the decision parameter."
            return base_prompt
        elif execution_phase == ExecutionPhase.DIRECT_EXECUTION:
            return DIRECT_EXECUTION_PROMPT
        return None

    @staticmethod
    def setup_workspace(kwargs: dict) -> None:
        """Set up workspace directory for claude-code if not already configured.

        Modifies kwargs in-place to add 'cwd' if not present.
        """
        if "cwd" not in kwargs:
            trace_id = kwargs.pop("trace_id", "default")
            root = os.getenv("DIPEO_CLAUDE_WORKSPACES", str(BASE_DIR / ".dipeo" / "workspaces"))
            workspace_dir = Path(root) / f"exec_{trace_id}"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            kwargs["cwd"] = str(workspace_dir)
        else:
            kwargs.pop("trace_id", None)

    @staticmethod
    def create_tool_options(
        execution_phase: ExecutionPhase | None = None, use_tools: bool = False
    ) -> dict[str, Any]:
        """Create MCP server configuration for tools based on execution phase."""
        if not use_tools:
            return {}

        from dipeo.infrastructure.mcp import dipeo_structured_output_server

        if execution_phase == ExecutionPhase.MEMORY_SELECTION:
            allowed_tools = ["mcp__dipeo_structured_output__select_memory_messages"]
        elif execution_phase == ExecutionPhase.DECISION_EVALUATION:
            allowed_tools = ["mcp__dipeo_structured_output__make_decision"]
        else:
            allowed_tools = ["mcp__dipeo_structured_output__*"]

        tool_options = {
            "mcp_servers": {
                "dipeo_structured_output": {
                    "module": dipeo_structured_output_server,
                    "args": {
                        "output_type": execution_phase.value if execution_phase else "default"
                    },
                }
            },
            "allowed_tools": allowed_tools,
        }

        logger.debug(
            f"[ClaudeCodeCustom] Created MCP server configuration for phase {execution_phase}, "
            f"allowed tools: {allowed_tools}"
        )
        return tool_options

    @staticmethod
    def build_claude_options(
        system_prompt, tool_options, hooks_config, stream=False, **kwargs
    ) -> dict[str, Any]:
        """Build options dictionary for ClaudeAgentOptions."""
        options_dict = {"system_prompt": system_prompt, **tool_options, "stream": stream}
        if "cwd" in kwargs:
            options_dict["cwd"] = kwargs["cwd"]
        if hooks_config:
            options_dict["hooks"] = hooks_config
        return options_dict
