from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime

# --- Family Profile Schemas ---
class FamilyProfileBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    karta_name: str = Field(..., min_length=2, max_length=120)
    business_name: str = Field(..., min_length=2, max_length=150)
    business_type: str = Field("Sole Proprietorship", max_length=80)
    city: str = Field("New Delhi", max_length=80)
    state: str = Field("Delhi", max_length=80)
    religion: str = Field("Hindu", max_length=40)
    governing_law: str = Field("Hindu Succession Act, 1956 (amended 2005)", max_length=120)
    pan_or_gstin: Optional[str] = Field(None, max_length=30)
    active_role: str = Field("patriarch", max_length=30)

class FamilyProfileCreate(FamilyProfileBase):
    karta_age: Optional[int] = Field(52, ge=18, le=125)
    karta_gender: Optional[str] = Field("Male", max_length=20)
    karta_marital_status: Optional[str] = Field("Married", max_length=30)

class FamilyProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    karta_name: Optional[str] = Field(None, min_length=2, max_length=120)
    karta_age: Optional[int] = Field(None, ge=18, le=125)
    business_name: Optional[str] = Field(None, min_length=2, max_length=150)
    business_type: Optional[str] = Field(None, max_length=80)
    city: Optional[str] = Field(None, max_length=80)
    state: Optional[str] = Field(None, max_length=80)
    religion: Optional[str] = Field(None, max_length=40)
    governing_law: Optional[str] = Field(None, max_length=120)
    pan_or_gstin: Optional[str] = Field(None, max_length=30)

class FamilyProfileResponse(FamilyProfileBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Family Member Schemas ---
class FamilyMemberBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    relation: str = Field(..., min_length=2, max_length=50)
    gender: str = Field("Male", max_length=20)
    age: int = Field(30, ge=0, le=125)
    is_alive: bool = True
    is_minor: bool = False
    marital_status: str = Field("Married", max_length=30)
    aadhaar_last4: Optional[str] = Field(None, max_length=4)
    contact_number: Optional[str] = Field(None, max_length=20)
    is_class_1_heir: bool = True
    is_coparcener: bool = True
    notes: Optional[str] = Field(None, max_length=1000)

class FamilyMemberCreate(FamilyMemberBase):
    profile_id: int

class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    relation: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=20)
    age: Optional[int] = Field(None, ge=0, le=125)
    is_alive: Optional[bool] = None
    is_minor: Optional[bool] = None
    marital_status: Optional[str] = Field(None, max_length=30)
    aadhaar_last4: Optional[str] = Field(None, max_length=4)
    contact_number: Optional[str] = Field(None, max_length=20)
    is_class_1_heir: Optional[bool] = None
    is_coparcener: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)

class FamilyMemberResponse(FamilyMemberBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)

# --- Asset Schemas ---
class AssetBase(BaseModel):
    category: str = Field(..., min_length=2, max_length=60)
    title: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    estimated_value_inr: float = Field(0.0, ge=0.0)
    location_or_institution: Optional[str] = Field(None, max_length=150)
    identifier_number: Optional[str] = Field(None, max_length=100)
    acquisition_type: str = Field("self_acquired", max_length=50)
    documents_available: bool = False
    current_nominee_name: Optional[str] = Field(None, max_length=120)
    nominee_relationship: Optional[str] = Field(None, max_length=50)
    has_nominee_discrepancy: bool = False

class AssetCreate(AssetBase):
    profile_id: int

class AssetUpdate(BaseModel):
    category: Optional[str] = Field(None, max_length=60)
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = Field(None, max_length=1000)
    estimated_value_inr: Optional[float] = Field(None, ge=0.0)
    location_or_institution: Optional[str] = Field(None, max_length=150)
    identifier_number: Optional[str] = Field(None, max_length=100)
    acquisition_type: Optional[str] = Field(None, max_length=50)
    documents_available: Optional[bool] = None
    current_nominee_name: Optional[str] = Field(None, max_length=120)
    nominee_relationship: Optional[str] = Field(None, max_length=50)
    has_nominee_discrepancy: Optional[bool] = None

class AssetResponse(AssetBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)

# --- Asset Allocation Schemas ---
class AssetAllocationBase(BaseModel):
    asset_id: int
    beneficiary_id: int
    share_percentage: float = Field(100.0, ge=0.0, le=100.0)
    contingency_clause: Optional[str] = Field(None, max_length=500)
    special_instructions: Optional[str] = Field(None, max_length=1000)

class AssetAllocationCreate(AssetAllocationBase):
    profile_id: int

class AssetAllocationResponse(AssetAllocationBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)

# --- Will Draft Schemas (Defaults strictly removed per LEGAL-02) ---
class WillDraftBase(BaseModel):
    executor_name: str = Field(..., min_length=2, max_length=120)
    executor_relationship: Optional[str] = Field(None, max_length=50)
    alternate_executor_name: Optional[str] = Field(None, max_length=120)
    guardian_minor_name: Optional[str] = Field(None, max_length=120)
    guardian_relationship: Optional[str] = Field(None, max_length=50)
    witness1_name: Optional[str] = Field(None, max_length=120)
    witness1_address: Optional[str] = Field(None, max_length=250)
    witness2_name: Optional[str] = Field(None, max_length=120)
    witness2_address: Optional[str] = Field(None, max_length=250)
    doctor_name: Optional[str] = Field(None, max_length=120)
    doctor_reg_no: Optional[str] = Field(None, max_length=60)
    doctor_certified: bool = False
    original_physical_location: Optional[str] = Field(None, max_length=200)
    status: str = Field("draft", max_length=30)
    sub_registrar_office: Optional[str] = Field(None, max_length=150)
    registration_date: Optional[str] = None
    registration_number: Optional[str] = None
    sro_reminder_date: Optional[str] = None

class WillDraftCreate(WillDraftBase):
    profile_id: int

class WillDraftResponse(WillDraftBase):
    id: int
    profile_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Vault Document Schemas ---
class VaultDocumentResponse(BaseModel):
    id: int
    profile_id: int
    asset_id: Optional[int] = None
    file_name: str
    file_type: str
    file_size_bytes: int
    category: str
    upload_date: datetime
    expiry_or_renewal_date: Optional[str] = None
    reminder_title: Optional[str] = None
    is_encrypted: bool
    original_checksum_sha256: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# --- Advisor Note Schemas ---
class AdvisorNoteBase(BaseModel):
    author_name: str = Field("CA / Legal Advisor", max_length=120)
    author_role: str = Field("Chartered Accountant", max_length=50)
    note_text: str = Field(..., min_length=2, max_length=2000)
    category: str = Field("succession_conflict", max_length=50)
    severity: str = Field("warning", max_length=20)

class AdvisorNoteCreate(AdvisorNoteBase):
    profile_id: int

class AdvisorNoteResponse(AdvisorNoteBase):
    id: int
    profile_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Role Switch Schema (Backwards compatibility) ---
class RoleSwitchRequest(BaseModel):
    role: str = Field(..., max_length=30)

# --- Real User Authentication Schemas ---
class UserLoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=80)
    password: str = Field(..., min_length=6, max_length=128)

class UserRegisterRequest(BaseModel):
    profile_id: int
    username: str = Field(..., min_length=3, max_length=80)
    full_name: Optional[str] = Field(None, max_length=120)
    role: str = Field("heir", max_length=30)
    password: str = Field(..., min_length=8, max_length=128)

class UserResponse(BaseModel):
    id: int
    profile_id: int
    username: str
    full_name: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuthTokenResponse(BaseModel):
    access_token: str
    token: Optional[str] = None
    token_type: str = "bearer"
    user: UserResponse

# --- Interactive Simulation Parameters Schema ---
class SimulationParams(BaseModel):
    predeceased_child_id: Optional[int] = None
    ademption_asset_id: Optional[int] = None
    unregistered_will: bool = False
    exclude_daughter: bool = False

# --- Reminder Schemas ---
class ReminderItem(BaseModel):
    id: str
    type: str
    title: str
    due_date: str
    severity: str
    description: str
    action_label: str
    action_tab: str

class RemindersResponse(BaseModel):
    profile_id: int
    total_active_reminders: int
    reminders: List[ReminderItem]

# --- Legacy OS & Wealth Planning Schemas ---
class AdvisorQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)

class AdvisorQueryResponse(BaseModel):
    query: str
    answer: str
    identified_gaps: List[str]
    action_items: List[str]
    suggested_followups: List[str]
    ai_provider: Optional[str] = "Waaris Local Statutory Engine (Offline / Zero Setup)"
    api_key_required: Optional[bool] = False
    api_key_note: Optional[str] = "No API key is required. The local Indian legal reasoning engine runs 100% offline and free."

class ReadinessScoreResponse(BaseModel):
    overall_score: float
    grade: str
    badge_color: str
    status_label: str
    pillars: dict
    priority_actions: List[dict]
    disclaimer: str

class NominationTrackerItem(BaseModel):
    asset_id: int
    title: str
    category: str
    estimated_value_inr: float
    acquisition_type: str
    owner: str
    current_nominee_name: str
    nominee_relationship: str
    beneficiaries: List[dict]
    primary_beneficiary_name: str
    vault_document_status: str
    vault_badge: str
    vault_label: str
    alignment_status: str
    status_badge: str
    status_desc: str
    legal_risk: str
    remedy: str

class MemberProfileDetailResponse(BaseModel):
    member: FamilyMemberResponse
    statutory_class: str
    coparcenary_rights: str
    assigned_bequests: List[dict]
    total_bequest_inr: float
    nominated_assets: List[dict]
    statutory_intestate_share_pct: float
    statutory_intestate_inr: float

