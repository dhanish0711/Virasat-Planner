"""
Role-Based Access Control (RBAC) & Persona Permissions for VirasatPlanner
Strictly enforces authenticated User session roles (Patriarch, Heir, CA/Advisor).
Never allows unauthenticated fallback to Patriarch.
"""

from typing import Union, Optional
from fastapi import HTTPException, status
from app.models import User

class RolePermissions:
    PATRIARCH = "patriarch"  # Full administrative rights (Karta / Business Owner)
    HEIR = "heir"            # Family member view (Bequests visibility, read-only)
    ADVISOR = "advisor"      # CA / Vakil audit & advisory notes rights

def check_permission(entity: Union[User, str, None], required_action: str):
    """
    Validates role permissions for an action.
    Accepts an authenticated User or an explicit role string from a verified identity.
    Rejects None / missing entities with 401 Unauthorized.
    """
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in to perform this action.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if isinstance(entity, str):
        role = entity.lower()
    elif hasattr(entity, "role") and entity.role:
        role = entity.role.lower()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user entity. Authentication required.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if role == RolePermissions.PATRIARCH:
        return True  # Full rights

    if role == RolePermissions.HEIR:
        allowed_actions = [
            "view_dashboard", "view_family", "view_bequests", "view_vault_summary",
            "view_vault", "download_vault", "view_simulator", "view_will_preview",
            "view_reminders", "view_all_assets", "download_will_pdf",
            "view_readiness", "view_nomination_tracker", "query_advisor", "view_member_detail"
        ]
        if required_action not in allowed_actions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission Denied: Heir account is restricted from '{required_action}'. Heirs have read-only visibility into family bequests and estate inventory."
            )
        return True

    if role == RolePermissions.ADVISOR:
        allowed_actions = [
            "view_dashboard", "view_family", "view_all_assets", "view_vault",
            "download_vault", "add_advisor_note", "audit_compliance", "view_simulator",
            "download_will_pdf", "view_reminders",
            "view_readiness", "view_nomination_tracker", "query_advisor", "view_member_detail"
        ]
        if required_action not in allowed_actions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission Denied: Legal Advisor/CA account cannot execute '{required_action}'. Advisors can audit, leave advisory notes, and review compliance."
            )
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Permission Denied: Unknown role '{role}'."
    )
