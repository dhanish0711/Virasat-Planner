"""
VirasatPlanner - Comprehensive Legal Succession Engine
Provides illustrative statutory inheritance calculations, will-based allocations,
dispute risk planning indicators, and 'What-If' simulation scenarios.

IMPORTANT: Automated calculations provide educational estimates based on statutory rules.
They do not constitute formal legal advice and require qualified advocate review.
"""

from typing import List, Dict, Any, Optional

def calculate_succession_shares(
    profile,
    members: List[Any],
    assets: List[Any],
    allocations: List[Any],
    simulation_toggles: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Computes both Intestate (statutory) and Testate (will-based) succession estimates.
    Applies branch-based representation for predeceased heirs and detects common planning pitfalls.
    Does NOT modify database records.
    """
    if simulation_toggles is None:
        simulation_toggles = {}

    predeceased_child_id = simulation_toggles.get("predeceased_child_id")
    ademption_asset_id = simulation_toggles.get("ademption_asset_id")
    is_unregistered_sim = simulation_toggles.get("unregistered_will", False)
    exclude_daughter_sim = simulation_toggles.get("exclude_daughter", False)

    religion = (getattr(profile, "religion", "Hindu") or "Hindu").strip()
    governing_law = getattr(profile, "governing_law", "Hindu Succession Act, 1956 (amended 2005)")

    # Filter out adeemed (sold/mortgaged) assets if simulated
    active_assets = []
    adeemed_assets = []
    for a in assets:
        if ademption_asset_id and a.id == ademption_asset_id:
            adeemed_assets.append(a)
        else:
            active_assets.append(a)

    total_asset_value = sum(a.estimated_value_inr for a in active_assets if a.category != "liability_loan")
    total_liabilities = sum(a.estimated_value_inr for a in active_assets if a.category == "liability_loan")
    # Do not conceal deficit estate: show true net estate
    net_worth = total_asset_value - total_liabilities

    # Classify Ancestral vs Self-Acquired property
    ancestral_assets = [a for a in active_assets if getattr(a, "acquisition_type", "self_acquired") == "ancestral_huf" and a.category != "liability_loan"]
    self_acquired_assets = [a for a in active_assets if getattr(a, "acquisition_type", "self_acquired") != "ancestral_huf" and a.category != "liability_loan"]
    ancestral_val = sum(a.estimated_value_inr for a in ancestral_assets)
    self_acquired_val = sum(a.estimated_value_inr for a in self_acquired_assets)

    # -------------------------------------------------------------
    # 1. Statutory Heir Classification & Branch Mapping
    # -------------------------------------------------------------
    direct_class_1 = []
    predeceased_branch_heirs = []
    class_2_heirs = []
    other_members = []

    simulated_predeceased = set()
    if predeceased_child_id:
        simulated_predeceased.add(predeceased_child_id)

    for m in members:
        if m.relation.lower() == "self" or not m.is_alive:
            continue
        
        if m.id in simulated_predeceased:
            continue

        rel = m.relation.lower()
        notes_str = (getattr(m, "notes", "") or "").lower()

        is_predeceased_branch = (
            "predeceased" in notes_str or
            "late" in notes_str or
            rel in ["widow of predeceased son", "son of predeceased son", "daughter of predeceased son"] or
            (rel in ["grandson", "granddaughter", "daughter-in-law"] and getattr(m, "is_class_1_heir", False))
        )

        if rel in ["spouse", "wife", "mother", "son", "daughter"]:
            direct_class_1.append(m)
        elif is_predeceased_branch:
            predeceased_branch_heirs.append(m)
        elif rel in ["father", "brother", "sister", "grandson", "granddaughter", "daughter-in-law"]:
            class_2_heirs.append(m)
        else:
            other_members.append(m)

    total_class_1_count = len(direct_class_1) + len(predeceased_branch_heirs)

    # -------------------------------------------------------------
    # 2. Intestate Succession Distribution Calculation
    # -------------------------------------------------------------
    intestate_shares = []
    calculation_basis_val = max(0.0, net_worth)

    is_muslim = religion.lower() == "muslim"
    is_christian = religion.lower() in ["christian", "parsi"]
    requires_manual_review = False
    review_notes = []

    if is_muslim:
        requires_manual_review = True
        review_notes.append("Manual legal review required: Muslim succession depends on applicable school of jurisprudence (Hanafi/Shia) and testamentary bequests are limited to 1/3 of net estate without heir consent.")
        
        wife_share_pct = 12.5 if any(m.relation.lower() in ["son", "daughter"] for m in direct_class_1) else 25.0
        wife_members = [m for m in direct_class_1 if m.relation.lower() in ["spouse", "wife"]]
        son_members = [m for m in direct_class_1 if m.relation.lower() == "son"]
        daughter_members = [m for m in direct_class_1 if m.relation.lower() == "daughter"]

        allocated_pct = 0.0
        for w in wife_members:
            w_pct = round(wife_share_pct / len(wife_members), 2)
            intestate_shares.append({
                "member_id": w.id,
                "name": w.name,
                "relation": w.relation,
                "heir_class": "Quranic Sharer (Zawil-Furood)",
                "share_pct": w_pct,
                "estimated_inr": round((w_pct / 100.0) * calculation_basis_val, 2),
                "statutory_note": "Fixed Quranic 1/8th share in presence of children under Muslim Law."
            })
            allocated_pct += w_pct

        residuary_pct = max(0.0, 100.0 - allocated_pct)
        total_units = (len(son_members) * 2) + len(daughter_members)
        if total_units > 0:
            unit_pct = residuary_pct / total_units
            for s in son_members:
                s_pct = round(unit_pct * 2, 2)
                intestate_shares.append({
                    "member_id": s.id,
                    "name": s.name,
                    "relation": s.relation,
                    "heir_class": "Residuary Heir (Asaba)",
                    "share_pct": s_pct,
                    "estimated_inr": round((s_pct / 100.0) * calculation_basis_val, 2),
                    "statutory_note": "Residuary 2-share allocation under Hanafi Shariat."
                })
            for d in daughter_members:
                d_pct = round(unit_pct, 2)
                intestate_shares.append({
                    "member_id": d.id,
                    "name": d.name,
                    "relation": d.relation,
                    "heir_class": "Residuary Heir (Asaba)",
                    "share_pct": d_pct,
                    "estimated_inr": round((d_pct / 100.0) * calculation_basis_val, 2),
                    "statutory_note": "Residuary 1-share allocation under Hanafi Shariat."
                })
    elif is_christian:
        requires_manual_review = True
        review_notes.append("Manual legal review required: Indian Succession Act 1925 Part V (Intestate Succession for Christians/Parsis) requires formal verification of lineal descendants.")
        # General ISA 1925: 1/3 to widow, 2/3 equally among lineal descendants
        widow_members = [m for m in direct_class_1 if m.relation.lower() in ["spouse", "wife"]]
        children = [m for m in direct_class_1 if m.relation.lower() in ["son", "daughter"]]
        if widow_members and children:
            w_pct = round(33.33 / len(widow_members), 2)
            c_pct = round(66.67 / len(children), 2)
            for w in widow_members:
                intestate_shares.append({
                    "member_id": w.id,
                    "name": w.name,
                    "relation": w.relation,
                    "heir_class": "Surviving Spouse (1/3 Share)",
                    "share_pct": w_pct,
                    "estimated_inr": round((w_pct / 100.0) * calculation_basis_val, 2),
                    "statutory_note": "Statutory 1/3rd share to surviving spouse under ISA 1925."
                })
            for c in children:
                intestate_shares.append({
                    "member_id": c.id,
                    "name": c.name,
                    "relation": c.relation,
                    "heir_class": "Lineal Descendant (Equal Share)",
                    "share_pct": c_pct,
                    "estimated_inr": round((c_pct / 100.0) * calculation_basis_val, 2),
                    "statutory_note": "Equal distribution of 2/3rd estate among lineal descendants."
                })
    else:
        # Hindu Succession Act 1956 (amended 2005) - Section 10 Rules:
        # Rule 1: Intestate's widow takes 1 share
        # Rule 2: Surviving sons, daughters, and mother take 1 share each
        # Rule 3: Heirs in the branch of each predeceased child take 1 share BETWEEN them (per stirpes)
        branch_count = len(direct_class_1) + (1 if len(predeceased_branch_heirs) > 0 else 0)
        
        if branch_count > 0:
            share_per_branch_pct = 100.0 / branch_count
            share_per_branch_val = calculation_basis_val / branch_count

            # Direct Class I heirs each get 1 full branch share
            for m in direct_class_1:
                intestate_shares.append({
                    "member_id": m.id,
                    "name": m.name,
                    "relation": m.relation,
                    "heir_class": "Class I Statutory Heir",
                    "share_pct": round(share_per_branch_pct, 2),
                    "estimated_inr": round(share_per_branch_val, 2),
                    "statutory_note": "Entitled to equal individual share under Section 10 Rules 1 & 2, HSA 1956."
                })

            # Predeceased son's branch divides 1 branch share equally between them (per stirpes Rule 3)
            if predeceased_branch_heirs:
                sub_count = len(predeceased_branch_heirs)
                sub_pct = share_per_branch_pct / sub_count
                sub_val = share_per_branch_val / sub_count
                for m in predeceased_branch_heirs:
                    intestate_shares.append({
                        "member_id": m.id,
                        "name": m.name,
                        "relation": m.relation,
                        "heir_class": "Class I Heir (Representation per stirpes)",
                        "share_pct": round(sub_pct, 2),
                        "estimated_inr": round(sub_val, 2),
                        "statutory_note": "Inherits equal portion of predeceased son's branch share under Section 10 Rule 3, HSA 1956."
                    })

            for m in class_2_heirs:
                intestate_shares.append({
                    "member_id": m.id,
                    "name": m.name,
                    "relation": m.relation,
                    "heir_class": "Class II Heir (Statutorily Excluded)",
                    "share_pct": 0.0,
                    "estimated_inr": 0.0,
                    "statutory_note": "Excluded under Section 9 because preferential Class I heirs exist."
                })
        else:
            # Fallback to Class II Priority (Section 9/11)
            num_class_2 = len(class_2_heirs)
            if num_class_2 > 0:
                equal_pct = 100.0 / num_class_2
                equal_val = calculation_basis_val / num_class_2
                for m in class_2_heirs:
                    intestate_shares.append({
                        "member_id": m.id,
                        "name": m.name,
                        "relation": m.relation,
                        "heir_class": "Class II Heir",
                        "share_pct": round(equal_pct, 2),
                        "estimated_inr": round(equal_val, 2),
                        "statutory_note": "Inherits in absence of Class I heirs."
                    })

    # -------------------------------------------------------------
    # 3. Testate (Will-Based) Distribution Calculation
    # -------------------------------------------------------------
    testate_shares_dict = {m.id: {"member": m, "value": 0.0, "assets": []} for m in members if m.relation.lower() != "self"}
    unallocated_assets = []

    allocations_by_asset = {}
    for alloc in allocations:
        allocations_by_asset.setdefault(alloc.asset_id, []).append(alloc)

    for asset in active_assets:
        if asset.category == "liability_loan":
            continue
        allocs = allocations_by_asset.get(asset.id, [])
        if not allocs:
            unallocated_assets.append(asset)
        else:
            for alloc in allocs:
                bene_id = alloc.beneficiary_id
                if exclude_daughter_sim:
                    bene_obj = next((m for m in members if m.id == bene_id), None)
                    if bene_obj and bene_obj.relation.lower() == "daughter":
                        continue

                portion = (alloc.share_percentage / 100.0) * asset.estimated_value_inr
                if bene_id in testate_shares_dict:
                    testate_shares_dict[bene_id]["value"] += portion
                    testate_shares_dict[bene_id]["assets"].append({
                        "asset_id": asset.id,
                        "title": asset.title,
                        "category": asset.category,
                        "share_pct": alloc.share_percentage,
                        "value_inr": portion,
                        "instructions": alloc.special_instructions
                    })

    testate_shares = []
    total_testate_distributed = 0.0
    for m_id, item in testate_shares_dict.items():
        m = item["member"]
        val = item["value"]
        total_testate_distributed += val
        pct = (val / total_asset_value * 100.0) if total_asset_value > 0 else 0.0
        testate_shares.append({
            "member_id": m.id,
            "name": m.name,
            "relation": m.relation,
            "share_pct": round(pct, 2),
            "estimated_inr": round(val, 2),
            "bequeathed_assets": item["assets"]
        })

    # -------------------------------------------------------------
    # 4. Legal Pitfalls & Dispute Risk Indicator
    # -------------------------------------------------------------
    pitfalls = []
    dispute_score = 10  # Internal planning baseline indicator

    # Deficit estate alert
    if net_worth < 0:
        dispute_score += 40
        pitfalls.append({
            "severity": "CRITICAL",
            "title": f"Deficit Estate: Liabilities Exceed Assets by ₹{abs(net_worth):,.0f}",
            "description": f"Total outstanding debts (₹{total_liabilities:,.0f}) exceed total asset valuation (₹{total_asset_value:,.0f}). Under Section 325 of the Indian Succession Act, debts must be satisfied before beneficiaries receive any legacies.",
            "remedy": "Devise a structured debt repayment plan or liquidate non-core commercial holdings to clear liabilities."
        })

    # Unregistered Will Warning
    if is_unregistered_sim:
        dispute_score += 25
        pitfalls.append({
            "severity": "CRITICAL",
            "title": "Unregistered Will Vulnerability (Evidentiary Challenge Risk)",
            "description": "While Section 18 of the Registration Act allows an unregistered will, disputes frequently involve allegations of suspicious circumstances or lack of testamentary capacity. Registration provides strong evidentiary presumption under Section 60(2).",
            "remedy": "Register the will at the local Sub-Registrar Office with two independent witnesses."
        })

    # Ademption Alert
    if adeemed_assets:
        dispute_score += 20
        adeemed_titles = ", ".join([a.title for a in adeemed_assets])
        pitfalls.append({
            "severity": "CRITICAL",
            "title": f"Ademption of Specific Bequests ({adeemed_titles})",
            "description": f"Under Section 152 of the Indian Succession Act 1925, when an asset specifically bequeathed ({adeemed_titles}) is sold, gifted, or destroyed prior to testator demise, the legacy fails (adeems). The named beneficiary receives no substitute unless provided by residuary clause.",
            "remedy": "Update your succession plan immediately upon disposal of an asset to provide alternative bequests."
        })

    # Muslim 1/3rd Limitation Check
    if is_muslim:
        non_heir_bequest_val = 0.0
        heir_ids = {h.id for h in direct_class_1 + class_2_heirs}
        for m_id, item in testate_shares_dict.items():
            if m_id not in heir_ids:
                non_heir_bequest_val += item["value"]
        
        max_allowed_bequest = calculation_basis_val / 3.0
        if non_heir_bequest_val > max_allowed_bequest:
            dispute_score += 35
            pitfalls.append({
                "severity": "CRITICAL",
                "title": "Muslim Law 1/3rd Testamentary Limit Exceeded",
                "description": f"Under Islamic succession law, testamentary bequests cannot exceed 1/3rd of the net estate (Max: ₹{max_allowed_bequest:,.0f}) without unanimous post-mortem consent of all legal heirs. Current non-heir bequests equal ₹{non_heir_bequest_val:,.0f}.",
                "remedy": "Reduce non-heir bequests below 33.33% or execute a registered gift (Hiba) during lifetime."
            })

    # Hindu Coparcenary Check
    if ancestral_assets:
        coparceners = [m for m in members if getattr(m, "is_coparcener", False) and m.is_alive and m.relation.lower() != "self"]
        total_coparceners = len(coparceners) + 1
        karta_undivided_share = ancestral_val / total_coparceners if total_coparceners > 0 else ancestral_val

        ancestral_bequeathed = 0.0
        for asset in ancestral_assets:
            allocs = allocations_by_asset.get(asset.id, [])
            for al in allocs:
                ancestral_bequeathed += (al.share_percentage / 100.0) * asset.estimated_value_inr

        if ancestral_bequeathed > (karta_undivided_share * 1.05):
            dispute_score += 30
            pitfalls.append({
                "severity": "CRITICAL",
                "title": f"Excessive Ancestral Property Bequest (Exceeds Karta's Undivided {round(100/total_coparceners, 1)}% Share)",
                "description": f"Total ancestral property equals ₹{ancestral_val:,.0f}. In a coparcenary with {total_coparceners} members, the testator's testamentary capacity is limited to their undivided share (₹{karta_undivided_share:,.0f}).",
                "remedy": "Limit testamentary bequests of ancestral property to the testator's undivided share or execute a registered family settlement deed."
            })

    # Daughter Disinheritance Check
    for m in members:
        if m.relation.lower() == "daughter" and m.is_alive and m.id not in simulated_predeceased:
            will_val = testate_shares_dict.get(m.id, {}).get("value", 0.0)
            if will_val == 0 or exclude_daughter_sim:
                dispute_score += 25
                pitfalls.append({
                    "severity": "CRITICAL",
                    "title": f"Coparcenary Rights Violation & Daughter Disinheritance Risk ({m.name})",
                    "description": f"Daughter '{m.name}' receives no testamentary allocation. Under the 2005 HSA Amendment and Supreme Court jurisprudence (Vineeta Sharma v. Rakesh Sharma, 2020), daughters hold equal birthright coparcenary status.",
                    "remedy": "Allocate a fair testamentary share or execute a registered relinquishment deed."
                })
                break

    # Nominee Discrepancy Check
    for a in active_assets:
        if a.category in ["bank_fd", "savings_account", "demat_stocks"] and a.current_nominee_name:
            nominee_name = a.current_nominee_name.strip().lower()
            allocs = allocations_by_asset.get(a.id, [])
            if allocs:
                bene_member = next((m for m in members if m.id == allocs[0].beneficiary_id), None)
                if bene_member and nominee_name not in bene_member.name.lower() and bene_member.name.lower() not in nominee_name:
                    dispute_score += 15
                    pitfalls.append({
                        "severity": "WARNING",
                        "title": f"Nominee vs Will Beneficiary Conflict ({a.title})",
                        "description": f"Asset '{a.title}' lists nominee '{a.current_nominee_name}', but will bequeaths to '{bene_member.name}'. In Indian law, nominees are trustees and legal heirs remain owners, but discrepancies frequently cause disbursement delays and litigation.",
                        "remedy": f"Submit updated nomination at the financial institution in favor of '{bene_member.name}'."
                    })

    # Partnership Firm Dissolution Risk
    for a in active_assets:
        if a.category == "partnership_firm":
            dispute_score += 20
            pitfalls.append({
                "severity": "CRITICAL",
                "title": f"Partnership Firm Dissolution Risk ({a.title})",
                "description": f"Under Section 42(c) of the Indian Partnership Act 1932, a partnership firm dissolves upon a partner's death unless the partnership deed contains an express continuation/succession clause.",
                "remedy": "Execute an addendum to the partnership deed providing for continuation with designated legal heirs."
            })

    # Unallocated Assets
    if unallocated_assets:
        dispute_score += 15
        unallocated_names = ", ".join([getattr(u, "title", "Asset") for u in unallocated_assets[:3]])
        pitfalls.append({
            "severity": "WARNING",
            "title": f"{len(unallocated_assets)} Unallocated Assets (Intestate Residuary Risk)",
            "description": f"Assets including '{unallocated_names}' have no specific beneficiary assignment. Without a valid residuary clause, unallocated assets devolve under intestate succession rules.",
            "remedy": "Assign specific bequest percentages or ensure a residuary clause is included in the will draft."
        })

    # Debt-to-Liquid Ratio
    liquid_value = sum(a.estimated_value_inr for a in active_assets if a.category in ["bank_fd", "savings_account", "demat_stocks", "gold_jewellery"])
    if total_liabilities > 0 and total_liabilities > (liquid_value * 0.7):
        dispute_score += 15
        pitfalls.append({
            "severity": "WARNING",
            "title": "High Debt-to-Liquid Asset Ratio",
            "description": f"Outstanding business liabilities (₹{total_liabilities:,.0f}) exceed 70% of liquid assets (₹{liquid_value:,.0f}). Creditors may attach commercial properties during probate or settlement.",
            "remedy": "Maintain an earmarked liquid reserve for debt clearance."
        })

    dispute_score = min(98, max(5, dispute_score))

    if dispute_score < 30:
        risk_level = "LOW RISK"
        risk_badge = "emerald"
    elif dispute_score < 60:
        risk_level = "MODERATE RISK"
        risk_badge = "amber"
    elif dispute_score < 80:
        risk_level = "HIGH RISK"
        risk_badge = "orange"
    else:
        risk_level = "CRITICAL / SEVERE RISK"
        risk_badge = "red"

    return {
        "net_worth_inr": net_worth,
        "total_asset_value_inr": total_asset_value,
        "total_liabilities_inr": total_liabilities,
        "ancestral_property_value_inr": ancestral_val,
        "self_acquired_property_value_inr": self_acquired_val,
        "religion": religion,
        "governing_law": governing_law,
        "dispute_risk_score": dispute_score,
        "risk_level": risk_level,
        "risk_badge": risk_badge,
        "class_1_heirs_count": total_class_1_count,
        "intestate_shares": intestate_shares,
        "testate_shares": testate_shares,
        "pitfalls": pitfalls,
        "unallocated_assets_count": len(unallocated_assets),
        "adeemed_assets_count": len(adeemed_assets),
        "simulation_toggles_applied": simulation_toggles,
        "manual_legal_review_required": requires_manual_review,
        "legal_review_notes": review_notes,
        "planning_indicator_notice": "The Family Dispute Risk Score is an internal planning indicator highlighting documented estate vulnerabilities; it is not a statistical prediction of litigation."
    }


def calculate_succession_readiness(
    profile,
    members: List[Any],
    assets: List[Any],
    allocations: List[Any],
    vault_docs: List[Any],
    will_draft: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Computes a comprehensive 0-100 Succession Readiness / Health Score for the family estate.
    Divided into 4 institutional pillars (25 points each):
    1. Documentation & Vault Coverage (25 pts)
    2. Nomination Completeness & Alignment (25 pts)
    3. Testamentary Clarity & Will Draft (25 pts)
    4. Statutory & Coparcenary Equity (25 pts)
    """
    from datetime import date
    today = date.today()

    active_assets = [a for a in assets if a.category != "liability_loan"]
    total_active_assets = len(active_assets)
    total_asset_val = sum(a.estimated_value_inr for a in active_assets)
    total_liabilities = sum(a.estimated_value_inr for a in assets if a.category == "liability_loan")
    liquid_val = sum(a.estimated_value_inr for a in active_assets if a.category in ["bank_fd", "savings_account", "demat_stocks", "gold_jewellery"])

    allocations_by_asset = {}
    for al in allocations:
        allocations_by_asset.setdefault(al.asset_id, []).append(al)

    vault_by_asset = {}
    for d in vault_docs:
        if d.asset_id:
            vault_by_asset.setdefault(d.asset_id, []).append(d)

    # -------------------------------------------------------------
    # Pillar 1: Documentation & Vault Coverage (25 pts)
    # -------------------------------------------------------------
    doc_score = 0.0
    documented_count = 0
    expired_count = 0
    for a in active_assets:
        has_doc = (a.id in vault_by_asset and len(vault_by_asset[a.id]) > 0) or getattr(a, "documents_available", False)
        if has_doc:
            documented_count += 1
            # Check for expiration
            for d in vault_by_asset.get(a.id, []):
                if d.expiry_or_renewal_date:
                    try:
                        exp = date.fromisoformat(d.expiry_or_renewal_date)
                        if exp < today:
                            expired_count += 1
                    except Exception:
                        pass

    if total_active_assets > 0:
        doc_ratio = documented_count / total_active_assets
        doc_score += doc_ratio * 18.0
    else:
        doc_score += 18.0

    if len(vault_docs) > 0:
        doc_score += 4.0
    if expired_count == 0 and len(vault_docs) > 0:
        doc_score += 3.0
    doc_score = min(25.0, round(doc_score, 1))

    # -------------------------------------------------------------
    # Pillar 2: Nomination Completeness & Alignment (25 pts)
    # -------------------------------------------------------------
    nom_score = 0.0
    financial_assets = [a for a in active_assets if a.category in ["bank_fd", "savings_account", "demat_stocks", "partnership_firm"]]
    nominated_count = 0
    discrepancy_count = 0

    for a in financial_assets:
        if a.current_nominee_name and a.current_nominee_name.strip():
            nominated_count += 1
            nom_name = a.current_nominee_name.strip().lower()
            allocs = allocations_by_asset.get(a.id, [])
            if allocs:
                bene = next((m for m in members if m.id == allocs[0].beneficiary_id), None)
                if bene:
                    b_name = bene.name.strip().lower()
                    if b_name not in nom_name and nom_name not in b_name:
                        discrepancy_count += 1

    if financial_assets:
        nom_ratio = nominated_count / len(financial_assets)
        nom_score += nom_ratio * 18.0
        # Deduct for Sarbati Devi discrepancies
        nom_score -= (discrepancy_count * 4.0)
    else:
        nom_score += 18.0

    # Extra points for full nominee relationship recording
    has_relationships = all(bool(a.nominee_relationship) for a in financial_assets if a.current_nominee_name)
    if has_relationships and nominated_count > 0:
        nom_score += 7.0
    elif nominated_count > 0:
        nom_score += 3.0

    nom_score = max(0.0, min(25.0, round(nom_score, 1)))

    # -------------------------------------------------------------
    # Pillar 3: Testamentary Clarity & Will Completeness (25 pts)
    # -------------------------------------------------------------
    will_score = 0.0
    allocated_count = sum(1 for a in active_assets if a.id in allocations_by_asset and len(allocations_by_asset[a.id]) > 0)
    if total_active_assets > 0:
        alloc_ratio = allocated_count / total_active_assets
        will_score += alloc_ratio * 12.0
    else:
        will_score += 12.0

    if will_draft:
        if getattr(will_draft, "executor_name", None):
            will_score += 3.0
        if getattr(will_draft, "witness1_name", None) and getattr(will_draft, "witness2_name", None):
            will_score += 4.0
        if getattr(will_draft, "doctor_certified", False) or getattr(will_draft, "doctor_name", None):
            will_score += 3.0
        if getattr(will_draft, "status", None) == "registered" or getattr(will_draft, "sro_reminder_date", None):
            will_score += 3.0

    will_score = min(25.0, round(will_score, 1))

    # -------------------------------------------------------------
    # Pillar 4: Statutory & Coparcenary Equity (25 pts)
    # -------------------------------------------------------------
    stat_score = 25.0

    # Ancestral property check
    ancestral_assets = [a for a in active_assets if getattr(a, "acquisition_type", "self_acquired") == "ancestral_huf"]
    ancestral_val = sum(a.estimated_value_inr for a in ancestral_assets)
    if ancestral_assets:
        coparceners = [m for m in members if getattr(m, "is_coparcener", False) and m.is_alive and m.relation.lower() != "self"]
        total_coparceners = len(coparceners) + 1
        karta_undivided_share = ancestral_val / total_coparceners if total_coparceners > 0 else ancestral_val
        ancestral_bequeathed = 0.0
        for asset in ancestral_assets:
            for al in allocations_by_asset.get(asset.id, []):
                ancestral_bequeathed += (al.share_percentage / 100.0) * asset.estimated_value_inr
        if ancestral_bequeathed > (karta_undivided_share * 1.05):
            stat_score -= 8.0

    # Daughter inclusion check
    daughters = [m for m in members if m.relation.lower() == "daughter" and m.is_alive]
    for d in daughters:
        d_allocs = [al for al in allocations if al.beneficiary_id == d.id]
        if not d_allocs:
            stat_score -= 7.0
            break

    # Solvency check
    if total_liabilities > 0 and liquid_val > 0 and total_liabilities > (liquid_val * 0.7):
        stat_score -= 6.0

    # Muslim 1/3 limit check
    religion = (getattr(profile, "religion", "Hindu") or "Hindu").strip()
    if religion.lower() == "muslim":
        direct_heir_ids = {m.id for m in members if m.relation.lower() in ["spouse", "wife", "son", "daughter", "mother", "father"] and m.is_alive}
        non_heir_bequest = sum((al.share_percentage / 100.0) * next((a.estimated_value_inr for a in active_assets if a.id == al.asset_id), 0.0) for al in allocations if al.beneficiary_id not in direct_heir_ids)
        if non_heir_bequest > (total_asset_val * 0.333):
            stat_score -= 8.0

    stat_score = max(5.0, min(25.0, round(stat_score, 1)))

    overall_score = round(doc_score + nom_score + will_score + stat_score, 1)
    overall_score = min(100.0, max(5.0, overall_score))

    if overall_score >= 85:
        grade = "A+ (Institutional Grade)"
        badge_color = "emerald"
        status_label = "EXCELLENT PREPAREDNESS"
    elif overall_score >= 70:
        grade = "A (Ready / Minor Polish Needed)"
        badge_color = "teal"
        status_label = "WELL PREPARED"
    elif overall_score >= 50:
        grade = "B (Moderate Vulnerabilities)"
        badge_color = "amber"
        status_label = "ACTION REQUIRED"
    else:
        grade = "C (High Dispute Vulnerability)"
        badge_color = "rose"
        status_label = "CRITICAL GAPS DETECTED"

    # Priority Action Checklist to reach 100%
    actions = []
    if doc_score < 20:
        missing_docs = [a.title for a in active_assets if a.id not in vault_by_asset and not getattr(a, "documents_available", False)]
        if missing_docs:
            actions.append({
                "pillar": "Documentation",
                "impact": f"+{min(6, 25 - int(doc_score))} pts",
                "action": f"Upload title registry/FDR receipts for: {', '.join(missing_docs[:2])}",
                "urgency": "HIGH"
            })
    if discrepancy_count > 0:
        actions.append({
            "pillar": "Nomination",
            "impact": f"+{discrepancy_count * 4} pts",
            "action": f"Harmonize {discrepancy_count} nomination discrepancy (nominee vs will beneficiary conflict under Sarbati Devi)",
            "urgency": "CRITICAL"
        })
    elif nom_score < 20 and financial_assets:
        unnominated = [a.title for a in financial_assets if not a.current_nominee_name]
        if unnominated:
            actions.append({
                "pillar": "Nomination",
                "impact": "+5 pts",
                "action": f"Record official nominees for accounts: {', '.join(unnominated[:2])}",
                "urgency": "HIGH"
            })
    if will_score < 20:
        if will_draft and not getattr(will_draft, "sro_reminder_date", None):
            actions.append({
                "pillar": "Testamentary",
                "impact": "+3 pts",
                "action": "Schedule SRO appointment reminder date for Book 3 will registration",
                "urgency": "MEDIUM"
            })
        if will_draft and not (getattr(will_draft, "witness1_name", None) and getattr(will_draft, "witness2_name", None)):
            actions.append({
                "pillar": "Testamentary",
                "impact": "+4 pts",
                "action": "Record 2 independent adult non-beneficiary witnesses in Will draft",
                "urgency": "HIGH"
            })
    if stat_score < 20:
        if daughters and any(not [al for al in allocations if al.beneficiary_id == d.id] for d in daughters):
            actions.append({
                "pillar": "Legal Equity",
                "impact": "+7 pts",
                "action": "Include daughter in will bequests to respect Section 6 coparcenary parity",
                "urgency": "CRITICAL"
            })

    return {
        "overall_score": overall_score,
        "grade": grade,
        "badge_color": badge_color,
        "status_label": status_label,
        "pillars": {
            "documentation": {
                "score": doc_score,
                "max": 25,
                "percentage": round((doc_score / 25.0) * 100, 1),
                "documented_assets": documented_count,
                "total_assets": total_active_assets,
                "expired_documents": expired_count
            },
            "nomination": {
                "score": nom_score,
                "max": 25,
                "percentage": round((nom_score / 25.0) * 100, 1),
                "financial_assets_count": len(financial_assets),
                "nominated_count": nominated_count,
                "discrepancies": discrepancy_count
            },
            "testamentary": {
                "score": will_score,
                "max": 25,
                "percentage": round((will_score / 25.0) * 100, 1),
                "allocated_assets": allocated_count,
                "total_assets": total_active_assets,
                "has_executor": bool(getattr(will_draft, "executor_name", None)) if will_draft else False,
                "has_witnesses": bool(getattr(will_draft, "witness1_name", None) and getattr(will_draft, "witness2_name", None)) if will_draft else False,
                "has_doctor": bool(getattr(will_draft, "doctor_name", None)) if will_draft else False
            },
            "statutory_equity": {
                "score": stat_score,
                "max": 25,
                "percentage": round((stat_score / 25.0) * 100, 1),
                "coparcenary_compliant": True if not ancestral_assets else (stat_score >= 17),
                "daughter_included": True if not daughters else all(any(al.beneficiary_id == d.id for al in allocations) for d in daughters),
                "solvency_healthy": total_liabilities <= (liquid_val * 0.7) if liquid_val > 0 else True
            }
        },
        "priority_actions": actions,
        "disclaimer": "The Succession Readiness Score evaluates procedural and statutory planning completeness; it is an educational tool and does not substitute for qualified legal review."
    }


def generate_nomination_vs_will_tracker(
    profile,
    members: List[Any],
    assets: List[Any],
    allocations: List[Any],
    vault_docs: List[Any]
) -> List[Dict[str, Any]]:
    """
    Constructs an asset-by-asset comparison grid mapping:
    Asset -> Current Nominee -> Will Beneficiary -> Vault Document -> Legal Conflict Status.
    Enforces the landmark Supreme Court rule in Sarbati Devi v. Usha Devi (1984).
    """
    from datetime import date
    today = date.today()

    allocations_by_asset = {}
    for al in allocations:
        allocations_by_asset.setdefault(al.asset_id, []).append(al)

    vault_by_asset = {}
    for d in vault_docs:
        if d.asset_id:
            vault_by_asset.setdefault(d.asset_id, []).append(d)

    member_map = {m.id: m for m in members}
    tracker = []

    for a in assets:
        if a.category == "liability_loan":
            continue

        # 1. Document Vault Status
        docs = vault_by_asset.get(a.id, [])
        if docs:
            has_expired = False
            for doc in docs:
                if doc.expiry_or_renewal_date:
                    try:
                        exp = date.fromisoformat(doc.expiry_or_renewal_date)
                        if exp < today:
                            has_expired = True
                    except Exception:
                        pass
            if has_expired:
                vault_status = "REVIEW_REQUIRED"
                vault_badge = "amber"
                vault_label = "🟡 Expired / Review Needed"
            else:
                vault_status = "UPDATED"
                vault_badge = "emerald"
                vault_label = "🟢 Verified in Vault"
        elif getattr(a, "documents_available", False):
            vault_status = "UPDATED"
            vault_badge = "emerald"
            vault_label = "🟢 Available Offline"
        else:
            vault_status = "MISSING"
            vault_badge = "rose"
            vault_label = "🔴 Missing Title Deed"

        # 2. Will Beneficiaries
        asset_allocs = allocations_by_asset.get(a.id, [])
        beneficiaries = []
        for al in asset_allocs:
            m = member_map.get(al.beneficiary_id)
            if m:
                beneficiaries.append({
                    "member_id": m.id,
                    "name": m.name,
                    "relation": m.relation,
                    "share_percentage": al.share_percentage
                })

        # 3. Nominee & Alignment Status
        nominee_name = (a.current_nominee_name or "").strip()
        nominee_rel = (a.nominee_relationship or "").strip()
        is_financial = a.category in ["bank_fd", "savings_account", "demat_stocks", "partnership_firm"]

        if not nominee_name:
            if beneficiaries:
                status = "MISSING_NOMINEE"
                badge = "amber"
                status_desc = "No institutional nominee recorded, but bequeathed in will."
                legal_risk = "Financial institution will withhold payout without succession certificate or probate, causing 6-18 month delays."
                remedy = f"File nomination form at the institution naming {beneficiaries[0]['name']}."
            else:
                status = "UNPROTECTED"
                badge = "rose"
                status_desc = "Neither nominee nor will bequest recorded."
                legal_risk = "Asset will fall into unadministered intestate estate subject to multi-heir partition claims."
                remedy = "Designate both an institutional nominee and a specific will beneficiary."
        elif not beneficiaries:
            status = "MISSING_WILL_BEQUEST"
            badge = "blue"
            status_desc = f"Nominated to {nominee_name}, but omitted from will draft."
            legal_risk = "Under Sarbati Devi (1984), nominee is merely a trustee; legal heirs can claim intestate shares."
            remedy = f"Add specific clause in Will assigning this asset to {nominee_name} to confirm full ownership."
        else:
            # Both nominee and will beneficiary exist: Check for Sarbati Devi conflict
            primary_bene = beneficiaries[0]["name"].strip().lower()
            nom_lower = nominee_name.lower()
            if primary_bene in nom_lower or nom_lower in primary_bene:
                status = "ALIGNED"
                badge = "emerald"
                status_desc = "Nominee and Will Beneficiary match seamlessly."
                legal_risk = "Minimal dispute risk. Nominee receives funds as trustee and holds legal beneficial title under the will."
                remedy = "Ensure copy of registered will is kept with bank passbook/policy."
            else:
                status = "DISCREPANCY"
                badge = "rose"
                status_desc = f"Nominee is {nominee_name}, but Will bequeaths to {beneficiaries[0]['name']}!"
                legal_risk = "Critical legal conflict (Sarbati Devi v. Usha Devi, 1984): Bank will release funds to nominee, who may refuse to hand them over to the will beneficiary, triggering civil litigation."
                remedy = f"Submit updated nomination at the bank/depository in favor of {beneficiaries[0]['name']}."

        tracker.append({
            "asset_id": a.id,
            "title": a.title,
            "category": a.category,
            "estimated_value_inr": a.estimated_value_inr,
            "acquisition_type": a.acquisition_type,
            "owner": profile.karta_name,
            "current_nominee_name": nominee_name or "None Recorded",
            "nominee_relationship": nominee_rel or "-",
            "beneficiaries": beneficiaries,
            "primary_beneficiary_name": beneficiaries[0]["name"] if beneficiaries else "Unassigned",
            "vault_document_status": vault_status,
            "vault_badge": vault_badge,
            "vault_label": vault_label,
            "alignment_status": status,
            "status_badge": badge,
            "status_desc": status_desc,
            "legal_risk": legal_risk,
            "remedy": remedy
        })

    return tracker


def _try_groq_advisor(query_str: str, estate_context: str) -> Optional[str]:
    """Queries Groq Cloud API with configured GROQ_API_KEY for live high-speed AI legal advisory."""
    import os
    try:
        from app.config import GROQ_API_KEY
    except ImportError:
        GROQ_API_KEY = ""
    api_key = os.getenv("GROQ_API_KEY") or GROQ_API_KEY
    if not api_key:
        return None
    try:
        import httpx
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Waaris AI, a specialized legacy and succession advisor for Indian small business owners, traders, and joint families. "
                            "Provide empathetic, structured, legally accurate advice referencing the Indian Succession Act 1925, Hindu Succession Act 1956, "
                            "Partnership Act 1932, and Supreme Court rulings (Sarbati Devi, Vineeta Sharma). "
                            "Format key points clearly with Markdown. Respond in the exact same language as the user query (English, Hindi, or Hinglish)."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"ESTATE CONTEXT:\n{estate_context}\n\nUSER QUESTION: {query_str}"
                    }
                ],
                "temperature": 0.25,
                "max_tokens": 2048
            }
            resp = httpx.post(url, headers=headers, json=payload, timeout=8.0)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"].get("content")
                if content and content.strip():
                    return content.strip()
    except Exception:
        pass
    return None


def _try_gemini_advisor(query_str: str, estate_context: str) -> Optional[str]:
    """Optionally queries Google Gemini API if GEMINI_API_KEY is configured in the environment."""
    import os
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    try:
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "You are Waaris AI, a specialized legacy and succession advisor for Indian small business owners and joint families. "
                                "Provide empathetic, structured, legally accurate advice referencing the Indian Succession Act 1925, Hindu Succession Act 1956, "
                                "Partnership Act 1932, and Supreme Court rulings (Sarbati Devi, Vineeta Sharma). "
                                "Respond in the same language as the user query (Hindi, Hinglish, or English).\n\n"
                                f"ESTATE CONTEXT:\n{estate_context}\n\n"
                                f"USER QUESTION: {query_str}"
                            )
                        }
                    ]
                }
            ]
        }
        with httpx.Client(timeout=4.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        pass
    return None


def query_legacy_advisor(
    query_str: str,
    profile,
    members: List[Any],
    assets: List[Any],
    allocations: List[Any],
    vault_docs: List[Any],
    will_draft: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Context-aware interactive AI Family Legacy Advisor.
    Analyzes user questions against actual family records, succession rules, and statutory principles.
    Supports English, Hindi, and Hinglish queries with optional Gemini AI integration.
    """
    q = (query_str or "").strip().lower()
    active_assets = [a for a in assets if a.category != "liability_loan"]
    total_asset_val = sum(a.estimated_value_inr for a in active_assets)
    total_liabilities = sum(a.estimated_value_inr for a in assets if a.category == "liability_loan")
    daughters = [m for m in members if m.relation.lower() == "daughter" and m.is_alive]
    sons = [m for m in members if m.relation.lower() == "son" and m.is_alive]

    allocations_by_asset = {}
    for al in allocations:
        allocations_by_asset.setdefault(al.asset_id, []).append(al)

    # Detect if user asks in Hindi or Hinglish
    is_hindi_or_hinglish = any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in query_str) or any(
        w in q for w in ["kya", "hai", "kaise", "hissa", "batwara", "batao", "karein", "nirdesh", "beti", "ladki", "vyapar", "karobar", "dukaan", "namini"]
    )

    # Context string for Gemini
    tracker = generate_nomination_vs_will_tracker(profile, members, assets, allocations, vault_docs)
    discrepancies = [t for t in tracker if t["alignment_status"] == "DISCREPANCY"]
    missing_noms = [t for t in tracker if t["alignment_status"] == "MISSING_NOMINEE"]
    readiness = calculate_succession_readiness(profile, members, assets, allocations, vault_docs, will_draft)

    estate_context = (
        f"Family: {profile.name}, Karta: {profile.karta_name}, Business: {profile.business_name} ({profile.business_type}), "
        f"City: {profile.city}, State: {profile.state}, Governing Law: {profile.governing_law}. "
        f"Active Assets: {len(active_assets)} valued at Rs {total_asset_val:,.0f}. Liabilities: Rs {total_liabilities:,.0f}. "
        f"Readiness Score: {readiness['overall_score']}/100. "
        f"Discrepancies: {len(discrepancies)}. Living Daughters: {len(daughters)}, Sons: {len(sons)}."
    )

    # Try Groq AI Advisor (using provided API key)
    groq_answer = _try_groq_advisor(query_str, estate_context)
    if groq_answer:
        return {
            "query": query_str,
            "answer": groq_answer,
            "identified_gaps": [
                f"Readiness Score: {readiness['overall_score']}/100",
                f"{len(discrepancies)} nominee vs will discrepancies evaluated",
                f"{len(daughters)} living daughters evaluated under Section 6 HSA"
            ],
            "action_items": [a["action"] for a in readiness.get("priority_actions", [])[:3]],
            "suggested_followups": [
                "What is the difference between nominee and legal heir?",
                "What are daughters' coparcenary rights in ancestral property?",
                "How to protect partnership firm and business continuity?"
            ] if not is_hindi_or_hinglish else [
                "नॉमिनी और वसीयत में क्या अंतर है?",
                "पुश्तैनी संपत्ति में बेटियों का क्या अधिकार है?",
                "दुकान और पार्टनरशिप फर्म कैसे सुरक्षित रखें?"
            ],
            "ai_provider": "Groq Cloud (openai/gpt-oss-120b)",
            "api_key_required": False,
            "api_key_note": "Powered by Groq Cloud AI inference with local statutory fallback."
        }

    # Try Gemini if API key is provided
    gemini_answer = _try_gemini_advisor(query_str, estate_context)
    if gemini_answer:
        return {
            "query": query_str,
            "answer": gemini_answer,
            "identified_gaps": [
                f"Readiness Score: {readiness['overall_score']}/100",
                f"{len(discrepancies)} nominee vs will discrepancies evaluated",
                f"{len(daughters)} living daughters evaluated under Section 6 HSA"
            ],
            "action_items": [a["action"] for a in readiness.get("priority_actions", [])[:3]],
            "suggested_followups": [
                "What is the difference between nominee and legal heir?",
                "What are daughters' coparcenary rights in ancestral property?",
                "How to protect partnership firm and business continuity?"
            ] if not is_hindi_or_hinglish else [
                "नॉमिनी और वसीयत में क्या अंतर है?",
                "पुश्तैनी संपत्ति में बेटियों का क्या अधिकार है?",
                "दुकान और पार्टनरशिप फर्म कैसे सुरक्षित रखें?"
            ],
            "ai_provider": "Google Gemini 1.5 Flash (via API Key)",
            "api_key_required": False,
            "api_key_note": "No API key is required. The built-in Indian legal reasoning engine runs 100% locally and free."
        }

    # Built-in deterministic Indian legal reasoning engine
    # 1. Topic: Nominee vs Will Beneficiary (Sarbati Devi)
    if any(k in q for k in ["nominee", "nomination", "bank nominee", "sarbati", "नॉमिनी", "अमानतदार", "namini"]):
        disc_details = "\n".join([f"- **{d['title']}** (₹{d['estimated_value_inr']:,.0f}): Bank nominee is *{d['current_nominee_name']}*, but Will bequeaths to *{d['primary_beneficiary_name']}*." for d in discrepancies]) if discrepancies else "None! All institutional nominees match will beneficiaries."
        missing_details = "\n".join([f"- **{m['title']}** (₹{m['estimated_value_inr']:,.0f}): Missing nominee at bank/registry." for m in missing_noms]) if missing_noms else "All financial assets have recorded nominees."

        if is_hindi_or_hinglish:
            answer = (
                f"### बैंक नॉमिनी व वसीयत मिलान (सरबती देवी नियम)\n\n"
                f"👉 **भारतीय कानून का मुख्य नियम:**\n"
                f"सुप्रीम कोर्ट के ऐतिहासिक फैसले (**Sarbati Devi v. Usha Devi, 1984** व **Ram Chander Talwar, 2010**) के अनुसार बैंक नॉमिनी केवल **अमानतदार (Trustee)** होता है, असली कानूनी मालिक नहीं।\n\n"
                f"बैंक से पैसा तो नॉमिनी को मिल जाएगा, लेकिन उस पैसे पर कानूनी हक वसीयत में लिखे वारिस या कानूनी उत्तराधिकारियों का ही रहेगा।\n\n"
                f"#### आपके परिवार ({profile.name}) की वर्तमान स्थिति:\n"
                f"- **नॉमिनी व वसीयत में विवाद (Discrepancies):** {len(discrepancies)}\n{disc_details}\n\n"
                f"- **बिना नॉमिनी वाले खाते (Missing Nominees):** {len(missing_noms)}\n{missing_details}\n\n"
                f"**कानूनी सलाह:** यदि नॉमिनी और वसीयत के वारिस का नाम अलग-अलग है, तो बैंक में जाकर तुरंत नॉमिनी का नाम वसीयत के वारिस के अनुसार अपडेट कराएं।"
            )
            actions = [
                "जिन खातों में नॉमिनी अलग है, उनका बैंक नॉमिनेशन फॉर्म तुरंत अपडेट कराएं",
                "वसीयत में लिखे वारिस का नाम ही बैंक व डीमैट खाते में नॉमिनी के रूप में दर्ज करें",
                "बैंक नॉमिनेशन पावती (Acknowledgment Slip) की कॉपी लॉकर में अपलोड करें"
            ]
            followups = [
                "पुश्तैनी संपत्ति में बेटियों का क्या अधिकार है?",
                "दुकान और पार्टनरशिप फर्म कैसे सुरक्षित रखें?",
                "सब-रजिस्ट्रार ऑफिस (तहसील) में वसीयत रजिस्ट्री कैसे कराएं?"
            ]
        else:
            answer = (
                f"### Institutional Nomination vs. Will Succession Analysis\n\n"
                f"Under landmark Supreme Court jurisprudence (**Sarbati Devi v. Usha Devi, 1984** and **Ram Chander Talwar v. Devender Kumar Talwar, 2010**), a nominee in Indian banking and insurance law is **merely an authorized trustee / collection agent**, not the beneficial owner.\n\n"
                f"#### Current Status in {profile.name}:\n"
                f"- **Nominee vs. Will Discrepancies:** {len(discrepancies)}\n{disc_details}\n\n"
                f"- **Missing Nominees:** {len(missing_noms)}\n{missing_details}\n\n"
                f"**Legal Consequence:** If a discrepancy exists, the bank will disburse money to the nominee. If the nominee refuses to transfer the funds to the will beneficiary, the family is forced into protracted civil litigation."
            )
            actions = [
                "Download updated nomination forms for any conflicting bank accounts",
                "Submit revised nomination forms matching the designated will beneficiaries",
                "Attach bank nomination acknowledgment receipts to the Encrypted Document Vault"
            ]
            followups = [
                "What happens if our will is not registered at SRO?",
                "How do we protect our partnership business from dissolving?",
                "What are the rights of daughters under Hindu coparcenary law?"
            ]

    # 2. Topic: Daughters & Coparcenary Rights (Vineeta Sharma)
    elif any(k in q for k in ["daughter", "coparcener", "vineeta", "sharma", "female", "sister", "girls", "beti", "ladki", "बेटी", "पुत्री", "हक", "जन्मसिद्ध", "bahin", "behan"]):
        d_status = []
        for d in daughters:
            d_allocs = [al for al in allocations if al.beneficiary_id == d.id]
            d_val = sum((al.share_percentage / 100.0) * next((a.estimated_value_inr for a in active_assets if a.id == al.asset_id), 0.0) for al in d_allocs)
            d_status.append(f"- **{d.name}** (Age: {d.age}, Marital: {d.marital_status}): Received ₹{d_val:,.0f} ({len(d_allocs)} assets allocated)")

        daughters_text = "\n".join(d_status) if daughters else "No living daughters listed in current family tree."

        if is_hindi_or_hinglish:
            answer = (
                f"### पुश्तैनी संपत्ति में बेटियों का कानूनी अधिकार (विनीता शर्मा फैसला)\n\n"
                f"सुप्रीम कोर्ट के ऐतिहासिक 3-जज बेंच फैसले (**Vineeta Sharma v. Rakesh Sharma, 2020**) के अनुसार:\n"
                f"👉 **बेटियों का पुश्तैनी जायदाद में बेटों के बराबर जन्मसिद्ध अधिकार (Coparcenary) है।**\n"
                f"चाहे बेटी शादीशुदा हो या अविवाहित, और चाहे 2005 से पहले पिता की मृत्यु हो चुकी हो या बाद में — बेटी का हक हमेशा बरकरार रहता है।\n\n"
                f"#### आपके परिवार में बेटियां:\n"
                f"{daughters_text}\n\n"
                f"**महत्वपूर्ण कानूनी दिशा-निर्देश:**\n"
                f"1. **पुश्तैनी संपत्ति (Ancestral Property):** पिता वसीयत के जरिए केवल अपने व्यक्तिगत हिस्से की वसीयत कर सकते हैं, बेटी का जन्मसिद्ध हिस्सा नहीं छीन सकते।\n"
                f"2. **खुद कमाई संपत्ति (Self-Acquired):** अपनी कमाई संपत्ति को आप अपनी मर्जी से किसी को भी दे सकते हैं, लेकिन बेटियों को बिल्कुल बाहर रखने पर वसीयत पर 'दबाव या अनुचित प्रभाव' का केस होने का जोखिम रहता है।\n"
                f"3. **हकत्याग (Relinquishment):** यदि बेटी अपनी मर्जी से हिस्सा छोड़ती है, तो उसका रजिस्टर्ड हकत्यागनामा (Registered Relinquishment Deed) होना अनिवार्य है।"
            )
            actions = [
                "पुश्तैनी संपत्ति का बंटवारा करते समय बेटियों के जन्मसिद्ध हिस्से का सम्मान करें",
                "वसीयत में बेटियों के लिए स्पष्ट व्यवस्था या रजिस्टर्ड हकत्यागनामा सुरक्षित रखें",
                "परिवार के सभी समझौते रजिस्टर्ड करवाकर एन्क्रिप्टेड लॉकर में रखें"
            ]
            followups = [
                "दुकान और व्यापार को टूटने से कैसे बचाएं?",
                "तैयारी का स्कोर कैसे बढ़ाएं?",
                "नॉमिनी और वसीयत में क्या अंतर है?"
            ]
        else:
            answer = (
                f"### Daughter's Rights & Coparcenary Parity (HSA 1956 amended 2005)\n\n"
                f"In the landmark three-judge bench ruling in **Vineeta Sharma v. Rakesh Sharma (2020) 9 SCC 1**, the Supreme Court of India held that daughters have an **unrestricted, equal birthright as coparceners** in joint Hindu family property, irrespective of whether the father was alive on September 9, 2005.\n\n"
                f"#### Current Daughters in {profile.name}:\n"
                f"{daughters_text}\n\n"
                f"**Key Succession Guidelines:**\n"
                f"1. **Ancestral Property:** A father cannot disinherit a daughter from her undivided coparcenary share via a Will. Testamentary capacity is strictly limited to the father's own undivided share.\n"
                f"2. **Self-Acquired Property:** While a testator has testamentary freedom over self-acquired property, total exclusion of daughters frequently invites lawsuits under 'undue influence' or 'suspicious circumstances'.\n"
                f"3. **Relinquishment Deeds:** If a daughter voluntarily foregoes property claims (e.g. at the time of marriage or business settlement), it **must be executed as a registered Release / Relinquishment Deed with stamp duty** to be legally binding."
            )
            actions = [
                "Ensure ancestral assets are allocated within Karta's undivided coparcenary share",
                "Verify all daughters have explicit testamentary shares or registered release deeds",
                "Store any family settlement deeds in the Encrypted Vault"
            ]
            followups = [
                "What are the biggest vulnerabilities in our succession plan?",
                "Explain our Succession Readiness Score",
                "How do we handle our outstanding business loans?"
            ]

    # 3. Topic: Business / Partnership Firm Succession
    elif any(k in q for k in ["business", "firm", "dukaan", "shop", "partnership", "trade", "proprietorship", "vyapar", "karobar", "दुकान", "व्यापार", "पार्टनरशिप", "फर्म", "karobaar", "dhandha"]):
        if is_hindi_or_hinglish:
            answer = (
                f"### दुकान व पारिवारिक व्यापार की सुरक्षा: {profile.business_name}\n\n"
                f"आपकी व्यापारिक इकाई **{profile.business_type}** के रूप में **{profile.city}, {profile.state}** में दर्ज है।\n\n"
                f"#### दुकानदारों के लिए 3 जरूरी कानूनी सावधानियां:\n"
                f"1. **पार्टनरशिप फर्म विघटन (धारा 42c, भारतीय पार्टनरशिप अधिनियम 1932):** किसी भी पार्टनर की मृत्यु पर फर्म स्वतः कानूनी रूप से भंग हो जाती है और बैंक खाते फ्रीज हो जाते हैं — जब तक कि पार्टनरशिप डीड में कानूनी वारिस को पार्टनर बनाने का स्पष्ट क्लॉज न हो।\n"
                f"2. **प्रोपराइटरशिप दुकान:** मालिक की मृत्यु पर GSTIN, पैन व म्युनिसिपल लाइसेंस समाप्त हो जाते हैं। वारिस को लीगल हायर सर्टिफिकेट के आधार पर नया GST नंबर लेना पड़ता है।\n"
                f"3. **दुकान का संचालन बनाम मुनाफा:** स्पष्ट करें कि दुकान की गद्दी पर कौन बैठेगा (मैनेजमेंट) और बाकी परिवार को मुनाफे में कितना हिस्सा मिलेगा।"
            )
            actions = [
                "पार्टनरशिप डीड में धारा 42(c) उत्तराधिकार क्लॉज की जांच करें",
                "फर्म में स्पष्ट पूरक डीड बनाएं कि मृत्यु के बाद कौन सा वारिस पार्टनर बनेगा",
                "ट्रेड लाइसेंस, GST विवरण व बैंक खाते के कागजात लॉकर में अपलोड करें"
            ]
            followups = [
                "नॉमिनी और वसीयत में क्या अंतर है?",
                "सब-रजिस्ट्रार ऑफिस (तहसील) में वसीयत रजिस्ट्री कैसे कराएं?",
                "तैयारी का स्कोर कैसे बढ़ाएं?"
            ]
        else:
            answer = (
                f"### Business Continuity & Succession: {profile.business_name}\n\n"
                f"Your business entity is registered as **{profile.business_type}** in **{profile.city}, {profile.state}**.\n\n"
                f"#### Critical Statutory Caveats for Traders:\n"
                f"1. **Partnership Dissolution (Section 42(c), Indian Partnership Act 1932):** By default, death of any partner immediately causes legal dissolution of the partnership firm, freezing bank accounts and GSTIN operations, *unless* the partnership deed contains an explicit continuation clause admitting legal heirs.\n"
                f"2. **Sole Proprietorship:** A sole proprietorship has no perpetual succession. The GSTIN, PAN, and municipal trade licenses terminate upon death of the proprietor. The designated successor must apply for a fresh GSTIN with legal heir inheritance transfer.\n"
                f"3. **Management vs. Ownership:** Distinguish between family members managing day-to-day operations (shop counter/vendors) and passive equity beneficiaries receiving profits."
            )
            actions = [
                "Inspect partnership deed to ensure Section 42(c) continuation clause is present",
                "Execute an explicit addendum designating which legal heir enters as partner",
                "Document trade licenses, GST credentials, and supplier credit agreements in the Vault"
            ]
            followups = [
                "Which assets in our estate have nominee conflicts?",
                "What happens to our bank accounts if we don't have a registered will?",
                "Explain our Succession Readiness Score"
            ]

    # 4. Topic: SRO Will Registration
    elif any(k in q for k in ["register", "registration", "sro", "registry", "panjikaran", "रजिस्ट्री", "पंजीकरण", "सब-रजिस्ट्रार", "तहसील", "sub registrar"]):
        if is_hindi_or_hinglish:
            answer = (
                f"### सब-रजिस्ट्रार ऑफिस (तहसील) में वसीयत रजिस्ट्री नियम\n\n"
                f"👉 **1. क्या रजिस्ट्री अनिवार्य है?**\n"
                f"नहीं! भारतीय पंजीकरण अधिनियम 1908 (धारा 18) के तहत वसीयत को रजिस्टर कराना अनिवार्य नहीं है। सादे कागज पर दो स्वतंत्र गवाहों के सामने लिखी वसीयत भी पूर्णतः कानूनी है।\n\n"
                f"👉 **2. फिर रजिस्ट्री क्यों करानी चाहिए?**\n"
                f"सब-रजिस्ट्रार ऑफिस (Book 3) में वसीयत दर्ज कराने से भविष्य में कोई फर्जी वसीयत या मानसिक अस्वस्थता का झूठा आरोप नहीं लगा सकता। कोर्ट में इसका प्रमाणिक मूल्य (Evidentiary Value) बहुत मजबूत होता है।\n\n"
                f"👉 **3. खर्चा व स्टांप ड्यूटी:**\n"
                f"वसीयत पर कोई स्टांप ड्यूटी (Zero Stamp Duty) नहीं लगती! केवल ₹100 से ₹500 की सामान्य सरकारी फीस लगती है।\n\n"
                f"👉 **4. जरूरी लोग:** टेस्टेटर (Karta) स्वयं उपस्थित हों + 2 स्वतंत्र गवाह (जो वारिस न हों) अपने मूल आधार कार्ड के साथ।"
            )
            actions = [
                "वसीयत पर डॉक्टर का मानसिक स्वस्थता प्रमाणपत्र (Medical Fitness Certificate) संलग्न करें",
                "2 स्वतंत्र गवाह चुनें जो वसीयत में संपत्ति के लाभार्थी (Beneficiary) न हों",
                "स्थानीय सब-रजिस्ट्रार ऑफिस (तहसील) में Book 3 रजिस्ट्रेशन की तारीख तय करें"
            ]
            followups = [
                "नॉमिनी और वसीयत में क्या अंतर है?",
                "दुकान और व्यापार को टूटने से कैसे बचाएं?",
                "पुश्तैनी संपत्ति में बेटियों का क्या अधिकार है?"
            ]
        else:
            answer = (
                f"### Sub-Registrar Office (SRO) Will Registration Guide\n\n"
                f"1. **Is Registration Mandatory?** NO (Section 18, Indian Registration Act 1908). An unregistered written will is legally valid if signed by 2 witnesses. However, registration strongly protects against future allegations of forgery.\n\n"
                f"2. **Stamp Duty:** ZERO (Nil across all Indian states). Only a nominal government registration fee (₹100 - ₹500) applies.\n\n"
                f"3. **Procedure at SRO:** The Testator must visit the local Sub-Registrar Office with 2 independent adult witnesses (with original Aadhaar/Voter IDs) and optional doctor's fitness certificate.\n\n"
                f"4. **Safe Custody:** Registered wills are recorded in official Book 3 registers maintained by the State Government."
            )
            actions = [
                "Schedule appointment at the local Sub-Registrar Office",
                "Ensure both witnesses are independent and not beneficiaries under the will",
                "Obtain a medical fitness certificate from an MBBS practitioner"
            ]
            followups = [
                "Which assets in our estate have nominee conflicts?",
                "How do we protect our business from dissolving?",
                "Explain our Succession Readiness Score"
            ]

    # 5. Topic: Readiness Score & Improvement
    elif any(k in q for k in ["readiness", "score", "health", "grade", "improve", "checklist", "tayari", "sudhar", "स्कोर", "तैयारी", "बंटवारा", "batwara", "hissa"]):
        p = readiness["pillars"]
        action_text = "\n".join([f"{i+1}. **[{a['pillar']}]** {a['action']} (*Impact: {a['impact']}*)" for i, a in enumerate(readiness["priority_actions"])]) if readiness["priority_actions"] else "All standard checklist criteria fulfilled!"

        if is_hindi_or_hinglish:
            answer = (
                f"### पारिवारिक विरासत व तैयारी स्कोर समीक्षा: {readiness['grade']}\n\n"
                f"आपके परिवार का समग्र तैयारी स्कोर **{readiness['overall_score']}/100** ({readiness['status_label']}) है।\n\n"
                f"#### 4 मुख्य स्तंभ (Pillars):\n"
                f"- **1. कागजात व लॉकर कवरेज:** {p['documentation']['score']}/25 ({p['documentation']['documented_assets']}/{p['documentation']['total_assets']} संपत्तियां दर्ज)\n"
                f"- **2. बैंक नॉमिनी कवरेज:** {p['nomination']['score']}/25 ({p['nomination']['nominated_count']}/{p['nomination']['financial_assets_count']} खातों में नॉमिनी दर्ज; {p['nomination']['discrepancies']} विवाद)\n"
                f"- **3. वसीयत ड्राफ्ट व स्पष्टता:** {p['testamentary']['score']}/25 ({p['testamentary']['allocated_assets']}/{p['testamentary']['total_assets']} संपत्तियां आवंटित)\n"
                f"- **4. कानूनी व पुश्तैनी समता:** {p['statutory_equity']['score']}/25 (बेटियों व उत्तराधिकारियों का संरक्षण)\n\n"
                f"#### स्कोर 95+ पहुंचाने के लिए जरूरी कदम:\n"
                f"{action_text}"
            )
            actions = [a["action"] for a in readiness["priority_actions"]]
            followups = [
                "नॉमिनी और वसीयत में क्या अंतर है?",
                "पुश्तैनी संपत्ति में बेटियों का क्या अधिकार है?",
                "सब-रजिस्ट्रार ऑफिस (तहसील) में वसीयत रजिस्ट्री कैसे कराएं?"
            ]
        else:
            answer = (
                f"### Succession Readiness / Health Audit: {readiness['grade']}\n\n"
                f"Your overall estate succession readiness score is **{readiness['overall_score']}/100** ({readiness['status_label']}).\n\n"
                f"#### 4 Institutional Pillars Breakdown:\n"
                f"- **1. Documentation & Vault Coverage:** {p['documentation']['score']}/25 ({p['documentation']['documented_assets']}/{p['documentation']['total_assets']} assets documented)\n"
                f"- **2. Institutional Nomination Coverage:** {p['nomination']['score']}/25 ({p['nomination']['nominated_count']}/{p['nomination']['financial_assets_count']} accounts nominated; {p['nomination']['discrepancies']} discrepancies)\n"
                f"- **3. Testamentary Clarity & Will Draft:** {p['testamentary']['score']}/25 ({p['testamentary']['allocated_assets']}/{p['testamentary']['total_assets']} assets allocated)\n"
                f"- **4. Statutory & Coparcenary Equity:** {p['statutory_equity']['score']}/25 (Coparcenary & daughter protections evaluated)\n\n"
                f"#### Priority Actions to Reach Institutional Grade (95+):\n"
                f"{action_text}"
            )
            actions = [a["action"] for a in readiness["priority_actions"]]
            followups = [
                "Which assets have nominee conflicts?",
                "What are the rights of daughters under Hindu coparcenary law?",
                "How do we register our will at the Sub-Registrar Office?"
            ]

    # 6. Default / General Gap Analysis
    else:
        unallocated = [a for a in active_assets if a.id not in allocations_by_asset]
        unalloc_names = ", ".join([u.title for u in unallocated[:3]]) if unallocated else "None"
        disc_names = ", ".join([d["title"] for d in discrepancies[:3]]) if discrepancies else "None"

        if is_hindi_or_hinglish:
            answer = (
                f"### पारिवारिक विरासत और उत्तराधिकार समीक्षा: {profile.name}\n\n"
                f"हमने आपके **{len(members)} पारिवारिक सदस्यों**, कुल ₹{total_asset_val:,.0f} मूल्य की **{len(active_assets)} सक्रिय संपत्तियों**, और ₹{total_liabilities:,.0f} की देनदारियों का **{profile.governing_law}** के अनुसार विश्लेषण किया।\n\n"
                f"#### मुख्य निष्कर्ष व कमियां:\n"
                f"1. **तैयारी स्कोर:** **{readiness['overall_score']}/100** ({readiness['grade']})।\n"
                f"2. **बिना वारिस वाली संपत्तियां:** {len(unallocated)} संपत्तियों ({unalloc_names}) का वसीयत में कोई स्पष्ट वारिस तय नहीं है।\n"
                f"3. **नॉमिनी विवाद:** {len(discrepancies)} संपत्तियों ({disc_names}) में बैंक नॉमिनी और वसीयत का वारिस अलग-अलग हैं (सरबती देवी कानूनी विवाद जोखिम)।\n"
                f"4. **रजिस्ट्री स्थिति:** सब-रजिस्ट्रार ऑफिस में पंजीकरण {'तय है' if (will_draft and will_draft.sro_reminder_date) else 'लंबित है'}।\n\n"
                f"परिवार में भविष्य के विवादों से बचने के लिए सभी संपत्तियों का पक्का वारिस तय करें और कागजात एन्क्रिप्टेड लॉकर में रखें।"
            )
            actions = [
                "बैंक नॉमिनी को वसीयत में नामित वारिस के साथ मिलाएँ",
                "सभी शेष संपत्तियों के लिए वसीयत में स्पष्ट वारिस तय करें",
                "सब-रजिस्ट्रार ऑफिस (तहसील) में वसीयत पंजीकरण का समय तय करें"
            ]
            followups = [
                "नॉमिनी और वसीयत में क्या अंतर है?",
                "पुश्तैनी संपत्ति में बेटियों का क्या अधिकार है?",
                "दुकान और पार्टनरशिप फर्म कैसे सुरक्षित रखें?"
            ]
        else:
            answer = (
                f"### Comprehensive Family Legacy Assessment for {profile.name}\n\n"
                f"We evaluated **{len(members)} family members**, **{len(active_assets)} active assets** valued at **₹{total_asset_val:,.0f}**, and outstanding liabilities of **₹{total_liabilities:,.0f}** under the **{profile.governing_law}**.\n\n"
                f"#### Key Vulnerabilities Identified:\n"
                f"1. **Succession Readiness Score:** **{readiness['overall_score']}/100** ({readiness['grade']}).\n"
                f"2. **Unallocated Assets:** {len(unallocated)} properties ({unalloc_names}) have no assigned successor in the will.\n"
                f"3. **Nomination Conflicts:** {len(discrepancies)} assets ({disc_names}) feature conflicting nominees vs will beneficiaries (Sarbati Devi litigation hazard).\n"
                f"4. **Registration Status:** Will registration at the local Sub-Registrar Office is currently {'scheduled' if (will_draft and will_draft.sro_reminder_date) else 'pending'}.\n\n"
                f"To achieve maximum legal certainty, ensure all title deeds are encrypted in the Vault and book an SRO Book 3 registration appointment."
            )
            actions = [
                "Harmonize bank nominees with designated will beneficiaries",
                "Assign testamentary shares to all unallocated assets",
                "Schedule Sub-Registrar Office Book 3 will registration appointment"
            ]
            followups = [
                "Which assets have nominee conflicts?",
                "Explain our Succession Readiness Score",
                "What are the rights of daughters under Hindu coparcenary law?"
            ]

    return {
        "query": query_str,
        "answer": answer,
        "identified_gaps": [
            f"Succession Readiness Score: {readiness['overall_score']}/100",
            f"{len(daughters)} living daughters evaluated for coparcenary parity",
            f"Business: {profile.business_type} continuity assessment"
        ],
        "action_items": actions,
        "suggested_followups": followups,
        "ai_provider": "Waaris Local Statutory Engine (Offline / Zero Setup)",
        "api_key_required": False,
        "api_key_note": "No API key is required to use the AI Legacy Advisor. The built-in Indian legal reasoning engine runs 100% locally and free."
    }

