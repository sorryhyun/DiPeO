"""Helper for aggregating conversation states from person_job nodes."""

import logging
from typing import Any

from dipeo.domain.execution.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


class ConversationAggregator:
    """Aggregates conversation states from person_job nodes."""

    def aggregate_conversations(self, context: ExecutionContext, diagram: Any) -> dict[str, Any]:
        aggregated = {"messages": []}

        from dipeo.diagram_generated.generated_nodes import NodeType

        person_job_nodes = []
        all_person_jobs = diagram.get_nodes_by_type(NodeType.PERSON_JOB)
        for node in all_person_jobs:
            node_result = context.state.get_node_result(node.id)
            if node_result:
                person_job_nodes.append(node)

        for node in person_job_nodes:
            node_result = context.state.get_node_result(node.id)
            if not node_result:
                continue

            value = node_result.get("value")

            is_conversation_list = self._is_conversation_list(value)

            logger.debug(
                f"Node {node.id} ({getattr(node, 'label', 'unlabeled')}): "
                f"value type={type(value)}, is_conversation_list={is_conversation_list}, "
                f"has conversation dict={isinstance(value, dict) and 'conversation' in value}"
            )

            if is_conversation_list:
                messages = value
                aggregated["messages"].extend(messages)
            elif isinstance(value, dict) and "conversation" in value:
                messages = value["conversation"]
                aggregated["messages"].extend(messages)

        logger.debug(
            f"ConversationAggregator: Total aggregated messages: {len(aggregated['messages'])}"
        )
        return aggregated

    def get_latest_conversation(
        self, context: ExecutionContext, diagram: Any
    ) -> dict[str, Any] | None:
        from dipeo.diagram_generated.generated_nodes import NodeType

        person_job_nodes = diagram.get_nodes_by_type(NodeType.PERSON_JOB)
        for node in person_job_nodes:
            node_result = context.state.get_node_result(node.id)
            if node_result:
                value = node_result.get("value")
                if isinstance(value, list) and len(value) > 0:
                    return {"messages": value}
                elif isinstance(value, dict) and "conversation" in value:
                    return {"messages": value["conversation"]}
        return None

    def _is_conversation_list(self, value: Any) -> bool:
        if not isinstance(value, list) or len(value) == 0:
            return False

        first_msg = value[0]
        if isinstance(first_msg, dict):
            return "role" in first_msg and "content" in first_msg
        elif hasattr(first_msg, "role") or hasattr(first_msg, "content"):
            return True
        return False
