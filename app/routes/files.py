from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.responses import StreamingResponse, Response, JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Union, Dict, Any
import uuid
import io
import os
from urllib.parse import urlparse
from app.utils.gcs_client import gcs_client
from app.utils.auth import get_current_user, get_optional_current_user
from app.utils.encryption_middleware import handle_encrypted_request, create_encrypted_response, requires_encryption
from app.utils.form_parser import parse_large_form

router = APIRouter(prefix="/api", tags=["files"])

class UploadURLRequest(BaseModel):
    url: HttpUrl
    file_id: Optional[str] = None
    is_public: bool = False

class EncryptedRequest(BaseModel):
    encrypted_payload: str

class RenameRequest(BaseModel):
    new_file_id: str

class FileResponse(BaseModel):
    file_id: str
    object_path: str
    size: int
    is_public: bool

@router.post("/upload/url", response_model=dict)
async def upload_from_url(request: Union[UploadURLRequest, EncryptedRequest], current_user: dict = Depends(get_current_user)):
    try:
        # Handle encrypted request
        if isinstance(request, EncryptedRequest):
            decrypted_data = handle_encrypted_request(request.dict())
            url = decrypted_data.get('url')
            file_id = decrypted_data.get('file_id')
            is_public = decrypted_data.get('is_public', False)
        else:
            url = str(request.url)
            file_id = request.file_id
            is_public = request.is_public
        
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        # Priority: API input -> filename from URL -> UUID
        if file_id:
            final_file_id = file_id
        else:
            # Extract filename from URL
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            # Use filename if it exists and is not empty, otherwise use UUID
            final_file_id = filename if filename and filename != '/' else str(uuid.uuid4())
        
        # Check if file already exists
        if gcs_client.file_exists(final_file_id, True) or gcs_client.file_exists(final_file_id, False):
            raise HTTPException(status_code=409, detail="File already exists")
        
        object_path, size = gcs_client.upload_from_url(
            url, 
            final_file_id, 
            is_public
        )
        
        response_data = {
            "file_id": final_file_id,
            "object_path": object_path,
            "size": size,
            "is_public": is_public
        }
        
        # Return encrypted response if request was encrypted and encryption is available
        should_encrypt = isinstance(request, EncryptedRequest) and requires_encryption()
        return create_encrypted_response(response_data, should_encrypt)
    
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/upload/direct", response_model=dict)
async def upload_direct(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Parse form with large size limit
        form_data = await parse_large_form(request)
        
        # Extract form fields
        file = form_data.get('file')
        file_id = form_data.get('file_id')
        is_public = form_data.get('is_public')
        encrypted_payload = form_data.get('encrypted_payload')
        
        # Debug logging
        print(f"DEBUG: encrypted_payload present: {encrypted_payload is not None}")
        print(f"DEBUG: file present: {file is not None}")
        if encrypted_payload:
            print(f"DEBUG: encrypted_payload length: {len(encrypted_payload)}")
            
        # Handle encrypted request
        if encrypted_payload:
            decrypted_data = handle_encrypted_request({"encrypted_payload": encrypted_payload})
            # For encrypted uploads, file data is base64 encoded in the payload
            file_data_b64 = decrypted_data.get('file_data')
            if not file_data_b64:
                raise HTTPException(status_code=400, detail="Missing file_data in encrypted payload")
            
            import base64
            file_data = base64.b64decode(file_data_b64)
            final_file_id = decrypted_data.get('file_id')
            is_public_final = decrypted_data.get('is_public', False)
            original_filename = decrypted_data.get('filename')
        else:
            if not file:
                raise HTTPException(status_code=400, detail="File is required")
            file_data = await file.read()
            final_file_id = file_id
            is_public_final = is_public if is_public is not None else False
            original_filename = file.filename if hasattr(file, 'filename') else None
        
        # Priority: API input -> original filename -> UUID
        if not final_file_id:
            final_file_id = original_filename if original_filename else str(uuid.uuid4())
        
        # Check if file already exists
        if gcs_client.file_exists(final_file_id, True) or gcs_client.file_exists(final_file_id, False):
            raise HTTPException(status_code=409, detail="File already exists")
        
        object_path, size = gcs_client.upload_from_file(file_data, final_file_id, is_public_final)
        
        response_data = {
            "file_id": final_file_id,
            "object_path": object_path,
            "size": size,
            "is_public": is_public_final,
            "original_filename": original_filename
        }
        
        # Return encrypted response if request was encrypted and encryption is available
        should_encrypt = encrypted_payload is not None and requires_encryption()
        return create_encrypted_response(response_data, should_encrypt)
    
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/files")
async def list_files(
    is_public: Optional[bool] = None, 
    encrypted: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        files = gcs_client.list_files(is_public)
        response_data = files
        
        # Return encrypted response if requested and encryption is available
        should_encrypt = encrypted is True and requires_encryption()
        if should_encrypt:
            return create_encrypted_response({"files": response_data}, should_encrypt)
        else:
            return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.api_route("/download/private/{file_id}", methods=["GET", "HEAD"])
async def download_private_file(
    file_id: str, 
    request: Request, 
    encrypted: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Download private file - requires authentication"""
    try:
        # For HEAD requests, only get file info without downloading
        if request.method == "HEAD":
            file_info = gcs_client.get_file_info(file_id, is_public=False)
            return Response(
                headers={
                    "Content-Length": str(file_info['size']),
                    "Content-Type": file_info.get('content_type', 'application/octet-stream'),
                    "Content-Disposition": f"attachment; filename={file_id}"
                }
            )
        
        # For GET requests, download and stream the file
        file_data = gcs_client.download_file(file_id, is_public=False)
        
        # If encryption is requested and available, return encrypted response
        should_encrypt = encrypted is True and requires_encryption()
        if should_encrypt:
            import base64
            file_data_b64 = base64.b64encode(file_data).decode()
            response_data = {
                "file_id": file_id,
                "file_data": file_data_b64,
                "size": len(file_data)
            }
            encrypted_response = create_encrypted_response(response_data, should_encrypt)
            return JSONResponse(content=encrypted_response)
        else:
            # Return normal file stream
            return StreamingResponse(
                io.BytesIO(file_data), 
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={file_id}"}
            )
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.api_route("/download/public/{file_id}", methods=["GET", "HEAD"])
async def download_public_file(file_id: str, request: Request):
    """Download public file - no authentication required"""
    try:
        # For HEAD requests, only get file info without downloading
        if request.method == "HEAD":
            file_info = gcs_client.get_file_info(file_id, is_public=True)
            return Response(
                headers={
                    "Content-Length": str(file_info['size']),
                    "Content-Type": file_info.get('content_type', 'application/octet-stream'),
                    "Content-Disposition": f"attachment; filename={file_id}"
                }
            )
        
        # For GET requests, download and stream the file
        file_data = gcs_client.download_file(file_id, is_public=True)
        
        return StreamingResponse(
            io.BytesIO(file_data), 
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file_id}"}
        )
    
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

# Keep the old endpoint for backward compatibility (deprecated)
@router.api_route("/download/{file_id}", methods=["GET", "HEAD"])
async def download_file(file_id: str, request: Request, is_public: bool = False, current_user: Optional[dict] = Depends(get_optional_current_user)):
    # For private files, require authentication
    if not is_public and not current_user:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required for private files"
        )
    
    try:
        # For HEAD requests, only get file info without downloading
        if request.method == "HEAD":
            file_info = gcs_client.get_file_info(file_id, is_public)
            return Response(
                headers={
                    "Content-Length": str(file_info['size']),
                    "Content-Type": file_info.get('content_type', 'application/octet-stream'),
                    "Content-Disposition": f"attachment; filename={file_id}"
                }
            )
        
        # For GET requests, download and stream the file
        file_data = gcs_client.download_file(file_id, is_public)
        
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
async def rename_file(file_id: str, request: RenameRequest, is_public: bool = False, current_user: dict = Depends(get_current_user)):
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
async def toggle_share(file_id: str, current_is_public: bool = False, current_user: dict = Depends(get_current_user)):
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
async def delete_file(file_id: str, is_public: bool = False, current_user: dict = Depends(get_current_user)):
    try:
        success = gcs_client.delete_file(file_id, is_public)
        
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {"message": f"File {file_id} deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")