"""
Base handler for codegen operations.

This base class provides ONLY shared handler patterns, not service functionality.
Services remain in the infrastructure layer as per DiPeO's architecture.
"""

from typing import Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.domain.execution.envelope import Envelope


class BaseCodegenHandler(TypedNodeHandler):
    """Base handler for codegen operations with minimal shared patterns.

    This class provides only common handler patterns like envelope extraction
    and batch detection. It does NOT duplicate service functionality which
    belongs in the infrastructure layer.
    """

    def extract_envelope_body(self, envelope: Envelope) -> Any:
        """Extract body content from an envelope.

        Common pattern used by all codegen handlers to unwrap envelope data.

        Args:
            envelope: The envelope to extract data from

        Returns:
            The body content of the envelope
        """
        if hasattr(envelope, "body"):
            return envelope.body
        elif hasattr(envelope, "get_body"):
            return envelope.get_body()
        else:
            # For backward compatibility with different envelope formats
            return envelope

    def extract_envelope_inputs(self, inputs: dict[str, Envelope]) -> dict[str, Any]:
        """Extract data from multiple envelope inputs.

        Common pattern for extracting data from 'default' and other envelope patterns.

        Args:
            inputs: Dictionary of input key to envelope

        Returns:
            Dictionary of input key to extracted data
        """
        result = {}
        for key, envelope in inputs.items():
            if envelope:
                result[key] = self.extract_envelope_body(envelope)
        return result

    def detect_batch_mode(
        self, node: BaseModel, inputs: dict[str, Any]
    ) -> tuple[bool, dict | None]:
        """Detect if node should run in batch mode.

        Common batch detection logic used across codegen handlers.

        Args:
            node: The node configuration
            inputs: Processed inputs

        Returns:
            Tuple of (is_batch, batch_data)
        """
        # Check explicit batch flag
        if hasattr(node, "batch") and node.batch:
            # Look for batch input key
            batch_key = getattr(node, "batchInputKey", "default")
            batch_data = inputs.get(batch_key)
            if batch_data and isinstance(batch_data, dict):
                return True, batch_data

        # Check for 'sources' key (common batch pattern)
        if "sources" in inputs and isinstance(inputs.get("sources"), dict):
            return True, inputs["sources"]

        return False, None

    def build_standard_metadata(self, node: BaseModel, **extra) -> dict:
        """Build consistent metadata structure for envelopes.

        Args:
            node: The node being executed
            **extra: Additional metadata fields

        Returns:
            Standard metadata dictionary
        """
        metadata = {
            "node_id": str(node.id),
            "node_type": str(node.type),
        }

        # Add any extra metadata
        metadata.update(extra)

        return metadata
