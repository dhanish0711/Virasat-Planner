import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Response, Request, status
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import APP_NAME, APP_VERSION, BASE_DIR, ENVIRONMENT
from app.database import engine, Base, get_db, SessionLocal
from app.models import FamilyProfile, FamilyMember, Asset, AssetAllocation, WillDraft, VaultDocument, AdvisorNote, User
from app.schemas import (
    FamilyProfileCreate, FamilyProfileUpdate, FamilyProfileResponse,
    FamilyMemberCreate, FamilyMemberUpdate, FamilyMemberResponse,
    AssetCreate, AssetUpdate, AssetResponse,
    AssetAllocationCreate, AssetAllocationResponse,
    WillDraftCreate, WillDraftResponse,
    VaultDocumentResponse,
    AdvisorNoteCreate, AdvisorNoteResponse,
    RoleSwitchRequest,
    UserLoginRequest, UserRegisterRequest, UserResponse, AuthTokenResponse,
    SimulationParams, RemindersResponse, ReminderItem,
    AdvisorQueryRequest, AdvisorQueryResponse, ReadinessScoreResponse,
    NominationTrackerItem, MemberProfileDetailResponse
)
from app.seed_data import seed_database
from app.crypto_vault import (
    encrypt_and_save_file, decrypt_vault_file, audit_vault_integrity,
    sanitize_vault_filename, delete_vault_file
)
from app.succession_engine import (
    calculate_succession_shares, calculate_succession_readiness,
    generate_nomination_vs_will_tracker, query_legacy_advisor
)
from app.pdf_generator import generate_will_pdf
from app.auth import check_permission, RolePermissions
from app.auth_service import (
    hash_password, verify_password, create_session_token,
    get_current_user, get_current_user_optional, require_role, security_scheme,
    verify_family_access, record_failed_attempt, is_rate_limited, reset_failed_attempts
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Controlled application lifecycle:
    1. Initialize database tables.
    2. Seed initial demo scenarios ONLY in development/testing mode when database is clean.
    Never seeds sample data in production (OPS-01 & OPS-02).
    """
    Base.metadata.create_all(bind=engine)
    if ENVIRONMENT != "production":
        db = SessionLocal()
        try:
            existing = db.query(FamilyProfile).first()
            if not existing:
                seed_database(db)
        finally:
            db.close()
    yield

app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ---------------------------------------------------------
# UI Routes
# ---------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    profile = db.query(FamilyProfile).first()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "initial_profile_id": profile.id if profile else 1
        }
    )


# ---------------------------------------------------------
# User Authentication & RBAC Session API
# ---------------------------------------------------------
@app.post("/api/auth/login")
def login_user(payload: UserLoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    """Authenticate user with username and password, returns signed bearer token."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please wait 60 seconds before trying again."
        )

    user = db.query(User).filter(User.username == payload.username.strip().lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        record_failed_attempt(client_ip)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    reset_failed_attempts(client_ip)
    token = create_session_token(user.id, user.username, user.role, user.profile_id)
    
    # Set HttpOnly, Secure (in production), SameSite cookie
    response.set_cookie(
        key="virasat_auth_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax",
        secure=(ENVIRONMENT == "production")
    )
    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "profile_id": user.profile_id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at.isoformat()
        }
    }

@app.post("/api/auth/register")
async def register_user(
    payload: UserRegisterRequest,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """
    Register a family member account.
    Eliminates role escalation (SEC-02): Unauthenticated or non-patriarch callers
    can only register with 'heir' role. Only an authenticated patriarch of the family
    can assign 'patriarch' or 'advisor' role.
    """
    existing = db.query(User).filter(User.username == payload.username.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    profile = db.query(FamilyProfile).filter(FamilyProfile.id == payload.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")
    
    caller = await get_current_user_optional(request, creds, db)
    assigned_role = payload.role.lower()

    if assigned_role in [RolePermissions.PATRIARCH, RolePermissions.ADVISOR]:
        if not caller or caller.profile_id != payload.profile_id or caller.role != RolePermissions.PATRIARCH:
            assigned_role = RolePermissions.HEIR

    user = User(
        profile_id=payload.profile_id,
        username=payload.username.strip().lower(),
        full_name=(payload.full_name or payload.username).strip(),
        role=assigned_role,
        password_hash=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "profile_id": user.profile_id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    }

@app.get("/api/auth/me")
async def get_my_session(
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """Returns currently authenticated user profile and permissions."""
    user = await get_current_user_optional(request, creds, db)
    if not user:
        return {"authenticated": False, "user": None, "role": "anonymous"}
    return {
        "authenticated": True,
        "username": user.username,
        "id": user.id,
        "profile_id": user.profile_id,
        "role": user.role,
        "user": {
            "id": user.id,
            "profile_id": user.profile_id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at.isoformat()
        }
    }

@app.post("/api/auth/logout")
def logout_user(response: Response):
    """Clears authentication session cookie."""
    response.delete_cookie(key="virasat_auth_token")
    return {"status": "success", "message": "Logged out successfully"}


# ---------------------------------------------------------
# Profile & Multi-Family Scenarios API
# ---------------------------------------------------------
@app.get("/api/scenarios")
def get_all_scenarios(db: Session = Depends(get_db)):
    """Public scenario summary for demo overview and profile selection."""
    profiles = db.query(FamilyProfile).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "karta_name": p.karta_name,
            "business_name": p.business_name,
            "business_type": p.business_type,
            "city": p.city,
            "active_role": p.active_role
        } for p in profiles
    ]

@app.get("/api/profile/{profile_id}")
async def get_family_profile(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """Protected profile view with family-scoped authorization."""
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_dashboard")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")
    return {
        "id": profile.id,
        "name": profile.name,
        "karta_name": profile.karta_name,
        "business_name": profile.business_name,
        "business_type": profile.business_type,
        "city": profile.city,
        "state": profile.state,
        "religion": profile.religion,
        "governing_law": profile.governing_law,
        "pan_or_gstin": profile.pan_or_gstin,
        "active_role": profile.active_role,
        "created_at": profile.created_at.isoformat()
    }

@app.post("/api/profile")
def create_family_profile(payload: FamilyProfileCreate, response: Response, db: Session = Depends(get_db)):
    """
    Creates a new custom estate profile and automatically provisions the Patriarch user account.
    Returns the created profile along with authentication token for immediate administrative access.
    """
    profile = FamilyProfile(
        name=payload.name,
        karta_name=payload.karta_name,
        business_name=payload.business_name,
        business_type=payload.business_type,
        city=payload.city,
        state=payload.state,
        religion=payload.religion,
        governing_law=payload.governing_law,
        pan_or_gstin=payload.pan_or_gstin,
        active_role="patriarch"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # 1. Automatically add Karta (Self) to the family tree with user-specified age & demographics
    karta_age = getattr(payload, "karta_age", None) or 52
    karta_gender = getattr(payload, "karta_gender", None) or "Male"
    karta_marital = getattr(payload, "karta_marital_status", None) or "Married"

    karta_member = FamilyMember(
        profile_id=profile.id,
        name=payload.karta_name,
        relation="Self",
        gender=karta_gender,
        age=int(karta_age),
        is_alive=True,
        is_minor=False,
        marital_status=karta_marital,
        is_class_1_heir=False,
        is_coparcener=True,
        notes="Business owner & Head of Family (Karta)"
    )
    db.add(karta_member)

    # 2. Initialize clean Will draft (No invented fake defaults - LEGAL-02)
    will = WillDraft(
        profile_id=profile.id,
        executor_name=f"{payload.karta_name}'s Designated Executor",
        executor_relationship="Family Member / Trusted Representative",
        witness1_name=None,
        witness1_address=None,
        witness2_name=None,
        witness2_address=None,
        doctor_name=None,
        doctor_reg_no=None,
        doctor_certified=False,
        original_physical_location=None,
        status="draft",
        sub_registrar_office=f"Sub-Registrar Office, {payload.city}" if payload.city else None
    )
    db.add(will)

    # 3. Add welcome guidance advisor note
    note = AdvisorNote(
        profile_id=profile.id,
        author_name="Succession Advisor",
        author_role="System Guidance",
        note_text=f"Welcome {payload.karta_name}! To build your succession plan: 1) Add family members in Family Tree, 2) Add shops/properties/bank FDs in Asset Inventory, 3) Allocate bequests to see your custom dispute score and legal will draft.",
        category="tax_risk",
        severity="info"
    )
    db.add(note)

    # 4. Create primary Patriarch User account for this new family
    username_base = payload.karta_name.strip().lower().replace(" ", "_")
    username_candidate = f"karta_{username_base}_{profile.id}"
    patriarch_user = User(
        profile_id=profile.id,
        username=username_candidate,
        full_name=payload.karta_name,
        role=RolePermissions.PATRIARCH,
        password_hash=hash_password("Virasat@2026")
    )
    db.add(patriarch_user)
    db.commit()
    db.refresh(patriarch_user)
    db.refresh(profile)

    # Issue auth token so creator is immediately logged in as Patriarch
    auth_token = create_session_token(patriarch_user.id, patriarch_user.username, RolePermissions.PATRIARCH, profile.id)
    response.set_cookie(
        key="virasat_auth_token",
        value=auth_token,
        httponly=True,
        max_age=86400,
        samesite="lax",
        secure=(ENVIRONMENT == "production")
    )

    return {
        "id": profile.id,
        "name": profile.name,
        "karta_name": profile.karta_name,
        "business_name": profile.business_name,
        "business_type": profile.business_type,
        "city": profile.city,
        "state": profile.state,
        "religion": profile.religion,
        "governing_law": profile.governing_law,
        "pan_or_gstin": profile.pan_or_gstin,
        "active_role": profile.active_role,
        "created_at": profile.created_at.isoformat(),
        "auth_token": auth_token,
        "username": patriarch_user.username
    }

@app.put("/api/profile/{profile_id}")
async def update_family_profile(
    profile_id: int,
    payload: FamilyProfileUpdate,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "edit_profile")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            setattr(profile, k, v)
    
    karta_member = db.query(FamilyMember).filter(FamilyMember.profile_id == profile_id, FamilyMember.relation == "Self").first()
    if karta_member:
        if payload.karta_name:
            karta_member.name = payload.karta_name
        if getattr(payload, "karta_age", None) is not None:
            karta_member.age = payload.karta_age

    db.commit()
    db.refresh(profile)
    return {
        "id": profile.id,
        "name": profile.name,
        "karta_name": profile.karta_name,
        "business_name": profile.business_name,
        "business_type": profile.business_type,
        "city": profile.city,
        "state": profile.state,
        "religion": profile.religion,
        "governing_law": profile.governing_law,
        "pan_or_gstin": profile.pan_or_gstin,
        "active_role": profile.active_role
    }

@app.delete("/api/profile/{profile_id}")
async def delete_family_profile(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "delete_profile")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")
    
    total_count = db.query(FamilyProfile).count()
    if total_count <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the only existing estate profile")
    
    db.delete(profile)
    db.commit()
    
    remaining = db.query(FamilyProfile).first()
    return {"status": "success", "message": f"Profile '{profile.name}' deleted", "next_profile_id": remaining.id if remaining else None}

async def _execute_role_switch(request: Request, payload: RoleSwitchRequest, profile_id: int, creds, db: Session):
    """
    Role view switch helper.
    Eliminates Privilege Escalation (SEC-02):
    Heir accounts CANNOT escalate to Patriarch or Advisor.
    Patriarch accounts can toggle between administrative and heir view.
    """
    user = await get_current_user(request, creds, db)
    if user.profile_id != profile_id and user.role != RolePermissions.ADVISOR:
        raise HTTPException(status_code=403, detail="Cross-family access denied.")

    requested_role = payload.role.lower()
    if requested_role not in [RolePermissions.PATRIARCH, RolePermissions.HEIR, RolePermissions.ADVISOR]:
        raise HTTPException(status_code=400, detail="Invalid role specified")

    if user.role == RolePermissions.HEIR and requested_role in [RolePermissions.PATRIARCH, RolePermissions.ADVISOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role Escalation Denied: Heir accounts cannot elevate permissions to Patriarch or Advisor."
        )

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")

    profile.active_role = requested_role
    db.commit()
    return {"status": "success", "active_role": profile.active_role}

@app.post("/api/role/switch")
async def switch_active_role_query(
    request: Request,
    payload: RoleSwitchRequest,
    profile_id: int = 1,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    return await _execute_role_switch(request, payload, profile_id, creds, db)

@app.post("/api/role/{profile_id}")
async def switch_active_role_path(
    request: Request,
    profile_id: int,
    payload: RoleSwitchRequest,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    return await _execute_role_switch(request, payload, profile_id, creds, db)


# ---------------------------------------------------------
# Family Tree API
# ---------------------------------------------------------
@app.get("/api/family/{profile_id}")
async def get_family_members(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_family")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")
    members = db.query(FamilyMember).filter(FamilyMember.profile_id == profile_id).all()
    
    return {
        "profile": {
            "id": profile.id,
            "karta_name": profile.karta_name,
            "business_name": profile.business_name,
            "active_role": profile.active_role
        },
        "members": [
            {
                "id": m.id,
                "name": m.name,
                "relation": m.relation,
                "gender": m.gender,
                "age": m.age,
                "is_alive": m.is_alive,
                "is_minor": m.is_minor,
                "marital_status": m.marital_status,
                "aadhaar_last4": m.aadhaar_last4,
                "contact_number": m.contact_number,
                "is_class_1_heir": m.is_class_1_heir,
                "is_coparcener": m.is_coparcener,
                "notes": m.notes
            } for m in members
        ]
    }

@app.post("/api/family/{profile_id}/member")
async def add_family_member(
    profile_id: int,
    payload: FamilyMemberCreate,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "edit_family")

    rel = payload.relation.lower()
    is_class_1 = rel in ["spouse", "wife", "mother", "son", "daughter"]

    member = FamilyMember(
        profile_id=profile_id,
        name=payload.name,
        relation=payload.relation,
        gender=payload.gender,
        age=payload.age,
        is_alive=payload.is_alive,
        is_minor=payload.is_minor or (payload.age < 18),
        marital_status=payload.marital_status,
        aadhaar_last4=payload.aadhaar_last4,
        contact_number=payload.contact_number,
        is_class_1_heir=is_class_1,
        is_coparcener=rel in ["son", "daughter"],
        notes=payload.notes
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

@app.put("/api/family/{profile_id}/member/{member_id}")
async def update_family_member(
    profile_id: int,
    member_id: int,
    payload: FamilyMemberUpdate,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "edit_family")

    member = db.query(FamilyMember).filter(FamilyMember.id == member_id, FamilyMember.profile_id == profile_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            setattr(member, k, v)
    
    if payload.age is not None:
        member.is_minor = member.age < 18

    db.commit()
    db.refresh(member)
    return member

@app.delete("/api/family/{profile_id}/member/{member_id}")
async def delete_family_member(
    profile_id: int,
    member_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "edit_family")

    member = db.query(FamilyMember).filter(FamilyMember.id == member_id, FamilyMember.profile_id == profile_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.relation.lower() == "self":
        raise HTTPException(status_code=400, detail="Cannot delete Patriarch/Self from the family tree")
    
    db.delete(member)
    db.commit()
    return {"status": "success", "message": f"Family member '{member.name}' removed"}


# ---------------------------------------------------------
# Asset Inventory API
# ---------------------------------------------------------
@app.get("/api/assets/{profile_id}")
async def get_assets(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_all_assets")

    assets = db.query(Asset).filter(Asset.profile_id == profile_id).all()
    total_val = sum(a.estimated_value_inr for a in assets if a.category != "liability_loan")
    total_liab = sum(a.estimated_value_inr for a in assets if a.category == "liability_loan")

    return {
        "summary": {
            "total_assets_inr": total_val,
            "total_liabilities_inr": total_liab,
            "net_worth_inr": total_val - total_liab,
            "assets_count": len([a for a in assets if a.category != "liability_loan"]),
            "liabilities_count": len([a for a in assets if a.category == "liability_loan"])
        },
        "assets": [
            {
                "id": a.id,
                "category": a.category,
                "title": a.title,
                "description": a.description,
                "estimated_value_inr": a.estimated_value_inr,
                "location_or_institution": a.location_or_institution,
                "identifier_number": a.identifier_number,
                "acquisition_type": a.acquisition_type,
                "documents_available": a.documents_available,
                "current_nominee_name": a.current_nominee_name,
                "nominee_relationship": a.nominee_relationship,
                "has_nominee_discrepancy": a.has_nominee_discrepancy
            } for a in assets
        ]
    }

@app.post("/api/assets/{profile_id}")
async def add_asset(
    profile_id: int,
    payload: AssetCreate,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "add_asset")

    asset = Asset(
        profile_id=profile_id,
        category=payload.category,
        title=payload.title,
        description=payload.description,
        estimated_value_inr=payload.estimated_value_inr,
        location_or_institution=payload.location_or_institution,
        identifier_number=payload.identifier_number,
        acquisition_type=payload.acquisition_type,
        documents_available=payload.documents_available,
        current_nominee_name=payload.current_nominee_name,
        nominee_relationship=payload.nominee_relationship,
        has_nominee_discrepancy=payload.has_nominee_discrepancy
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset

@app.put("/api/assets/{profile_id}/{asset_id}")
async def update_asset(
    profile_id: int,
    asset_id: int,
    payload: AssetUpdate,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "edit_asset")

    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.profile_id == profile_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            setattr(asset, k, v)

    db.commit()
    db.refresh(asset)
    return asset

@app.delete("/api/assets/{profile_id}/{asset_id}")
async def delete_asset(
    profile_id: int,
    asset_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "delete_asset")

    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.profile_id == profile_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    db.delete(asset)
    db.commit()
    return {"status": "success", "message": f"Asset '{asset.title}' removed"}


# ---------------------------------------------------------
# Asset Allocations (Will Bequests) API
# ---------------------------------------------------------
@app.get("/api/allocations/{profile_id}")
async def get_allocations(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_bequests")

    allocs = db.query(AssetAllocation).filter(AssetAllocation.profile_id == profile_id).all()
    return [
        {
            "id": al.id,
            "asset_id": al.asset_id,
            "beneficiary_id": al.beneficiary_id,
            "share_percentage": al.share_percentage,
            "contingency_clause": al.contingency_clause,
            "special_instructions": al.special_instructions
        } for al in allocs
    ]

@app.post("/api/allocations/{profile_id}")
async def update_allocations(
    profile_id: int,
    payload: AssetAllocationCreate,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "edit_bequests")

    # 1. Verify asset belongs to this profile (SEC-03 & DATA-02)
    asset = db.query(Asset).filter(Asset.id == payload.asset_id, Asset.profile_id == profile_id).first()
    if not asset:
        raise HTTPException(
            status_code=400,
            detail="Asset validation error: Specified asset does not belong to this family profile."
        )

    # 2. Verify beneficiary belongs to this profile (SEC-03 & DATA-02)
    beneficiary = db.query(FamilyMember).filter(FamilyMember.id == payload.beneficiary_id, FamilyMember.profile_id == profile_id).first()
    if not beneficiary:
        raise HTTPException(
            status_code=400,
            detail="Beneficiary validation error: Specified family member does not belong to this family profile."
        )

    # 3. Validate total percentage does not exceed 100% (SEC-08 / Important allocation bug fix)
    other_allocs = db.query(AssetAllocation).filter(
        AssetAllocation.profile_id == profile_id,
        AssetAllocation.asset_id == payload.asset_id,
        AssetAllocation.beneficiary_id != payload.beneficiary_id
    ).all()
    current_other_pct = sum(a.share_percentage for a in other_allocs)

    if current_other_pct + payload.share_percentage > 100.001:
        raise HTTPException(
            status_code=400,
            detail=f"Allocation rejected: Combined share for asset '{asset.title}' would equal {current_other_pct + payload.share_percentage:.1f}%, exceeding 100% (Already allocated: {current_other_pct:.1f}%)."
        )

    existing = db.query(AssetAllocation).filter(
        AssetAllocation.profile_id == profile_id,
        AssetAllocation.asset_id == payload.asset_id,
        AssetAllocation.beneficiary_id == payload.beneficiary_id
    ).first()

    if existing:
        existing.share_percentage = payload.share_percentage
        existing.special_instructions = payload.special_instructions
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_alloc = AssetAllocation(
            profile_id=profile_id,
            asset_id=payload.asset_id,
            beneficiary_id=payload.beneficiary_id,
            share_percentage=payload.share_percentage,
            contingency_clause=payload.contingency_clause,
            special_instructions=payload.special_instructions
        )
        db.add(new_alloc)
        db.commit()
        db.refresh(new_alloc)
        return new_alloc


# ---------------------------------------------------------
# Will Draft & PDF Generation API
# ---------------------------------------------------------
@app.get("/api/will/{profile_id}")
async def get_will_draft(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_will_preview")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")
    will = db.query(WillDraft).filter(WillDraft.profile_id == profile_id).first()
    if not will:
        will = WillDraft(
            profile_id=profile_id,
            executor_name=f"{profile.karta_name}'s Trusted Executor",
            executor_relationship="Family Member / Trusted Representative",
            status="draft"
        )
        db.add(will)
        db.commit()
        db.refresh(will)
    return will

@app.post("/api/will/{profile_id}")
async def save_will_draft(
    profile_id: int,
    payload: WillDraftCreate,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "save_will")

    will = db.query(WillDraft).filter(WillDraft.profile_id == profile_id).first()
    if not will:
        will = WillDraft(profile_id=profile_id, executor_name=payload.executor_name)
        db.add(will)

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if k != "profile_id":
            setattr(will, k, v)

    db.commit()
    db.refresh(will)
    return will

@app.get("/api/will/{profile_id}/pdf")
@app.post("/api/export-pdf/{profile_id}")
async def export_will_pdf(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "download_will_pdf")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")

    members = db.query(FamilyMember).filter(FamilyMember.profile_id == profile_id).all()
    assets = db.query(Asset).filter(Asset.profile_id == profile_id).all()
    allocations = db.query(AssetAllocation).filter(AssetAllocation.profile_id == profile_id).all()
    will = db.query(WillDraft).filter(WillDraft.profile_id == profile_id).first()

    will_dict = {}
    if will:
        will_dict = {
            "executor_name": will.executor_name,
            "executor_relationship": will.executor_relationship,
            "alternate_executor_name": will.alternate_executor_name,
            "guardian_minor_name": will.guardian_minor_name,
            "guardian_relationship": will.guardian_relationship,
            "witness1_name": will.witness1_name,
            "witness1_address": will.witness1_address,
            "witness2_name": will.witness2_name,
            "witness2_address": will.witness2_address,
            "doctor_name": will.doctor_name,
            "doctor_reg_no": will.doctor_reg_no,
            "doctor_certified": will.doctor_certified,
            "original_physical_location": will.original_physical_location,
            "sub_registrar_office": will.sub_registrar_office
        }

    pdf_bytes = generate_will_pdf(profile, will_dict, members, assets, allocations)
    safe_filename = sanitize_vault_filename(f"Will_Draft_{profile.karta_name.replace(' ', '_')}.pdf")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )


# ---------------------------------------------------------
# Document Deadlines & SRO Registration Reminders API
# ---------------------------------------------------------
@app.get("/api/reminders/{profile_id}")
async def get_profile_reminders(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_reminders")

    from datetime import date
    today = date.today()

    will = db.query(WillDraft).filter(WillDraft.profile_id == profile_id).first()
    sro_date_str = will.sro_reminder_date if will else None
    
    sro_status = "NOT_SET"
    days_to_sro = None
    if sro_date_str:
        try:
            target_dt = date.fromisoformat(sro_date_str)
            days_to_sro = (target_dt - today).days
            sro_status = "OVERDUE" if days_to_sro < 0 else "UPCOMING"
        except Exception:
            pass

    vault_docs = db.query(VaultDocument).filter(
        VaultDocument.profile_id == profile_id,
        VaultDocument.expiry_or_renewal_date.isnot(None)
    ).all()

    expiry_items = []
    for d in vault_docs:
        try:
            exp_dt = date.fromisoformat(d.expiry_or_renewal_date)
            diff = (exp_dt - today).days
            expiry_items.append({
                "doc_id": d.id,
                "file_name": d.file_name,
                "category": d.category,
                "reminder_title": d.reminder_title or f"Renewal for {d.file_name}",
                "expiry_or_renewal_date": d.expiry_or_renewal_date,
                "days_remaining": diff,
                "status": "EXPIRED" if diff < 0 else "EXPIRING_SOON" if diff <= 30 else "ACTIVE"
            })
        except Exception:
            pass

    return {
        "profile_id": profile_id,
        "sro_will_registration": {
            "reminder_date": sro_date_str,
            "status": sro_status,
            "days_remaining": days_to_sro,
            "recommendation": "Book appointment at local Sub-Registrar Office to register Book 3 entry with 2 witnesses."
        },
        "vault_expiries": expiry_items,
        "total_active_alerts": (1 if sro_status in ["UPCOMING", "OVERDUE"] else 0) + len(expiry_items)
    }

@app.post("/api/reminders/{profile_id}/sro")
async def update_sro_reminder(
    profile_id: int,
    payload: dict,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "save_will")

    will = db.query(WillDraft).filter(WillDraft.profile_id == profile_id).first()
    if not will:
        will = WillDraft(profile_id=profile_id, executor_name="Designated Executor")
        db.add(will)
    will.sro_reminder_date = payload.get("sro_reminder_date")
    db.commit()
    return {"status": "success", "sro_reminder_date": will.sro_reminder_date}


# ---------------------------------------------------------
# Encrypted Document Vault API
# ---------------------------------------------------------
@app.get("/api/vault/{profile_id}")
async def list_vault_documents(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_vault")

    docs = db.query(VaultDocument).filter(VaultDocument.profile_id == profile_id).all()
    return [
        {
            "id": d.id,
            "asset_id": d.asset_id,
            "file_name": d.file_name,
            "file_type": d.file_type,
            "file_size_bytes": d.file_size_bytes,
            "category": d.category,
            "upload_date": d.upload_date.isoformat(),
            "expiry_or_renewal_date": d.expiry_or_renewal_date,
            "reminder_title": d.reminder_title,
            "is_encrypted": d.is_encrypted,
            "checksum_sha256": d.original_checksum_sha256
        } for d in docs
    ]

@app.post("/api/vault/{profile_id}/upload")
async def upload_vault_document(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    file: UploadFile = File(...),
    category: str = Form("registry_deed"),
    asset_id: Optional[int] = Form(None),
    expiry_or_renewal_date: Optional[str] = Form(None),
    reminder_title: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "upload_document")

    # Validate asset belongs to profile if specified (SEC-06)
    if asset_id is not None:
        asset = db.query(Asset).filter(Asset.id == asset_id, Asset.profile_id == profile_id).first()
        if not asset:
            raise HTTPException(
                status_code=400,
                detail="Asset validation failed: Specified asset does not belong to this family profile."
            )

    contents = await file.read()
    # Encrypt & save file (enforces size and extension validation)
    enc_path, sha_hash, orig_size = encrypt_and_save_file(contents, file.filename)

    try:
        doc = VaultDocument(
            profile_id=profile_id,
            asset_id=asset_id,
            file_name=file.filename,
            file_type=file.content_type or "application/octet-stream",
            file_size_bytes=orig_size,
            encrypted_file_path=enc_path,
            original_checksum_sha256=sha_hash,
            category=category,
            expiry_or_renewal_date=expiry_or_renewal_date,
            reminder_title=reminder_title,
            is_encrypted=True
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return {"status": "success", "id": doc.id, "file_name": doc.file_name, "checksum": sha_hash}
    except Exception as e:
        db.rollback()
        # Clean up orphaned encrypted file on disk if DB commit fails (SEC-06)
        delete_vault_file(enc_path)
        raise HTTPException(status_code=500, detail=f"Failed to record uploaded document: {str(e)}")

@app.get("/api/vault/{profile_id}/download/{doc_id}")
async def download_vault_document(
    profile_id: int,
    doc_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "download_vault")

    doc = db.query(VaultDocument).filter(VaultDocument.id == doc_id, VaultDocument.profile_id == profile_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Vault Document not found")

    decrypted_bytes = decrypt_vault_file(doc.encrypted_file_path, doc.original_checksum_sha256)
    safe_filename = sanitize_vault_filename(doc.file_name)
    return Response(
        content=decrypted_bytes,
        media_type=doc.file_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )

@app.delete("/api/vault/{profile_id}/{doc_id}")
async def delete_vault_document(
    profile_id: int,
    doc_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "delete_document")

    doc = db.query(VaultDocument).filter(VaultDocument.id == doc_id, VaultDocument.profile_id == profile_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Vault Document not found")

    file_path = doc.encrypted_file_path
    db.delete(doc)
    db.commit()
    delete_vault_file(file_path)
    return {"status": "success", "message": f"Document '{doc.file_name}' deleted"}

@app.get("/api/vault-security-audit")
async def vault_security_audit(
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """Audits vault encryption integrity. Restricted to Patriarch or Legal Advisor."""
    user = await get_current_user(request, creds, db)
    if user.role not in [RolePermissions.PATRIARCH, RolePermissions.ADVISOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission Denied: Vault security audit report is restricted to Patriarch or Legal Advisor."
        )
    return audit_vault_integrity()


# ---------------------------------------------------------
# 'What happens if...' Legal Scenario Simulator API
# ---------------------------------------------------------
@app.get("/api/simulation/{profile_id}")
async def run_simulation_get(
    profile_id: int,
    request: Request,
    unregistered_will: bool = False,
    exclude_daughter: bool = False,
    predeceased_child_id: Optional[int] = None,
    ademption_asset_id: Optional[int] = None,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_simulator")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")
    
    members = db.query(FamilyMember).filter(FamilyMember.profile_id == profile_id).all()
    assets = db.query(Asset).filter(Asset.profile_id == profile_id).all()
    allocations = db.query(AssetAllocation).filter(AssetAllocation.profile_id == profile_id).all()

    toggles = {
        "unregistered_will": unregistered_will,
        "exclude_daughter": exclude_daughter,
        "predeceased_child_id": predeceased_child_id,
        "ademption_asset_id": ademption_asset_id
    }
    return calculate_succession_shares(profile, members, assets, allocations, toggles)

@app.post("/api/simulation/{profile_id}")
async def run_simulation_post(
    profile_id: int,
    payload: SimulationParams,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """Interactive What-If simulator executing dynamic scenario parameters."""
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_simulator")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")
    
    members = db.query(FamilyMember).filter(FamilyMember.profile_id == profile_id).all()
    assets = db.query(Asset).filter(Asset.profile_id == profile_id).all()
    allocations = db.query(AssetAllocation).filter(AssetAllocation.profile_id == profile_id).all()

    return calculate_succession_shares(profile, members, assets, allocations, payload.model_dump())


# ---------------------------------------------------------
# CA / Legal Advisor Notes API
# ---------------------------------------------------------
@app.get("/api/advisor-notes/{profile_id}")
async def get_advisor_notes(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_dashboard")

    notes = db.query(AdvisorNote).filter(AdvisorNote.profile_id == profile_id).order_by(AdvisorNote.created_at.desc()).all()
    return [
        {
            "id": n.id,
            "author_name": n.author_name,
            "author_role": n.author_role,
            "note_text": n.note_text,
            "category": n.category,
            "severity": n.severity,
            "created_at": n.created_at.isoformat()
        } for n in notes
    ]

@app.post("/api/advisor-notes/{profile_id}")
async def add_advisor_note(
    profile_id: int,
    payload: AdvisorNoteCreate,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "add_advisor_note")

    note = AdvisorNote(
        profile_id=profile_id,
        author_name=payload.author_name,
        author_role=payload.author_role,
        note_text=payload.note_text,
        category=payload.category,
        severity=payload.severity
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# ---------------------------------------------------------
# Sub-Registrar Office (SRO) Registration Guide API
# ---------------------------------------------------------
@app.get("/api/sro-guide")
def get_sro_guide():
    return {
        "title": "Sub-Registrar Office (SRO) Will Registration Guide for Indian Traders",
        "key_facts": [
            {"label": "Is Registration Mandatory?", "value": "NO (Section 18, Indian Registration Act 1908). An unregistered written will is legally valid if signed by 2 witnesses. However, registration is STRONGLY recommended to deter false claims of forgery."},
            {"label": "Stamp Duty Required?", "value": "ZERO (Nil). Wills are exempt from stamp duty across India."},
            {"label": "Official Registration Fee", "value": "Nominal fee ranging from ₹100 to ₹500 depending on State rules."},
            {"label": "Mandatory Attendees", "value": "1. Testator in person, 2. Two independent adult witnesses with Original Aadhaar/Voter IDs."}
        ],
        "step_by_step_checklist": [
            {
                "step": 1,
                "title": "Finalize Will Draft & Medical Certificate",
                "desc": "Print the Will on plain ledger or executive paper. Obtain a signed mental fitness certificate from an MBBS doctor on their official prescription letterhead with MCI reg number."
            },
            {
                "step": 2,
                "title": "Book SRO Slot Online",
                "desc": "Access your state's revenue portal (e.g. DORIS in Delhi, Inspector General of Registration in Gujarat/UP/Rajasthan). Book an appointment at the Sub-Registrar Office having jurisdiction over your residence."
            },
            {
                "step": 3,
                "title": "Biometric & Photograph Verification",
                "desc": "Testator and both witnesses appear in person before the Sub-Registrar. Live digital photograph and thumb biometric impressions are captured."
            },
            {
                "step": 4,
                "title": "Sub-Registrar Oral Inquiry",
                "desc": "The Sub-Registrar directly questions the testator: 'Kya aapne yeh vasiyat apni marzi se bina kisi dabav ke banayi hai?' (Have you made this will voluntarily without undue pressure?)."
            },
            {
                "step": 5,
                "title": "Endorsement & Registration Number",
                "desc": "Sub-Registrar endorses Book 3 (Wills Registry) entry. The original registered will is returned with official seal, barcode, and Book 3 volume number within 24 to 48 hours."
            }
        ]
    }


# ---------------------------------------------------------
# Legacy OS & Succession Readiness API
# ---------------------------------------------------------
@app.get("/api/readiness/{profile_id}")
async def get_succession_readiness(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """Computes 0-100 Succession Readiness / Health Score across 4 institutional pillars."""
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_readiness")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")

    members = db.query(FamilyMember).filter(FamilyMember.profile_id == profile_id).all()
    assets = db.query(Asset).filter(Asset.profile_id == profile_id).all()
    allocations = db.query(AssetAllocation).filter(AssetAllocation.profile_id == profile_id).all()
    vault_docs = db.query(VaultDocument).filter(VaultDocument.profile_id == profile_id).all()
    will = db.query(WillDraft).filter(WillDraft.profile_id == profile_id).first()

    return calculate_succession_readiness(profile, members, assets, allocations, vault_docs, will)


@app.get("/api/nomination-tracker/{profile_id}")
async def get_nomination_tracker(
    profile_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """Returns asset-by-asset comparison of Nominee vs Will Beneficiary with Sarbati Devi discrepancy detection."""
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_nomination_tracker")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")

    members = db.query(FamilyMember).filter(FamilyMember.profile_id == profile_id).all()
    assets = db.query(Asset).filter(Asset.profile_id == profile_id).all()
    allocations = db.query(AssetAllocation).filter(AssetAllocation.profile_id == profile_id).all()
    vault_docs = db.query(VaultDocument).filter(VaultDocument.profile_id == profile_id).all()

    return generate_nomination_vs_will_tracker(profile, members, assets, allocations, vault_docs)


@app.post("/api/legacy-advisor/{profile_id}/query")
async def post_legacy_advisor_query(
    profile_id: int,
    payload: AdvisorQueryRequest,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """Context-aware AI Family Legacy Advisor answering questions against the family's estate records."""
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "query_advisor")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Family Profile not found")

    members = db.query(FamilyMember).filter(FamilyMember.profile_id == profile_id).all()
    assets = db.query(Asset).filter(Asset.profile_id == profile_id).all()
    allocations = db.query(AssetAllocation).filter(AssetAllocation.profile_id == profile_id).all()
    vault_docs = db.query(VaultDocument).filter(VaultDocument.profile_id == profile_id).all()
    will = db.query(WillDraft).filter(WillDraft.profile_id == profile_id).first()

    return query_legacy_advisor(payload.query, profile, members, assets, allocations, vault_docs, will)


@app.get("/api/family/{profile_id}/member-detail/{member_id}")
async def get_family_member_detail(
    profile_id: int,
    member_id: int,
    request: Request,
    creds = Depends(security_scheme),
    db: Session = Depends(get_db)
):
    """Returns comprehensive portfolio and statutory rights breakdown for a family member."""
    user = await get_current_user(request, creds, db)
    verify_family_access(user, profile_id, "view_member_detail")

    member = db.query(FamilyMember).filter(FamilyMember.id == member_id, FamilyMember.profile_id == profile_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family Member not found")

    profile = db.query(FamilyProfile).filter(FamilyProfile.id == profile_id).first()
    members = db.query(FamilyMember).filter(FamilyMember.profile_id == profile_id).all()
    assets = db.query(Asset).filter(Asset.profile_id == profile_id).all()
    allocations = db.query(AssetAllocation).filter(AssetAllocation.profile_id == profile_id).all()

    # Find bequests assigned to this member
    member_allocs = [al for al in allocations if al.beneficiary_id == member_id]
    assigned_bequests = []
    total_bequest_inr = 0.0
    for al in member_allocs:
        ast = next((a for a in assets if a.id == al.asset_id), None)
        if ast:
            val = (al.share_percentage / 100.0) * ast.estimated_value_inr
            total_bequest_inr += val
            assigned_bequests.append({
                "asset_id": ast.id,
                "asset_title": ast.title,
                "category": ast.category,
                "share_percentage": al.share_percentage,
                "value_inr": val
            })

    # Find assets nominated to this member
    nominated_assets = []
    m_name_lower = member.name.lower()
    for a in assets:
        if a.current_nominee_name and (m_name_lower in a.current_nominee_name.lower() or a.current_nominee_name.lower() in m_name_lower):
            nominated_assets.append({
                "asset_id": a.id,
                "title": a.title,
                "category": a.category,
                "estimated_value_inr": a.estimated_value_inr,
                "nominee_relationship": a.nominee_relationship
            })

    # Calculate statutory intestate share
    sim = calculate_succession_shares(profile, members, assets, allocations)
    member_stat = next((s for s in sim.get("intestate_shares", []) if s.get("member_id") == member_id), None)
    intestate_pct = member_stat["share_pct"] if member_stat else 0.0
    intestate_inr = member_stat["estimated_inr"] if member_stat else 0.0

    statutory_class = "Class I Statutory Heir" if member.is_class_1_heir else "Class II Statutory Heir / Extended Family"
    coparcenary_rights = "Full birthright coparcener under Section 6 Hindu Succession Act." if member.is_coparcener else "No ancestral coparcenary share."

    return {
        "member": {
            "id": member.id,
            "profile_id": member.profile_id,
            "name": member.name,
            "relation": member.relation,
            "gender": member.gender,
            "age": member.age,
            "is_alive": member.is_alive,
            "is_minor": member.is_minor,
            "marital_status": member.marital_status,
            "aadhaar_last4": member.aadhaar_last4,
            "contact_number": member.contact_number,
            "is_class_1_heir": member.is_class_1_heir,
            "is_coparcener": member.is_coparcener,
            "notes": member.notes
        },
        "statutory_class": statutory_class,
        "coparcenary_rights": coparcenary_rights,
        "assigned_bequests": assigned_bequests,
        "total_bequest_inr": total_bequest_inr,
        "nominated_assets": nominated_assets,
        "statutory_intestate_share_pct": intestate_pct,
        "statutory_intestate_inr": intestate_inr
    }

