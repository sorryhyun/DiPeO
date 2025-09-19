"""Main translator for converting Claude Code sessions into DiPeO diagrams.

This is the main entry point for translation, providing backward compatibility
while delegating to the new phase-based architecture.
"""

from typing import Any, Optional

from dipeo.infrastructure.claude_code import ClaudeCodeSession

from .phase_coordinator import PhaseCoordinator
from .post_processing import PipelineConfig


class ClaudeCodeTranslator:
    """Translates Claude Code sessions into DiPeO light format diagrams.

    This class provides the main interface for translation while delegating
    to the new phase-based architecture internally.
    """

    def __init__(self) -> None:
        """Initialize the translator."""
        self.coordinator = PhaseCoordinator()

    def translate(
        self,
        session: ClaudeCodeSession,
        post_process: bool = False,
        processing_config: Optional[PipelineConfig] = None,
    ) -> dict[str, Any]:
        """
        Translate a Claude Code session into a light format diagram.

        This method provides backward compatibility while delegating to
        the new phase-based architecture internally.

        Args:
            session: Parsed Claude Code session
            post_process: Whether to apply post-processing optimizations
            processing_config: Custom post-processing configuration

        Returns:
            Light format diagram dictionary
        """
        return self.coordinator.translate(session, post_process, processing_config)
