# Application service for diagram operations with high-level business logic.

import os
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dipeo.domain.diagram.services import (
    DiagramFormatService,
    DiagramOperationsService
)
from dipeo.domain.validators.diagram_validator import DiagramValidator
from dipeo.models import DiagramFormat

if TYPE_CHECKING:
    from dipeo.core.ports.diagram_port import DiagramPort


class DiagramService:

    def __init__(self, storage_service: "DiagramPort"):
        self._storage = storage_service
        # Initialize domain services
        self._operations_service = DiagramOperationsService()
        self._validator = DiagramValidator()
        self._format_service = DiagramFormatService()

    async def clone_diagram(
        self, source_id: str, new_name: str, new_description: str | None = None
    ) -> dict[str, Any]:
        """Clone a diagram using domain service for business logic."""
        try:
            # Load source diagram
            source_diagram = await self._storage.load_diagram(source_id)
            
            # Validate source diagram
            self._validator.validate_diagram(source_diagram)
            
            # Use domain service to clone
            cloned_diagram = self._operations_service.clone_diagram(
                diagram=source_diagram,
                new_name=new_name,
                new_description=new_description
            )
            
            # Persist cloned diagram
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
        imported = []
        failed = []

        try:
            files = await self._storage.list_diagrams()

            for file_info in files:
                if format_filter and file_info.get("format") != format_filter:
                    continue

                try:
                    diagram = await self._storage.load_diagram(file_info["id"])

                    imported.append(
                        {
                            "id": diagram.metadata.id,
                            "name": diagram.metadata.name,
                            "format": file_info.get("format", DiagramFormat.NATIVE),
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
        exported = []
        failed = []

        try:
            os.makedirs(export_path, exist_ok=True)

            bundle_metadata = {
                "export_date": datetime.utcnow().isoformat(),
                "diagram_count": len(diagram_ids),
                "diagrams": [],
            }

            for diagram_id in diagram_ids:
                try:
                    diagram = await self._storage.load_diagram(diagram_id)

                    # Use domain service for safe filename generation
                    safe_filename = self._operations_service.generate_safe_filename(
                        diagram.metadata.name, ".json"
                    )
                    export_file = os.path.join(export_path, safe_filename)

                    await self._storage.save_diagram_to_path(diagram, export_file)

                    # Use domain service to calculate statistics
                    stats = self._operations_service.calculate_diagram_statistics(diagram)
                    
                    exported_info = {
                        "id": diagram.metadata.id,
                        "name": diagram.metadata.name,
                        "file": export_file,
                        "nodes": stats["total_nodes"],
                        "arrows": stats["total_arrows"],
                        "complexity": stats["complexity_score"],
                    }

                    exported.append(exported_info)
                    bundle_metadata["diagrams"].append(exported_info)

                except Exception as e:
                    failed.append({"diagram_id": diagram_id, "error": str(e)})

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
