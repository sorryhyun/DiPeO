from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import Optional

from ...services.unified_file_service import UnifiedFileService
from ...utils.dependencies import get_unified_file_service

router = APIRouter(prefix="/api", tags=["files"])


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    target_path: Optional[str] = None,
    file_service: UnifiedFileService = Depends(get_unified_file_service)
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