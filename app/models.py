from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)

class FamilyProfile(Base):
    __tablename__ = "family_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    karta_name = Column(String(120), nullable=False)
    business_name = Column(String(150), nullable=False)
    business_type = Column(String(80), default="Sole Proprietorship")  # Partnership, HUF, Sole Proprietorship, Pvt Ltd
    city = Column(String(80), default="New Delhi")
    state = Column(String(80), default="Delhi")
    religion = Column(String(40), default="Hindu")  # Hindu (HSA 1956/2005), Muslim (Shariat), Christian/Parsi (ISA 1925)
    governing_law = Column(String(80), default="Hindu Succession Act, 1956 (amended 2005)")
    pan_or_gstin = Column(String(30), nullable=True)
    active_role = Column(String(30), default="patriarch")
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    users = relationship("User", back_populates="profile", cascade="all, delete-orphan")
    members = relationship("FamilyMember", back_populates="profile", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="profile", cascade="all, delete-orphan")
    allocations = relationship("AssetAllocation", back_populates="profile", cascade="all, delete-orphan")
    vault_docs = relationship("VaultDocument", back_populates="profile", cascade="all, delete-orphan")
    will_drafts = relationship("WillDraft", back_populates="profile", cascade="all, delete-orphan")
    advisor_notes = relationship("AdvisorNote", back_populates="profile", cascade="all, delete-orphan")


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("family_profiles.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False)
    relation = Column(String(50), nullable=False)  # Self, Spouse, Mother, Father, Son, Daughter, Grandson, etc.
    gender = Column(String(20), default="Male")     # Male, Female, Other
    age = Column(Integer, default=30)
    is_alive = Column(Boolean, default=True)
    is_minor = Column(Boolean, default=False)
    marital_status = Column(String(30), default="Married")
    aadhaar_last4 = Column(String(4), nullable=True)
    contact_number = Column(String(20), nullable=True)
    is_class_1_heir = Column(Boolean, default=True)
    is_coparcener = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    profile = relationship("FamilyProfile", back_populates="members")
    allocations = relationship("AssetAllocation", back_populates="beneficiary", cascade="all, delete-orphan")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("family_profiles.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(60), nullable=False)  # commercial_shop, residential_property, agricultural_land, partnership_firm, bank_fd, savings_account, demat_stocks, gold_jewellery, vehicle, liability_loan
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    estimated_value_inr = Column(Float, default=0.0)
    location_or_institution = Column(String(150), nullable=True)
    identifier_number = Column(String(100), nullable=True)
    acquisition_type = Column(String(50), default="self_acquired") # self_acquired, ancestral_huf, inherited, gift
    documents_available = Column(Boolean, default=False)
    current_nominee_name = Column(String(120), nullable=True)
    nominee_relationship = Column(String(50), nullable=True)
    has_nominee_discrepancy = Column(Boolean, default=False)

    profile = relationship("FamilyProfile", back_populates="assets")
    allocations = relationship("AssetAllocation", back_populates="asset", cascade="all, delete-orphan")
    vault_docs = relationship("VaultDocument", back_populates="asset")


class AssetAllocation(Base):
    __tablename__ = "asset_allocations"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("family_profiles.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    beneficiary_id = Column(Integer, ForeignKey("family_members.id", ondelete="CASCADE"), nullable=False)
    share_percentage = Column(Float, default=100.0)
    contingency_clause = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)

    profile = relationship("FamilyProfile", back_populates="allocations")
    asset = relationship("Asset", back_populates="allocations")
    beneficiary = relationship("FamilyMember", back_populates="allocations")


class VaultDocument(Base):
    __tablename__ = "vault_documents"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("family_profiles.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    file_name = Column(String(200), nullable=False)
    file_type = Column(String(50), default="application/pdf")
    file_size_bytes = Column(Integer, default=0)
    encrypted_file_path = Column(String(300), nullable=False)
    original_checksum_sha256 = Column(String(64), nullable=True)
    category = Column(String(50), default="registry_deed")
    upload_date = Column(DateTime, default=utc_now)
    expiry_or_renewal_date = Column(String(50), nullable=True)
    reminder_title = Column(String(150), nullable=True)
    is_encrypted = Column(Boolean, default=True)

    profile = relationship("FamilyProfile", back_populates="vault_docs")
    asset = relationship("Asset", back_populates="vault_docs")


class WillDraft(Base):
    __tablename__ = "will_drafts"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("family_profiles.id", ondelete="CASCADE"), nullable=False)
    executor_name = Column(String(120), nullable=False)
    executor_relationship = Column(String(50), nullable=True)
    alternate_executor_name = Column(String(120), nullable=True)
    guardian_minor_name = Column(String(120), nullable=True)
    guardian_relationship = Column(String(50), nullable=True)
    witness1_name = Column(String(120), nullable=True)
    witness1_address = Column(String(250), nullable=True)
    witness2_name = Column(String(120), nullable=True)
    witness2_address = Column(String(250), nullable=True)
    doctor_name = Column(String(120), nullable=True)
    doctor_reg_no = Column(String(60), nullable=True)
    doctor_certified = Column(Boolean, default=False)
    original_physical_location = Column(String(200), nullable=True)
    status = Column(String(30), default="draft")
    sub_registrar_office = Column(String(150), nullable=True)
    registration_date = Column(String(50), nullable=True)
    registration_number = Column(String(50), nullable=True)
    sro_reminder_date = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    profile = relationship("FamilyProfile", back_populates="will_drafts")


class AdvisorNote(Base):
    __tablename__ = "advisor_notes"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("family_profiles.id", ondelete="CASCADE"), nullable=False)
    author_name = Column(String(120), default="CA / Legal Advisor")
    author_role = Column(String(50), default="Chartered Accountant")
    note_text = Column(Text, nullable=False)
    category = Column(String(50), default="succession_conflict")
    severity = Column(String(20), default="warning")
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("FamilyProfile", back_populates="advisor_notes")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("family_profiles.id", ondelete="CASCADE"), nullable=False)
    username = Column(String(80), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=False)
    role = Column(String(30), nullable=False) # patriarch, heir, advisor
    password_hash = Column(String(250), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    profile = relationship("FamilyProfile", back_populates="users")
