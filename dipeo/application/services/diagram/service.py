"""Application service for diagram operations with high-level business logic."""

import os
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dipeo.models import DiagramFormat, DomainDiagram

if TYPE_CHECKING:
    from dipeo.core.ports.diagram_port import DiagramPort


class DiagramService:
    """High-level application service for diagram operations and management."""

    def __init__(self, storage_service: "DiagramPort"):
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