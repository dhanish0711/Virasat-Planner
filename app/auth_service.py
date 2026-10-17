"""
Authentication and Role-Based Access Control (RBAC) Service
Provides:
- PBKDF2-HMAC-SHA256 salted password hashing (600,000 rounds) & verification
- Cryptographically signed HMAC-SHA256 session tokens with expiration
- In-memory rate limiting against brute force attempts
- Role-based and family-scoped authorization dependencies for FastAPI endpoints
"""

import os
import hmac
import hashlib
import base64
import json
import time
from typing import Optional, Dict, Any
from collections import defaultdict
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, AUTH_TOKEN_EXPIRE_HOURS, ENVIRONMENT
from app.database import get_db
from app.auth import RolePermissions, check_permission

security_scheme = HTTPBearer(auto_error=False)

# In-memory rate limiter for failed login attempts: IP -> list of timestamps
_failed_attempts: Dict[str, list] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
MAX_FAILED_ATTEMPTS = 5

def record_failed_attempt(client_ip: str):
    """Record a failed login attempt for rate limiting."""
    now = time.time()
    _failed_attempts[client_ip] = [t for t in _failed_attempts[client_ip] if now - t < RATE_LIMIT_WINDOW]
    _failed_attempts[client_ip].append(now)

def is_rate_limited(client_ip: str) -> bool:
    """Check if the client has exceeded the failed attempt threshold."""
    now = time.time()
    _failed_attempts[client_ip] = [t for t in _failed_attempts[client_ip] if now - t < RATE_LIMIT_WINDOW]
    return len(_failed_attempts[client_ip]) >= MAX_FAILED_ATTEMPTS

def reset_failed_attempts(client_ip: str):
    """Reset failed attempts upon successful login."""
    if client_ip in _failed_attempts:
        del _failed_attempts[client_ip]

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 600,000 rounds and a 16-byte random salt."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 600000)
    return f"{salt.hex()}:{dk.hex()}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verify plain password against stored salt:hash using constant-time comparison."""
    try:
        salt_hex, hash_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        
        # Check rounds - support both legacy 100k and upgraded 600k for compatibility
        # If hash length matches 32 bytes (64 hex characters)
        dk = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 600000)
        if hmac.compare_digest(dk, expected_hash):
            return True
        # Fallback to 100,000 rounds for legacy accounts
        dk_legacy = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(dk_legacy, expected_hash)
    except Exception:
        return False

def create_session_token(user_id: int, username: str, role: str, profile_id: Optional[int] = None) -> str:
    """Generate a signed, tamper-evident session token."""
    expire_time = int(time.time()) + (AUTH_TOKEN_EXPIRE_HOURS * 3600)
    payload = {
        "uid": user_id,
        "sub": username,
        "role": role,
        "pid": profile_id,
        "exp": expire_time
    }
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode('ascii').rstrip('=')
    
    # Sign payload
    signature = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('ascii'), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('ascii').rstrip('=')
    return f"{payload_b64}.{sig_b64}"

def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify session token signature and expiration."""
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts
        
        # Verify signature
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('ascii'), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('ascii').rstrip('=')
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None
        
        # Decode payload (add padding back)
        padding = '=' * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode('utf-8')
        payload = json.loads(payload_json)
        
        # Check expiration
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None

def extract_token_from_request(request: Request, creds: Optional[HTTPAuthorizationCredentials], allow_query: bool = False) -> Optional[str]:
    """Extract auth token from Authorization header or cookie, or optional query param for direct downloads."""
    if creds and creds.credentials:
        return creds.credentials
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    cookie_token = request.cookies.get("virasat_auth_token")
    if cookie_token:
        return cookie_token
    if allow_query:
        query_token = request.query_params.get("token")
        if query_token:
            return query_token
    return None

async def get_current_user_optional(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[Any]:
    """Get currently authenticated user if token present and valid, otherwise None."""
    token = extract_token_from_request(request, creds, allow_query=True)
    if not token:
        return None
    payload = verify_session_token(token)
    if not payload:
        return None
    
    from app.models import User
    user = db.query(User).filter(User.id == payload.get("uid")).first()
    return user

async def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """Enforce authentication. Raises 401 if not logged in."""
    user = await get_current_user_optional(request, creds, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with your family credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

def require_role(allowed_roles: list):
    """Factory for endpoint role-based access control."""
    async def role_checker(user = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for role '{user.role}'. Required one of: {', '.join(allowed_roles)}."
            )
        return user
    return role_checker

def verify_family_access(user: Any, target_profile_id: int, required_action: str = "view"):
    """
    Enforces that:
    1. The user belongs to the requested profile_id, OR the user is an authorized Advisor.
    2. The user has permission for required_action.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Advisors can view all profiles for audit, but other roles are strictly isolated
    if user.role != RolePermissions.ADVISOR and user.profile_id != target_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cross-Family Access Denied: Your account belongs to Family #{user.profile_id}. You cannot access or modify Family #{target_profile_id} data."
        )
    
    check_permission(user, required_action)
    return True
