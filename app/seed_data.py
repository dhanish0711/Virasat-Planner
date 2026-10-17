"""
Preloads 5 realistic synthetic Indian trader family scenarios for:
- Demonstration
- Usability testing
- Legal scenario simulations
"""

from app.models import FamilyProfile, FamilyMember, Asset, AssetAllocation, WillDraft, AdvisorNote, VaultDocument, User
from app.crypto_vault import encrypt_and_save_file
from app.auth_service import hash_password

def seed_database(db):
    # Check if already seeded
    if db.query(FamilyProfile).count() > 0:
        return

    # -------------------------------------------------------------
    # SCENARIO 1: Sharma Kirana & General Store (Khari Baoli, Delhi)
    # -------------------------------------------------------------
    p1 = FamilyProfile(
        name="Sharma Family Estate",
        karta_name="Omprakash Sharma",
        business_name="M/s Sharma Kirana & General Store",
        business_type="Sole Proprietorship",
        city="Old Delhi",
        state="Delhi",
        religion="Hindu",
        governing_law="Hindu Succession Act, 1956 (amended 2005)",
        pan_or_gstin="07AAFPS1294C1Z5",
        active_role="patriarch"
    )
    db.add(p1)
    db.flush()

    # Seed User Accounts for Scenario 1
    u1_karta = User(profile_id=p1.id, username="karta_sharma", full_name="Omprakash Sharma (Karta)", role="patriarch", password_hash=hash_password("Virasat@2026"))
    u1_heir = User(profile_id=p1.id, username="rohit_heir", full_name="Rohit Sharma (Heir)", role="heir", password_hash=hash_password("Virasat@2026"))
    u1_adv = User(profile_id=p1.id, username="advisor_chawla", full_name="CA Ramesh Chawla", role="advisor", password_hash=hash_password("Virasat@2026"))
    db.add_all([u1_karta, u1_heir, u1_adv])


    # Family Members
    m1_self = FamilyMember(profile_id=p1.id, name="Omprakash Sharma", relation="Self", gender="Male", age=62, is_alive=True, marital_status="Married", is_class_1_heir=False)
    m1_wife = FamilyMember(profile_id=p1.id, name="Shanti Devi", relation="Spouse", gender="Female", age=58, is_alive=True, marital_status="Married", is_class_1_heir=True, notes="Wife, homemaker")
    m1_son1 = FamilyMember(profile_id=p1.id, name="Rohit Sharma", relation="Son", gender="Male", age=35, is_alive=True, marital_status="Married", is_class_1_heir=True, notes="Elder son, full-time store manager")
    m1_son2 = FamilyMember(profile_id=p1.id, name="Amit Sharma", relation="Son", gender="Male", age=31, is_alive=True, marital_status="Single", is_class_1_heir=True, notes="Younger son, Software Engineer in Bengaluru")
    m1_dau  = FamilyMember(profile_id=p1.id, name="Sunita Sharma (now Goyal)", relation="Daughter", gender="Female", age=33, is_alive=True, marital_status="Married", is_class_1_heir=True, notes="Married daughter living in Jaipur")
    m1_dil  = FamilyMember(profile_id=p1.id, name="Pooja Sharma", relation="Daughter-in-law", gender="Female", age=32, is_alive=True, marital_status="Married", is_class_1_heir=False)
    m1_gson = FamilyMember(profile_id=p1.id, name="Aarav Sharma", relation="Grandson", gender="Male", age=6, is_alive=True, is_minor=True, marital_status="Single", is_class_1_heir=False)

    for m in [m1_self, m1_wife, m1_son1, m1_son2, m1_dau, m1_dil, m1_gson]:
        db.add(m)
    db.flush()

    # Assets
    a1_shop = Asset(
        profile_id=p1.id, category="commercial_shop", title="Commercial Shop #14 Khari Baoli",
        description="Ground floor retail grocery shop (350 sq ft) + Mezzanine godown",
        estimated_value_inr=18000000.0, location_or_institution="Khari Baoli, Chandni Chowk, Delhi",
        identifier_number="Shop Registry Deed No. 4492/1986", acquisition_type="self_acquired",
        documents_available=True, current_nominee_name="Rohit Sharma", nominee_relationship="Son"
    )
    a1_home = Asset(
        profile_id=p1.id, category="residential_property", title="Ancestral Daryaganj Residential House",
        description="Three-story residential building (180 sq yards)",
        estimated_value_inr=12000000.0, location_or_institution="Daryaganj, Old Delhi",
        identifier_number="Khasra #128/4, Municipal Ward 6", acquisition_type="ancestral_huf",
        documents_available=True, current_nominee_name="Shanti Devi", nominee_relationship="Spouse"
    )
    a1_fd = Asset(
        profile_id=p1.id, category="bank_fd", title="SBI Fixed Deposits & Current Account",
        description="Auto-renewing 3-year cumulative Term Deposits (₹35L) + Trader Current A/c (₹10L)",
        estimated_value_inr=4500000.0, location_or_institution="State Bank of India, Chandni Chowk Branch",
        identifier_number="SBI A/c **4821 & FDR #994021", acquisition_type="self_acquired",
        documents_available=True, current_nominee_name="Amit Sharma", nominee_relationship="Son",
        has_nominee_discrepancy=True # Nominee is younger son in Bengaluru, but will draft gives it to wife & daughter!
    )
    a1_gold = Asset(
        profile_id=p1.id, category="gold_jewellery", title="Physical Gold & Diamond Jewellery (65 Tolas)",
        description="Traditional ancestral bridal jewellery (40 tolas) + Self-purchased gold bullion coins (25 tolas)",
        estimated_value_inr=5200000.0, location_or_institution="PNB Locker #118, Khari Baoli",
        identifier_number="Locker Key Registry #118", acquisition_type="inherited",
        documents_available=True, current_nominee_name="Shanti Devi", nominee_relationship="Spouse"
    )
    a1_van = Asset(
        profile_id=p1.id, category="vehicle", title="Tata Ace Commercial Delivery Vehicle",
        description="Delivery van used for bulk supplies across Delhi NCR",
        estimated_value_inr=450000.0, location_or_institution="DL-1L-AA-3842",
        identifier_number="Reg: DL1LAA3842", acquisition_type="self_acquired",
        documents_available=True, current_nominee_name="Rohit Sharma", nominee_relationship="Son"
    )
    a1_loan = Asset(
        profile_id=p1.id, category="liability_loan", title="Wholesale Supplier Credit & Business OD",
        description="Sundry trade creditors in Khari Baoli + PNB Cash Credit limit",
        estimated_value_inr=1800000.0, location_or_institution="Punjab National Bank",
        identifier_number="CC A/c #938201", acquisition_type="self_acquired",
        documents_available=True
    )

    for a in [a1_shop, a1_home, a1_fd, a1_gold, a1_van, a1_loan]:
        db.add(a)
    db.flush()

    # Asset Allocations (Will Bequests)
    alloc1 = AssetAllocation(profile_id=p1.id, asset_id=a1_shop.id, beneficiary_id=m1_son1.id, share_percentage=100.0, special_instructions="Sole ownership of shop & ongoing kirana goodwill granted to Rohit to ensure business continuity.")
    alloc2 = AssetAllocation(profile_id=p1.id, asset_id=a1_home.id, beneficiary_id=m1_wife.id, share_percentage=50.0, special_instructions="Life interest for wife Shanti Devi with absolute right of residence.")
    alloc3 = AssetAllocation(profile_id=p1.id, asset_id=a1_home.id, beneficiary_id=m1_son2.id, share_percentage=50.0, special_instructions="Co-ownership given to Amit Sharma to compensate for shop going to elder brother.")
    alloc4 = AssetAllocation(profile_id=p1.id, asset_id=a1_fd.id, beneficiary_id=m1_wife.id, share_percentage=60.0, special_instructions="Liquid financial security for medical & living expenses.")
    alloc5 = AssetAllocation(profile_id=p1.id, asset_id=a1_fd.id, beneficiary_id=m1_dau.id, share_percentage=40.0, special_instructions="Liquid cash bequest for daughter Sunita.")
    alloc6 = AssetAllocation(profile_id=p1.id, asset_id=a1_gold.id, beneficiary_id=m1_wife.id, share_percentage=50.0, special_instructions="Stridhan and personal ornaments.")
    alloc7 = AssetAllocation(profile_id=p1.id, asset_id=a1_gold.id, beneficiary_id=m1_dau.id, share_percentage=50.0, special_instructions="Ancestral necklace and gold bangles to daughter.")
    alloc8 = AssetAllocation(profile_id=p1.id, asset_id=a1_van.id, beneficiary_id=m1_son1.id, share_percentage=100.0, special_instructions="Commercial vehicle linked with retail shop operations.")

    for al in [alloc1, alloc2, alloc3, alloc4, alloc5, alloc6, alloc7, alloc8]:
        db.add(al)
    db.flush()

    # Will Draft
    w1 = WillDraft(
        profile_id=p1.id,
        executor_name="Rohit Sharma",
        executor_relationship="Elder Son / Store Manager",
        alternate_executor_name="Adv. Ramesh Chandra Aggarwal",
        guardian_minor_name="Rohit Sharma & Pooja Sharma",
        guardian_relationship="Parents",
        witness1_name="Shri Vinod Bihari Gupta (Neighbor Merchant)",
        witness1_address="Shop #12, Khari Baoli, Delhi - 110006",
        witness2_name="CA Naveen Jain (Family Auditor)",
        witness2_address="F-14, Connaught Place, New Delhi - 110001",
        doctor_name="Dr. Harish C. Manchanda, MBBS",
        doctor_reg_no="DMC-18290",
        doctor_certified=True,
        original_physical_location="Home Godrej Fireproof Safe + Copy at SBI Locker #42",
        status="reviewed_by_ca",
        sub_registrar_office="Sub-Registrar Office-I, Kashmere Gate, Central Delhi",
        registration_date="2026-03-15",
        registration_number="DL/SR1/WILL/2026/8421",
        sro_reminder_date="2026-11-01"
    )
    db.add(w1)

    # Advisor Notes
    adv1 = AdvisorNote(
        profile_id=p1.id,
        author_name="CA Naveen Jain",
        author_role="Chartered Accountant",
        note_text="CRITICAL NOMINEE MISMATCH: SBI Fixed Deposits have Amit (younger son) as registered bank nominee, but the will allocates 60% to mother Shanti Devi and 40% to daughter Sunita. Please submit a revised Form DA-1 to SBI to avoid bank payout hold-ups.",
        category="tax_risk",
        severity="warning"
    )
    adv2 = AdvisorNote(
        profile_id=p1.id,
        author_name="Adv. Ramesh Aggarwal",
        author_role="High Court Advocate",
        note_text="Daryaganj property is recorded as Ancestral HUF. Both sons and married daughter Sunita have equal birthright coparcenary rights under 2005 HSA amendment. We recommend executing a registered Family Settlement Deed during Karta's lifetime to prevent future partition challenges.",
        category="succession_conflict",
        severity="critical"
    )
    db.add(adv1)
    db.add(adv2)

    # Add Encrypted Mock Vault Documents with Active Renewal Reminders
    sample_registry_text = b"GOVERNMENT OF NCT OF DELHI - DEED OF CONVEYANCE / SALE DEED. Shop #14 Khari Baoli. Area: 350 sq ft. Consideration: INR 18,00,000 (1986). Vendor: Lala Radheshyam. Purchaser: Shri Omprakash Sharma. Registered Book I, Vol 1492, Page 88-92."
    f_path, f_hash, f_size = encrypt_and_save_file(sample_registry_text, "Sale_Deed_Shop14_KhariBaoli.txt")
    v1 = VaultDocument(
        profile_id=p1.id, asset_id=a1_shop.id, file_name="Sale_Deed_Shop14_KhariBaoli.pdf",
        file_type="application/pdf", file_size_bytes=f_size, encrypted_file_path=f_path,
        original_checksum_sha256=f_hash, category="registry_deed", is_encrypted=True,
        expiry_or_renewal_date="2026-11-15", reminder_title="MCD Commercial Shop Health License Annual Renewal"
    )
    db.add(v1)

    sample_fd_text = b"STATE BANK OF INDIA - FIXED DEPOSIT RECEIPT. A/c #99402129481. Principal: INR 35,00,000. Interest Rate: 7.25% p.a. Maturity Date: 12-Nov-2027. First Holder: Omprakash Sharma. Nominee: Amit Sharma (Son)."
    f_path2, f_hash2, f_size2 = encrypt_and_save_file(sample_fd_text, "SBI_Term_Deposit_Receipt_35L.txt")
    v2 = VaultDocument(
        profile_id=p1.id, asset_id=a1_fd.id, file_name="SBI_Term_Deposit_Receipt_35L.pdf",
        file_type="application/pdf", file_size_bytes=f_size2, encrypted_file_path=f_path2,
        original_checksum_sha256=f_hash2, category="fd_receipt", is_encrypted=True,
        expiry_or_renewal_date="2027-11-12", reminder_title="SBI Term Deposit Maturity & Auto-Renewal Check"
    )
    db.add(v2)


    # -------------------------------------------------------------
    # SCENARIO 2: Gupta Cloth Merchant & Sons (Surat / Chandni Chowk)
    # -------------------------------------------------------------
    p2 = FamilyProfile(
        name="Gupta Textile Trading Family",
        karta_name="Mohanlal Gupta",
        business_name="M/s Gupta Cloth Merchant & Sons",
        business_type="Partnership Firm",
        city="Surat",
        state="Gujarat",
        religion="Hindu",
        governing_law="Hindu Succession Act, 1956 (amended 2005)",
        pan_or_gstin="24AAEFG8831K1Z2",
        active_role="patriarch"
    )
    db.add(p2)
    db.flush()

    u2_karta = User(profile_id=p2.id, username="karta_gupta", full_name="Mohanlal Gupta (Karta)", role="patriarch", password_hash=hash_password("Virasat@2026"))
    u2_heir = User(profile_id=p2.id, username="vikas_heir", full_name="Vikas Gupta (Heir)", role="heir", password_hash=hash_password("Virasat@2026"))
    u2_adv = User(profile_id=p2.id, username="advisor_patel", full_name="CA Bhupendra Patel", role="advisor", password_hash=hash_password("Virasat@2026"))
    db.add_all([u2_karta, u2_heir, u2_adv])

    m2_self = FamilyMember(profile_id=p2.id, name="Mohanlal Gupta", relation="Self", gender="Male", age=68, is_alive=True, marital_status="Married", is_class_1_heir=False)
    m2_moth = FamilyMember(profile_id=p2.id, name="Kamla Devi Gupta", relation="Mother", gender="Female", age=89, is_alive=True, marital_status="Widow", is_class_1_heir=True, notes="Elderly mother, Class I statutory heir under Section 10 HSA!")
    m2_wife = FamilyMember(profile_id=p2.id, name="Pushpa Gupta", relation="Spouse", gender="Female", age=64, is_alive=True, marital_status="Married", is_class_1_heir=True)
    m2_son  = FamilyMember(profile_id=p2.id, name="Vikas Gupta", relation="Son", gender="Male", age=40, is_alive=True, marital_status="Married", is_class_1_heir=True, notes="Active working partner in firm")
    m2_dau  = FamilyMember(profile_id=p2.id, name="Dr. Neha Gupta (Bansal)", relation="Daughter", gender="Female", age=37, is_alive=True, marital_status="Married", is_class_1_heir=True, notes="Consultant Radiologist in Mumbai")

    for m in [m2_self, m2_moth, m2_wife, m2_son, m2_dau]:
        db.add(m)
    db.flush()

    a2_part = Asset(
        profile_id=p2.id, category="partnership_firm", title="50% Capital & Profit Share in Gupta Cloth Merchant",
        description="Partnership firm operating wholesale synthetic & cotton saree trade",
        estimated_value_inr=24000000.0, location_or_institution="Ring Road Textile Market, Surat",
        identifier_number="Partnership Reg #SRT-6642/2001", acquisition_type="self_acquired",
        documents_available=True
    )
    a2_godown = Asset(
        profile_id=p2.id, category="commercial_shop", title="Textile Market Godown & Shop #214",
        description="Commercial godown in prime Surat wholesale textile market",
        estimated_value_inr=15000000.0, location_or_institution="Surat, Gujarat",
        identifier_number="Deed #884/2009", acquisition_type="self_acquired",
        documents_available=True, current_nominee_name="Vikas Gupta", nominee_relationship="Son"
    )
    a2_demat = Asset(
        profile_id=p2.id, category="demat_stocks", title="HDFC Securities Demat & Mutual Funds",
        description="Bluechip equities (Reliance, L&T, TCS) + Balanced Advantage MFs",
        estimated_value_inr=8500000.0, location_or_institution="HDFC Bank, Ring Road Branch",
        identifier_number="Demat DP ID: IN300128 Client ID: 19842019", acquisition_type="self_acquired",
        documents_available=True, current_nominee_name="Pushpa Gupta", nominee_relationship="Spouse"
    )
    a2_loan = Asset(
        profile_id=p2.id, category="liability_loan", title="Bank of Baroda Business Cash Credit Limit",
        description="Secured against stock & book debts",
        estimated_value_inr=3500000.0, location_or_institution="Bank of Baroda, Surat",
        identifier_number="CC A/c #029410", acquisition_type="self_acquired",
        documents_available=True
    )

    for a in [a2_part, a2_godown, a2_demat, a2_loan]:
        db.add(a)
    db.flush()

    # Allocations
    db.add(AssetAllocation(profile_id=p2.id, asset_id=a2_part.id, beneficiary_id=m2_son.id, share_percentage=100.0, special_instructions="Full partnership share to son Vikas to maintain business continuity."))
    db.add(AssetAllocation(profile_id=p2.id, asset_id=a2_godown.id, beneficiary_id=m2_son.id, share_percentage=100.0, special_instructions="Godown linked to trading business."))
    db.add(AssetAllocation(profile_id=p2.id, asset_id=a2_demat.id, beneficiary_id=m2_wife.id, share_percentage=60.0, special_instructions="Retirement sustenance for spouse."))
    db.add(AssetAllocation(profile_id=p2.id, asset_id=a2_demat.id, beneficiary_id=m2_dau.id, share_percentage=40.0, special_instructions="Portfolio allocation for daughter."))
    db.flush()

    w2 = WillDraft(
        profile_id=p2.id,
        executor_name="Vikas Gupta",
        executor_relationship="Son",
        witness1_name="Shri Arvind Shah (Textile Association President)",
        witness1_address="Ring Road, Surat",
        witness2_name="Adv. J. K. Trivedi",
        witness2_address="Surat District Court",
        doctor_name="Dr. Paresh Rawal, MD",
        doctor_reg_no="GMC-39102",
        doctor_certified=True,
        original_physical_location="Home Vault + Bank Locker #88 BOB Surat",
        status="draft",
        sub_registrar_office="Sub-Registrar Office, Athwa Lines, Surat",
        sro_reminder_date="2026-11-20"
    )
    db.add(w2)

    adv_p2 = AdvisorNote(
        profile_id=p2.id,
        author_name="CA Bhupendra Patel",
        author_role="Chartered Accountant",
        note_text="DANGER ON INTESTACY: Mother Kamla Devi is 89 and a Class I heir. If Mohanlal ji passes away without a registered will, 1/4th of ALL assets (including partnership capital) statutory passes to the mother. Upon her demise, it would devolve upon Mohanlal's other brothers and sisters under Class II, splintering control of the textile business!",
        category="succession_conflict",
        severity="critical"
    )
    db.add(adv_p2)

    # -------------------------------------------------------------
    # SCENARIO 3: Verma Auto Spares & Hardware (Kanpur)
    # -------------------------------------------------------------
    p3 = FamilyProfile(
        name="Verma Auto & Hardware Family",
        karta_name="Rameshwar Verma",
        business_name="M/s Verma Auto Spares & Hardware",
        business_type="Sole Proprietorship",
        city="Kanpur",
        state="Uttar Pradesh",
        religion="Hindu",
        governing_law="Hindu Succession Act, 1956 (amended 2005)",
        pan_or_gstin="09AABPV3321D1ZA",
        active_role="patriarch"
    )
    db.add(p3)
    db.flush()

    u3_karta = User(profile_id=p3.id, username="karta_verma", full_name="Rameshwar Verma (Karta)", role="patriarch", password_hash=hash_password("Virasat@2026"))
    u3_heir = User(profile_id=p3.id, username="deepak_heir", full_name="Deepak Verma (Heir)", role="heir", password_hash=hash_password("Virasat@2026"))
    u3_adv = User(profile_id=p3.id, username="advisor_shukla", full_name="Adv. Sudhir Shukla", role="advisor", password_hash=hash_password("Virasat@2026"))
    db.add_all([u3_karta, u3_heir, u3_adv])


    m3_self = FamilyMember(profile_id=p3.id, name="Rameshwar Verma", relation="Self", gender="Male", age=65, is_alive=True, marital_status="Married", is_class_1_heir=False)
    m3_wife = FamilyMember(profile_id=p3.id, name="Geeta Verma", relation="Spouse", gender="Female", age=61, is_alive=True, marital_status="Married", is_class_1_heir=True)
    m3_widow_dil = FamilyMember(profile_id=p3.id, name="Sunidhi Verma", relation="Daughter-in-law", gender="Female", age=34, is_alive=True, marital_status="Widow", is_class_1_heir=True, notes="Widow of predeceased elder son Late Rahul Verma - statutory Class I heir!")
    m3_minor_gson = FamilyMember(profile_id=p3.id, name="Harsh Verma", relation="Grandson", gender="Male", age=9, is_alive=True, is_minor=True, marital_status="Single", is_class_1_heir=True, notes="Son of predeceased son - Class I heir by representation!")
    m3_son2 = FamilyMember(profile_id=p3.id, name="Deepak Verma", relation="Son", gender="Male", age=29, is_alive=True, marital_status="Single", is_class_1_heir=True, notes="Younger son, assists in warehouse")

    for m in [m3_self, m3_wife, m3_widow_dil, m3_minor_gson, m3_son2]:
        db.add(m)
    db.flush()

    a3_shop = Asset(
        profile_id=p3.id, category="commercial_shop", title="Transport Nagar Auto Spares Showroom",
        description="Prime showroom (500 sq ft) on GT Road, Kanpur",
        estimated_value_inr=11000000.0, location_or_institution="Transport Nagar, Kanpur",
        identifier_number="Plot #82/A Transport Nagar", acquisition_type="self_acquired",
        documents_available=True, current_nominee_name="Deepak Verma", nominee_relationship="Son"
    )
    a3_plot = Asset(
        profile_id=p3.id, category="residential_property", title="Residential Plot in Kalyanpur, Kanpur",
        description="250 sq yards freehold residential land",
        estimated_value_inr=6000000.0, location_or_institution="Kalyanpur, Kanpur",
        identifier_number="Registry #1029/2012", acquisition_type="self_acquired",
        documents_available=True
    )
    a3_fd = Asset(
        profile_id=p3.id, category="bank_fd", title="Canara Bank Fixed Deposit for Grandson Education",
        description="Dedicated term deposit earmarked for minor grandson's engineering/higher studies",
        estimated_value_inr=3000000.0, location_or_institution="Canara Bank, Mall Road, Kanpur",
        identifier_number="FDR #883921 Canara Bank", acquisition_type="self_acquired",
        documents_available=True, current_nominee_name="Harsh Verma (Minor)", nominee_relationship="Grandson"
    )
    for a in [a3_shop, a3_plot, a3_fd]:
        db.add(a)
    db.flush()

    db.add(AssetAllocation(profile_id=p3.id, asset_id=a3_shop.id, beneficiary_id=m3_son2.id, share_percentage=100.0, special_instructions="Showroom assigned to younger son Deepak who runs day-to-day operations."))
    db.add(AssetAllocation(profile_id=p3.id, asset_id=a3_plot.id, beneficiary_id=m3_widow_dil.id, share_percentage=50.0, special_instructions="Kalyanpur plot 50% to widowed daughter-in-law Sunidhi for family shelter."))
    db.add(AssetAllocation(profile_id=p3.id, asset_id=a3_plot.id, beneficiary_id=m3_wife.id, share_percentage=50.0, special_instructions="50% to wife Geeta Verma."))
    db.add(AssetAllocation(profile_id=p3.id, asset_id=a3_fd.id, beneficiary_id=m3_minor_gson.id, share_percentage=100.0, special_instructions="Earmarked for education of grandson Harsh with Sunidhi as legal guardian."))
    db.flush()

    w3 = WillDraft(
        profile_id=p3.id,
        executor_name="Adv. Sudhir Shukla",
        executor_relationship="Trusted Family Advocate",
        guardian_minor_name="Sunidhi Verma",
        guardian_relationship="Natural Mother",
        witness1_name="Shri Mahendra Pratap Singh",
        witness1_address="Transport Nagar, Kanpur",
        witness2_name="Shri R. P. Tiwari",
        witness2_address="Mall Road, Kanpur",
        doctor_name="Dr. B. K. Srivastava",
        doctor_reg_no="UPMC-48192",
        doctor_certified=True,
        original_physical_location="Almirah Locker + Advocate Sudhir Shukla Chamber Safe",
        status="reviewed_by_ca",
        sub_registrar_office="Sub-Registrar Office-II, Civil Lines, Kanpur"
    )
    db.add(w3)

    # -------------------------------------------------------------
    # SCENARIO 4: Agarwal Sweets & Namkeen (Jaipur)
    # -------------------------------------------------------------
    p4 = FamilyProfile(
        name="Agarwal Confectionery & Heritage Sweets",
        karta_name="Kailash Chand Agarwal",
        business_name="M/s Agarwal Sweets & Namkeen",
        business_type="Partnership Firm",
        city="Jaipur",
        state="Rajasthan",
        religion="Hindu",
        governing_law="Hindu Succession Act, 1956 (amended 2005)",
        pan_or_gstin="08AABCA4419E1ZC",
        active_role="patriarch"
    )
    db.add(p4)
    db.flush()

    u4_karta = User(profile_id=p4.id, username="karta_agarwal", full_name="Kailash Chand Agarwal (Karta)", role="patriarch", password_hash=hash_password("Virasat@2026"))
    u4_heir = User(profile_id=p4.id, username="gaurav_heir", full_name="Gaurav Agarwal (Heir)", role="heir", password_hash=hash_password("Virasat@2026"))
    u4_adv = User(profile_id=p4.id, username="advisor_mittal", full_name="CA Surendra Mittal", role="advisor", password_hash=hash_password("Virasat@2026"))
    db.add_all([u4_karta, u4_heir, u4_adv])

    m4_self = FamilyMember(profile_id=p4.id, name="Kailash Chand Agarwal", relation="Self", gender="Male", age=71, is_alive=True, marital_status="Married", is_class_1_heir=False)
    m4_wife = FamilyMember(profile_id=p4.id, name="Bhagwati Devi Agarwal", relation="Spouse", gender="Female", age=67, is_alive=True, marital_status="Married", is_class_1_heir=True)
    m4_son1 = FamilyMember(profile_id=p4.id, name="Gaurav Agarwal", relation="Son", gender="Male", age=43, is_alive=True, marital_status="Married", is_class_1_heir=True, notes="In charge of Johari Bazaar flagship outlet")
    m4_son2 = FamilyMember(profile_id=p4.id, name="Pradeep Agarwal", relation="Son", gender="Male", age=39, is_alive=True, marital_status="Married", is_class_1_heir=True, notes="In charge of Mansarovar outlet & factory")
    m4_dau  = FamilyMember(profile_id=p4.id, name="Ananya Agarwal (Singhal)", relation="Daughter", gender="Female", age=41, is_alive=True, marital_status="Married", is_class_1_heir=True, notes="Residing in South Delhi")

    for m in [m4_self, m4_wife, m4_son1, m4_son2, m4_dau]:
        db.add(m)
    db.flush()


    a4_tm = Asset(
        profile_id=p4.id, category="partnership_firm", title="Trademark & Goodwill of 'Agarwal Sweets Jaipur'",
        description="Registered IP, trademark and secret recipes for traditional ghewar & namkeen",
        estimated_value_inr=20000000.0, location_or_institution="Trade Marks Registry, Ahmedabad",
        identifier_number="TM Reg #2910481 (Class 30)", acquisition_type="self_acquired",
        documents_available=True
    )
    a4_shop = Asset(
        profile_id=p4.id, category="commercial_shop", title="Johari Bazaar Flagship Sweet Shop",
        description="Ground floor historical sweet shop (400 sq ft)",
        estimated_value_inr=22000000.0, location_or_institution="Johari Bazaar, Walled City, Jaipur",
        identifier_number="Patta Deed #1974/88", acquisition_type="ancestral_huf",
        documents_available=True
    )
    a4_land = Asset(
        profile_id=p4.id, category="agricultural_land", title="Agricultural Farmland & Dairy Unit (Chomu)",
        description="8 Bighas irrigated agricultural farmland providing fresh milk for sweet production",
        estimated_value_inr=15000000.0, location_or_institution="Chomu Tehsil, Jaipur Rural",
        identifier_number="Khasra #841/2 & Jamabandi Khewat #19", acquisition_type="ancestral_huf",
        documents_available=True
    )
    for a in [a4_tm, a4_shop, a4_land]:
        db.add(a)
    db.flush()

    db.add(AssetAllocation(profile_id=p4.id, asset_id=a4_tm.id, beneficiary_id=m4_son1.id, share_percentage=50.0, special_instructions="Co-brand ownership with brother Pradeep."))
    db.add(AssetAllocation(profile_id=p4.id, asset_id=a4_tm.id, beneficiary_id=m4_son2.id, share_percentage=50.0, special_instructions="Co-brand ownership with brother Gaurav."))
    db.add(AssetAllocation(profile_id=p4.id, asset_id=a4_shop.id, beneficiary_id=m4_son1.id, share_percentage=100.0, special_instructions="Johari Bazaar shop management to Gaurav."))
    db.add(AssetAllocation(profile_id=p4.id, asset_id=a4_land.id, beneficiary_id=m4_son2.id, share_percentage=50.0, special_instructions="Chomu dairy farm."))
    db.add(AssetAllocation(profile_id=p4.id, asset_id=a4_land.id, beneficiary_id=m4_dau.id, share_percentage=50.0, special_instructions="Equal 50% farmland share to daughter Ananya."))
    db.flush()

    w4 = WillDraft(
        profile_id=p4.id,
        executor_name="CA Surendra Mittal",
        executor_relationship="Family CA & Auditor",
        witness1_name="Shri Ghanshyam Khandelwal",
        witness1_address="Johari Bazaar, Jaipur",
        witness2_name="Adv. O. P. Mathur",
        witness2_address="Rajasthan High Court Bench, Jaipur",
        doctor_name="Dr. Suresh C. Sharma, MS",
        doctor_reg_no="RMC-29401",
        doctor_certified=True,
        original_physical_location="Bank of Baroda Locker #41 Johari Bazaar",
        status="registered",
        sub_registrar_office="Sub-Registrar Office (Walled City), Collectorate, Jaipur",
        registration_date="2025-11-20",
        registration_number="RJ/JPR/WILL/2025/11029"
    )
    db.add(w4)

    # -------------------------------------------------------------
    # SCENARIO 5: Patel Electronics & Mobile Care (Ahmedabad)
    # -------------------------------------------------------------
    p5 = FamilyProfile(
        name="Patel Electronics & Gadgets Family",
        karta_name="Jayantilal Patel",
        business_name="M/s Patel Electronics & Mobile Care",
        business_type="Sole Proprietorship",
        city="Ahmedabad",
        state="Gujarat",
        religion="Hindu",
        governing_law="Hindu Succession Act, 1956 (amended 2005)",
        pan_or_gstin="24ABCPP5519J1ZN",
        active_role="patriarch"
    )
    db.add(p5)
    db.flush()

    u5_karta = User(profile_id=p5.id, username="karta_patel", full_name="Jayantilal Patel (Karta)", role="patriarch", password_hash=hash_password("Virasat@2026"))
    u5_heir = User(profile_id=p5.id, username="priyanshi_heir", full_name="Priyanshi Patel (Heir)", role="heir", password_hash=hash_password("Virasat@2026"))
    u5_adv = User(profile_id=p5.id, username="advisor_bhatt", full_name="CA Nilesh Bhatt", role="advisor", password_hash=hash_password("Virasat@2026"))
    db.add_all([u5_karta, u5_heir, u5_adv])

    m5_self = FamilyMember(profile_id=p5.id, name="Jayantilal Patel", relation="Self", gender="Male", age=59, is_alive=True, marital_status="Married", is_class_1_heir=False)
    m5_wife = FamilyMember(profile_id=p5.id, name="Hansa Patel", relation="Spouse", gender="Female", age=56, is_alive=True, marital_status="Married", is_class_1_heir=True)
    m5_dau  = FamilyMember(profile_id=p5.id, name="Priyanshi Patel", relation="Daughter", gender="Female", age=28, is_alive=True, marital_status="Single", is_class_1_heir=True, notes="Manages online sales, accounting, and billing")
    m5_son  = FamilyMember(profile_id=p5.id, name="Harshil Patel", relation="Son", gender="Male", age=24, is_alive=True, marital_status="Single", is_class_1_heir=True, notes="Studying MS in Data Science in Toronto, Canada")

    for m in [m5_self, m5_wife, m5_dau, m5_son]:
        db.add(m)
    db.flush()

    a5_shop = Asset(
        profile_id=p5.id, category="commercial_shop", title="Relief Road Electronics Showroom",
        description="Multi-brand mobile & laptop showroom (650 sq ft)",
        estimated_value_inr=17500000.0, location_or_institution="Relief Road, Old City, Ahmedabad",
        identifier_number="Municipal Tenement #229-B", acquisition_type="self_acquired",
        documents_available=True, current_nominee_name="Priyanshi Patel", nominee_relationship="Daughter"
    )
    a5_flat = Asset(
        profile_id=p5.id, category="residential_property", title="3-BHK Residential Flat in Bodakdev",
        description="Luxury apartment (1850 sq ft) in West Ahmedabad",
        estimated_value_inr=11000000.0, location_or_institution="Bodakdev, Ahmedabad",
        identifier_number="Share Certificate #104, Shivalik Residency", acquisition_type="self_acquired",
        documents_available=True, current_nominee_name="Hansa Patel", nominee_relationship="Spouse"
    )
    a5_demat = Asset(
        profile_id=p5.id, category="demat_stocks", title="Zerodha Demat Account & ETF Basket",
        description="Nifty 50 ETFs, IT Sector Stocks, and Sovereign Gold Bonds",
        estimated_value_inr=6500000.0, location_or_institution="Zerodha Broking Ltd",
        identifier_number="Client ID: 8940219", acquisition_type="self_acquired",
        documents_available=True, current_nominee_name="Harshil Patel", nominee_relationship="Son"
    )
    for a in [a5_shop, a5_flat, a5_demat]:
        db.add(a)
    db.flush()

    db.add(AssetAllocation(profile_id=p5.id, asset_id=a5_shop.id, beneficiary_id=m5_dau.id, share_percentage=100.0, special_instructions="Electronics showroom bequeathed to daughter Priyanshi who already runs the business."))
    db.add(AssetAllocation(profile_id=p5.id, asset_id=a5_flat.id, beneficiary_id=m5_wife.id, share_percentage=100.0, special_instructions="Sole ownership of residential flat to wife Hansa."))
    db.add(AssetAllocation(profile_id=p5.id, asset_id=a5_demat.id, beneficiary_id=m5_son.id, share_percentage=100.0, special_instructions="Demat portfolio and foreign education support to son Harshil."))
    db.flush()

    w5 = WillDraft(
        profile_id=p5.id,
        executor_name="Priyanshi Patel",
        executor_relationship="Daughter",
        witness1_name="Shri Kiritbhai Somani",
        witness1_address="Relief Road, Ahmedabad",
        witness2_name="Shri Nitin Mehta",
        witness2_address="Navrangpura, Ahmedabad",
        doctor_name="Dr. Chetan Bhatt",
        doctor_reg_no="GMC-44821",
        doctor_certified=True,
        original_physical_location="Home Godrej Locker + Zerodha Digital Vault",
        status="ready_for_signing",
        sub_registrar_office="Sub-Registrar Office, Memnagar, Ahmedabad"
    )
    db.add(w5)

    db.commit()
    print("Database successfully seeded with 5 realistic Indian trader family scenarios!")
