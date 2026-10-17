# 🌳 VirasatPlanner — Plan Today, Preserve Tomorrow
> **AI & Legal Intelligence Succession Planning Portal for Indian Business Families & Small Traders**  
> *Governed under the Hindu Succession Act, 1956 (amended 2005) & Indian Succession Act, 1925.*

---

## 📌 Executive Summary
In India, over **67% of civil court disputes** arise from family property and succession conflicts, often paralyzing generational family businesses (such as Kirana stores, retail shops, wholesale dukaans, and MSMEs) upon the untimely demise of the Karta or patriarch.

**VirasatPlanner** bridges this critical gap by providing an end-to-end, empathetic, and legally compliant wealth succession and digital will management platform tailored specifically for Indian families.

---

## 🚀 Key Modules & Capabilities

1. **🏛️ Generational Family Tree & Coparcenary Mapping:**
   - Visual lineage mapping from Karta & Spouse through Class-I Statutory Heirs and Coparceners.
   - Built-in compliance checks for the Hindu Succession (Amendment) Act, 2005 ensuring equal birthright shares for daughters.

2. **🏪 Asset Inventory & Dukaan Portfolio:**
   - Catalog commercial shops, ancestral farmland, residential property, demat stocks, gold/jewellery, and bank fixed deposits.
   - Conflict detection between **Bank Nominee vs. Will Bequest** (addressing the landmark *Sarbati Devi v. Usha Devi* Supreme Court precedent).

3. **📜 Digital Will Drafting Engine & PDF Export:**
   - Generates bilingual, legally compliant Will drafts complete with Schedule of Properties, Executor appointment, and Section 63 Indian Succession Act two-witness attestation covenants.
   - One-click downloadable PDF with registration guidelines.

4. **🔐 Military-Grade Encrypted Vault:**
   - AES-256 Fernet cryptographic storage for confidential title deeds, partnership deeds, and PAN/Aadhaar documents.
   - Expiry reminders and document renewal tracking.

5. **⚡ What-If Demise & Succession Simulator:**
   - Real-time simulation of estate division under testate (with Will) vs. intestate (without Will) scenarios.
   - Instant calculation of Family Dispute Risk Scores (0–100).

6. **🏛️ SRO Sub-Registrar Office Readiness Tracker:**
   - Step-by-step checklist for formal Will registration at the local Sub-Registrar Office (stamp duty, witnesses, medical fitness certificate).

7. **⚖️ CA & Legal Audit Advisory:**
   - Real-time compliance observations by Chartered Accountants and Legal Counsel for HUF partition implications and tax liabilities.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Python 3.11+, SQLAlchemy, SQLite
- **Security:** Cryptography (AES-256 Fernet), Role-Based Access Control (RBAC)
- **Document Generation:** ReportLab PDF Engine
- **Frontend:** Semantic HTML5, Tailwind CSS, Chart.js, Vanilla ES6+ JavaScript
- **Theme:** Royal Heritage Emerald & Gold Palette with Accessible WCAG 2.1 AA UI

---

## 🏃 Quickstart Guide

### 1. Clone or Extract
Ensure you have Python 3.10+ installed.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Server
```bash
python run.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

### 4. Run Test Suite
```bash
pytest
```
*All 15 automated test cases verify database persistence, encryption, calculation logic, and API endpoints.*

---

## 📄 Legal Disclaimer
*VirasatPlanner is an educational and technological estate-planning advisory system informed by the Indian Succession Act 1925 and Hindu Succession Act 1956. It generates structured drafts and preliminary dispute evaluations. For formal court probate, contested estates, or complex corporate restructurings, users should consult an enrolled Advocate and registered Chartered Accountant.*
