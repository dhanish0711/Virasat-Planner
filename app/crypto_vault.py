import os
import re
import hashlib
import uuid
from pathlib import Path
from typing import Tuple
from cryptography.fernet import Fernet
from fastapi import HTTPException, status
from app.config import VAULT_ENCRYPTION_KEY, VAULT_DIR, VAULT_MAX_UPLOAD_BYTES, ALLOWED_VAULT_EXTENSIONS

fernet = Fernet(VAULT_ENCRYPTION_KEY)

DANGEROUS_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".bash", ".ps1", ".vbs", ".js", ".mjs",
    ".php", ".py", ".pyw", ".pl", ".cgi", ".jar", ".msi", ".dll", ".scr",
    ".html", ".htm", ".xhtml", ".svg"
}

def sanitize_vault_filename(filename: str) -> str:
    """Sanitize original filename to prevent path traversal and unsafe characters."""
    clean_name = Path(filename).name
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_name)
    if not clean_name or clean_name == ".":
        clean_name = f"vault_doc_{uuid.uuid4().hex[:8]}.pdf"
    return clean_name

def validate_vault_file(filename: str, file_bytes: bytes):
    """Validate file size and extension against security rules."""
    size = len(file_bytes)
    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )
    if size > VAULT_MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum vault upload size of {VAULT_MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
        )

    ext = Path(filename).suffix.lower()
    if ext in DANGEROUS_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security rejection: Uploading executable or script files ('{ext}') to the vault is strictly forbidden."
        )
    if ext not in ALLOWED_VAULT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_VAULT_EXTENSIONS))}."
        )

def encrypt_and_save_file(file_bytes: bytes, original_filename: str) -> Tuple[str, str, int]:
    """
    Encrypts file bytes using Fernet specification:
    - Cipher: AES-128 in CBC mode with PKCS7 padding
    - Authentication: HMAC using SHA-256
    - Key: 256-bit compound key (128-bit encryption + 128-bit signing)
    Returns: (stored_abs_path, sha256_checksum, original_size_bytes)
    """
    validate_vault_file(original_filename, file_bytes)
    safe_name = sanitize_vault_filename(original_filename)

    # 1. Compute SHA-256 hash of original unencrypted bytes for integrity checking
    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    original_size = len(file_bytes)
    
    # 2. Encrypt bytes using Fernet
    encrypted_data = fernet.encrypt(file_bytes)
    
    # 3. Generate secure random uuid filename with .enc extension
    unique_filename = f"{uuid.uuid4().hex}_{Path(safe_name).stem}.enc"
    dest_path = VAULT_DIR / unique_filename
    
    # 4. Write encrypted payload
    dest_path.write_bytes(encrypted_data)
    
    return str(dest_path), sha256_hash, original_size

def decrypt_vault_file(encrypted_file_path: str, expected_sha256: str = None) -> bytes:
    """
    Reads encrypted file from disk and decrypts it back to original bytes.
    Validates HMAC signature and optional SHA-256 integrity checksum.
    """
    path = Path(encrypted_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Encrypted vault file not found: {encrypted_file_path}")
        
    encrypted_data = path.read_bytes()
    decrypted_bytes = fernet.decrypt(encrypted_data)
    
    if expected_sha256:
        actual_hash = hashlib.sha256(decrypted_bytes).hexdigest()
        if actual_hash != expected_sha256:
            raise ValueError(f"Integrity check failed: Expected {expected_sha256}, got {actual_hash}")
            
    return decrypted_bytes

def delete_vault_file(encrypted_file_path: str):
    """Safely removes encrypted file from vault storage on rollback or deletion."""
    try:
        path = Path(encrypted_file_path)
        if path.exists() and path.is_file():
            path.unlink()
    except Exception:
        pass

def audit_vault_integrity() -> dict:
    """
    Audits the encrypted vault directory, verifying file counts, encryption signatures, and key validity.
    Returns status 'SECURE', 'DEGRADED', or 'FAILED'.
    """
    files = list(VAULT_DIR.glob("*.enc"))
    healthy_count = 0
    corrupted_count = 0
    total_bytes_stored = 0

    for f in files:
        try:
            total_bytes_stored += f.stat().st_size
            data = f.read_bytes()
            fernet.decrypt(data) # test decryption & HMAC verification
            healthy_count += 1
        except Exception:
            corrupted_count += 1

    has_env_key = bool(os.getenv("VAULT_SECRET_KEY"))

    if corrupted_count > 0:
        vault_status = "DEGRADED" if healthy_count > 0 else "FAILED"
    else:
        vault_status = "SECURE"

    return {
        "status": vault_status,
        "encryption_standard": "AES-128-CBC with PKCS7 padding & HMAC-SHA256 (Fernet 256-bit compound key)",
        "cipher": "AES-128-CBC",
        "mac": "HMAC-SHA256",
        "total_files": len(files),
        "verified_healthy_files": healthy_count,
        "corrupted_or_tampered_files": corrupted_count,
        "total_vault_storage_bytes": total_bytes_stored,
        "key_source": "VAULT_SECRET_KEY environment variable" if has_env_key else "data/vault.key local file (dev fallback)"
    }
