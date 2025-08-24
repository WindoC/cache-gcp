from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from typing import Union, Dict, Any
import json
from .crypto import crypto

def handle_encrypted_request(request_data: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    Handle encrypted request payload
    Returns decrypted data or original data if not encrypted
    """
    if isinstance(request_data, dict) and 'encrypted_payload' in request_data:
        try:
            decrypted = crypto.decrypt_payload(request_data['encrypted_payload'])
            if isinstance(decrypted, dict):
                return decrypted
            elif isinstance(decrypted, bytes):
                # Try to parse as JSON
                try:
                    return json.loads(decrypted.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    raise ValueError("Decrypted payload is not valid JSON")
            else:
                raise ValueError("Decrypted payload has unexpected type")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decrypt payload: {str(e)}")
    
    # Return original data if not encrypted
    return request_data if isinstance(request_data, dict) else {}

def create_encrypted_response(data: Dict[str, Any], should_encrypt: bool = True) -> Dict[str, Any]:
    """
    Create encrypted response if encryption is enabled
    Returns encrypted payload or original data
    """
    if should_encrypt:
        try:
            encrypted_payload = crypto.encrypt_payload(data)
            return {"encrypted_payload": encrypted_payload}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to encrypt response: {str(e)}")
    
    return data

def requires_encryption() -> bool:
    """
    Check if encryption is available (AES_KEY_HASH is set)
    """
    try:
        return crypto.key_hash is not None
    except:
        return False