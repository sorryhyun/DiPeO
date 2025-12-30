"""Filesystem-based subagent configuration loader."""

from pathlib import Path
from typing import Any

from dipeo.config.base_logger import get_module_logger

from .config import SubagentConfig

logger = get_module_logger(__name__)


class SubagentLoader:
    """Loader for subagent configurations from filesystem.

    Supports two patterns:
    1. Inline configuration in diagram YAML (SubagentConfig)
    2. Filesystem-based configuration with separate files for identity/characteristics

    Filesystem structure for subagents:
    ```
    agents/
      researcher/
        in_a_nutshell.md     # Brief identity (optional)
        characteristics.md   # Detailed behavior guidelines (optional)
        system.md            # Full system prompt (alternative to above)
    ```
    """

    def __init__(self, agents_dir: Path | None = None):
        """Initialize loader.

        Args:
            agents_dir: Base directory for agent configurations
        """
        self.agents_dir = agents_dir

    def load_identity(self, agent_name: str) -> tuple[str | None, str | None]:
        """Load agent identity files from filesystem.

        Args:
            agent_name: Name of the agent (matches directory name)

        Returns:
            Tuple of (in_a_nutshell content, characteristics content)
        """
        if not self.agents_dir:
            return None, None

        agent_dir = self.agents_dir / agent_name
        if not agent_dir.exists():
            logger.debug(f"Agent directory not found: {agent_dir}")
            return None, None

        nutshell = None
        characteristics = None

        nutshell_file = agent_dir / "in_a_nutshell.md"
        if nutshell_file.exists():
            nutshell = nutshell_file.read_text()

        characteristics_file = agent_dir / "characteristics.md"
        if characteristics_file.exists():
            characteristics = characteristics_file.read_text()

        return nutshell, characteristics

    def load_system_prompt(self, agent_name: str) -> str | None:
        """Load full system prompt from filesystem.

        Args:
            agent_name: Name of the agent

        Returns:
            System prompt content, or None if not found
        """
        if not self.agents_dir:
            return None

        agent_dir = self.agents_dir / agent_name
        system_file = agent_dir / "system.md"

        if system_file.exists():
            return system_file.read_text()

        return None

    def build_prompt_from_identity(
        self,
        agent_name: str,
        nutshell: str | None = None,
        characteristics: str | None = None,
    ) -> str:
        """Build system prompt from identity files.

        Args:
            agent_name: Name of the agent
            nutshell: Brief identity content
            characteristics: Behavioral characteristics content

        Returns:
            Combined system prompt
        """
        parts = []

        if nutshell:
            parts.append(f"# Identity\n\n{nutshell}")

        if characteristics:
            parts.append(f"# Behavioral Guidelines\n\n{characteristics}")

        if not parts:
            parts.append(f"You are {agent_name}, a specialized subagent.")

        return "\n\n".join(parts)

    def load_subagent_config(
        self,
        name: str,
        inline_config: dict[str, Any] | None = None,
    ) -> SubagentConfig:
        """Load subagent configuration from filesystem and/or inline config.

        Inline configuration takes precedence over filesystem.

        Args:
            name: Subagent name
            inline_config: Inline configuration from diagram YAML

        Returns:
            SubagentConfig with merged configuration
        """
        config_dict: dict[str, Any] = {"name": name}

        # Start with inline config if provided
        if inline_config:
            config_dict.update(inline_config)

        # Try to load from filesystem if prompt not provided
        if "prompt" not in config_dict and self.agents_dir:
            # First try system.md
            system_prompt = self.load_system_prompt(name)
            if system_prompt:
                config_dict["prompt"] = system_prompt
            else:
                # Fall back to identity files
                nutshell, characteristics = self.load_identity(name)
                if nutshell or characteristics:
                    config_dict["prompt"] = self.build_prompt_from_identity(
                        name, nutshell, characteristics
                    )

        # Ensure description exists
        if "description" not in config_dict:
            config_dict["description"] = f"Specialized subagent: {name}"

        return SubagentConfig.model_validate(config_dict)
