from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import uuid
import io
from app.utils.gcs_client import gcs_client

router = APIRouter(prefix="/api", tags=["files"])

class UploadURLRequest(BaseModel):
    url: HttpUrl
    file_id: Optional[str] = None
    is_public: bool = False

class RenameRequest(BaseModel):
    new_file_id: str

class FileResponse(BaseModel):
    file_id: str
    object_path: str
    size: int
    is_public: bool

@router.post("/upload", response_model=dict)
async def upload_from_url(request: UploadURLRequest):
    try:
        file_id = request.file_id or str(uuid.uuid4())
        
        # Check if file already exists
        if gcs_client.file_exists(file_id, request.is_public):
            raise HTTPException(status_code=409, detail="File already exists")
        
        object_path, size = gcs_client.upload_from_url(
            str(request.url), 
            file_id, 
            request.is_public
        )
        
        return {
            "file_id": file_id,
            "object_path": object_path,
            "size": size,
            "is_public": request.is_public
        }
    
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload/direct", response_model=dict)
async def upload_direct(
    file: UploadFile = File(...),
    file_id: Optional[str] = Form(None),
    is_public: bool = Form(False)
):
    try:
        file_id = file_id or str(uuid.uuid4())
        
        # Check if file already exists
        if gcs_client.file_exists(file_id, is_public):
            raise HTTPException(status_code=409, detail="File already exists")
        
        file_data = await file.read()
        object_path, size = gcs_client.upload_from_file(file_data, file_id, is_public)
        
        return {
            "file_id": file_id,
            "object_path": object_path,
            "size": size,
            "is_public": is_public,
            "original_filename": file.filename
        }
    
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/files", response_model=List[FileResponse])
async def list_files(is_public: Optional[bool] = None):
    try:
        files = gcs_client.list_files(is_public)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.get("/download/{file_id}")
async def download_file(file_id: str, is_public: bool = False):
    try:
        file_data = gcs_client.download_file(file_id, is_public)
        
        def iterfile():
            yield file_data
        
        return StreamingResponse(
            io.BytesIO(file_data), 
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file_id}"}
        )
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.post("/rename/{file_id}", response_model=dict)
async def rename_file(file_id: str, request: RenameRequest, is_public: bool = False):
    try:
        # Check if source file exists
        if not gcs_client.file_exists(file_id, is_public):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check if target file already exists
        if gcs_client.file_exists(request.new_file_id, is_public):
            raise HTTPException(status_code=409, detail="Target filename already exists")
        
        new_object_path = gcs_client.rename_file(file_id, request.new_file_id, is_public)
        
        return {
            "old_file_id": file_id,
            "new_file_id": request.new_file_id,
            "object_path": new_object_path,
            "is_public": is_public
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rename failed: {str(e)}")

@router.post("/share/{file_id}", response_model=dict)
async def toggle_share(file_id: str, current_is_public: bool = False):
    try:
        # Check if file exists
        if not gcs_client.file_exists(file_id, current_is_public):
            raise HTTPException(status_code=404, detail="File not found")
        
        new_object_path, new_is_public = gcs_client.toggle_share(file_id, current_is_public)
        
        return {
            "file_id": file_id,
            "object_path": new_object_path,
            "was_public": current_is_public,
            "is_public": new_is_public
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Share toggle failed: {str(e)}")

@router.delete("/files/{file_id}")
async def delete_file(file_id: str, is_public: bool = False):
    try:
        success = gcs_client.delete_file(file_id, is_public)
        
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {"message": f"File {file_id} deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")