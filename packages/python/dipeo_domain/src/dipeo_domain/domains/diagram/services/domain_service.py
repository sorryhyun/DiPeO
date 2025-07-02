"""Domain service for diagram operations with high-level business logic."""

import os
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dipeo_domain.models import DiagramFormat, DomainDiagram

if TYPE_CHECKING:
    from dipeo_core import SupportsDiagram


class DiagramStorageDomainService:
    """High-level domain service for diagram storage and management."""

    def __init__(self, storage_service: "SupportsDiagram"):
        """Initialize with required infrastructure service."""
        self._storage = storage_service

    async def clone_diagram(
        self, source_id: str, new_name: str, new_description: str | None = None
    ) -> dict[str, Any]:
        """Clone an existing diagram with a new name."""
        try:
            # Load source diagram
            source_diagram = await self._storage.load_diagram(source_id)

            # Create new metadata
            cloned_diagram = DomainDiagram(
                metadata=source_diagram.metadata.model_copy(
                    update={
                        "id": f"{new_name.lower().replace(' ', '-')}-{datetime.utcnow().timestamp():.0f}",
                        "name": new_name,
                        "description": new_description
                        or f"Cloned from {source_diagram.metadata.name}",
                        "createdAt": datetime.utcnow().isoformat(),
                        "updatedAt": datetime.utcnow().isoformat(),
                    }
                ),
                nodes=source_diagram.nodes,
                arrows=source_diagram.arrows,
                persons=source_diagram.persons,
                viewport=source_diagram.viewport,
            )

            # Save cloned diagram
            saved_id = await self._storage.save_diagram(cloned_diagram)

            return {
                "success": True,
                "diagram_id": saved_id,
                "source_id": source_id,
                "name": new_name,
                "created_at": cloned_diagram.metadata.created_at,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "source_id": source_id}

    async def batch_import(
        self, directory: str, format_filter: DiagramFormat | None = None
    ) -> dict[str, Any]:
        """Import multiple diagrams from a directory."""
        imported = []
        failed = []

        try:
            # List all diagram files in directory
            files = await self._storage.list_diagrams()

            for file_info in files:
                if format_filter and file_info.get("format") != format_filter:
                    continue

                try:
                    # Load and validate each diagram
                    diagram = await self._storage.load_diagram(file_info["id"])

                    imported.append(
                        {
                            "id": diagram.metadata.id,
                            "name": diagram.metadata.name,
                            "format": file_info.get("format", DiagramFormat.native),
                            "nodes": len(diagram.nodes),
                            "arrows": len(diagram.arrows),
                        }
                    )

                except Exception as e:
                    failed.append(
                        {
                            "file": file_info.get("path", file_info["id"]),
                            "error": str(e),
                        }
                    )

            return {
                "success": True,
                "imported_count": len(imported),
                "failed_count": len(failed),
                "imported": imported,
                "failed": failed,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "directory": directory}

    async def export_diagram_bundle(
        self, diagram_ids: list[str], export_path: str, include_metadata: bool = True
    ) -> dict[str, Any]:
        """Export multiple diagrams as a bundle."""
        exported = []
        failed = []

        try:
            os.makedirs(export_path, exist_ok=True)

            # Create bundle metadata
            bundle_metadata = {
                "export_date": datetime.utcnow().isoformat(),
                "diagram_count": len(diagram_ids),
                "diagrams": [],
            }

            for diagram_id in diagram_ids:
                try:
                    # Load diagram
                    diagram = await self._storage.load_diagram(diagram_id)

                    # Determine export filename
                    safe_name = "".join(
                        c for c in diagram.metadata.name if c.isalnum() or c in " -_"
                    )[:50]
                    export_file = os.path.join(export_path, f"{safe_name}.json")

                    # Save to export location
                    await self._storage.save_diagram_to_path(diagram, export_file)

                    exported_info = {
                        "id": diagram.metadata.id,
                        "name": diagram.metadata.name,
                        "file": export_file,
                        "nodes": len(diagram.nodes),
                        "arrows": len(diagram.arrows),
                    }

                    exported.append(exported_info)
                    bundle_metadata["diagrams"].append(exported_info)

                except Exception as e:
                    failed.append({"diagram_id": diagram_id, "error": str(e)})

            # Save bundle metadata if requested
            if include_metadata:
                metadata_file = os.path.join(export_path, "bundle_metadata.json")
                import json

                with open(metadata_file, "w") as f:
                    json.dump(bundle_metadata, f, indent=2)

            return {
                "success": True,
                "export_path": export_path,
                "exported_count": len(exported),
                "failed_count": len(failed),
                "exported": exported,
                "failed": failed,
                "metadata_file": metadata_file if include_metadata else None,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "export_path": export_path}

    async def analyze_diagram_complexity(self, diagram_id: str) -> dict[str, Any]:
        """Analyze the complexity of a diagram."""
        try:
            diagram = await self._storage.load_diagram(diagram_id)

            # Calculate various metrics
            node_types = {}
            for node in diagram.nodes:
                node_type = node.type
                node_types[node_type] = node_types.get(node_type, 0) + 1

            # Find start and end nodes
            start_nodes = [n for n in diagram.nodes if n.type == "start"]
            end_nodes = [n for n in diagram.nodes if n.type == "endpoint"]

            # Calculate edge metrics
            incoming_edges = {}
            outgoing_edges = {}
            for arrow in diagram.arrows:
                source = arrow.source
                target = arrow.target

                outgoing_edges[source] = outgoing_edges.get(source, 0) + 1
                incoming_edges[target] = incoming_edges.get(target, 0) + 1

            # Find nodes with high connectivity
            max_incoming = max(incoming_edges.values()) if incoming_edges else 0
            max_outgoing = max(outgoing_edges.values()) if outgoing_edges else 0

            # Identify potential issues
            issues = []
            if len(start_nodes) == 0:
                issues.append("No start node found")
            elif len(start_nodes) > 1:
                issues.append(f"Multiple start nodes found ({len(start_nodes)})")

            if len(end_nodes) == 0:
                issues.append("No endpoint node found")

            orphan_nodes = [
                n.id
                for n in diagram.nodes
                if n.id not in incoming_edges and n.id not in outgoing_edges
            ]
            if orphan_nodes:
                issues.append(f"Found {len(orphan_nodes)} orphan nodes")

            return {
                "success": True,
                "diagram_id": diagram_id,
                "metrics": {
                    "total_nodes": len(diagram.nodes),
                    "total_edges": len(diagram.arrows),
                    "node_types": node_types,
                    "start_nodes": len(start_nodes),
                    "end_nodes": len(end_nodes),
                    "max_incoming_edges": max_incoming,
                    "max_outgoing_edges": max_outgoing,
                    "persons_count": len(diagram.persons),
                },
                "issues": issues,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "diagram_id": diagram_id}

    async def validate_and_repair(
        self, diagram_id: str, auto_repair: bool = False
    ) -> dict[str, Any]:
        """Validate diagram structure and optionally repair issues."""
        try:
            diagram = await self._storage.load_diagram(diagram_id)

            validation_errors = []
            repairs_made = []

            # Check for orphan edges
            node_ids = {n.id for n in diagram.nodes}

            invalid_arrows = []
            for arrow in diagram.arrows:
                if arrow.source not in node_ids:
                    validation_errors.append(
                        f"Arrow references non-existent source node: {arrow.source}"
                    )
                    invalid_arrows.append(arrow)
                elif arrow.target not in node_ids:
                    validation_errors.append(
                        f"Arrow references non-existent target node: {arrow.target}"
                    )
                    invalid_arrows.append(arrow)

            # Check for duplicate node IDs
            seen_ids = set()
            duplicate_ids = []
            for node in diagram.nodes:
                if node.id in seen_ids:
                    duplicate_ids.append(node.id)
                    validation_errors.append(f"Duplicate node ID found: {node.id}")
                seen_ids.add(node.id)

            # Apply repairs if requested
            if auto_repair and (invalid_arrows or duplicate_ids):
                # Remove invalid arrows
                if invalid_arrows:
                    diagram.arrows = [
                        a for a in diagram.arrows if a not in invalid_arrows
                    ]
                    repairs_made.append(f"Removed {len(invalid_arrows)} invalid arrows")

                # Fix duplicate IDs by appending suffix
                if duplicate_ids:
                    id_counter = {}
                    for node in diagram.nodes:
                        if node.id in duplicate_ids:
                            count = id_counter.get(node.id, 0)
                            if count > 0:
                                new_id = f"{node.id}_{count}"
                                # Update arrows that reference this node
                                for arrow in diagram.arrows:
                                    if arrow.source == node.id:
                                        arrow.source = new_id
                                    if arrow.target == node.id:
                                        arrow.target = new_id
                                node.id = new_id
                                repairs_made.append(
                                    f"Renamed duplicate node {node.id} to {new_id}"
                                )
                            id_counter[node.id] = count + 1

                # Save repaired diagram
                await self._storage.save_diagram(diagram)

            return {
                "success": True,
                "diagram_id": diagram_id,
                "valid": len(validation_errors) == 0,
                "validation_errors": validation_errors,
                "repairs_made": repairs_made if auto_repair else [],
                "repaired": len(repairs_made) > 0,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "diagram_id": diagram_id}
