"""Domain logic for building executable edges from arrows."""

from dataclasses import dataclass
from typing import Any

from dipeo.diagram_generated import ContentType, DomainArrow, DomainNode, NodeID, NodeType
from dipeo.domain.diagram.models.executable_diagram import ExecutableEdgeV2


@dataclass
class TransformationMetadata:
    """Metadata describing how data should be transformed between nodes."""

    content_type: ContentType
    transformation_rules: dict[str, Any] = None

    def __post_init__(self):
        if self.transformation_rules is None:
            self.transformation_rules = {}


@dataclass
class ResolvedConnection:
    """Represents a resolved connection between nodes."""

    arrow_id: str
    source_node_id: NodeID
    target_node_id: NodeID
    source_handle_label: str | None = None
    target_handle_label: str | None = None


class EdgeBuilder:
    """Builds executable edges from domain arrows with transformation rules.

    This is pure domain logic that transforms arrows into executable edges
    with data flow rules, without any application dependencies.
    """

    def __init__(self):
        self._errors: list[str] = []

    def build_edges(
        self,
        arrows: list[DomainArrow],
        resolved_connections: list[ResolvedConnection],
        nodes: dict[NodeID, DomainNode],
    ) -> tuple[list[ExecutableEdgeV2], list[str]]:
        self._errors = []

        arrow_map = {arrow.id: arrow for arrow in arrows}

        edges = []
        for connection in resolved_connections:
            arrow = arrow_map.get(connection.arrow_id)
            if not arrow:
                self._errors.append(f"Arrow {connection.arrow_id} not found")
                continue

            edge = self._build_edge(connection, arrow, nodes)
            if edge:
                edges.append(edge)

        return edges, self._errors

    def _build_edge(
        self, connection: ResolvedConnection, arrow: DomainArrow, nodes: dict[NodeID, DomainNode]
    ) -> ExecutableEdgeV2 | None:
        source_node = nodes.get(connection.source_node_id)
        target_node = nodes.get(connection.target_node_id)

        if not source_node or not target_node:
            self._errors.append(
                f"Missing nodes for arrow {arrow.id}: "
                f"source={connection.source_node_id}, target={connection.target_node_id}"
            )
            return None

        transform_metadata = self._create_transformation_metadata(
            source_node, target_node, arrow, connection
        )

        edge_metadata = {
            "arrow_data": arrow.data or {},
            "source_type": source_node.type.value,
            "target_type": target_node.type.value,
            "label": getattr(arrow, "label", None),
        }

        is_first_execution = False
        if arrow.data and arrow.data.get("requires_first_execution"):
            is_first_execution = True
            edge_metadata["is_first_execution"] = True

        is_conditional = False
        if arrow.data and arrow.data.get("is_conditional"):
            is_conditional = True

        if connection.source_handle_label and str(connection.source_handle_label) in [
            "condtrue",
            "condfalse",
        ]:
            is_conditional = True

        source_output = None
        if connection.source_handle_label:
            source_output = (
                connection.source_handle_label.value
                if hasattr(connection.source_handle_label, "value")
                else str(connection.source_handle_label)
            )

        target_input = None
        if connection.target_handle_label:
            target_input = (
                connection.target_handle_label.value
                if hasattr(connection.target_handle_label, "value")
                else str(connection.target_handle_label)
            )

        if source_node.type == NodeType.CONDITION and str(source_output) in (
            "condtrue",
            "condfalse",
        ):
            is_conditional = True

        if arrow.label:
            edge_metadata = edge_metadata or {}
            edge_metadata["original_target_handle"] = target_input
            target_input = arrow.label

        execution_priority = self._determine_execution_priority(target_node, arrow)

        return ExecutableEdgeV2(
            id=arrow.id,
            source_node_id=connection.source_node_id,
            target_node_id=connection.target_node_id,
            source_output=source_output,
            target_input=target_input,
            content_type=transform_metadata.content_type,
            transform_rules=transform_metadata.transformation_rules,
            is_conditional=is_conditional,
            execution_priority=execution_priority,
            metadata=edge_metadata,
        )

    def _create_transformation_metadata(
        self,
        source_node: DomainNode,
        target_node: DomainNode,
        arrow: DomainArrow,
        connection: ResolvedConnection,
    ) -> TransformationMetadata:
        content_type = self._determine_content_type(source_node, arrow)

        rules = self._extract_transformation_rules(arrow, source_node, target_node)

        return TransformationMetadata(content_type=content_type, transformation_rules=rules)

    def _determine_execution_priority(self, target_node: DomainNode, arrow: DomainArrow) -> int:
        return 0

    def _determine_content_type(self, source_node: DomainNode, arrow: DomainArrow) -> ContentType:
        if arrow.content_type:
            return arrow.content_type

        if arrow.data and "contentType" in arrow.data:
            try:
                return ContentType(arrow.data["contentType"])
            except ValueError:
                self._errors.append(
                    f"Invalid content type in arrow {arrow.id}: {arrow.data['contentType']}"
                )

        if source_node.type == NodeType.PERSON_JOB:
            return ContentType.CONVERSATION_STATE
        elif source_node.type == NodeType.DB or source_node.type in [
            NodeType.CODE_JOB,
            NodeType.API_JOB,
        ]:
            return ContentType.OBJECT
        else:
            return ContentType.RAW_TEXT

    def _extract_transformation_rules(
        self, arrow: DomainArrow, source_node: DomainNode, target_node: DomainNode
    ) -> dict[str, Any]:
        rules = {}

        content_type = self._determine_content_type(source_node, arrow)
        if content_type:
            rules["content_type"] = (
                content_type.value if hasattr(content_type, "value") else content_type
            )

        if arrow.data:
            if "extractVariable" in arrow.data:
                rules["extract_variable"] = arrow.data["extractVariable"]

            if "format" in arrow.data:
                rules["format"] = arrow.data["format"]

            if "transform" in arrow.data:
                rules["custom_transform"] = arrow.data["transform"]

        if source_node.type == NodeType.DB and target_node.type == NodeType.PERSON_JOB:
            rules["format_for_conversation"] = True

        return rules
