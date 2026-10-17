import sys, requests
sys.stdout.reconfigure(encoding='utf-8')

base = 'http://127.0.0.1:8000'
results = []

def check(name, fn):
    try:
        ok, detail = fn()
        results.append((name, ok, detail))
    except Exception as e:
        results.append((name, False, str(e)))

# Public check: Homepage loads
check('M1-a: Homepage loads', lambda: (requests.get(base).status_code == 200, '200 OK'))

# Public check: Scenarios seeded
scenarios = requests.get(f'{base}/api/scenarios').json()
check('M1-b: 5 scenarios seeded', lambda: (len(scenarios) >= 5, f'{len(scenarios)} scenarios found (>= 5 seeded/custom)'))

# Login as Karta of Sharma Family (Profile 1)
login_res = requests.post(f'{base}/api/auth/login', json={'username': 'karta_sharma', 'password': 'Virasat@2026'}).json()
karta_token = login_res.get('token')
karta_headers = {'Authorization': f'Bearer {karta_token}'}

# Login as Heir of Sharma Family
heir_login = requests.post(f'{base}/api/auth/login', json={'username': 'rohit_heir', 'password': 'Virasat@2026'}).json()
heir_token = heir_login.get('token')
heir_headers = {'Authorization': f'Bearer {heir_token}'}

# M1 - Family tree + asset inventory (Authenticated)
members_res = requests.get(f'{base}/api/family/1', headers=karta_headers)
members = members_res.json().get('members', []) if members_res.status_code == 200 else []
check('M1-c: Family tree members', lambda: (len(members) > 0, f'{len(members)} members in Sharma family'))

assets_resp = requests.get(f'{base}/api/assets/1', headers=karta_headers).json()
assets = assets_resp.get('assets', assets_resp) if isinstance(assets_resp, dict) else assets_resp
check('M1-d: Asset inventory', lambda: (len(assets) > 0, f'{len(assets)} assets in Sharma family'))

summary = assets_resp.get('summary', {}) if isinstance(assets_resp, dict) else {}
total_val = summary.get('total_assets_inr', 0) or sum(a.get('estimated_value_inr', 0) for a in assets if isinstance(a, dict))
check('M1-e: Asset values calculated', lambda: (total_val > 0, f'Total estate: Rs {total_val:,.0f}'))

# M2 - Will/succession draft generator
will = requests.get(f'{base}/api/will/1', headers=karta_headers).json()
check('M2-a: Will draft exists', lambda: (will.get('executor_name') is not None, f"Executor: {will.get('executor_name')}"))

pdf_r = requests.post(f'{base}/api/export-pdf/1', headers=karta_headers)
check('M2-b: PDF generation', lambda: (pdf_r.status_code == 200, f'Content-Type: {pdf_r.headers.get("content-type")}'))
check('M2-c: PDF has content', lambda: (len(pdf_r.content) > 5000, f'{len(pdf_r.content):,} bytes'))

# M3 - Document vault
vault = requests.get(f'{base}/api/vault/1', headers=karta_headers).json()
check('M3-a: Vault endpoint', lambda: (isinstance(vault, list), f'{len(vault)} vault documents'))

sro = requests.get(f'{base}/api/sro-guide')
check('M3-b: SRO guide (register-will reminder)', lambda: (sro.status_code == 200, 'SRO guide endpoint available'))
sro_data = sro.json()
check('M3-c: SRO guide has steps', lambda: (len(sro_data.get('step_by_step_checklist', sro_data.get('steps', []))) > 0, f"{len(sro_data.get('step_by_step_checklist', sro_data.get('steps', [])))} registration steps"))

# M4 - Multi-member access / RBAC
r_switch = requests.post(f'{base}/api/role/1', json={'role': 'heir'}, headers=karta_headers)
active_role = r_switch.json().get('active_role') if r_switch.status_code == 200 else 'unknown'
check('M4-a: Role switch Patriarch->Heir view', lambda: (r_switch.status_code == 200, f'active_role={active_role}'))

# Heir blocked from adding assets (403 Forbidden)
r_blocked = requests.post(f'{base}/api/assets/1', json={
    'profile_id': 1, 'title': 'Unauthorized Shop', 'category': 'commercial_shop', 'estimated_value_inr': 1000000.0
}, headers=heir_headers)
check('M4-b: Heir blocked from mutations (403)', lambda: (r_blocked.status_code == 403, f'HTTP {r_blocked.status_code} - access denied correctly'))

# Switch back to patriarch
r_patriarch = requests.post(f'{base}/api/role/1', json={'role': 'patriarch'}, headers=karta_headers)
check('M4-c: Switch back to Patriarch', lambda: (r_patriarch.status_code == 200, 'Patriarch role restored'))

# Heir escalation blocked (403 Forbidden)
r_escalate = requests.post(f'{base}/api/role/1', json={'role': 'patriarch'}, headers=heir_headers)
check('M4-d: Heir role escalation blocked (403)', lambda: (r_escalate.status_code == 403, 'Role escalation prevented'))

# M5 - Scenario simulator
sim = requests.get(f'{base}/api/simulation/1', headers=karta_headers).json()
check('M5-a: Simulation runs', lambda: ('intestate_shares' in sim, f"Keys: {list(sim.keys())}"))
check('M5-b: Dispute risk score', lambda: (sim.get('dispute_risk_score') is not None, f"Risk score: {sim.get('dispute_risk_score')}/100"))
check('M5-c: Intestate shares calculated', lambda: (len(sim.get('intestate_shares', [])) > 0, f"{len(sim.get('intestate_shares', []))} heirs mapped"))
check('M5-d: Pitfalls detected', lambda: (isinstance(sim.get('pitfalls'), list), f"{len(sim.get('pitfalls', []))} pitfalls found"))

notes = requests.get(f'{base}/api/advisor-notes/1', headers=karta_headers).json()
check('M5-e: Advisor notes', lambda: (len(notes) > 0, f'{len(notes)} advisor notes'))

# M6 - Legacy OS & Intelligence Modules
r_readiness = requests.get(f'{base}/api/readiness/1', headers=karta_headers)
readiness_data = r_readiness.json() if r_readiness.status_code == 200 else {}
check('M6-a: Succession Readiness Score', lambda: (r_readiness.status_code == 200 and 'overall_score' in readiness_data, f"Score: {readiness_data.get('overall_score')}/100, Grade: {readiness_data.get('grade')}"))

r_tracker = requests.get(f'{base}/api/nomination-tracker/1', headers=karta_headers)
tracker_data = r_tracker.json() if r_tracker.status_code == 200 else []
check('M6-b: Nomination vs Will Tracker', lambda: (r_tracker.status_code == 200 and len(tracker_data) > 0, f"{len(tracker_data)} assets tracked with Sarbati Devi alignment"))

r_adv = requests.post(f'{base}/api/legacy-advisor/1/query', json={'query': 'What are our nominee discrepancies?'}, headers=karta_headers)
adv_data = r_adv.json() if r_adv.status_code == 200 else {}
check('M6-c: AI Family Legacy Advisor', lambda: (r_adv.status_code == 200 and len(adv_data.get('answer', '')) > 50, f"AI Answer returned ({len(adv_data.get('action_items', []))} action items)"))

r_mem_detail = requests.get(f'{base}/api/family/1/member-detail/1', headers=karta_headers)
mem_detail_data = r_mem_detail.json() if r_mem_detail.status_code == 200 else {}
check('M6-d: Member Portfolio & Statutory Rights', lambda: (r_mem_detail.status_code == 200 and 'statutory_class' in mem_detail_data, f"Class: {mem_detail_data.get('statutory_class')}, Intestate: {mem_detail_data.get('statutory_intestate_share_pct')}%"))

# Custom data entry (user-entered data)
new_p = requests.post(f'{base}/api/profile', json={
    'name': 'Audit Test Family',
    'karta_name': 'Ramesh Verma',
    'business_name': 'Verma Hardware Store',
    'business_type': 'Sole Proprietorship',
    'city': 'Lucknow',
    'state': 'Uttar Pradesh',
    'religion': 'Hindu',
    'governing_law': 'Hindu Succession Act, 1956 (amended 2005)'
})
check('CUSTOM-a: Create new profile from scratch', lambda: (new_p.status_code == 200, f"Profile ID={new_p.json().get('id')}"))
pid = new_p.json().get('id')
custom_token = new_p.json().get('auth_token')
custom_headers = {'Authorization': f'Bearer {custom_token}'}

new_m = requests.post(f'{base}/api/family/{pid}/member', json={
    'profile_id': pid, 'name': 'Sunita Verma', 'relation': 'Spouse',
    'gender': 'Female', 'age': 48, 'marital_status': 'Married'
}, headers=custom_headers)
check('CUSTOM-b: Add family member', lambda: (new_m.status_code == 200, f"Member: {new_m.json().get('name')}"))

new_a = requests.post(f'{base}/api/assets/{pid}', json={
    'profile_id': pid, 'category': 'commercial_shop', 'title': 'Shop at Aminabad',
    'estimated_value_inr': 3500000.0
}, headers=custom_headers)
check('CUSTOM-c: Add asset', lambda: (new_a.status_code == 200, f"Asset: {new_a.json().get('title')}, Rs {new_a.json().get('estimated_value_inr'):,.0f}"))

upd = requests.put(f'{base}/api/profile/{pid}', json={'city': 'Kanpur'}, headers=custom_headers)
check('CUSTOM-d: Edit profile', lambda: (upd.status_code == 200, 'Profile updated'))

# Cleanup test profile
del_r = requests.delete(f'{base}/api/profile/{pid}', headers=custom_headers)
check('CUSTOM-e: Delete test profile', lambda: (del_r.status_code == 200, 'Test profile cleaned up'))

# Summary
print()
print('=' * 65)
print('    VIRASAT PLANNER — LIVE FEATURE AUDIT RESULTS')
print('=' * 65)
for name, ok, detail in results:
    icon = '✅' if ok else '❌'
    print(f'  {icon}  {name}')
    print(f'       → {detail}')
print('=' * 65)
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f'  RESULT: {passed}/{total} checks PASSED {"🎉 ALL CLEAR" if passed == total else "⚠️  SOME FAILURES"}')
print('=' * 65)
