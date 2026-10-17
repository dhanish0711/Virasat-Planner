import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.crypto_vault import (
    encrypt_and_save_file, decrypt_vault_file, audit_vault_integrity,
    validate_vault_file, sanitize_vault_filename
)
from app.succession_engine import calculate_succession_shares
from app.pdf_generator import generate_will_pdf
from app.database import SessionLocal
from app.models import FamilyProfile, FamilyMember, Asset, AssetAllocation, WillDraft, User
from app.auth import RolePermissions

client = TestClient(app)

def get_auth_token(username="karta_sharma", password="Virasat@2026"):
    """Helper to authenticate and return a valid Bearer token."""
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["token"]

def get_auth_headers(username="karta_sharma", password="Virasat@2026"):
    """Helper to return Authorization header dict."""
    token = get_auth_token(username, password)
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------
# Test 1: Public Homepage & Public Endpoints
# ------------------------------------------------------------------
def test_homepage_renders():
    response = client.get("/")
    assert response.status_code == 200
    assert "वारिस" in response.text
    assert "Virasat" in response.text

def test_five_scenarios_seeded():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) >= 5
    names = [s["karta_name"] for s in scenarios]
    assert "Omprakash Sharma" in names
    assert "Mohanlal Gupta" in names
    assert "Rameshwar Verma" in names
    assert "Kailash Chand Agarwal" in names
    assert "Jayantilal Patel" in names


# ------------------------------------------------------------------
# Test 2: SEC-01 — Mandatory Authentication on Sensitive Endpoints
# ------------------------------------------------------------------
def test_anonymous_requests_rejected_on_sensitive_endpoints():
    """Verify that unauthenticated callers are rejected with 401 on protected routes."""
    endpoints = [
        ("GET", "/api/profile/1"),
        ("GET", "/api/family/1"),
        ("GET", "/api/assets/1"),
        ("GET", "/api/allocations/1"),
        ("GET", "/api/will/1"),
        ("GET", "/api/will/1/pdf"),
        ("GET", "/api/vault/1"),
        ("GET", "/api/vault-security-audit"),
        ("GET", "/api/reminders/1"),
        ("GET", "/api/simulation/1"),
        ("GET", "/api/advisor-notes/1"),
        ("GET", "/api/readiness/1"),
        ("GET", "/api/nomination-tracker/1"),
        ("POST", "/api/legacy-advisor/1/query"),
        ("GET", "/api/family/1/member-detail/1")
    ]
    for method, path in endpoints:
        if method == "GET":
            res = client.get(path)
        else:
            res = client.post(path, json={"query": "test"})
        assert res.status_code == 401, f"Expected 401 Unauthorized for anonymous {method} {path}, got {res.status_code}"


# ------------------------------------------------------------------
# Test 3: Family Tree & Asset Inventory (Authenticated)
# ------------------------------------------------------------------
def test_family_tree_members():
    headers = get_auth_headers("karta_sharma")
    response = client.get("/api/family/1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["members"]) >= 6
    karta = next(m for m in data["members"] if m["relation"] == "Self")
    assert karta["name"] == "Omprakash Sharma"

def test_asset_inventory_calculation():
    headers = get_auth_headers("karta_sharma")
    response = client.get("/api/assets/1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    summary = data["summary"]
    assert summary["total_assets_inr"] > 0
    assert summary["total_liabilities_inr"] > 0
    assert summary["net_worth_inr"] == summary["total_assets_inr"] - summary["total_liabilities_inr"]


# ------------------------------------------------------------------
# Test 4: Succession Engine Core Logic
# ------------------------------------------------------------------
def test_succession_engine_sharma_family():
    db = SessionLocal()
    profile = db.query(FamilyProfile).filter(FamilyProfile.id == 1).first()
    members = db.query(FamilyMember).filter(FamilyMember.profile_id == 1).all()
    assets = db.query(Asset).filter(Asset.profile_id == 1).all()
    allocs = db.query(AssetAllocation).filter(AssetAllocation.profile_id == 1).all()

    result = calculate_succession_shares(profile, members, assets, allocs)
    db.close()

    assert result["net_worth_inr"] > 0
    assert result["class_1_heirs_count"] >= 4  # Wife, 2 Sons, 1 Daughter
    assert len(result["intestate_shares"]) > 0
    assert len(result["testate_shares"]) > 0
    assert result["dispute_risk_score"] > 0
    # Nominee mismatch warning should be triggered
    pitfall_titles = [p["title"] for p in result["pitfalls"]]
    assert any("Nominee vs Will Beneficiary Conflict" in t for t in pitfall_titles)
    # Check planning indicator notice is present
    assert "planning_indicator_notice" in result


# ------------------------------------------------------------------
# Test 5: SEC-06 — Crypto Vault AES-128-CBC + HMAC-SHA256 Encryption & Upload Constraints
# ------------------------------------------------------------------
def test_crypto_vault_aes256_encryption():
    raw_content = b"STRICTLY CONFIDENTIAL SHOP DEED #14 KHARI BAOLI"
    enc_path, sha_hash, orig_size = encrypt_and_save_file(raw_content, "test_deed.txt")
    
    assert orig_size == len(raw_content)
    assert len(sha_hash) == 64

    # Read encrypted data on disk and ensure it's NOT plaintext
    with open(enc_path, "rb") as f:
        disk_bytes = f.read()
    assert disk_bytes != raw_content
    assert b"STRICTLY CONFIDENTIAL" not in disk_bytes

    # Decrypt and verify matching plaintext
    decrypted = decrypt_vault_file(enc_path, expected_sha256=sha_hash)
    assert decrypted == raw_content

def test_vault_file_validation_and_size_limits():
    """Verify that executable scripts and empty files are rejected."""
    with pytest.raises(Exception) as excinfo:
        validate_vault_file("malicious_script.bat", b"echo hacked")
    assert "forbidden" in str(excinfo.value).lower() or "security" in str(excinfo.value).lower()

    with pytest.raises(Exception):
        validate_vault_file("empty.pdf", b"")

def test_vault_security_audit_api():
    """Vault security audit requires Patriarch or Advisor authorization."""
    # Anonymous fails 401
    client.cookies.clear()
    assert client.get("/api/vault-security-audit").status_code == 401

    # Heir role fails 403
    heir_headers = get_auth_headers("rohit_heir")
    assert client.get("/api/vault-security-audit", headers=heir_headers).status_code == 403

    # Patriarch succeeds 200
    karta_headers = get_auth_headers("karta_sharma")
    res = client.get("/api/vault-security-audit", headers=karta_headers)
    assert res.status_code == 200
    audit = res.json()
    assert audit["status"] in ["SECURE", "DEGRADED", "FAILED"]
    assert audit["total_files"] >= 1
    assert audit["corrupted_or_tampered_files"] == 0
    assert "AES-128-CBC" in audit["cipher"]


# ------------------------------------------------------------------
# Test 6: SEC-07 & LEGAL-01/02 — ReportLab Will PDF Generation & Escaping
# ------------------------------------------------------------------
def test_reportlab_will_pdf_generation():
    headers = get_auth_headers("karta_sharma")
    response = client.get("/api/will/1/pdf", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
    assert len(response.content) > 1000

def test_pdf_escapes_special_characters():
    """Verify ReportLab Paragraph safe escaping when text contains XML characters."""
    db = SessionLocal()
    profile = db.query(FamilyProfile).filter(FamilyProfile.id == 1).first()
    members = db.query(FamilyMember).filter(FamilyMember.profile_id == 1).all()
    assets = db.query(Asset).filter(Asset.profile_id == 1).all()
    allocs = db.query(AssetAllocation).filter(AssetAllocation.profile_id == 1).all()

    # Pass strings with XML/HTML injection characters
    will_data = {
        "executor_name": "Rohit <Executor & Trustee> Sharma",
        "executor_relationship": "Son <Eldest>",
        "witness1_name": "Witness & Sons <Test>",
        "doctor_name": None # Test no invented default
    }
    pdf_bytes = generate_will_pdf(profile, will_data, members, assets, allocs)
    db.close()
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000


# ------------------------------------------------------------------
# Test 7: SEC-02 — RBAC Heir Mutation Restriction & Role Escalation Prevention
# ------------------------------------------------------------------
def test_rbac_heir_mutation_restriction():
    heir_headers = get_auth_headers("rohit_heir")

    # 1. Heir attempting to add an asset must be denied 403
    forbidden_res = client.post("/api/assets/1", json={
        "profile_id": 1,
        "title": "Unauthorized Asset",
        "category": "commercial_shop",
        "estimated_value_inr": 5000000.0,
        "acquisition_type": "self_acquired"
    }, headers=heir_headers)
    assert forbidden_res.status_code == 403

    # 2. Heir attempting to escalate role to patriarch must be denied 403
    escalate_res = client.post("/api/role/switch?profile_id=1", json={"role": "patriarch"}, headers=heir_headers)
    assert escalate_res.status_code == 403

    # 3. Patriarch can view as heir or switch back
    karta_headers = get_auth_headers("karta_sharma")
    switch_res = client.post("/api/role/switch?profile_id=1", json={"role": "heir"}, headers=karta_headers)
    assert switch_res.status_code == 200
    reset_res = client.post("/api/role/switch?profile_id=1", json={"role": "patriarch"}, headers=karta_headers)
    assert reset_res.status_code == 200


# ------------------------------------------------------------------
# Test 8: SEC-03 — Cross-Family Isolation
# ------------------------------------------------------------------
def test_cross_family_isolation():
    """User belonging to Family 1 cannot access Family 2's data."""
    sharma_headers = get_auth_headers("karta_sharma") # Profile 1

    # Attempting to read Family 2's profile
    res_prof2 = client.get("/api/profile/2", headers=sharma_headers)
    assert res_prof2.status_code == 403
    assert "Cross-Family" in res_prof2.json().get("detail", "")

    # Attempting to add an asset to Family 2
    res_asset2 = client.post("/api/assets/2", json={
        "profile_id": 2,
        "title": "Cross Family Intrusive Shop",
        "category": "commercial_shop",
        "estimated_value_inr": 1000000.0
    }, headers=sharma_headers)
    assert res_asset2.status_code == 403


# ------------------------------------------------------------------
# Test 9: SEC-08 & DATA-02 — Allocation Validation & Percentage Bounds
# ------------------------------------------------------------------
def test_allocation_validation_rules():
    karta_headers = get_auth_headers("karta_sharma")

    # 1. Total allocation cannot exceed 100% (Bug fix test)
    # Attempting to allocate 120%
    over_alloc = client.post("/api/allocations/1", json={
        "profile_id": 1,
        "asset_id": 1,
        "beneficiary_id": 2,
        "share_percentage": 120.0
    }, headers=karta_headers)
    assert over_alloc.status_code in [400, 422]

    # 2. Cross-family allocation rejection (Asset from Family 2 into Family 1)
    cross_alloc = client.post("/api/allocations/1", json={
        "profile_id": 1,
        "asset_id": 9999, # Non-existent or foreign asset
        "beneficiary_id": 2,
        "share_percentage": 50.0
    }, headers=karta_headers)
    assert cross_alloc.status_code == 400


# ------------------------------------------------------------------
# Test 10: Educational Sub-Registrar Office Guide
# ------------------------------------------------------------------
def test_sro_guide_endpoint():
    res = client.get("/api/sro-guide")
    assert res.status_code == 200
    data = res.json()
    assert "Sub-Registrar" in data["title"]
    assert len(data["step_by_step_checklist"]) == 5


# ------------------------------------------------------------------
# Test 11: Dynamic Custom Profile Creation and Data Entry
# ------------------------------------------------------------------
def test_user_can_create_custom_profile_and_enter_data():
    # 1. User enters their own estate info
    create_res = client.post("/api/profile", json={
        "name": "Mishra Family Trust & Estate",
        "karta_name": "Shri Ramakant Mishra",
        "business_name": "M/s Mishra Sarees & Cloth Emporium",
        "business_type": "Sole Proprietorship",
        "city": "Varanasi",
        "state": "Uttar Pradesh",
        "religion": "Hindu",
        "pan_or_gstin": "09AAAFM1294C1Z9",
        "governing_law": "Hindu Succession Act, 1956 (amended 2005)"
    })
    assert create_res.status_code == 200
    new_profile = create_res.json()
    prof_id = new_profile["id"]
    auth_token = new_profile["auth_token"]
    custom_headers = {"Authorization": f"Bearer {auth_token}"}

    assert new_profile["karta_name"] == "Shri Ramakant Mishra"
    assert new_profile["city"] == "Varanasi"

    # Verify Karta is in the family tree
    fam_res = client.get(f"/api/family/{prof_id}", headers=custom_headers)
    assert fam_res.status_code == 200
    members = fam_res.json()["members"]
    assert len(members) == 1
    assert members[0]["name"] == "Shri Ramakant Mishra"
    assert members[0]["relation"] == "Self"

    # 2. User adds custom family member
    add_mem_res = client.post(f"/api/family/{prof_id}/member", json={
        "profile_id": prof_id,
        "name": "Radha Mishra",
        "relation": "Spouse",
        "gender": "Female",
        "age": 48,
        "marital_status": "Married",
        "notes": "Wife & co-decision maker"
    }, headers=custom_headers)
    assert add_mem_res.status_code == 200
    spouse = add_mem_res.json()
    spouse_id = spouse["id"]

    # 3. User adds custom asset
    add_ast_res = client.post(f"/api/assets/{prof_id}", json={
        "profile_id": prof_id,
        "title": "Godowlia Chowk Saree Showroom #4",
        "category": "commercial_shop",
        "estimated_value_inr": 25000000.0,
        "identifier_number": "Deed 8821/VNS",
        "acquisition_type": "self_acquired"
    }, headers=custom_headers)
    assert add_ast_res.status_code == 200
    shop = add_ast_res.json()
    shop_id = shop["id"]

    # 4. User allocates bequest
    alloc_res = client.post(f"/api/allocations/{prof_id}", json={
        "profile_id": prof_id,
        "asset_id": shop_id,
        "beneficiary_id": spouse_id,
        "share_percentage": 100.0,
        "special_instructions": "Complete showroom management granted to wife Radha"
    }, headers=custom_headers)
    assert alloc_res.status_code == 200

    # 5. User checks simulation
    sim_res = client.get(f"/api/simulation/{prof_id}", headers=custom_headers)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["net_worth_inr"] == 25000000.0
    assert len(sim_data["testate_shares"]) >= 1

    # 6. User exports custom PDF draft
    pdf_res = client.get(f"/api/will/{prof_id}/pdf", headers=custom_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.content.startswith(b"%PDF-")

    # 7. Clean up custom profile
    del_res = client.delete(f"/api/profile/{prof_id}", headers=custom_headers)
    assert del_res.status_code == 200


# ------------------------------------------------------------------
# Test 12: Authentication Token & Session Verification
# ------------------------------------------------------------------
def test_user_auth_pbkdf2_token_and_rbac():
    # 1. Invalid login fails
    bad_login = client.post("/api/auth/login", json={"username": "karta_sharma", "password": "WrongPassword"})
    assert bad_login.status_code == 401

    # 2. Valid login for Karta succeeds and issues bearer token
    karta_login = client.post("/api/auth/login", json={"username": "karta_sharma", "password": "Virasat@2026"})
    assert karta_login.status_code == 200
    karta_data = karta_login.json()
    assert "token" in karta_data
    assert karta_data["user"]["role"] == "patriarch"
    karta_token = karta_data["token"]

    # 3. Verify /api/auth/me with Bearer token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {karta_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "karta_sharma"

    # 4. Valid login for Heir
    heir_login = client.post("/api/auth/login", json={"username": "rohit_heir", "password": "Virasat@2026"})
    assert heir_login.status_code == 200
    heir_token = heir_login.json()["token"]
    assert heir_login.json()["user"]["role"] == "heir"


# ------------------------------------------------------------------
# Test 13: Reminders and Deadlines Subsystem
# ------------------------------------------------------------------
def test_reminders_and_sro_subsystem():
    headers = get_auth_headers("karta_sharma")

    # 1. Fetch reminders for Profile 1
    res = client.get("/api/reminders/1", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "sro_will_registration" in data
    assert "vault_expiries" in data

    # 2. Update SRO reminder date
    update_res = client.post("/api/reminders/1/sro", json={"sro_reminder_date": "2026-12-15"}, headers=headers)
    assert update_res.status_code == 200
    assert update_res.json()["sro_reminder_date"] == "2026-12-15"

    # 3. Verify updated date
    verify_res = client.get("/api/reminders/1", headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["sro_will_registration"]["reminder_date"] == "2026-12-15"


# ------------------------------------------------------------------
# Test 14: Interactive Simulator Toggles
# ------------------------------------------------------------------
def test_interactive_simulator_toggles():
    headers = get_auth_headers("karta_sharma")

    # 1. Unregistered will toggle
    sim_unreg = client.post("/api/simulation/1", json={"unregistered_will": True}, headers=headers)
    assert sim_unreg.status_code == 200
    pitfall_titles = [p["title"] for p in sim_unreg.json()["pitfalls"]]
    assert any("Unregistered Will" in t for t in pitfall_titles)

    # 2. Exclude daughter toggle
    sim_daughter = client.post("/api/simulation/1", json={"exclude_daughter": True}, headers=headers)
    assert sim_daughter.status_code == 200
    pitfall_titles2 = [p["title"] for p in sim_daughter.json()["pitfalls"]]
    assert any("Coparcenary Rights Violation" in t for t in pitfall_titles2)

    # 3. Ademption asset toggle
    sim_ademption = client.post("/api/simulation/1", json={"ademption_asset_id": 1}, headers=headers)
    assert sim_ademption.status_code == 200
    pitfall_titles3 = [p["title"] for p in sim_ademption.json()["pitfalls"]]
    assert any("Ademption" in t for t in pitfall_titles3)


# ------------------------------------------------------------------
# Test 15: Verma Family Predeceased Son Branch Representation (HSA Sec 8/10 Rule 3)
# ------------------------------------------------------------------
def test_verma_predeceased_son_class1_representation():
    verma_headers = get_auth_headers("karta_verma")
    fam_res = client.get("/api/family/3", headers=verma_headers)
    assert fam_res.status_code == 200
    members = fam_res.json()["members"]

    sunidhi = next((m for m in members if m["relation"] == "Daughter-in-law"), None)
    harsh = next((m for m in members if m["relation"] == "Grandson"), None)

    assert sunidhi is not None
    assert harsh is not None
    assert sunidhi["is_class_1_heir"] == True
    assert harsh["is_class_1_heir"] == True

    sim_res = client.get("/api/simulation/3", headers=verma_headers)
    assert sim_res.status_code == 200
    shares = sim_res.json()["intestate_shares"]
    sunidhi_share = next((s for s in shares if s["name"] == sunidhi["name"]), None)
    harsh_share = next((s for s in shares if s["name"] == harsh["name"]), None)

    assert sunidhi_share is not None and sunidhi_share["share_pct"] > 0
    assert harsh_share is not None and harsh_share["share_pct"] > 0


# ------------------------------------------------------------------
# Test 16: Deficit Estate Handling (Liabilities > Assets)
# ------------------------------------------------------------------
def test_succession_engine_deficit_estate():
    """Verify that deficit estate is not concealed by max(0, ...)."""
    class MockProfile:
        religion = "Hindu"
        governing_law = "Hindu Succession Act, 1956 (amended 2005)"

    class MockMember:
        id = 1
        name = "Kavita Sharma"
        relation = "Wife"
        is_alive = True
        notes = ""

    class MockAsset:
        id = 1
        title = "Chandni Chowk Shop"
        category = "commercial_shop"
        estimated_value_inr = 1000000.0
        acquisition_type = "self_acquired"

    class MockDebt:
        id = 2
        title = "Bank Commercial Loan"
        category = "liability_loan"
        estimated_value_inr = 3000000.0  # Outstanding debt 30L exceeds 10L asset

    res = calculate_succession_shares(MockProfile(), [MockMember()], [MockAsset(), MockDebt()], [])
    assert res["net_worth_inr"] == -2000000.0
    assert any("Deficit Estate" in p["title"] for p in res["pitfalls"])


# ------------------------------------------------------------------
# Test 17: Religion-Based Branching Review Flags
# ------------------------------------------------------------------
def test_succession_engine_religion_flags():
    """Verify that Muslim and Christian regimes flag manual legal review required."""
    class MuslimProfile:
        religion = "Muslim"
        governing_law = "Muslim Personal Law (Shariat) Application Act, 1937"

    class MockMember:
        id = 1
        name = "Fatima"
        relation = "Wife"
        is_alive = True
        notes = ""

    res_muslim = calculate_succession_shares(MuslimProfile(), [MockMember()], [], [])
    assert res_muslim["manual_legal_review_required"] == True
    assert any("Muslim succession depends on applicable school" in note for note in res_muslim["legal_review_notes"])


# ------------------------------------------------------------------
# Test 18: Legacy OS Modules — Readiness, Nomination Tracker & AI Advisor
# ------------------------------------------------------------------
def test_legacy_os_modules_endpoints():
    """Verify that Readiness Score, Nomination Tracker, AI Advisor, and Member Detail operate properly."""
    headers = get_auth_headers("karta_sharma")

    # 1. Readiness Score
    r_readiness = client.get("/api/readiness/1", headers=headers)
    assert r_readiness.status_code == 200
    readiness = r_readiness.json()
    assert "overall_score" in readiness
    assert 0 <= readiness["overall_score"] <= 100
    assert "pillars" in readiness
    assert "documentation" in readiness["pillars"]
    assert "nomination" in readiness["pillars"]
    assert "testamentary" in readiness["pillars"]
    assert "statutory_equity" in readiness["pillars"]
    assert len(readiness["priority_actions"]) > 0

    # 2. Nomination vs Will Tracker
    r_tracker = client.get("/api/nomination-tracker/1", headers=headers)
    assert r_tracker.status_code == 200
    tracker = r_tracker.json()
    assert isinstance(tracker, list)
    assert len(tracker) > 0
    first = tracker[0]
    assert "asset_id" in first
    assert "alignment_status" in first
    assert "vault_document_status" in first
    assert "remedy" in first

    # 3. AI Legacy Advisor Query
    r_advisor = client.post(
        "/api/legacy-advisor/1/query",
        json={"query": "What are our nominee discrepancies and biggest gaps?"},
        headers=headers
    )
    assert r_advisor.status_code == 200
    adv = r_advisor.json()
    assert "answer" in adv
    assert len(adv["answer"]) > 100
    assert len(adv["action_items"]) > 0
    assert len(adv["suggested_followups"]) > 0

    # 4. Member Profile Detail
    # Get members to find Sharma's ID
    fam = client.get("/api/family/1", headers=headers).json()
    first_member = fam["members"][0]
    r_detail = client.get(f"/api/family/1/member-detail/{first_member['id']}", headers=headers)
    assert r_detail.status_code == 200
    detail = r_detail.json()
    assert "member" in detail
    assert "assigned_bequests" in detail
    assert "statutory_class" in detail
    assert "coparcenary_rights" in detail


# ------------------------------------------------------------------
# Test 24: Custom Karta Age & Explicit Member Age Lifecycle
# ------------------------------------------------------------------
def test_create_profile_with_custom_karta_age_and_update():
    """Verify that user-entered Karta age is preserved on creation, editable on update, and member age is exact."""
    profile_payload = {
        "name": "Agnihotri Family Heritage Plan",
        "karta_name": "Dinanath Agnihotri",
        "karta_age": 63,
        "karta_gender": "Male",
        "karta_marital_status": "Married",
        "business_name": "M/s Agnihotri Hardware",
        "business_type": "Sole Proprietorship",
        "city": "Lucknow",
        "state": "Uttar Pradesh",
        "governing_law": "Hindu Succession Act, 1956 (amended 2005)"
    }
    create_res = client.post("/api/profile", json=profile_payload)
    assert create_res.status_code == 200, f"Failed to create profile: {create_res.text}"
    created = create_res.json()
    new_profile_id = created["id"]
    token = created["auth_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Verify Karta member was initialized with user-entered age (63, not 52)
    fam_res = client.get(f"/api/family/{new_profile_id}", headers=headers)
    assert fam_res.status_code == 200
    members = fam_res.json()["members"]
    karta = next(m for m in members if m["relation"].lower() == "self")
    assert karta["name"] == "Dinanath Agnihotri"
    assert karta["age"] == 63, f"Expected Karta age 63, got {karta['age']}"

    # 2. Update Karta age to 64 via profile update
    upd_res = client.put(f"/api/profile/{new_profile_id}", json={"karta_age": 64}, headers=headers)
    assert upd_res.status_code == 200
    fam_res2 = client.get(f"/api/family/{new_profile_id}", headers=headers)
    karta2 = next(m for m in fam_res2.json()["members"] if m["relation"].lower() == "self")
    assert karta2["age"] == 64, f"Expected updated Karta age 64, got {karta2['age']}"

    # 3. Add family member with explicit age 35
    mem_payload = {
        "profile_id": new_profile_id,
        "name": "Alok Agnihotri",
        "relation": "Son",
        "gender": "Male",
        "age": 35,
        "marital_status": "Married"
    }
    add_res = client.post(f"/api/family/{new_profile_id}/member", json=mem_payload, headers=headers)
    assert add_res.status_code == 200
    fam_res3 = client.get(f"/api/family/{new_profile_id}", headers=headers)
    son = next(m for m in fam_res3.json()["members"] if m["name"] == "Alok Agnihotri")
    assert son["age"] == 35, f"Expected son age 35, got {son['age']}"


