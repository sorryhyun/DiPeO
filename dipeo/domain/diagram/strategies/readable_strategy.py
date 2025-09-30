from __future__ import annotations

import logging

from dipeo.config.base_logger import get_module_logger
import re
from typing import Any

from dipeo.diagram_generated import (
    DomainDiagram,
    HandleDirection,
)
from dipeo.domain.diagram.models.format_models import ReadableArrow, ReadableDiagram, ReadableNode
from dipeo.domain.diagram.utils import (
    ArrowDataProcessor,
    HandleParser,
    NodeFieldMapper,
    PersonExtractor,
    _YamlMixin,
    build_node,
    create_handle_id,
    parse_handle_id,
    process_dotted_keys,
)

from ..utils.conversion_utils import diagram_maps_to_arrays
from .base_strategy import BaseConversionStrategy

logger = get_module_logger(__name__)

class ReadableYamlStrategy(_YamlMixin, BaseConversionStrategy):
    """Human-friendly workflow YAML."""

    format_id = "readable"
    format_info = {
        "name": "Readable Workflow",
        "description": "Human-friendly workflow format",
        "extension": ".readable.yaml",
        "supports_import": True,
        "supports_export": True,
    }

    def deserialize_to_domain(self, content: str, diagram_path: str | None = None) -> DomainDiagram:
        data = self.parse(content)
        data = self._clean_graphql_fields(data)
        readable_diagram = self._parse_to_readable_diagram(data)
        diagram_dict = self._readable_diagram_to_dict(readable_diagram, data)
        diagram_dict = self._apply_format_transformations(diagram_dict, data)
        array_based_dict = diagram_maps_to_arrays(diagram_dict)

        if "metadata" in diagram_dict:
            array_based_dict["metadata"] = diagram_dict["metadata"]

        return DomainDiagram.model_validate(array_based_dict)

    def _parse_to_readable_diagram(self, data: dict[str, Any]) -> ReadableDiagram:
        nodes = []
        for index, node_data in enumerate(data.get("nodes", [])):
            if not isinstance(node_data, dict):
                continue

            step = node_data
            ((name, cfg),) = step.items()

            position = {}
            clean_name = name
            if " @(" in name and name.endswith(")"):
                parts = name.split(" @(")
                if len(parts) == 2:
                    clean_name = parts[0]
                    pos_str = parts[1][:-1]  # Remove trailing )
                    try:
                        x, y = pos_str.split(",")
                        position = {"x": int(x.strip()), "y": int(y.strip())}
                    except (ValueError, IndexError):
                        pass

            if not position:
                position = cfg.get("position", {})

            node_type = cfg.get("type") or ("start" if index == 0 else "job")

            props = {k: v for k, v in cfg.items() if k not in {"position", "type"}}

            node = ReadableNode(
                id=self._create_node_id(index),
                type=node_type,
                label=clean_name,
                position=position if position else {"x": 0, "y": 0},
                props=props,
            )
            nodes.append(node)

        arrows = self._parse_flow_to_arrows(data.get("flow", []), nodes)

        return ReadableDiagram(
            version="readable",
            nodes=nodes,
            arrows=arrows,
            persons=data.get("persons"),
            api_keys=data.get("api_keys"),
            metadata=data.get("metadata"),
        )

    def _parse_flow_to_arrows(
        self, flow_data: list[Any], nodes: list[ReadableNode]
    ) -> list[ReadableArrow]:
        arrows = []
        label_to_node = {node.label: node for node in nodes}
        arrow_counter = 0

        for flow_item in flow_data:
            if isinstance(flow_item, str):
                if " -> " in flow_item:
                    parts = flow_item.split(" -> ")
                    if len(parts) == 2:
                        src_label, dst_label = parts[0].strip(), parts[1].strip()
                        if src_label in label_to_node and dst_label in label_to_node:
                            arrow = ReadableArrow(
                                id=f"arrow_{arrow_counter}",
                                source=label_to_node[src_label].id,
                                target=label_to_node[dst_label].id,
                            )
                            arrows.append(arrow)
                            arrow_counter += 1
            elif isinstance(flow_item, dict):
                for src, dst_data in flow_item.items():
                    src_node, src_handle = self._parse_node_and_handle(src, label_to_node)
                    if not src_node:
                        continue

                    if isinstance(dst_data, str):
                        parsed_arrows = self._parse_flow_destination(
                            src_node, src_handle, dst_data, label_to_node, arrow_counter
                        )
                        arrows.extend(parsed_arrows)
                        arrow_counter += len(parsed_arrows)
                    elif isinstance(dst_data, list):
                        for dst in dst_data:
                            if isinstance(dst, str):
                                parsed_arrows = self._parse_flow_destination(
                                    src_node, src_handle, dst, label_to_node, arrow_counter
                                )
                                arrows.extend(parsed_arrows)
                                arrow_counter += len(parsed_arrows)

        return arrows

    def _parse_node_and_handle(
        self, node_str: str, label_to_node: dict[str, ReadableNode]
    ) -> tuple[ReadableNode | None, str]:
        if "_" in node_str:
            parts = node_str.rsplit("_", 1)
            base_label = parts[0]
            handle = parts[1]

            if handle in ["condtrue", "condfalse"]:
                if base_label in label_to_node:
                    return label_to_node[base_label], handle
            elif node_str in label_to_node:
                return label_to_node[node_str], "default"
            elif base_label in label_to_node:
                return label_to_node[base_label], handle

        if node_str in label_to_node:
            return label_to_node[node_str], "default"

        return None, ""

    def _parse_flow_destination(
        self,
        src_node: ReadableNode,
        src_handle: str,
        dst_str: str,
        label_to_node: dict[str, ReadableNode],
        arrow_counter: int,
    ) -> list[ReadableArrow]:
        arrows = []
        dst_str = dst_str.strip()

        if self._is_new_format(dst_str):
            parsed = self._parse_new_format_flow(dst_str, label_to_node)
            if parsed:
                for dst_node, dst_handle, content_type, label, from_handle in parsed:
                    actual_src_handle = from_handle if from_handle else src_handle

                    arrow = ReadableArrow(
                        id=f"arrow_{arrow_counter}",
                        source=src_node.id,
                        target=dst_node.id,
                        source_handle=actual_src_handle if actual_src_handle != "default" else None,
                        target_handle=dst_handle if dst_handle != "default" else None,
                        label=label,
                        data={"content_type": content_type} if content_type else None,
                    )
                    arrows.append(arrow)
        else:
            parsed = self._parse_old_format_flow(dst_str, label_to_node)
            if parsed:
                dst_node, dst_handle, content_type, label = parsed
                arrow = ReadableArrow(
                    id=f"arrow_{arrow_counter}",
                    source=src_node.id,
                    target=dst_node.id,
                    source_handle=src_handle if src_handle != "default" else None,
                    target_handle=dst_handle if dst_handle != "default" else None,
                    label=label,
                    data={"content_type": content_type} if content_type else None,
                )
                arrows.append(arrow)

        return arrows

    def _is_new_format(self, dst_str: str) -> bool:
        new_keywords = [' to "', ' from "', ' in "', ' as "', ' naming "']
        return any(keyword in dst_str for keyword in new_keywords)

    def _parse_new_format_flow(
        self, flow_str: str, label_to_node: dict[str, ReadableNode]
    ) -> list[tuple]:
        results = []

        if " - to " in flow_str:
            destinations = flow_str.split(" - ")
            for dest in destinations:
                if dest.strip().startswith("to "):
                    parsed = self._parse_single_new_format(dest.strip(), label_to_node)
                    if parsed:
                        results.append(parsed)
        else:
            parsed = self._parse_single_new_format(flow_str, label_to_node)
            if parsed:
                results.append(parsed)

        return results

    def _parse_single_new_format(
        self, flow_str: str, label_to_node: dict[str, ReadableNode]
    ) -> tuple | None:
        import re

        dst_node = None
        dst_handle = "default"
        content_type = None
        label = None
        from_handle = None

        from_match = re.search(r'from\s+"([^"]+)"', flow_str)
        if from_match:
            from_handle = from_match.group(1)

        to_match = re.search(r'to\s+"([^"]+)"', flow_str)
        if to_match:
            node_name = to_match.group(1)
            if node_name in label_to_node:
                dst_node = label_to_node[node_name]

        in_match = re.search(r'in\s+"([^"]+)"', flow_str)
        if in_match:
            dst_handle = in_match.group(1)

        as_match = re.search(r'as\s+"([^"]+)"', flow_str)
        if as_match:
            content_type = as_match.group(1)

        naming_match = re.search(r'naming\s+"([^"]+)"', flow_str)
        if naming_match:
            label = naming_match.group(1)

        if dst_node:
            return (dst_node, dst_handle, content_type, label, from_handle)

        return None

    def _parse_old_format_flow(
        self, dst_str: str, label_to_node: dict[str, ReadableNode]
    ) -> tuple | None:
        content_type = None
        label = None
        clean_dst = dst_str

        if "(" in clean_dst and ")" in clean_dst:
            paren_matches = re.findall(r"\(([^)]+)\)", clean_dst)
            if paren_matches:
                known_types = ["raw_text", "conversation_state", "variable", "json", "object"]
                for _i, match in enumerate(paren_matches):
                    if match in known_types and not content_type:
                        content_type = match
                        clean_dst = clean_dst.replace(f"({match})", "", 1)
                    elif not label:
                        label = match
                        clean_dst = clean_dst.replace(f"({match})", "", 1)

        clean_dst = clean_dst.strip()

        dst_node, dst_handle = self._parse_node_and_handle(clean_dst, label_to_node)

        if dst_node:
            return (dst_node, dst_handle, content_type, label)

        return None

    def _readable_diagram_to_dict(
        self, readable_diagram: ReadableDiagram, original_data: dict[str, Any]
    ) -> dict[str, Any]:
        nodes_list = []
        for node in readable_diagram.nodes:
            props = process_dotted_keys(node.props)
            props = NodeFieldMapper.map_import_fields(node.type, props)

            node_dict = build_node(
                id=node.id, type_=node.type, pos=node.position, label=node.label, **props
            )
            nodes_list.append(node_dict)

        nodes_dict = self._build_nodes_dict(nodes_list)

        arrows_dict = {}
        for arrow in readable_diagram.arrows:
            arrows_dict[arrow.id] = {
                "id": arrow.id,
                "source": create_handle_id(
                    arrow.source, arrow.source_handle or "default", HandleDirection.OUTPUT
                ),
                "target": create_handle_id(
                    arrow.target, arrow.target_handle or "default", HandleDirection.INPUT
                ),
                "data": arrow.data or {},
                "label": arrow.label,
            }

        handles_dict = self._extract_handles_dict(original_data)
        persons_dict = self._extract_persons_dict(original_data)

        return {
            "nodes": nodes_dict,
            "arrows": arrows_dict,
            "handles": handles_dict,
            "persons": persons_dict,
            "metadata": readable_diagram.metadata,
        }

    def _create_node_id(self, index: int, prefix: str = "node") -> str:
        return f"{prefix}_{index}"

    def _build_nodes_dict(self, nodes_list: list[dict[str, Any]]) -> dict[str, Any]:
        from dipeo.diagram_generated.conversions import (
            node_kind_to_domain_type,
        )
        from dipeo.domain.diagram.utils.shared_components import PositionCalculator

        position_calculator = PositionCalculator()
        nodes_dict = {}

        for index, node_data in enumerate(nodes_list):
            if "id" not in node_data:
                continue

            node_id = node_data["id"]
            node_type_str = node_data.get("type", "person_job")

            # Handle 'job' as alias for 'person_job'
            if node_type_str == "job":
                node_type_str = "person_job"

            try:
                node_type = node_kind_to_domain_type(node_type_str)
            except ValueError:
                logger.warning(f"Unknown node type '{node_type_str}', defaulting to 'person_job'")
                node_type = node_kind_to_domain_type("person_job")

            position = node_data.get("position")
            if not position:
                position = position_calculator.calculate_grid_position(index)

            exclude_fields = {"id", "type", "position", "handles", "arrows"}
            properties = {k: v for k, v in node_data.items() if k not in exclude_fields}

            nodes_dict[node_id] = {
                "id": node_id,
                "type": node_type_str.lower(),
                "position": position,
                "data": properties,
            }

        return nodes_dict

    def _parse_single_flow(
        self, src: str, dst: str | bool | int, label2id: dict[str, str], idx: int
    ) -> list[dict[str, Any]]:
        arrows = []

        dst_str = str(dst)

        content_type = None
        label = None
        clean_dst = dst_str.strip()

        if "(" in clean_dst:
            paren_matches = re.findall(r"\(([^)]+)\)", clean_dst)
            if paren_matches:
                known_types = ["raw_text", "conversation_state", "variable", "json", "object"]
                for match in paren_matches:
                    if match in known_types:
                        content_type = match
                        clean_dst = clean_dst.replace(f"({match})", "").strip()
                        break

        if "(" in clean_dst and ")" in clean_dst:
            start = clean_dst.find("(")
            end = clean_dst.find(")", start)
            if start != -1 and end != -1:
                label = clean_dst[start + 1 : end]
                clean_dst = clean_dst[:start].strip() + clean_dst[end + 1 :].strip()

        src_id, src_handle_from_split, src_label = HandleParser.parse_label_with_handle(
            src.strip(), label2id
        )
        dst_id, dst_handle_from_split, dst_label = HandleParser.parse_label_with_handle(
            clean_dst.strip(), label2id
        )

        src_handle = src_handle_from_split if src_handle_from_split else "default"
        dst_handle = dst_handle_from_split if dst_handle_from_split else "default"

        if src_id and dst_id:
            source_handle_id, target_handle_id = HandleParser.create_handle_ids(
                src_id, dst_id, src_handle, dst_handle
            )

            arrow_dict = ArrowDataProcessor.build_arrow_dict(
                f"arrow_{idx}",
                source_handle_id,
                target_handle_id,
                None,
                content_type,
                label,
            )

            arrows.append(arrow_dict)
        else:
            logger.warning(f"Could not find nodes for flow: {src_label} -> {dst_label}")

        return arrows

    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        readable_diagram = self._domain_to_readable_diagram(diagram)

        data = self._readable_diagram_to_export_dict(readable_diagram)

        return self.format(data)

    def _domain_to_readable_diagram(self, diagram: DomainDiagram) -> ReadableDiagram:
        nodes = []
        for n in diagram.nodes:
            node = ReadableNode(
                id=n.id,
                type=str(n.type).split(".")[-1].lower(),
                label=n.data.get("label") or n.id,
                position={"x": round(n.position.x), "y": round(n.position.y)},
                props={
                    k: v for k, v in n.data.items() if k != "label" and v not in (None, "", {}, [])
                },
            )
            nodes.append(node)

        arrows = []
        for a in diagram.arrows:
            s_node_id, s_handle, _ = parse_handle_id(a.source)
            t_node_id, t_handle, _ = parse_handle_id(a.target)

            arrow = ReadableArrow(
                id=a.id,
                source=s_node_id,
                target=t_node_id,
                source_handle=s_handle if s_handle != "default" else None,
                target_handle=t_handle if t_handle != "default" else None,
                label=a.label,
                data=a.data if a.data else None,
            )
            arrows.append(arrow)

        persons_data = None
        if diagram.persons:
            persons_data = []
            for p in diagram.persons:
                person_dict = {
                    "id": p.id,
                    "label": p.label,
                    "llm_config": {
                        "service": p.llm_config.service.value
                        if hasattr(p.llm_config.service, "value")
                        else str(p.llm_config.service),
                        "model": p.llm_config.model,
                        "api_key_id": p.llm_config.api_key_id,
                    },
                }
                if p.llm_config.system_prompt:
                    person_dict["llm_config"]["system_prompt"] = p.llm_config.system_prompt
                persons_data.append(person_dict)

        return ReadableDiagram(
            version="readable",
            nodes=nodes,
            arrows=arrows,
            persons=persons_data,
            metadata=diagram.metadata.model_dump(exclude_none=True) if diagram.metadata else None,
        )

    def _readable_diagram_to_export_dict(self, readable_diagram: ReadableDiagram) -> dict[str, Any]:
        id_to_label: dict[str, str] = {}
        for n in readable_diagram.nodes:
            id_to_label[n.id] = n.label

        nodes = []
        for n in readable_diagram.nodes:
            label = n.label

            if n.position and (n.position["x"] != 0 or n.position["y"] != 0):
                label_with_pos = f"{label} @({int(n.position['x'])},{int(n.position['y'])})"
            else:
                label_with_pos = label

            node_config = {"type": n.type} if n.type != "job" else {}
            if n.props:
                mapped_props = NodeFieldMapper.map_export_fields(n.type, n.props.copy())
                filtered_props = {
                    k: v for k, v in mapped_props.items() if v not in (None, "", {}, [])
                }
                node_config.update(filtered_props)

            if node_config:
                nodes.append({label_with_pos: node_config})
            else:
                nodes.append({label_with_pos: {}})

        flow = self._build_enhanced_flow(readable_diagram, id_to_label)

        persons = []
        if readable_diagram.persons:
            for person_data in readable_diagram.persons:
                person_dict = {}
                if "label" in person_data and "llm_config" in person_data:
                    config = person_data["llm_config"]
                    person_config = {
                        "service": config.get("service", "openai"),
                        "model": config.get("model", "gpt-4"),
                    }
                    if config.get("system_prompt"):
                        person_config["system_prompt"] = config["system_prompt"]
                    if config.get("api_key_id"):
                        person_config["api_key_id"] = config["api_key_id"]
                    person_dict[person_data["label"]] = person_config
                    persons.append(person_dict)

        out: dict[str, Any] = {"version": "readable"}
        if persons:
            out["persons"] = persons
        out["nodes"] = nodes
        if flow:
            out["flow"] = flow
        return out

    def _build_enhanced_flow(
        self, readable_diagram: ReadableDiagram, id_to_label: dict[str, str]
    ) -> list[str]:
        source_groups: dict[str, list] = {}

        for a in readable_diagram.arrows:
            source_label = id_to_label.get(a.source, a.source)

            if a.source_handle and a.source_handle not in ("output", "default"):
                if a.source_handle in ["condtrue", "condfalse"]:
                    source_key = source_label
                else:
                    source_key = f"{source_label}_{a.source_handle}"
            else:
                source_key = source_label

            if source_key not in source_groups:
                source_groups[source_key] = []

            target_str = self._build_flow_target_string(
                id_to_label.get(a.target, a.target),
                a.target_handle,
                a.source_handle,
                a.data.get("content_type") if a.data else None,
                a.label,
            )

            source_groups[source_key].append(target_str)

        flow = []
        for source_key, targets in source_groups.items():
            if len(targets) == 1:
                flow.append({source_key: targets[0]})
            else:
                flow.append({source_key: targets})

        return flow

    def _build_flow_target_string(
        self,
        target_label: str,
        target_handle: str | None,
        source_handle: str | None,
        content_type: str | None,
        label: str | None,
    ) -> str:
        parts = []

        if source_handle and source_handle in ["condtrue", "condfalse"]:
            parts.append(f'from "_{source_handle}"')

        parts.append(f'to "{target_label}"')

        if target_handle and target_handle not in ("input", "default", "_first"):
            parts.append(f'in "{target_handle}"')
        elif target_handle == "_first":
            parts.append('in "_first"')

        if content_type:
            parts.append(f'as "{content_type}"')

        if label:
            parts.append(f'naming "{label}"')

        return " ".join(parts)

    def detect_confidence(self, data: dict[str, Any]) -> float:
        if data.get("format") == "readable" or data.get("version") == "readable":
            return 0.95
        if "nodes" in data and "flow" in data:
            nodes = data.get("nodes", [])
            if isinstance(nodes, list) and nodes:
                first_node = nodes[0]
                if isinstance(first_node, dict) and len(first_node) == 1:
                    return 0.85
            return 0.7
        return 0.1

    def quick_match(self, content: str) -> bool:
        if "version: readable" in content or "format: readable" in content:
            return True
        return "nodes:" in content and "flow:" in content and "persons:" in content

    def parse(self, content: str) -> dict[str, Any]:
        return super().parse(content)

    def format(self, data: dict[str, Any]) -> str:
        return super().format(data)

    def _extract_handles_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        return data.get("handles", {})

    def _extract_persons_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        persons_data = data.get("persons", [])
        if isinstance(persons_data, list):
            return PersonExtractor.extract_from_list(persons_data)
        elif isinstance(persons_data, dict):
            return persons_data
        return {}

    def _apply_format_transformations(
        self, diagram_dict: dict[str, Any], original_data: dict[str, Any]
    ) -> dict[str, Any]:
        return diagram_dict
