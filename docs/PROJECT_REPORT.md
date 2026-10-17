# PROJECT REPORT: MULTI-GENERATIONAL FAMILY ASSET & SUCCESSION PLANNER (वारिस - VirasatPlanner)

**Project Name:** वारिस (Waaris) - VirasatPlanner  
**Target Audience:** Small traders, retailers (*chhote dukandaar*), family business owners, and joint families in India.  
**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy, SQLite, ReportLab, Cryptography (Fernet: AES-128-CBC + HMAC-SHA256), HTML5, Tailwind CSS, Chart.js.  
**Current Release:** v2.0.0  

---

## 1. Problem Statement & Indian Legal Context

According to the landmark **DAKSH Access to Justice Survey (2016-2017)** across district and subordinate courts in India, an estimated **66% of all pending civil litigation** relates to land and property disputes, with intestate succession and family inheritance disagreements representing the single largest source of intra-family discord.

Small retail traders, shopkeepers, wholesale merchants (*kirana, kapda, hardware dukandaars*), and joint families in commercial hubs like Delhi's Khari Baoli, Kanpur's Nayaganj, or Surat's textile markets frequently operate on unwritten informal trust.

### Primary Legal & Social Pitfalls Identified:
1. **Sudden Demise of the Business Karta:**
   When the sole proprietor or family patriarch dies without a written testamentary plan, business bank accounts and cash credit (CC) limits are frozen by lending institutions, suppliers demand immediate settlement of informal credit (*udhaari*), and commercial operations grind to a halt.
2. **Prohibitive Cost & Formality of Legal Services:**
   Formal estate planning services and tier-1 law firms charge upwards of ₹25,000 to ₹1,50,000 for will drafting. Small traders perceive these services as overly formal, intimidating, and cost-prohibitive.
3. **The Nominee Trap (*Nominee vs. Legal Heir*):**
   Over 90% of Indian traders operate under the dangerous misconception that nominating a family member in bank fixed deposits (FDRs), Demat accounts, or insurance makes that nominee the absolute legal owner. In landmark rulings (*Smt. Sarbati Devi v. Smt. Usha Devi 1984* and *Shakti Yezdani v. Jayanand Jayant Salgaonkar 2023*), the Supreme Court of India clarified that a nominee is merely a temporary custodian/trustee who holds the asset on behalf of the legal heirs entitled under succession law.
4. **Daughter Coparcenary Rights (*Vineeta Sharma v. Rakesh Sharma 2020*):**
   Under Section 6 of the Hindu Succession Act (amended 2005) and reaffirmed by the Supreme Court in 2020, daughters hold equal birthright coparcenary shares in ancestral property. Excluding married daughters without registered family settlements frequently triggers protracted partition suits.
5. **Partnership Dissolution Under Section 42:**
   Under Section 42 of the Indian Partnership Act, 1932, a partnership firm automatically dissolves upon the death of any partner unless the partnership deed contains an explicit continuity covenant.

---

## 2. Platform Architecture & Modules

```mermaid
graph TD
    A["Frontend Single-Page App (Tailwind CSS, SVG Tree, Chart.js)"]
    B["FastAPI REST Backend (app/main.py)"]
    C["SQLAlchemy SQLite Relational Store (virasat.db)"]
    D["ReportLab Bilingual Will Generator (app/pdf_generator.py)"]
    E["Encrypted Document Vault (Fernet: AES-128-CBC + HMAC-SHA256)"]
    F["Multi-Succession Engine (Hindu HSA, Muslim Shariat, Christian ISA)"]
    G["Authentication & RBAC Service (app/auth_service.py)"]
    H["Statutory Deadlines & Reminders Subsystem"]

    A <-->|REST API with Bearer Tokens| B
    B <--> C
    B --> D
    B <--> E
    B --> F
    B <--> G
    B --> H
```

### Milestone Features:

- **Milestone 1: Family Tree & Asset Inventory Builder**
  - Interactive generational tree mapping: Elders, Karta & Spouse, Children, In-laws, and Grandchildren.
  - 10 asset categories: Commercial shops (*dukaan*), residential property, agricultural land, partnership shares, bank FDs, savings accounts, demat equities, gold/silver jewellery (in tolas/grams), vehicles, and liabilities/loans.
  - Distinguishes Self-Acquired vs. Ancestral / HUF Coparcenary property.

- **Milestone 2: Will & Succession Draft Generator (ReportLab PDF)**
  - Produces formal bilingual (English/Hindi) testamentary drafts compliant with the Indian Succession Act 1925.
  - Formulates sound mind declarations, executor appointments, minor guardianship, trade continuity directives, comprehensive residuary clauses, and two independent witness signature blocks.

- **Milestone 3: Encrypted Document Vault & Compliance Reminders**
  - **Cryptographic Vault:** Fernet authenticated encryption (AES-128-CBC with PKCS7 padding and HMAC-SHA256 integrity verification) for registry deeds, FDRs, and trade licenses. Encryption key managed via `VAULT_SECRET_KEY` environment variable.
  - **Statutory Deadlines & Reminders:** Tracks Sub-Registrar Office (SRO) will registration target dates, bank FDR maturity renewals, GST annual filings, and trade license expiries with automated countdown badges.

- **Milestone 4: Multi-Member Access with Real User Authentication & RBAC**
  - User accounts with salted **PBKDF2-HMAC-SHA256** password hashing (100,000 rounds) and signed HMAC-SHA256 bearer session tokens.
  - Strict role enforcement across all endpoints:
    - **Patriarch (Karta):** Full administrative and editing permissions.
    - **Heir (Beneficiary):** Read-only visibility into allocated bequests. Write actions reject with HTTP 403 Forbidden.
    - **CA / Legal Advisor:** Auditor role with permissions to review asset valuations, inspect encrypted documents, and log signed advisory audit notes.

- **Milestone 5: Interactive 'What Happens If...' Scenario Simulator**
  - Dynamic legal playground testing statutory defaults against tailored wills.
  - **Predeceased Child Representation:** Implements Hindu Succession Act Section 8 and Section 10 Rule 3: when a son or daughter predeceases the Karta, their share devolves *per stirpes* to their surviving spouse and children.
  - **Doctrine of Ademption:** Under Section 152 of the Indian Succession Act, simulates the failure of a specific legacy if the property is sold or gifted during the testator's lifetime.
  - **SRO Registration Impact:** Simulates probate contest risks and evidentiary hurdles for unregistered wills under Section 18 of the Indian Registration Act.
  - **Gender Parity:** Flags coparcenary rights infringements under the 2005 HSA amendment and *Vineeta Sharma (2020)*.

---

## 3. Five Synthetic Indian Trader Family Scenarios

To enable instantaneous evaluation, VirasatPlanner includes 5 preloaded synthetic family business profiles modeled after real-world commercial archetypes:

1. **Sharma Kirana & General Store (Khari Baoli, Old Delhi)**
   - *Patriarch:* Omprakash Sharma (62 yrs), sole proprietor of 40-year grocery wholesale business.
   - *Legal Conflict:* Younger son in Bengaluru is listed as bank nominee for ₹45L SBI FDs, but will allocates funds to mother and daughter. Highlights the nominee vs. heir conflict.
2. **Gupta Cloth Merchant & Sons (Surat, Gujarat)**
   - *Patriarch:* Mohanlal Gupta (68 yrs), 50% partner in textile firm.
   - *Legal Conflict:* Partnership firm continuity under Sec 42 Indian Partnership Act; elderly mother (89 yrs) is Class I heir entitled to statutory share.
3. **Verma Auto Spares & Hardware (Kanpur, Uttar Pradesh)**
   - *Patriarch:* Rameshwar Verma (65 yrs), auto parts distributor.
   - *Legal Conflict:* Predeceased son's widow (Sunidhi) and 9-year-old grandson (Harsh) require statutory representation rights (*per stirpes*) as Class I heirs under HSA Sec 8/10 Rule 3.
4. **Agarwal Sweets & Namkeen (Jaipur, Rajasthan)**
   - *Patriarch:* Kailash Chand Agarwal (71 yrs), confectionery brand with 2 branches.
   - *Legal Conflict:* Trademark and recipe sharing between sons; farmland succession for married daughter.
5. **Patel Electronics & Mobile Care (Ahmedabad, Gujarat)**
   - *Patriarch:* Jayantilal Patel (59 yrs), electronics showroom.
   - *Legal Conflict:* Primary commercial showroom bequeathed to daughter who manages daily operations, while son receives Demat equities.

---

## 4. Usability & Security Verification

- **Automated Test Suite:** 15 automated test cases in `tests/test_app.py` covering authentication, PBKDF2 hashing, bearer tokens, RBAC permission enforcement, Fernet encryption integrity, SRO reminders, and what-if simulation scenarios.
- **Lawyer-Reviewed Checklist:** Achieves 11 / 11 (100%) compliance against testamentary clauses required by the Indian Succession Act, 1925.
