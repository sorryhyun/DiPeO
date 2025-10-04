"""Person registry management for Claude Code translation.

This module manages the registration and configuration of AI agents (persons)
that participate in the conversation within DiPeO diagrams.
"""

from typing import Any, Optional


class PersonRegistry:
    """Manages registration of persons (AI agents) in DiPeO diagrams."""

    def __init__(self):
        """Initialize the person registry."""
        self.persons: dict[str, dict[str, Any]] = {}
        self._default_claude_config = {
            "service": "anthropic",
            "model": "claude-code",
            "api_key_id": "APIKEY_CLAUDE",
            "system_prompt": "You are Claude Code, an AI assistant helping with software development.",
        }
        self._default_user_config = {
            "service": "human",
            "model": "user",
            "api_key_id": None,
            "system_prompt": "Human user providing input and feedback.",
        }

    def reset(self):
        """Reset the person registry."""
        self.persons = {}

    def register_claude(
        self,
        person_id: str = "claude_code",
        system_messages: list[str] | None = None,
        custom_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register Claude as a person in the diagram.

        Args:
            person_id: Identifier for Claude person
            system_messages: Optional system messages to include in prompt
            custom_config: Optional custom configuration to override defaults

        Returns:
            The registered Claude person configuration
        """
        if person_id in self.persons:
            return self.persons[person_id]

        # Build system prompt with additional context if provided
        base_prompt = self._default_claude_config["system_prompt"]
        if system_messages:
            # Add meta/system messages to provide context (limit to first 5)
            system_context = "\n\nAdditional context:\n" + "\n".join(system_messages[:5])
            full_system_prompt = base_prompt + system_context
        else:
            full_system_prompt = base_prompt

        # Create Claude configuration
        claude_config = self._default_claude_config.copy()
        claude_config["system_prompt"] = full_system_prompt

        # Apply any custom configuration
        if custom_config:
            claude_config.update(custom_config)

        self.persons[person_id] = claude_config
        return claude_config

    def register_user(
        self,
        person_id: str = "user",
        custom_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a human user as a person in the diagram.

        Args:
            person_id: Identifier for user person
            custom_config: Optional custom configuration to override defaults

        Returns:
            The registered user person configuration
        """
        if person_id in self.persons:
            return self.persons[person_id]

        user_config = self._default_user_config.copy()

        # Apply any custom configuration
        if custom_config:
            user_config.update(custom_config)

        self.persons[person_id] = user_config
        return user_config

    def register_custom_person(
        self,
        person_id: str,
        service: str,
        model: str,
        api_key_id: str | None = None,
        system_prompt: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Register a custom AI agent as a person.

        Args:
            person_id: Unique identifier for the person
            service: Service provider (e.g., "openai", "anthropic")
            model: Model name (e.g., "gpt-5", "claude-code")
            api_key_id: Optional API key identifier
            system_prompt: System prompt for the agent
            **kwargs: Additional configuration parameters

        Returns:
            The registered person configuration
        """
        if person_id in self.persons:
            return self.persons[person_id]

        person_config = {
            "service": service,
            "model": model,
            "api_key_id": api_key_id,
            "system_prompt": system_prompt,
            **kwargs,
        }

        self.persons[person_id] = person_config
        return person_config

    def get_person(self, person_id: str) -> dict[str, Any] | None:
        """Get a registered person's configuration.

        Args:
            person_id: The person identifier

        Returns:
            Person configuration if registered, None otherwise
        """
        return self.persons.get(person_id)

    def is_registered(self, person_id: str) -> bool:
        """Check if a person is registered.

        Args:
            person_id: The person identifier

        Returns:
            True if person is registered, False otherwise
        """
        return person_id in self.persons

    def get_all_persons(self) -> dict[str, dict[str, Any]]:
        """Get all registered persons.

        Returns:
            Dictionary of all registered persons
        """
        return self.persons.copy()

    def update_person(self, person_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        """Update an existing person's configuration.

        Args:
            person_id: The person identifier
            updates: Dictionary of fields to update

        Returns:
            Updated person configuration if exists, None otherwise
        """
        if person_id not in self.persons:
            return None

        self.persons[person_id].update(updates)
        return self.persons[person_id]

    def ensure_claude_registered(self, system_messages: list[str] | None = None) -> str:
        """Ensure Claude is registered and return the person ID.

        Args:
            system_messages: Optional system messages to include

        Returns:
            The Claude person ID
        """
        person_id = "claude_code"
        if not self.is_registered(person_id):
            self.register_claude(person_id, system_messages)
        return person_id
