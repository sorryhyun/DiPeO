"""Output formatting and representation building for PersonJob nodes."""

from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.person_job_node import PersonJobNode
from dipeo.domain.conversation import Person

from .conversation_handler import ConversationHandler
from .text_format_handler import TextFormatHandler

logger = get_module_logger(__name__)


class OutputBuilder:
    """Handles output formatting and representation building for PersonJob results."""

    def __init__(
        self, text_format_handler: TextFormatHandler, conversation_handler: ConversationHandler
    ):
        """Initialize OutputBuilder with required dependencies.

        Args:
            text_format_handler: Handler for text format processing
            conversation_handler: Handler for conversation operations
        """
        self._text_format_handler = text_format_handler
        self._conversation_handler = conversation_handler

    def build_single_output(
        self,
        result: Any,
        person: Person,
        node: PersonJobNode,
        diagram: Any,
        model: str,
        trace_id: str = "",
        selected_messages: list | None = None,
        execution_orchestrator: Any = None,
    ) -> dict[str, Any]:
        """Build node output as dict for single execution.

        Args:
            result: LLM result
            person: Person executing the job
            node: PersonJobNode configuration
            diagram: Diagram containing the node
            model: LLM model used
            trace_id: Execution trace ID
            selected_messages: Messages selected for context
            execution_orchestrator: Orchestrator for accessing conversation

        Returns:
            Dictionary with body and metadata
        """
        # Extract LLM usage
        llm_usage = None
        if hasattr(result, "llm_usage") and result.llm_usage:
            llm_usage = result.llm_usage

        # Get person and conversation IDs
        person_id = str(person.id) if person.id else None
        conversation_id = None

        # Build all representations
        text_repr = self._extract_text(result)
        object_repr = self._extract_object(result, node)

        # Lazy evaluation for conversation
        conversation_repr = None
        if self._any_edge_needs_conversation(node.id, diagram):
            conversation_repr = self._build_conversation_repr(
                person, selected_messages, model, result, execution_orchestrator
            )

        # Determine primary body content
        natural_body = text_repr  # Default to text

        # Check if conversation output is needed
        if self._conversation_handler.needs_conversation_output(str(node.id), diagram):
            natural_body = (
                conversation_repr if conversation_repr else {"messages": [], "last_message": None}
            )
        # Check if structured data is available
        elif object_repr is not None:
            natural_body = object_repr

        # Prepare memory selection info for metadata
        memory_selection = self._build_memory_selection_info(
            selected_messages, node, execution_orchestrator
        )

        # Build all representations
        representations = {"text": text_repr}
        if object_repr is not None:
            representations["object"] = object_repr
        if conversation_repr is not None:
            representations["conversation"] = conversation_repr

        # Return as dict with metadata
        return {
            "body": natural_body,
            "metadata": {
                "person_id": person_id,
                "conversation_id": conversation_id,
                "model": model,
                "llm_usage": llm_usage.model_dump() if llm_usage else None,
                "memory_selection": memory_selection,
                "preview": text_repr[:200] if text_repr else None,
                "is_structured": object_repr is not None,
                "representations": representations,
            },
        }

    def _extract_text(self, result: Any) -> str:
        """Extract text representation from result.

        Args:
            result: LLM result

        Returns:
            Text representation
        """
        if hasattr(result, "content"):
            return result.content
        elif hasattr(result, "text"):
            return result.text
        return str(result)

    def _extract_object(self, result: Any, node: PersonJobNode) -> dict | None:
        """Extract structured object if text_format was used.

        Args:
            result: LLM result
            node: PersonJobNode configuration

        Returns:
            Structured object or None
        """
        has_text_format = (hasattr(node, "text_format") and node.text_format) or (
            hasattr(node, "text_format_file") and node.text_format_file
        )

        if has_text_format:
            return self._text_format_handler.process_structured_output(result, True)
        return None

    def _build_conversation_repr(
        self,
        person: Person,
        selected_messages: list | None,
        model: str,
        result: Any,
        execution_orchestrator: Any = None,
    ) -> dict[str, Any]:
        """Build conversation representation.

        Args:
            person: Person executing the job
            selected_messages: Messages selected for context
            model: LLM model used
            result: LLM result
            execution_orchestrator: Orchestrator for accessing conversation

        Returns:
            Dictionary with conversation data
        """
        if selected_messages is not None:
            messages = selected_messages
        else:
            all_conv_messages = (
                execution_orchestrator.get_conversation().messages
                if execution_orchestrator and hasattr(execution_orchestrator, "get_conversation")
                else []
            )
            # Filter messages relevant to this person
            messages = [
                msg
                for msg in all_conv_messages
                if msg.from_person_id == person.id or msg.to_person_id == person.id
            ]

        return {
            "messages": messages,
            "last_message": messages[-1] if messages else None,
            "person_id": str(person.id),
            "model": model,
        }

    def _any_edge_needs_conversation(self, node_id: str, diagram: Any) -> bool:
        """Check if any outgoing edge needs conversation representation.

        Args:
            node_id: Node ID to check
            diagram: Diagram containing the node

        Returns:
            True if any edge needs conversation representation
        """
        from dipeo.diagram_generated.enums import ContentType

        if not diagram or not hasattr(diagram, "get_outgoing_edges"):
            return False

        edges = diagram.get_outgoing_edges(node_id)
        return any(
            hasattr(edge, "content_type") and edge.content_type == ContentType.CONVERSATION_STATE
            for edge in edges
        )

    def _build_memory_selection_info(
        self,
        selected_messages: list | None,
        node: PersonJobNode,
        execution_orchestrator: Any = None,
    ) -> dict[str, Any] | None:
        """Build memory selection information for metadata.

        Args:
            selected_messages: Messages selected for context
            node: PersonJobNode configuration
            execution_orchestrator: Orchestrator for accessing conversation

        Returns:
            Dictionary with memory selection info or None
        """
        if selected_messages is None:
            return None

        # Get all messages from conversation to determine the total count
        all_messages = (
            execution_orchestrator.get_conversation().messages
            if execution_orchestrator and hasattr(execution_orchestrator, "get_conversation")
            else []
        )
        total_available = len(all_messages) if all_messages else 0

        return {
            "selected_count": len(selected_messages),
            "total_messages": total_available,
            "criteria": getattr(node, "memorize_to", None),
            "at_most": getattr(node, "at_most", None),
        }
