from fastapi import Request, HTTPException
from typing import Optional, Dict, Any
import asyncio

async def parse_large_form(request: Request) -> Dict[str, Any]:
    """
    Parse multipart form with increased size limit for encrypted file uploads
    """
    try:
        # Set max part size to 250MB to handle encrypted files
        max_bytes = 250 * 1024 * 1024
        form = await request.form(max_part_size=max_bytes)
        return dict(form)
    except Exception as e:
        if "maximum size" in str(e).lower():
            raise HTTPException(
                status_code=413, 
                detail="File too large. Maximum size is 250MB for encrypted uploads."
            )
        raise HTTPException(status_code=400, detail=f"Form parsing failed: {str(e)}")

class LargeFormData:
    """Dependency class for handling large multipart form data"""
    
    def __init__(self, request: Request):
        self.request = request
        self._form_data = None
    
    async def get_form(self) -> Dict[str, Any]:
        if self._form_data is None:
            self._form_data = await parse_large_form(self.request)
        return self._form_data
    
    async def get_file(self, field_name: str = "file"):
        form_data = await self.get_form()
        return form_data.get(field_name)
    
    async def get_field(self, field_name: str, default: Any = None):
        form_data = await self.get_form()
        return form_data.get(field_name, default)