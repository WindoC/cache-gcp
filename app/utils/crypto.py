import base64
import json
import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Union, Dict, Any

class AESCrypto:
    """AES-GCM encryption/decryption utility for end-to-end encryption"""
    
    def __init__(self, key_hash: str = None):
        """Initialize with AES key hash from environment or parameter"""
        self.key_hash = key_hash or os.getenv('AES_KEY_HASH')
        if not self.key_hash:
            raise ValueError("AES_KEY_HASH environment variable not set")
    
    def _derive_key_from_hash(self, key_hash: str) -> bytes:
        """Derive 32-byte AES key from SHA256 hash"""
        # Use the hash as-is if it's already 64 hex chars (SHA256)
        if len(key_hash) == 64:
            return bytes.fromhex(key_hash)[:32]  # Take first 32 bytes
        else:
            # Hash the provided string to get consistent 32 bytes
            return hashlib.sha256(key_hash.encode()).digest()
    
    def encrypt_payload(self, data: Union[Dict[Any, Any], str, bytes]) -> str:
        """
        Encrypt data using AES-GCM
        Returns base64-encoded encrypted payload with nonce
        """
        try:
            # Convert data to JSON string if it's a dict
            if isinstance(data, dict):
                plaintext = json.dumps(data).encode()
            elif isinstance(data, str):
                plaintext = data.encode()
            elif isinstance(data, bytes):
                plaintext = data
            else:
                plaintext = str(data).encode()
            
            # Derive key from hash
            key = self._derive_key_from_hash(self.key_hash)
            
            # Generate random nonce
            nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
            
            # Encrypt
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            
            # Combine nonce + ciphertext and base64 encode
            encrypted_data = nonce + ciphertext
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt_payload(self, encrypted_data: str) -> Union[Dict[Any, Any], bytes]:
        """
        Decrypt base64-encoded AES-GCM payload
        Returns decrypted data (dict if JSON, bytes otherwise)
        """
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]
            
            # Derive key from hash
            key = self._derive_key_from_hash(self.key_hash)
            
            # Decrypt
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            # Try to parse as JSON, return bytes if not valid JSON
            try:
                return json.loads(plaintext.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                return plaintext
                
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def is_encrypted_request(self, data: Any) -> bool:
        """Check if request data appears to be encrypted"""
        if isinstance(data, dict) and 'encrypted_payload' in data:
            return True
        return False

# Global crypto instance
crypto = AESCrypto()