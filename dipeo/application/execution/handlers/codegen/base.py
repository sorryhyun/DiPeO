"""Base handler for codegen operations.

Provides shared handler patterns for codegen operations.
Service functionality remains in the infrastructure layer.
"""

from typing import Any

from pydantic import BaseModel

from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.domain.execution.messaging.envelope import Envelope


class BaseCodegenHandler(TypedNodeHandler):
    """Base handler for codegen operations with shared patterns.

    Provides common patterns for envelope extraction and batch detection.
    """

    def extract_envelope_body(self, envelope: Envelope) -> Any:
        """Extract body content from an envelope."""
        if hasattr(envelope, "body"):
            return envelope.body
        elif hasattr(envelope, "get_body"):
            return envelope.get_body()
        else:
            # For backward compatibility with different envelope formats
            return envelope

    def extract_envelope_inputs(self, inputs: dict[str, Envelope]) -> dict[str, Any]:
        """Extract data from multiple envelope inputs."""
        result = {}
        for key, envelope in inputs.items():
            if envelope:
                result[key] = self.extract_envelope_body(envelope)
        return result

    def detect_batch_mode(
        self, node: BaseModel, inputs: dict[str, Any]
    ) -> tuple[bool, dict | None]:
        """Detect if node should run in batch mode."""
        if hasattr(node, "batch") and node.batch:
            batch_key = getattr(node, "batchInputKey", "default")
            batch_data = inputs.get(batch_key)
            if batch_data and isinstance(batch_data, dict):
                return True, batch_data

        if "sources" in inputs and isinstance(inputs.get("sources"), dict):
            return True, inputs["sources"]

        return False, None

    def build_standard_metadata(self, node: BaseModel, **extra) -> dict:
        """Build consistent metadata structure for envelopes."""
        metadata = {
            "node_id": str(node.id),
            "node_type": str(node.type),
        }

        metadata.update(extra)

        return metadata
