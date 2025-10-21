"""Transformer for light format - handles bidirectional transformations."""

from __future__ import annotations

import logging
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import DomainDiagram, HandleDirection, NodeType
from dipeo.diagram_generated.conversions import node_kind_to_domain_type
from dipeo.domain.diagram.models.format_models import LightConnection, LightDiagram, LightNode
from dipeo.domain.diagram.utils import (
    HandleIdOperations,
    HandleLabelParser,
    HandleValidator,
    NodeFieldMapper,
    PersonReferenceResolver,
    _node_id_map,
    arrows_list_to_dict,
    create_arrow_dict,
    create_node_id,
    nodes_list_to_dict,
)

logger = get_module_logger(__name__)


class LightTransformer:
    """Transforms data between light format and domain format."""

    def light_diagram_to_dict(
        self,
        light_diagram: LightDiagram,
        original_data: dict[str, Any],
        diagram_path: str | None = None,
        prompt_compiler: Any = None,
    ) -> dict[str, Any]:
        """Convert LightDiagram to dictionary format for DomainDiagram.

        Args:
            light_diagram: The light diagram to convert
            original_data: Original parsed data (for handles/persons)
            diagram_path: Optional path to diagram file (for prompt compilation)
            prompt_compiler: Optional prompt compiler instance

        Returns:
            Dictionary ready for DomainDiagram validation
        """
        from dipeo.domain.diagram.strategies.light.parser import LightDiagramParser

        nodes_list = []
        for index, node in enumerate(light_diagram.nodes):
            node_dict = node.model_dump(exclude_none=True)
            props = LightDiagramParser.extract_node_props_from_light(node_dict)

            if node.label:
                props["label"] = node.label

            processed_node = {
                "id": create_node_id(index),
                "type": node.type.lower() if isinstance(node.type, str) else node.type,
                "position": node.position or {"x": 0, "y": 0},
                "data": props,
            }
            nodes_list.append(processed_node)

        # Compile prompts if available
        if prompt_compiler:
            effective_path = diagram_path or original_data.get("metadata", {}).get("diagram_id")
            nodes_list = prompt_compiler.resolve_prompt_files(nodes_list, effective_path)

        nodes_dict = nodes_list_to_dict(nodes_list)
        arrows_list = self.process_light_connections(light_diagram, nodes_list)
        arrows_dict = arrows_list_to_dict(arrows_list)

        # Extract handles and persons from original data
        from dipeo.domain.diagram.strategies.light.parser import LightDiagramParser

        handles_dict = LightDiagramParser.extract_handles_dict(original_data)
        persons_dict = LightDiagramParser.extract_persons_dict(original_data)

        return {
            "nodes": nodes_dict,
            "arrows": arrows_dict,
            "handles": handles_dict,
            "persons": persons_dict,
            "metadata": light_diagram.metadata,
        }

    def apply_format_transformations(
        self, diagram_dict: dict[str, Any], original_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply light format-specific transformations.

        Args:
            diagram_dict: The diagram dictionary to transform
            original_data: Original parsed data

        Returns:
            Transformed diagram dictionary
        """
        # Resolve person references (label → ID)
        person_label_to_id = PersonReferenceResolver.build_label_to_id_map(diagram_dict["persons"])
        PersonReferenceResolver.resolve_persons_in_nodes(diagram_dict["nodes"], person_label_to_id)

        # Generate and validate handles
        self.generate_missing_handles(diagram_dict)
        self.create_arrow_handles(diagram_dict)
        self.preserve_condition_content_types(diagram_dict)

        return diagram_dict

    def domain_to_light_diagram(self, diagram: DomainDiagram) -> LightDiagram:
        """Convert DomainDiagram to LightDiagram for export.

        Args:
            diagram: The domain diagram to convert

        Returns:
            LightDiagram ready for serialization
        """
        id_to_label: dict[str, str] = {}
        label_counts: dict[str, int] = {}

        person_id_to_label = PersonReferenceResolver.build_id_to_label_map(diagram.persons)

        def _unique(base: str) -> str:
            cnt = label_counts.get(base, 0)
            label_counts[base] = cnt + 1
            return f"{base}~{cnt}" if cnt else base

        nodes_out = []
        for n in diagram.nodes:
            base = n.data.get("label") or str(n.type).split(".")[-1].title()
            label = _unique(base)
            id_to_label[n.id] = label
            node_type = str(n.type).split(".")[-1].lower()

            props = {
                k: v
                for k, v in (n.data or {}).items()
                if k not in {"label", "position"}
                and v not in (None, "", {})
                and not (k != "flipped" and v == [])
            }

            if node_type == "person_job" and "person" in props:
                person_id = props["person"]
                if person_id in person_id_to_label:
                    props["person"] = person_id_to_label[person_id]

            props = NodeFieldMapper.map_export_fields(node_type, props)

            node = LightNode(
                type=node_type,
                label=label,
                position={"x": round(n.position.x), "y": round(n.position.y)},
                **props,
            )
            nodes_out.append(node)

        connections = []
        for a in diagram.arrows:
            s_node_id, s_handle, _ = HandleIdOperations.parse_handle_id(a.source)
            t_node_id, t_handle, _ = HandleIdOperations.parse_handle_id(a.target)

            # Use bracket syntax for handles (modern format)
            from_str = f"{id_to_label[s_node_id]}{'[' + s_handle + ']' if s_handle != 'default' else ''}"
            to_str = f"{id_to_label[t_node_id]}{'[' + t_handle + ']' if t_handle != 'default' else ''}"

            conn_kwargs = {
                "from": from_str,
                "to": to_str,
                "label": a.label,
                "type": a.content_type if a.content_type else None,
            }
            # Include branch data if present and not from conditional handles
            if a.data and "branch" in a.data and s_handle not in ["condtrue", "condfalse"]:
                conn_kwargs["data"] = {"branch": a.data["branch"]}  # type: ignore[assignment]

            conn = LightConnection(**conn_kwargs)  # type: ignore[arg-type]
            connections.append(conn)

        persons_data = None
        if diagram.persons:
            persons_dict = {}
            for p in diagram.persons:
                person_data = {
                    "service": p.llm_config.service
                    if hasattr(p.llm_config.service, "value")
                    else str(p.llm_config.service),
                    "model": p.llm_config.model,
                }
                if p.llm_config.system_prompt:
                    person_data["system_prompt"] = p.llm_config.system_prompt
                if p.llm_config.api_key_id:
                    person_data["api_key_id"] = p.llm_config.api_key_id
                persons_dict[p.label] = person_data
            persons_data = persons_dict

        return LightDiagram(
            nodes=nodes_out,
            connections=connections,
            persons=persons_data,  # type: ignore[arg-type]
            metadata=diagram.metadata.model_dump(exclude_none=True) if diagram.metadata else None,
        )

    def process_light_connections(
        self, light_diagram: LightDiagram, nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Process light diagram connections into arrow dictionaries.

        Args:
            light_diagram: The light diagram with connections to process
            nodes: List of node dictionaries for label-to-ID mapping

        Returns:
            List of arrow dictionaries ready for diagram compilation
        """
        arrows: list[dict[str, Any]] = []
        label2id = _node_id_map(nodes)
        nodes_by_id = {node["id"]: node for node in nodes}

        for idx, conn in enumerate(light_diagram.connections):
            arrow = self._process_single_connection(conn, idx, label2id, nodes_by_id)
            if arrow:
                arrows.append(arrow)
        return arrows

    def _process_single_connection(
        self, conn: Any, idx: int, label2id: dict[str, str], nodes_by_id: dict[str, dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Process a single connection into an arrow dictionary.

        Args:
            conn: Connection object from light diagram
            idx: Connection index for generating arrow IDs
            label2id: Mapping from node labels to node IDs
            nodes_by_id: Mapping from node IDs to node dictionaries

        Returns:
            Arrow dictionary or None if connection is invalid
        """
        # Parse source and target endpoints
        source_endpoint = self._parse_connection_endpoint(
            conn.from_, label2id, nodes_by_id, is_source=True
        )
        target_endpoint = self._parse_connection_endpoint(
            conn.to, label2id, nodes_by_id, is_source=False
        )

        if not source_endpoint or not target_endpoint:
            logger.warning(
                f"Skipping connection: could not find nodes for "
                f"'{source_endpoint[3] if source_endpoint else conn.from_}' -> "
                f"'{target_endpoint[3] if target_endpoint else conn.to}'"
            )
            return None

        src_id, src_handle, _, _ = source_endpoint
        dst_id, dst_handle, dst_handle_from_split, _ = target_endpoint

        # Extract connection data
        conn_dict = conn.model_dump(by_alias=True, exclude={"from", "to", "label", "type"})
        arrow_data = conn_dict.get("data", {})

        arrow_data_processed = self._build_arrow_data(arrow_data, src_handle, dst_handle_from_split)

        source_handle_id, target_handle_id = HandleIdOperations.create_handle_ids(
            src_id, dst_id, src_handle, dst_handle
        )

        return create_arrow_dict(
            arrow_data.get("id", f"arrow_{idx}"),
            source_handle_id,
            target_handle_id,
            arrow_data_processed,
            conn.type,
            conn.label,
        )

    def _parse_connection_endpoint(
        self,
        endpoint_raw: str,
        label2id: dict[str, str],
        nodes_by_id: dict[str, dict[str, Any]],
        is_source: bool,
    ) -> tuple[str, str, str, str] | None:
        """Parse a connection endpoint (source or target).

        Supports both bracket syntax (NodeLabel[handle]) and underscore syntax (NodeLabel_handle).
        When bracket syntax is used, performs strict validation against HANDLE_SPECS.

        Args:
            endpoint_raw: Raw endpoint string (e.g., "NodeLabel[handle]" or "NodeLabel_handle")
            label2id: Mapping from node labels to node IDs
            nodes_by_id: Mapping from node IDs to node dictionaries
            is_source: True if parsing source endpoint, False for target

        Returns:
            Tuple of (node_id, handle_name, handle_from_split, node_label) or None if invalid

        Raises:
            ValueError: If bracket syntax is used with an invalid handle for the node type
        """
        from dipeo.domain.diagram.utils.core.handle_operations import HandleValidator

        uses_bracket_syntax = "[" in endpoint_raw and "]" in endpoint_raw

        node_id, handle_from_split, node_label = HandleLabelParser.parse_label_with_handle(
            endpoint_raw, label2id
        )

        if not node_id:
            return None

        # Determine the actual handle name (may differ from split value)
        handle_name = HandleLabelParser.determine_handle_name(
            handle_from_split, {}, is_source=is_source
        )

        if uses_bracket_syntax and handle_from_split:
            node = nodes_by_id.get(node_id)
            if node:
                node_type = node["type"]
                direction = "output" if is_source else "input"
                HandleValidator.validate_bracket_syntax_handle(
                    node_label, handle_name, node_type, direction
                )

        return (node_id, handle_name, handle_from_split, node_label)

    def _build_arrow_data(
        self, arrow_data: dict[str, Any] | None, src_handle: str, dst_handle_from_split: str
    ) -> dict[str, Any]:
        """Build arrow data with special handling for first execution and conditionals.

        Args:
            arrow_data: Original arrow data from connection
            src_handle: Source handle name
            dst_handle_from_split: Target handle name from label split

        Returns:
            Processed arrow data dictionary
        """
        arrow_data_copy = arrow_data.copy() if arrow_data else {}

        # Handle first execution requirement
        if dst_handle_from_split == "_first":
            arrow_data_copy["requires_first_execution"] = True

        # Handle conditional branches
        if src_handle in ["condtrue", "condfalse"]:
            if "branch" not in arrow_data_copy:
                arrow_data_copy["branch"] = "true" if src_handle == "condtrue" else "false"
            arrow_data_copy["is_conditional"] = True

        return arrow_data_copy

    @staticmethod
    def generate_missing_handles(diagram_dict: dict[str, Any]) -> None:
        """Generate missing handles for nodes that don't have any.

        Args:
            diagram_dict: The diagram dictionary to modify
        """
        from dipeo.domain.diagram.utils.shared_components import HandleGenerator

        handle_generator = HandleGenerator()

        for node_id, node in diagram_dict["nodes"].items():
            node_has_handles = any(
                handle.get("nodeId") == node_id or handle.get("node_id") == node_id
                for handle in diagram_dict["handles"].values()
            )
            if not node_has_handles:
                node_type_str = node.get("type", "code_job")
                try:
                    node_type = node_kind_to_domain_type(node_type_str)
                except ValueError:
                    node_type = NodeType.CODE_JOB

                handle_generator.generate_for_node(diagram_dict, node_id, node_type)

    @staticmethod
    def create_arrow_handles(diagram_dict: dict[str, Any]) -> None:
        """Create handles referenced by arrows if they don't exist.

        Args:
            diagram_dict: The diagram dictionary to modify
        """
        nodes_dict = diagram_dict["nodes"]

        for _arrow_id, arrow in diagram_dict["arrows"].items():
            if "_" in arrow.get("source", ""):
                LightTransformer._ensure_handle_exists(
                    arrow["source"],
                    HandleDirection.OUTPUT,
                    nodes_dict,
                    diagram_dict["handles"],
                    arrow,
                )

            if "_" in arrow.get("target", ""):
                LightTransformer._ensure_handle_exists(
                    arrow["target"],
                    HandleDirection.INPUT,
                    nodes_dict,
                    diagram_dict["handles"],
                    arrow,
                )

    @staticmethod
    def _ensure_handle_exists(
        handle_ref: str,
        direction: HandleDirection,
        nodes_dict: dict[str, Any],
        handles_dict: dict[str, Any],
        arrow: dict[str, Any],
    ) -> None:
        """Ensure a handle exists, creating it if necessary.

        Args:
            handle_ref: Handle reference string
            direction: Handle direction (INPUT or OUTPUT)
            nodes_dict: Nodes dictionary
            handles_dict: Handles dictionary to modify
            arrow: Arrow dictionary
        """
        HandleValidator.ensure_handle_exists(handle_ref, direction, nodes_dict, handles_dict, arrow)

    @staticmethod
    def preserve_condition_content_types(diagram_dict: dict[str, Any]) -> None:
        """Preserve content types through condition nodes.

        Args:
            diagram_dict: The diagram dictionary to modify
        """
        nodes_dict = diagram_dict["nodes"]
        arrows_dict = diagram_dict["arrows"]

        for _arrow_id, arrow in arrows_dict.items():
            if arrow.get("source"):
                try:
                    node_id, handle_label, _ = HandleIdOperations.parse_handle_id(arrow["source"])
                    source_node = nodes_dict.get(node_id)

                    if (
                        source_node
                        and source_node.get("type") == "condition"
                        and handle_label in ["condtrue", "condfalse"]
                    ):
                        input_content_types = []
                        for other_arrow in arrows_dict.values():
                            if (
                                other_arrow.get("target")
                                and node_id in other_arrow["target"]
                                and other_arrow.get("content_type")
                            ):
                                input_content_types.append(other_arrow["content_type"])

                        if input_content_types and all(
                            ct == input_content_types[0] for ct in input_content_types
                        ):
                            arrow["content_type"] = input_content_types[0]
                except Exception:
                    pass
