# DOCUMENT VAULT & SYSTEM SECURITY AUDIT (v2.1.0)

**Platform:** वारिस (Waaris) - VirasatPlanner  
**Component:** Encrypted Document Vault (`app/crypto_vault.py`), Authentication & RBAC Service (`app/auth_service.py`), Data Integrity Rules, and REST Endpoints  
**Audit Standard:** Comprehensive Application Security, Cryptographic Verification & Data Integrity Audit  
**Date:** October 2026 (Updated for v2.1.0 Security Hardening Release)  

---

## 1. Threat Model & Assets at Risk
Small traders, dukandaars, and joint-family businesses upload sensitive documents containing high-stakes estate records:
- Registered Land Sale Deeds (*Bainama* / Conveyance Deeds)
- Commercial Tenancy Agreements & Municipal Mutation Records
- Bank Fixed Deposit Receipts (FDRs) with Account & CIF numbers
- Commercial Partnership Deeds & Profit-sharing ratios
- Certified Medical Fitness Certificates & Last Wills

**Primary Threat Vectors Mitigated:**
1. *Unauthorized Access & Information Disclosure (SEC-01):* Every sensitive endpoint (profile, family members, assets, bequests, will drafts, vault files, reminders, simulations, and advisor notes) strictly requires an authenticated session with family-scoped authorization.
2. *Privilege Escalation (SEC-02):* New account registrations cannot request privileged roles (`patriarch` or `advisor`) without an authenticated family administrator. Role switching strictly derives authority from database records and forbids heirs from escalating privileges (HTTP 403 Forbidden).
3. *Cross-Family Tampering (SEC-03):* Enforced boundary checks prevent User A (Family #1) from reading, modifying, or deleting Family #2 records. Asset allocations and document uploads reject cross-family foreign keys.
4. *Frontend Injection & Stored XSS (SEC-05):* All dynamic text rendered in `innerHTML` templates across `app.js` and `family_tree.js` is sanitized via `escapeHtml()`.
5. *ReportLab PDF Injection (SEC-07):* All user-supplied text interpolated into ReportLab `Paragraph` XML markup is escaped with `html.escape()` to prevent formatting disruption and markup injection.
6. *Vault File Integrity & Resource Exhaustion (SEC-06):* Enforces a 15 MB streaming upload ceiling, restricts extensions to approved non-executable documents (`.pdf`, `.jpg`, `.png`, `.tiff`, `.docx`), validates SHA-256 digests, and deletes orphaned files if database commits fail.
7. *Over-Allocation & Deficit Concealment (SEC-08 / DATA-01):* Rejects asset allocations exceeding 100% and explicitly reports negative net estates when liabilities exceed assets.

---

## 2. Cryptographic Architecture & Cipher Specification

```mermaid
flowchart LR
    Upload["Plaintext Document (PDF / Image)"] --> Validate["Validate Size (<= 15MB) & Allowed Ext"]
    Validate --> Hash["Compute SHA-256 Digest"]
    Validate --> Cipher["Fernet Authenticated Encryption (AES-128-CBC + HMAC-SHA256)"]
    Cipher --> Disk["Secure Storage (/storage/encrypted_vault/*.enc)"]
    Hash --> DB["SQLAlchemy Metadata Transaction"]
    DB -->|Fail| CleanDisk["Rollback: Delete Disk File"]

    Disk --> AuthCheck{"PBKDF2 / Bearer Token & Family ID Check"}
    AuthCheck -->|Authorized (Family Member/Advisor)| Decrypt["Fernet Decryption + SHA-256 Verification"]
    AuthCheck -->|Unauthorized / Cross-Family| Reject["401 Unauthorized / 403 Forbidden"]
    Decrypt --> Stream["In-Memory Decrypted Stream with Sanitized Filename"]
```

### Encryption Specifications:
- **Cipher Standard:** **Fernet Specification (RFC 4880 equivalent)**.
- **Underlying Primitive:** **AES-128 in CBC mode** with PKCS7 padding.
- **Compound Key Length:** 256-bit symmetric key comprising:
  - 128-bit encryption sub-key for AES-128-CBC.
  - 128-bit signing sub-key for HMAC-SHA256 authentication.
- **Initialization Vector (IV):** 128-bit unique random IV generated per file (`os.urandom(16)`) to eliminate ciphertext pattern recognition.
- **Ciphertext Authentication:** HMAC-SHA256 message authentication code appended to the ciphertext guarantees integrity; any bit modification aborts decryption with an `InvalidSignature` exception before plaintext is processed.
- **Key Hierarchy & Storage:**
  - Production: Loads key from the `VAULT_SECRET_KEY` environment variable. Refuses to start if missing or insecure (`ENVIRONMENT == "production"`).
  - Development fallback: Auto-generates `data/vault.key` with restricted OS permissions if the env var is unset.

---

## 3. User Authentication & Role-Based Access Control (RBAC)

1. **Password Hashing:**
   - Algorithm: **PBKDF2-HMAC-SHA256**
   - Salt: 16-byte cryptographically secure random salt generated via `os.urandom(16)`.
   - Iterations: **600,000 rounds** (OWASP recommended standard for SHA-256).
2. **Brute Force Protection:**
   - In-memory rate limiting rejects IP clients exceeding 5 failed attempts within 60 seconds with **HTTP 429 Too Many Requests**.
3. **Session Tokens:**
   - Cryptographically signed HMAC-SHA256 bearer tokens with 24-hour expiration (`AUTH_TOKEN_EXPIRE_HOURS = 24`).
   - Constant-time signature comparison (`hmac.compare_digest`) prevents timing side-channel attacks.
   - Session cookies configured with `HttpOnly=True`, `SameSite="Lax"`, and conditional `Secure=True` in production.
4. **Role Matrix & Enforcement:**
   - **Patriarch (Karta):** Full administrative privileges for their family (add/edit/delete assets, family members, will bequests, and vault documents).
   - **Heir (Beneficiary):** Read-only visibility into personal bequests and estate inventory. All write endpoints (`POST /api/assets`, `DELETE /api/family/...`, etc.) reject Heir requests with **HTTP 403 Forbidden**.
   - **CA / Legal Advisor:** Auditor role with permissions to view assets, verify valuations, download vault documents for compliance checks, and submit signed advisory notes.

---

## 4. Automated Security Verification Results

The automated test suite (`pytest tests/test_app.py`) verifies these controls across 22 comprehensive tests:

```
tests/test_app.py::test_homepage_renders PASSED                          [  4%]
tests/test_app.py::test_five_scenarios_seeded PASSED                     [  9%]
tests/test_app.py::test_anonymous_requests_rejected_on_sensitive_endpoints PASSED [ 13%]
tests/test_app.py::test_family_tree_members PASSED                       [ 18%]
tests/test_app.py::test_asset_inventory_calculation PASSED               [ 22%]
tests/test_app.py::test_succession_engine_sharma_family PASSED           [ 27%]
tests/test_app.py::test_crypto_vault_aes256_encryption PASSED            [ 31%]
tests/test_app.py::test_vault_file_validation_and_size_limits PASSED     [ 36%]
tests/test_app.py::test_vault_security_audit_api PASSED                  [ 40%]
tests/test_app.py::test_reportlab_will_pdf_generation PASSED             [ 45%]
tests/test_app.py::test_pdf_escapes_special_characters PASSED            [ 50%]
tests/test_app.py::test_rbac_heir_mutation_restriction PASSED            [ 54%]
tests/test_app.py::test_cross_family_isolation PASSED                    [ 59%]
tests/test_app.py::test_allocation_validation_rules PASSED               [ 63%]
tests/test_app.py::test_sro_guide_endpoint PASSED                        [ 68%]
tests/test_app.py::test_user_can_create_custom_profile_and_enter_data PASSED [ 72%]
tests/test_app.py::test_user_auth_pbkdf2_token_and_rbac PASSED           [ 77%]
tests/test_app.py::test_reminders_and_sro_subsystem PASSED               [ 81%]
tests/test_app.py::test_interactive_simulator_toggles PASSED             [ 86%]
tests/test_app.py::test_verma_predeceased_son_class1_representation PASSED [ 90%]
tests/test_app.py::test_succession_engine_deficit_estate PASSED          [ 95%]
tests/test_app.py::test_succession_engine_religion_flags PASSED          [100%]

============================= 22 passed in 18.33s =============================
```

In addition, the live system audit (`python audit_features.py`) verified **25 / 25 checks passed** against the running HTTP server.

---

## 5. Security & Deployment Hardening Checklist

1. **Environment Configuration:**
   - Copy `.env.example` to `.env` and configure strong random keys for `SECRET_KEY` and `VAULT_SECRET_KEY`.
   - Set `ENVIRONMENT=production` to enforce strict startup secret validation and disable demo seeding.
2. **Reverse Proxy & Transport Security:**
   - Terminate TLS 1.3 at Nginx / Caddy with HTTP Strict Transport Security (HSTS) headers enabled (`max-age=31536000; includeSubDomains`).
3. **Database & File Isolation:**
   - Store SQLite database or configure PostgreSQL connection with process-isolated permissions.
   - Keep `.gitignore` active to prevent committing keys, SQLite databases, or uploaded ciphertext to source control.
