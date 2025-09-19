"""Processor to deduplicate read file nodes in diagrams."""

import time
from collections import defaultdict
from typing import Any, Optional

from ..base import BaseProcessor, ChangeType, ProcessingChange, ProcessingReport
from ..config import ReadDeduplicatorConfig


class ReadNodeDeduplicator(BaseProcessor):
    """
    Removes duplicate read file nodes from the diagram.

    When the same file is read multiple times, this processor:
    - Keeps the first read node for each file
    - Removes duplicate read nodes
    - Updates connections to route through the kept node
    """

    def __init__(self, config: Optional[ReadDeduplicatorConfig] = None):
        """Initialize with configuration."""
        self.dedup_config = config or ReadDeduplicatorConfig()
        # Pass a dict to the base class, but keep our typed config separate
        super().__init__({"enabled": self.dedup_config.enabled})

    @property
    def name(self) -> str:
        """Return processor name."""
        return "ReadNodeDeduplicator"

    def process(self, diagram: dict[str, Any]) -> tuple[dict[str, Any], ProcessingReport]:
        """
        Process diagram to remove duplicate read nodes.

        Args:
            diagram: The diagram to process

        Returns:
            Tuple of (processed diagram, report)
        """
        start_time = time.time()
        report = ProcessingReport(processor_name=self.name)

        # Check applicability
        if not self.is_applicable(diagram):
            return diagram, report

        try:
            # Clone diagram for processing
            processed = self._clone_diagram(diagram)

            # Find duplicate read nodes
            duplicates = self._find_duplicate_read_nodes(processed["nodes"])

            if not duplicates:
                # No duplicates found
                report.processing_time_ms = (time.time() - start_time) * 1000
                return diagram, report

            # Process each set of duplicates
            for _file_path, nodes in duplicates.items():
                if len(nodes) <= 1:
                    continue

                # Determine which node to keep
                kept_node = nodes[0] if self.dedup_config.preserve_first else nodes[-1]
                nodes_to_remove = [n for n in nodes if n["label"] != kept_node["label"]]

                # Remove duplicate nodes and update connections
                for node_to_remove in nodes_to_remove:
                    self._remove_and_reroute_node(processed, node_to_remove, kept_node, report)

            # Clean up any orphaned connections
            self._clean_orphaned_connections(processed, report)

            # Add metadata about deduplication if configured
            if self.dedup_config.update_metadata and duplicates:
                self._add_deduplication_metadata(processed, duplicates, report)

        except Exception as e:
            report.error = f"Error during deduplication: {e!s}"
            return diagram, report

        finally:
            report.processing_time_ms = (time.time() - start_time) * 1000

        return processed, report

    def _find_duplicate_read_nodes(
        self, nodes: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Find all duplicate read nodes grouped by file path.

        Args:
            nodes: List of nodes to analyze

        Returns:
            Dictionary mapping file path to list of duplicate nodes
        """
        read_nodes_by_file = defaultdict(list)

        for node in nodes:
            # Check if this is a read node
            if node.get("type") == "db" and node.get("props", {}).get("operation") == "read":
                file_path = node.get("props", {}).get("file")
                if file_path:
                    read_nodes_by_file[file_path].append(node)

        # Filter to only include actual duplicates
        duplicates = {
            file_path: nodes for file_path, nodes in read_nodes_by_file.items() if len(nodes) > 1
        }

        return duplicates

    def _remove_and_reroute_node(
        self,
        diagram: dict[str, Any],
        node_to_remove: dict[str, Any],
        target_node: dict[str, Any],
        report: ProcessingReport,
    ) -> None:
        """
        Remove a node and reroute its connections to target node.

        Args:
            diagram: The diagram being processed
            node_to_remove: Node to remove
            target_node: Node to route connections to
            report: Report to update with changes
        """
        removed_label = node_to_remove["label"]
        target_label = target_node["label"]

        # Remove the node
        diagram["nodes"] = [n for n in diagram["nodes"] if n["label"] != removed_label]

        # Record the removal
        report.add_change(
            ProcessingChange(
                change_type=ChangeType.NODE_REMOVED,
                description=f"Removed duplicate read node for file: {node_to_remove.get('props', {}).get('file')}",
                target=removed_label,
                details={
                    "file_path": node_to_remove.get("props", {}).get("file"),
                    "replaced_by": target_label,
                },
            )
        )

        # Update connections
        if "connections" in diagram:
            connections_to_update = []
            connections_to_remove = []

            for conn in diagram["connections"]:
                # If connection goes FROM removed node, reroute from target
                if conn.get("from") == removed_label:
                    # Check if this would create a self-loop
                    if conn.get("to") != target_label:
                        new_conn = conn.copy()
                        new_conn["from"] = target_label
                        connections_to_update.append((conn, new_conn))
                    else:
                        connections_to_remove.append(conn)

                # If connection goes TO removed node, reroute to target
                elif conn.get("to") == removed_label:
                    # Check if this would create a self-loop
                    if conn.get("from") != target_label:
                        new_conn = conn.copy()
                        new_conn["to"] = target_label
                        connections_to_update.append((conn, new_conn))
                    else:
                        connections_to_remove.append(conn)

            # Apply connection updates
            for old_conn, new_conn in connections_to_update:
                diagram["connections"].remove(old_conn)

                # Check if this connection already exists
                existing = any(
                    c.get("from") == new_conn["from"] and c.get("to") == new_conn["to"]
                    for c in diagram["connections"]
                )

                if not existing:
                    diagram["connections"].append(new_conn)
                    report.add_change(
                        ProcessingChange(
                            change_type=ChangeType.CONNECTION_MODIFIED,
                            description="Rerouted connection through deduplicated node",
                            target=f"{new_conn['from']} -> {new_conn['to']}",
                            details={
                                "original": f"{old_conn['from']} -> {old_conn['to']}",
                                "updated": f"{new_conn['from']} -> {new_conn['to']}",
                            },
                        )
                    )
                else:
                    report.add_change(
                        ProcessingChange(
                            change_type=ChangeType.CONNECTION_REMOVED,
                            description="Removed redundant connection after deduplication",
                            target=f"{old_conn['from']} -> {old_conn['to']}",
                            details={"reason": "connection already exists after rerouting"},
                        )
                    )

            # Remove self-loops and marked connections
            for conn in connections_to_remove:
                if conn in diagram["connections"]:
                    diagram["connections"].remove(conn)
                    report.add_change(
                        ProcessingChange(
                            change_type=ChangeType.CONNECTION_REMOVED,
                            description="Removed self-loop connection",
                            target=f"{conn['from']} -> {conn['to']}",
                            details={"reason": "self-loop after deduplication"},
                        )
                    )

    def _clean_orphaned_connections(
        self, diagram: dict[str, Any], report: ProcessingReport
    ) -> None:
        """
        Remove connections that reference non-existent nodes.

        Args:
            diagram: The diagram being processed
            report: Report to update with changes
        """
        if "connections" not in diagram:
            return

        # Get all valid node labels
        valid_labels = {node["label"] for node in diagram.get("nodes", [])}

        # Find and remove orphaned connections
        orphaned = []
        for conn in diagram["connections"]:
            if conn.get("from") not in valid_labels or conn.get("to") not in valid_labels:
                orphaned.append(conn)

        for conn in orphaned:
            diagram["connections"].remove(conn)
            report.add_change(
                ProcessingChange(
                    change_type=ChangeType.CONNECTION_REMOVED,
                    description="Removed orphaned connection",
                    target=f"{conn.get('from', '?')} -> {conn.get('to', '?')}",
                    details={"reason": "references non-existent node"},
                )
            )

    def _add_deduplication_metadata(
        self,
        diagram: dict[str, Any],
        duplicates: dict[str, list[dict[str, Any]]],
        report: ProcessingReport,
    ) -> None:
        """
        Add metadata about deduplication to the diagram.

        Args:
            diagram: The diagram being processed
            duplicates: Map of file paths to duplicate nodes
            report: Report to update with changes
        """
        if "metadata" not in diagram:
            diagram["metadata"] = {}

        dedup_info = {
            "files_deduplicated": len(duplicates),
            "total_nodes_removed": sum(len(nodes) - 1 for nodes in duplicates.values()),
            "deduplicated_files": {
                file_path: {
                    "original_count": len(nodes),
                    "kept_node": nodes[0]["label"]
                    if self.dedup_config.preserve_first
                    else nodes[-1]["label"],
                    "removed_nodes": [
                        n["label"]
                        for n in nodes
                        if n["label"]
                        != (
                            nodes[0]["label"]
                            if self.dedup_config.preserve_first
                            else nodes[-1]["label"]
                        )
                    ],
                }
                for file_path, nodes in duplicates.items()
            },
        }

        diagram["metadata"]["deduplication"] = dedup_info

        report.add_change(
            ProcessingChange(
                change_type=ChangeType.METADATA_UPDATED,
                description="Added deduplication metadata",
                target="metadata.deduplication",
                details=dedup_info,
            )
        )
