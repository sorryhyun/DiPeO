"""AgentDefinition builder for Claude Agent SDK subagents."""

from pathlib import Path
from typing import Any

from claude_agent_sdk import AgentDefinition

from dipeo.config.base_logger import get_module_logger

from .config import SubagentConfig
from .loader import SubagentLoader

logger = get_module_logger(__name__)


def build_subagent_definition(
    config: SubagentConfig,
    agents_dir: Path | None = None,
    base_path: str | None = None,
) -> AgentDefinition | None:
    """Build an AgentDefinition from SubagentConfig.

    Args:
        config: Subagent configuration
        agents_dir: Directory containing agent filesystem configs
        base_path: Base path for resolving relative file paths

    Returns:
        AgentDefinition for use with Claude Agent SDK, or None if invalid
    """
    # Get system prompt
    prompt = config.get_effective_prompt(base_path)

    # If no inline prompt, try filesystem loader
    if not prompt and agents_dir:
        loader = SubagentLoader(agents_dir)
        loaded_config = loader.load_subagent_config(config.name)
        prompt = loaded_config.prompt

    if not prompt:
        logger.warning(f"No prompt found for subagent '{config.name}'")
        prompt = f"You are {config.name}, a specialized subagent. {config.description}"

    # Build AgentDefinition
    try:
        definition = AgentDefinition(
            description=config.description,
            prompt=prompt,
            tools=config.tools if config.tools else None,
            model=config.model if config.model != "inherit" else None,
        )
        return definition
    except Exception as e:
        logger.error(f"Failed to create AgentDefinition for '{config.name}': {e}")
        return None


def build_subagent_definitions(
    subagent_configs: dict[str, SubagentConfig | dict[str, Any]],
    agents_dir: Path | None = None,
    base_path: str | None = None,
) -> dict[str, AgentDefinition]:
    """Build multiple AgentDefinitions from configuration.

    Args:
        subagent_configs: Dict mapping subagent names to configs
        agents_dir: Directory containing agent filesystem configs
        base_path: Base path for resolving relative file paths

    Returns:
        Dict mapping subagent names to AgentDefinitions
    """
    definitions: dict[str, AgentDefinition] = {}

    for name, config in subagent_configs.items():
        # Convert dict to SubagentConfig if needed
        if isinstance(config, dict):
            config = SubagentConfig(name=name, **config)
        elif not isinstance(config, SubagentConfig):
            logger.warning(f"Invalid config type for subagent '{name}': {type(config)}")
            continue

        definition = build_subagent_definition(
            config,
            agents_dir=agents_dir,
            base_path=base_path,
        )

        if definition:
            definitions[name] = definition
            logger.debug(f"Built AgentDefinition for subagent '{name}'")

    return definitions


def subagent_definitions_from_node_config(
    node_subagents: list[str],
    diagram_subagents: dict[str, SubagentConfig | dict[str, Any]],
    agents_dir: Path | None = None,
    base_path: str | None = None,
) -> dict[str, AgentDefinition]:
    """Build AgentDefinitions for subagents referenced by a node.

    Args:
        node_subagents: List of subagent names referenced by the node
        diagram_subagents: Full subagent configs from diagram level
        agents_dir: Directory containing agent filesystem configs
        base_path: Base path for resolving relative file paths

    Returns:
        Dict mapping subagent names to AgentDefinitions
    """
    # Filter to only subagents referenced by this node
    relevant_configs = {
        name: config
        for name, config in diagram_subagents.items()
        if name in node_subagents
    }

    return build_subagent_definitions(
        relevant_configs,
        agents_dir=agents_dir,
        base_path=base_path,
    )
