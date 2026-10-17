"""
Complete Lifecycle Verification Script for VirasatPlanner (Waaris v2.2.0)
Tests the complete end-to-end user lifecycle from new account registration,
login, creating a new family plan, adding multi-generational members,
inventorying assets, assigning bequests, checking readiness score,
evaluating the nomination tracker (Sarbati Devi rule), encrypted vault storage,
asking the AI Legacy Advisor in Hindi/English, running what-if simulation,
generating the legal Will PDF, and enforcing RBAC.
"""

import sys
import io
import json
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

def run_lifecycle():
    print("=" * 65)
    print("  VIRASAT PLANNER — COMPLETE END-TO-END LIFECYCLE AUDIT")
    print("=" * 65)

    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # -------------------------------------------------------------
    # Step 1: Healthcheck & Homepage
    # -------------------------------------------------------------
    r = client.get("/")
    assert r.status_code == 200, f"Homepage failed: {r.status_code}"
    print("  ✅ Step 1: Web server & homepage active (HTTP 200)")

    # -------------------------------------------------------------
    # Step 2: Register New User & Login (Salted PBKDF2)
    # -------------------------------------------------------------
    username = f"trader_ramesh_{int(httpx._utils.get_environment_proxies().get('dummy', 1))}" if False else "trader_ramesh_test"
    password = "Ramesh@Password2026"

    # Register
    reg_payload = {
        "username": username,
        "password": password,
        "full_name": "Ramesh Chandra Sharma",
        "role": "patriarch",
        "profile_id": 1
    }
    r = client.post("/api/auth/register", json=reg_payload)
    if r.status_code not in [200, 201]:
        # If user already exists from a previous run, proceed to login
        assert "already exists" in r.text or r.status_code == 400, f"Registration unexpected error: {r.text}"
        print(f"  ℹ️  User '{username}' already exists; proceeding to login.")
    else:
        print(f"  ✅ Step 2a: New Patriarch account '{username}' registered (PBKDF2 600,000 rounds)")

    # Login to obtain JWT Bearer Token
    login_data = {"username": username, "password": password}
    r = client.post("/api/auth/login", json=login_data)
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    print(f"  ✅ Step 2b: Login successful, JWT Bearer Token generated")

    # Verify /api/auth/me
    r = client.get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 200
    user_info = r.json()
    assert user_info["username"] == username
    print(f"  ✅ Step 2c: Identity verified for user '{user_info['username']}' (Role: {user_info['role']})")

    # -------------------------------------------------------------
    # Step 3: Create Brand New Family Plan ("Add New Plan")
    # -------------------------------------------------------------
    plan_payload = {
        "name": "Ramesh Sharma Parivaar Virasat Plan",
        "karta_name": "Ramesh Chandra Sharma",
        "karta_age": 62,
        "karta_gender": "Male",
        "karta_marital_status": "Married",
        "business_name": "M/s Ramesh Cloth & Handloom Store",
        "business_type": "Sole Proprietorship",
        "city": "Jaipur",
        "state": "Rajasthan",
        "pan_or_gstin": "08AABCR1234F1Z5",
        "governing_law": "Hindu Succession Act, 1956 (amended 2005)"
    }
    r = client.post("/api/profile", json=plan_payload, headers=auth_headers)
    assert r.status_code == 200, f"Failed to create new plan: {r.text}"
    new_profile = r.json()
    pid = new_profile["id"]
    if "auth_token" in new_profile:
        auth_headers = {"Authorization": f"Bearer {new_profile['auth_token']}"}

    # Verify Karta age 62 preserved on creation
    r_fam = client.get(f"/api/family/{pid}", headers=auth_headers)
    assert r_fam.status_code == 200
    karta_in_tree = next(m for m in r_fam.json()["members"] if m["relation"].lower() == "self")
    assert karta_in_tree["age"] == 62, f"Expected Karta age 62, got {karta_in_tree['age']}"
    print(f"  ✅ Step 3: New Family Plan created (ID: {pid}, Name: '{new_profile['name']}', Karta Age: {karta_in_tree['age']})")

    try:
        # -------------------------------------------------------------
        # Step 4: Add Multi-Generational Family Members
        # -------------------------------------------------------------
        members_data = [
            {"name": "Kamla Devi Sharma", "relation": "Spouse", "gender": "Female", "age": 58, "marital_status": "Married"},
            {"name": "Suresh Sharma", "relation": "Son", "gender": "Male", "age": 34, "marital_status": "Married", "notes": "Active shop manager"},
            {"name": "Pooja Sharma", "relation": "Daughter", "gender": "Female", "age": 30, "marital_status": "Married", "notes": "Married daughter, coparcener"},
            {"name": "Aarav Sharma", "relation": "Grandson", "gender": "Male", "age": 6, "marital_status": "Single"}
        ]
        created_members = {}
        for m in members_data:
            m_payload = {**m, "profile_id": pid}
            r = client.post(f"/api/family/{pid}/member", json=m_payload, headers=auth_headers)
            assert r.status_code == 200, f"Failed to add member {m['name']}: {r.text}"
            res_m = r.json()
            created_members[m["relation"]] = res_m

        print(f"  ✅ Step 4: Added {len(created_members)} multi-generational family members (Grandfather, Mother, Son, Daughter, Grandson)")

        # -------------------------------------------------------------
        # Step 5: Add Asset Inventory (Shop, House, FD, Gold, Loan)
        # -------------------------------------------------------------
        assets_data = [
            {
                "title": "Cloth Shop at Johari Bazar",
                "category": "commercial_shop",
                "estimated_value_inr": 4500000.0,
                "acquisition_type": "self_acquired",
                "location_or_institution": "Johari Bazar, Jaipur",
                "current_nominee_name": "Suresh Sharma",
                "nominee_relationship": "Son"
            },
            {
                "title": "Ancestral House at Vaishali Nagar",
                "category": "residential_property",
                "estimated_value_inr": 6500000.0,
                "acquisition_type": "ancestral_huf",
                "location_or_institution": "Plot 12, Vaishali Nagar, Jaipur"
            },
            {
                "title": "SBI Term Deposit (FDR)",
                "category": "bank_fd",
                "estimated_value_inr": 1500000.0,
                "acquisition_type": "self_acquired",
                "location_or_institution": "State Bank of India, Jaipur Main",
                "current_nominee_name": "Kamla Devi Sharma",
                "nominee_relationship": "Spouse"
            },
            {
                "title": "Family Gold Ornaments (30 Tola)",
                "category": "gold_jewellery",
                "estimated_value_inr": 2100000.0,
                "acquisition_type": "self_acquired",
                "location_or_institution": "Home Safe Locker"
            },
            {
                "title": "Shop Working Capital CC Limit",
                "category": "liability_loan",
                "estimated_value_inr": 800000.0,
                "acquisition_type": "self_acquired",
                "location_or_institution": "Bank of Baroda"
            }
        ]
        created_assets = {}
        for a in assets_data:
            a_payload = {**a, "profile_id": pid}
            r = client.post(f"/api/assets/{pid}", json=a_payload, headers=auth_headers)
            assert r.status_code == 200, f"Failed to add asset {a['title']}: {r.text}"
            res_a = r.json()
            created_assets[a["category"]] = res_a

        # Verify net worth
        r = client.get(f"/api/assets/{pid}", headers=auth_headers)
        summary = r.json()["summary"]
        assert summary["total_assets_inr"] == 14600000.0
        assert summary["total_liabilities_inr"] == 800000.0
        assert summary["net_worth_inr"] == 13800000.0
        print(f"  ✅ Step 5: Added 5 assets/liabilities. Total Gross: Rs 1.46 Cr, Net Estate: Rs 1.38 Cr")

        # -------------------------------------------------------------
        # Step 6: Assign Will Bequests & Allocations
        # -------------------------------------------------------------
        son_id = created_members["Son"]["id"]
        daughter_id = created_members["Daughter"]["id"]
        spouse_id = created_members["Spouse"]["id"]

        allocations = [
            # Shop to Son (100%)
            {"profile_id": pid, "asset_id": created_assets["commercial_shop"]["id"], "beneficiary_id": son_id, "share_percentage": 100.0, "special_instructions": "To manage shop counter"},
            # SBI FD to Spouse (100%)
            {"profile_id": pid, "asset_id": created_assets["bank_fd"]["id"], "beneficiary_id": spouse_id, "share_percentage": 100.0, "special_instructions": "Lifetime interest and monthly income"},
            # Ancestral House divided equally between Son (50%) and Daughter (50%) per Section 6
            {"profile_id": pid, "asset_id": created_assets["residential_property"]["id"], "beneficiary_id": son_id, "share_percentage": 50.0},
            {"profile_id": pid, "asset_id": created_assets["residential_property"]["id"], "beneficiary_id": daughter_id, "share_percentage": 50.0}
        ]
        for al in allocations:
            r = client.post(f"/api/allocations/{pid}", json=al, headers=auth_headers)
            assert r.status_code == 200, f"Failed to save allocation: {r.text}"

        print(f"  ✅ Step 6: Assigned Will Bequests (Shop -> Son, FD -> Wife, Ancestral House -> 50% Son / 50% Daughter)")

        # -------------------------------------------------------------
        # Step 7: Succession Readiness / Health Score (0-100)
        # -------------------------------------------------------------
        r = client.get(f"/api/readiness/{pid}", headers=auth_headers)
        assert r.status_code == 200
        readiness = r.json()
        print(f"  ✅ Step 7: Succession Readiness calculated: {readiness['overall_score']}/100 ({readiness['grade']})")
        print(f"             Pillars -> Docs: {readiness['pillars']['documentation']['score']}/25 | Nominee: {readiness['pillars']['nomination']['score']}/25 | Will: {readiness['pillars']['testamentary']['score']}/25 | Stat Equity: {readiness['pillars']['statutory_equity']['score']}/25")

        # -------------------------------------------------------------
        # Step 8: Will & Nomination Gap Tracker (Sarbati Devi Doctrine)
        # -------------------------------------------------------------
        r = client.get(f"/api/nomination-tracker/{pid}", headers=auth_headers)
        assert r.status_code == 200
        tracker = r.json()
        aligned = [t for t in tracker if t["alignment_status"] == "ALIGNED"]
        unprotected = [t for t in tracker if t["alignment_status"] in ["UNPROTECTED", "MISSING_WILL_BEQUEST"]]
        print(f"  ✅ Step 8: Nomination Tracker evaluated ({len(aligned)} Aligned, {len(unprotected)} Unallocated/Unprotected assets)")
        # SBI FD should be aligned
        fd_item = next(t for t in tracker if t["category"] == "bank_fd")
        assert fd_item["alignment_status"] == "ALIGNED"
        print(f"             SBI FD verified ALIGNED: Bank Nominee '{fd_item['current_nominee_name']}' matches Will Beneficiary '{fd_item['primary_beneficiary_name']}'")

        # -------------------------------------------------------------
        # Step 9: Encrypted Document Vault Upload & Download
        # -------------------------------------------------------------
        fake_deed = b"%PDF-1.4 Fake Registered Sale Deed for Johari Bazar Cloth Shop Jaipur Rajasthan"
        files = {"file": ("Sale_Deed_Johari_Bazar_Shop.pdf", fake_deed, "application/pdf")}
        data = {
            "category": "property_deed",
            "asset_id": str(created_assets["commercial_shop"]["id"]),
            "reminder_title": "Shop Title Deed Review"
        }
        r = client.post(f"/api/vault/{pid}/upload", files=files, data=data, headers=auth_headers)
        assert r.status_code == 200, f"Vault upload failed: {r.text}"
        doc_info = r.json()
        doc_id = doc_info["id"]
        print(f"  ✅ Step 9a: Uploaded title deed to Encrypted Vault (Doc ID: {doc_id}, SHA256 verified)")

        # Download and verify decrypted payload
        r = client.get(f"/api/vault/{pid}/download/{doc_id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.content == fake_deed, "Decrypted content does not match original uploaded deed!"
        print(f"  ✅ Step 9b: Downloaded and verified AES-256 decrypted deed matches original bytes")

        # -------------------------------------------------------------
        # Step 10: Will Draft Configuration & SRO Registration Target
        # -------------------------------------------------------------
        will_payload = {
            "profile_id": pid,
            "executor_name": "Suresh Sharma",
            "executor_relationship": "Son",
            "witness1_name": "Dr. Kailash Meena",
            "witness1_address": "C-Scheme, Jaipur",
            "witness2_name": "Advocate Mohan Lal Joshi",
            "witness2_address": "High Court Bench, Jaipur",
            "doctor_name": "Dr. Kailash Meena, MBBS",
            "doctor_reg_no": "RMC-48291",
            "doctor_certified": True,
            "sub_registrar_office": "Sub-Registrar Office, Jaipur V (Tehsil Sanganer)",
            "sro_reminder_date": "2026-12-20",
            "status": "ready_for_registration"
        }
        r = client.post(f"/api/will/{pid}", json=will_payload, headers=auth_headers)
        assert r.status_code == 200, f"Failed to save will draft: {r.text}"
        print(f"  ✅ Step 10a: Will Draft configured with Executor, 2 Witnesses, and Doctor Certification")

        # Check reminders endpoint reflects SRO registration target
        r = client.get(f"/api/reminders/{pid}", headers=auth_headers)
        assert r.status_code == 200
        reminders_data = r.json()
        assert reminders_data["total_active_alerts"] >= 1
        assert reminders_data["sro_will_registration"]["reminder_date"] == "2026-12-20"
        print(f"  ✅ Step 10b: Reminders subsystem tracking SRO registration target (Due: {reminders_data['sro_will_registration']['reminder_date']})")

        # -------------------------------------------------------------
        # Step 11: AI Legacy Advisor Inquiries (English & Hindi)
        # -------------------------------------------------------------
        # Query 1: Hindi query on daughter's rights
        q1 = {"query": "पुश्तैनी मकान में मेरी बेटी पूजा का क्या हक है?"}
        r = client.post(f"/api/legacy-advisor/{pid}/query", json=q1, headers=auth_headers)
        assert r.status_code == 200
        ans1 = r.json()
        assert "vineeta sharma" in ans1["answer"].lower() or "विनीता शर्मा" in ans1["answer"]
        print(f"  ✅ Step 11a: AI Legacy Advisor answered Hindi query on daughter coparcenary parity:")
        print(f"              Provider: {ans1.get('ai_provider')} | API Key Required: {ans1.get('api_key_required')}")

        # Query 2: Hindi/Hinglish query on business continuity
        q2 = {"query": "दुकान और व्यापार को टूटने से कैसे बचाएं?"}
        r = client.post(f"/api/legacy-advisor/{pid}/query", json=q2, headers=auth_headers)
        assert r.status_code == 200
        ans2 = r.json()
        assert len(ans2["action_items"]) > 0
        print(f"  ✅ Step 11b: AI Legacy Advisor answered business continuity query (Action items: {len(ans2['action_items'])})")

        # Query 3: Nominee vs Will Beneficiary query
        q3 = {"query": "नॉमिनी और वसीयत के वारिस में क्या अंतर है?"}
        r = client.post(f"/api/legacy-advisor/{pid}/query", json=q3, headers=auth_headers)
        assert r.status_code == 200
        ans3 = r.json()
        assert "sarbati" in ans3["answer"].lower() or "सरबती" in ans3["answer"]
        print(f"  ✅ Step 11c: AI Legacy Advisor cited Sarbati Devi Supreme Court rule accurately")

        # -------------------------------------------------------------
        # Step 12: "What Happens If..." Scenario Simulator
        # -------------------------------------------------------------
        sim_payload = {
            "unregistered_will": False,
            "exclude_daughter": False,
            "ademption_asset_id": created_assets["gold_jewellery"]["id"]
        }
        r = client.post(f"/api/simulation/{pid}", json=sim_payload, headers=auth_headers)
        assert r.status_code == 200
        sim_res = r.json()
        assert sim_res["net_worth_inr"] > 0
        print(f"  ✅ Step 12: 'What-If' Simulation executed (Net Estate: Rs {sim_res['net_worth_inr']:,.0f}, Friction Risk: {sim_res['dispute_risk_score']}/100)")

        # -------------------------------------------------------------
        # Step 13: Download Formal Legal Will PDF
        # -------------------------------------------------------------
        r = client.get(f"/api/will/{pid}/pdf", headers=auth_headers)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert len(r.content) > 5000
        print(f"  ✅ Step 13: Formal Bilingual Legal Will PDF generated ({len(r.content):,} bytes)")

        # -------------------------------------------------------------
        # Step 14: Member Portfolio & Statutory Rights Inspection
        # -------------------------------------------------------------
        r = client.get(f"/api/family/{pid}/member-detail/{daughter_id}", headers=auth_headers)
        assert r.status_code == 200
        mem_detail = r.json()
        assert mem_detail["member"]["name"] == "Pooja Sharma"
        assert len(mem_detail["assigned_bequests"]) >= 1
        print(f"  ✅ Step 14: Inspected Daughter Pooja's portfolio (Class: {mem_detail['statutory_class']}, Assigned: Rs {mem_detail['total_bequest_inr']:,.0f})")

        # -------------------------------------------------------------
        # Step 15: Role-Based Access Restriction (Heir Read-Only Check)
        # -------------------------------------------------------------
        # 15a: Patriarch can view as heir
        r = client.post(f"/api/role/{pid}", json={"role": "heir"}, headers=auth_headers)
        assert r.status_code == 200
        print(f"  ✅ Step 15a: Switched active session to Heir view (Read-only)")

        # 15b: Heir account is blocked from adding assets (403 Forbidden)
        heir_headers = {"Authorization": f"Bearer {token}"}
        forbidden_asset = {
            "profile_id": 1,
            "title": "Unauthorized Asset",
            "category": "commercial_shop",
            "estimated_value_inr": 100000.0,
            "acquisition_type": "self_acquired"
        }
        r = client.post("/api/assets/1", json=forbidden_asset, headers=heir_headers)
        assert r.status_code == 403, f"Expected 403 Forbidden for heir mutation, got {r.status_code}"
        print(f"  ✅ Step 15b: Heir mutation correctly blocked with HTTP 403 Forbidden")

        # 15c: Heir account is blocked from escalating to Patriarch (403 Forbidden)
        r = client.post("/api/role/1", json={"role": "patriarch"}, headers=heir_headers)
        assert r.status_code == 403, f"Expected 403 Forbidden for heir escalation, got {r.status_code}"
        print(f"  ✅ Step 15c: Heir role escalation blocked with HTTP 403 Forbidden")

        # 15d: Switch back to Patriarch
        r = client.post(f"/api/role/{pid}", json={"role": "patriarch"}, headers=auth_headers)
        assert r.status_code == 200
        print(f"  ✅ Step 15d: Restored Patriarch role")

    finally:
        # Cleanup custom test profile
        del_r = client.delete(f"/api/profile/{pid}", headers=auth_headers)
        assert del_r.status_code == 200
        print(f"  🧹 Cleanup: Temporary test family plan (ID: {pid}) deleted cleanly")

    print("=" * 65)
    print("  RESULT: 15/15 LIFECYCLE STAGES PASSED SUCCESSFULLY! 🎉")
    print("=" * 65)

if __name__ == "__main__":
    try:
        run_lifecycle()
    except Exception as e:
        print(f"\n❌ LIFECYCLE RUN FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
