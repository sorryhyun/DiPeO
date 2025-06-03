from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel
import yaml

from ...services.file_service import FileService
from ...services.diagram_service import DiagramService
from ...utils.dependencies import get_file_service, get_diagram_service

router = APIRouter(prefix="/api", tags=["files"])


class SaveDiagramRequest(BaseModel):
    diagram: Dict[str, Any]
    filename: str
    format: str  # "json" or "yaml"


class ImportYamlRequest(BaseModel):
    yaml: str


class ExportYamlRequest(BaseModel):
    diagram: Dict[str, Any]


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    target_path: Optional[str] = None,
    file_service: FileService = Depends(get_file_service)
):
    """Upload a file to the server."""
    try:
        content = await file.read()
        result = await file_service.save_file(
            content=content,
            filename=file.filename,
            target_path=target_path
        )
        
        return {
            "success": True,
            "path": result["path"],
            "size": result["size"],
            "message": "File uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_diagram(
    request: SaveDiagramRequest,
    file_service: FileService = Depends(get_file_service)
):
    """Save diagram to the diagrams directory."""
    try:
        # Determine file path in diagrams directory
        filename = request.filename
        if not filename.endswith(('.json', '.yaml', '.yml')):
            if request.format == "yaml":
                filename += ".yaml"
            else:
                filename += ".json"
        
        # Save to diagrams directory (which is now under files/)
        saved_path = await file_service.write(
            path=f"../diagrams/{filename}",
            content=request.diagram,
            format=request.format
        )
        
        return {
            "success": True,
            "message": f"Diagram saved to {saved_path}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-yaml")
async def import_yaml(
    request: ImportYamlRequest,
    diagram_service: DiagramService = Depends(get_diagram_service)
):
    """Import YAML and convert to diagram format."""
    try:
        diagram = diagram_service.import_yaml(request.yaml)
        return diagram
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/yaml_diagram")
async def export_yaml_diagram(
    request: ExportYamlRequest
):
    """Export diagram to YAML format."""
    try:
        # Convert diagram to YAML
        yaml_content = yaml.dump(
            request.diagram,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            indent=2
        )
        
        return {
            "success": True,
            "yaml": yaml_content,
            "message": "Diagram exported to YAML format"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))