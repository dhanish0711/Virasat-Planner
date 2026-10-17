/**
 * VirasatPlanner - Main Frontend Application Logic
 * Full-Stack Succession Planning with Real RBAC, Salted Password Auth,
 * AES-128-CBC + HMAC-SHA256 Encrypted Vault, Deadlines/Reminders Subsystem,
 * and Interactive Hindu/Muslim/Christian Succession Simulator.
 */

let state = {
  currentProfileId: 1,
  currentProfile: null,
  scenarios: [],
  members: [],
  assets: [],
  allocations: [],
  willDraft: null,
  vaultDocs: [],
  advisorNotes: [],
  simulationData: null,
  reminders: null,
  activeTab: 'dashboard',
  currentLang: 'en', // 'en' or 'hi'
  activeRole: 'patriarch', // 'patriarch', 'heir', 'advisor'
  authToken: localStorage.getItem("virasat_token") || null,
  currentUser: null,
  simParams: {
    unregistered_will: false,
    exclude_daughter: false,
    predeceased_child_id: null,
    ademption_asset_id: null
  },
  readinessData: null,
  nominationTrackerData: [],
  advisorChatMessages: [],
  trackerFilter: 'all'
};

// Seed credentials mapping per profile for fast 1-click test role authentication
const scenarioRoleUserMap = {
  1: { patriarch: "karta_sharma", heir: "rohit_heir", advisor: "advisor_chawla" },
  2: { patriarch: "karta_gupta", heir: "vikas_heir", advisor: "advisor_patel" },
  3: { patriarch: "karta_verma", heir: "deepak_heir", advisor: "advisor_shukla" },
  4: { patriarch: "karta_agarwal", heir: "gaurav_heir", advisor: "advisor_mittal" },
  5: { patriarch: "karta_patel", heir: "priyanshi_heir", advisor: "advisor_bhatt" }
};

// Language Dictionary (English, Hindi & Hinglish)
const i18n = {
  en: {
    appTitle: "Waaris — Multi-Generational Asset & Succession Planner",
    appSubtitle: "Dedicated to Indian small traders, businesses & joint families",
    tabDashboard: "Dashboard",
    tabFamily: "Family Tree",
    tabAssets: "Asset Inventory",
    tabWill: "Will & Succession",
    tabVault: "Document Vault",
    tabSimulator: "'What-If' Simulator",
    tabAdvisor: "CA & Legal Audit",
    tabTracker: "Nominee Gap Tracker",
    tabLegacyAdvisor: "AI Legacy Advisor",
    netWorth: "Total Family Net Worth",
    assetsValue: "Gross Assets",
    liabilitiesValue: "Outstanding Liabilities",
    disputeRisk: "Family Dispute Risk",
    btnCreatePlan: "Create My Plan",
    btnEditDetails: "Edit Details",
    btnSroGuide: "SRO Checklist",
    btnSimulate: "Simulate Demise",
    switchRole: "Active Role:",
    patriarchRole: "Patriarch / Karta",
    heirRole: "Heir / Nominee",
    advisorRole: "CA / Legal Advisor",
    downloadPDF: "Download Formal Will PDF",
    uploadDoc: "Upload to Encrypted Vault",
    runSimulation: "Run Legal Simulation",
    addMemberBtn: "+ Add Family Member",
    addAssetBtn: "+ Add Asset",
    sroGuideTitle: "Sub-Registrar Registration Guide",
    nomineeNotice: "Note: In Indian law, a bank nominee is merely a temporary custodian/trustee, NOT the legal owner!",
    // Onboarding Wizard
    wizTitle: "Simple 4 Steps — Secure Your Family Estate & Succession Plan",
    wizHint: "Click any step to begin →",
    wizStep1Title: "Map Family Lineage",
    wizStep1Desc: "Record parents, spouse, children, daughters, and coparceners in the family tree.",
    wizStep2Title: "Record Assets & Business",
    wizStep2Desc: "List shops, commercial property, gold, bank accounts, FDs, and existing nominees.",
    wizStep3Title: "Draft Succession Will",
    wizStep3Desc: "Designate which heir receives which asset; appoint trusted executor and witnesses.",
    wizStep4Title: "Encrypted Vault Storage",
    wizStep4Desc: "Safeguard registry title deeds, share certificates, and partnership pacts in AES-256 vault.",
    // Legal Essentials
    legalTitle: "4 Essential Legal Rules for Family Businesses & Joint Families:",
    legal1Title: "🏦 Bank Nominee ≠ Legal Owner",
    legal1Desc: "Under Supreme Court precedent (Sarbati Devi), a nominee is only a temporary trustee. Final legal ownership passes strictly via the Will or succession law.",
    legal2Title: "⚖️ Equal Coparcenary for Daughters",
    legal2Desc: "Under the 2005 HSA amendment & Vineeta Sharma ruling, daughters possess birthright coparcenary rights equal to sons in ancestral property, even after marriage.",
    legal3Title: "🏢 Partnership Firm Protection",
    legal3Desc: "Under Section 42(c) of the Indian Partnership Act, a firm automatically dissolves upon a partner's demise unless the deed includes an explicit succession clause.",
    legal4Title: "🏛️ Sub-Registrar (SRO) Registration",
    legal4Desc: "While an un-registered will is legally valid with 2 witnesses, registering at the Sub-Registrar office prevents fraudulent dispute challenges.",
    // Simulator
    simScenarioATitle: "Scenario A: Without Will (Intestate Distribution)",
    simScenarioBTitle: "Scenario B: With Registered Will (Testamentary Plan)",
    simThIntestate: "Intestate Share (Without Will)",
    simThTestate: "Will Share (With Will)",
    // AI Advisor
    advInquiriesTitle: "Suggested Quick Inquiries:",
    advPill1Text: "⚠️ Nominee vs Will Beneficiary",
    advPill1Query: "What is the difference between a bank nominee and a will beneficiary under Indian law?",
    advPill2Text: "👩‍👧 Daughters' Coparcenary Rights",
    advPill2Query: "What are daughters coparcenary rights in ancestral joint family property?",
    advPill3Text: "🏢 Protect Business & Shop",
    advPill3Query: "How can we protect our partnership firm and shop from dissolution upon demise?",
    advPill4Text: "📊 Improve Readiness Score",
    advPill4Query: "How can our family improve our estate and succession readiness score?",
    advPill5Text: "🏛️ SRO Will Registration Rules",
    advPill5Query: "What are the rules and process to register a will at the Sub-Registrar office?",
    advPlaceholder: "Ask a legal or succession question: e.g. 'Daughter rights', 'Nominee rules', 'Business continuity'...",
    advSendBtn: "Ask Advisor",
    // Role Banners
    heirBannerTitle: "HEIR VIEW",
    heirBannerDesc: "Read-only estate visibility. Modifications to assets, family tree, and will clauses are strictly locked.",
    advisorBannerTitle: "CA / ADVOCATE AUDIT VIEW",
    advisorBannerDesc: "You have auditor access. Reviewing asset titles, nominee discrepancies, and posting advisory notes.",
    // Toast validations
    errAgeMember: "Please enter a valid age for the family member",
    errAgeKarta: "Please enter a valid age"
  },
  hi: {
    appTitle: "वारिस (Waaris) — पारिवारिक संपत्ति एवं वसीयत नियोजक",
    appSubtitle: "छोटे व्यापारियों, दुकानदारों और संयुक्त परिवारों के लिए सुलभ कानूनी समाधान",
    tabDashboard: "डैशबोर्ड",
    tabFamily: "परिवार वृक्ष",
    tabAssets: "संपत्ति विवरण",
    tabWill: "वसीयत ड्राफ्ट",
    tabVault: "दस्तावेज़ लॉकर",
    tabSimulator: "विभाजन सिमुलेटर",
    tabAdvisor: "कानूनी समीक्षा",
    tabTracker: "नॉमिनी व गैप ट्रैकर",
    tabLegacyAdvisor: "AI विरासत सलाहकार",
    netWorth: "कुल पारिवारिक शुद्ध संपत्ति",
    assetsValue: "कुल संपत्ति",
    liabilitiesValue: "बाजार उधारी व देनदारियां",
    disputeRisk: "विवाद जोखिम",
    btnCreatePlan: "नया प्लान बनाएं",
    btnEditDetails: "विवरण बदलें",
    btnSroGuide: "रजिस्ट्री गाइड",
    btnSimulate: "विभाजन जांचें",
    switchRole: "वर्तमान भूमिका:",
    patriarchRole: "मुखिया / कर्ता",
    heirRole: "वारिस / परिवार सदस्य",
    advisorRole: "सीए / वकील (सलाहकार)",
    downloadPDF: "कानूनी वसीयत PDF डाउनलोड करें",
    uploadDoc: "सुरक्षित लॉकर में अपलोड करें",
    runSimulation: "विभाजन सिमुलेटर चलाएं",
    addMemberBtn: "+ नया सदस्य जोड़ें",
    addAssetBtn: "+ नई संपत्ति जोड़ें",
    sroGuideTitle: "सब-रजिस्ट्रार ऑफिस रजिस्ट्री गाइड",
    nomineeNotice: "स्मरण रहे: भारतीय कानून में बैंक नॉमिनी सिर्फ अमानतदार (Trustee) होता है, कानूनी मालिक नहीं!",
    // Onboarding Wizard
    wizTitle: "आसान 4 चरण — अपने परिवार की संपत्ति और उत्तराधिकार योजना सुरक्षित करें",
    wizHint: "शुरू करने के लिए किसी भी चरण पर क्लिक करें →",
    wizStep1Title: "पारिवारिक वंशावली दर्ज करें",
    wizStep1Desc: "माता-पिता, जीवनसाथी, पुत्र, पुत्री और सह-दायिकी सदस्यों को परिवार वृक्ष में जोड़ें।",
    wizStep2Title: "दुकान व संपत्ति दर्ज करें",
    wizStep2Desc: "दुकान, व्यावसायिक संपत्ति, सोना, बैंक खाते, एफडी और मौजूदा नॉमिनी दर्ज करें।",
    wizStep3Title: "वसीयत का मसौदा तैयार करें",
    wizStep3Desc: "तय करें कि किस वारिस को कौन सी संपत्ति मिलेगी; निष्पादक और गवाह नियुक्त करें।",
    wizStep4Title: "सुरक्षित लॉकर में सहेजें",
    wizStep4Desc: "रजिस्ट्री डीड, शेयर प्रमाणपत्र और पार्टनरशिप अनुबंध को AES-256 लॉकर में सुरक्षित रखें।",
    // Legal Essentials
    legalTitle: "व्यापारिक व संयुक्त परिवारों के लिए 4 अनिवार्य कानूनी नियम:",
    legal1Title: "🏦 बैंक नॉमिनी ≠ कानूनी मालिक",
    legal1Desc: "सुप्रीम कोर्ट (सरबती देवी) के अनुसार नॉमिनी केवल ट्रस्टी होता है। असली मालिकाना हक वसीयत या उत्तराधिकार कानून से मिलता है।",
    legal2Title: "⚖️ बेटियों का समान जन्मसिद्ध हक",
    legal2Desc: "2005 संशोधन व विनीता शर्मा फैसले के तहत पुश्तैनी संपत्ति में बेटियों का बेटों के बराबर जन्मसिद्ध अधिकार है, शादी के बाद भी।",
    legal3Title: "🏢 पार्टनरशिप फर्म सुरक्षा",
    legal3Desc: "पार्टनरशिप एक्ट की धारा 42(c) के तहत पार्टनर की मृत्यु पर फर्म भंग हो जाती है, जब तक कि डीड में उत्तराधिकार क्लॉज न हो।",
    legal4Title: "🏛️ सब-रजिस्ट्रार (तहसील) रजिस्ट्री",
    legal4Desc: "2 गवाहों के साथ बिना रजिस्ट्री की वसीयत भी वैध है, पर सब-रजिस्ट्रार कार्यालय में रजिस्ट्री कराने से धोखाधड़ी व विवाद रुकते हैं।",
    // Simulator
    simScenarioATitle: "परिदृश्य अ: बिना वसीयत (कानूनी बंटवारा)",
    simScenarioBTitle: "परिदृश्य ब: वसीयत के साथ (नियोजित बंटवारा)",
    simThIntestate: "कानूनी हिस्सा (बिना वसीयत)",
    simThTestate: "वसीयत अनुसार हिस्सा",
    // AI Advisor
    advInquiriesTitle: "सुझाए गए कानूनी प्रश्न:",
    advPill1Text: "⚠️ नॉमिनी बनाम वसीयत वारिस",
    advPill1Query: "भारतीय कानून में बैंक नॉमिनी और वसीयत के वारिस में क्या अंतर है?",
    advPill2Text: "👩‍👧 पुश्तैनी संपत्ति में बेटियों का हक",
    advPill2Query: "पुश्तैनी संपत्ति में बेटियों का क्या कानूनी अधिकार है?",
    advPill3Text: "🏢 दुकान व व्यापार की सुरक्षा",
    advPill3Query: "पार्टनर की मृत्यु पर दुकान और पार्टनरशिप फर्म को टूटने से कैसे बचाएं?",
    advPill4Text: "📊 तैयारी स्कोर कैसे सुधारें",
    advPill4Query: "हमारे परिवार की उत्तराधिकार तैयारी का स्कोर कैसे बढ़ाएं?",
    advPill5Text: "🏛️ तहसील वसीयत रजिस्ट्री नियम",
    advPill5Query: "सब-रजिस्ट्रार ऑफिस में वसीयत रजिस्ट्री कराने की क्या प्रक्रिया और नियम हैं?",
    advPlaceholder: "कानूनी प्रश्न पूछें: जैसे 'बेटियों का हक', 'नॉमिनी नियम', 'व्यापार सुरक्षा'...",
    advSendBtn: "सलाहकार से पूछें",
    // Role Banners
    heirBannerTitle: "वारिस दृश्य (वारिस मोड)",
    heirBannerDesc: "केवल देखने का अधिकार। संपत्ति, परिवार वृक्ष और वसीयत में बदलाव पूरी तरह लॉक हैं।",
    advisorBannerTitle: "सीए / वकील ऑडिट दृश्य",
    advisorBannerDesc: "आपको लेखा परीक्षक पहुंच प्राप्त है। संपत्ति के स्वामित्व, नॉमिनी विसंगतियों की समीक्षा कर रहे हैं।",
    // Toast validations
    errAgeMember: "कृपया परिवार सदस्य की सही उम्र दर्ज करें",
    errAgeKarta: "कृपया सही उम्र दर्ज करें"
  },
  hinglish: {
    appTitle: "Waaris — Family Asset aur Wasiyat Planner",
    appSubtitle: "Chhote dukandaaron aur joint families ke liye aasaan legal tool",
    tabDashboard: "Dashboard",
    tabFamily: "Family Tree",
    tabAssets: "Dukaan & Assets",
    tabWill: "Wasiyat & Waris",
    tabVault: "Document Locker",
    tabSimulator: "'Kya Hoga Agar' Simulator",
    tabAdvisor: "CA & Legal Audit",
    tabTracker: "Nominee Gap Tracker",
    tabLegacyAdvisor: "AI Legal Advisor",
    netWorth: "Total Parivaar Net Worth",
    assetsValue: "Kul Sampatti",
    liabilitiesValue: "Bazaar Udhaari / Loans",
    disputeRisk: "Vivadh Risk",
    btnCreatePlan: "Naya Plan Banayein",
    btnEditDetails: "Details Badlein",
    btnSroGuide: "Registry Checklist",
    btnSimulate: "Batwara Test Karein",
    switchRole: "Active Role:",
    patriarchRole: "Karta / Dukaan Maalik",
    heirRole: "Waris / Family Member",
    advisorRole: "CA / Vakil (Advisor)",
    downloadPDF: "Formal Wasiyat PDF Download",
    uploadDoc: "Encrypted Locker me Upload Karein",
    runSimulation: "Legal Batwara Simulation",
    addMemberBtn: "+ Naya Sadasya Jodein",
    addAssetBtn: "+ Nayi Dukaan/Asset Jodein",
    sroGuideTitle: "Sub-Registrar Office Registry Guide",
    nomineeNotice: "Dhyan rahe: Indian law mein bank nominee sirf custodian/trustee hota hai, legal owner nahi!",
    // Onboarding Wizard
    wizTitle: "Aasaan 4 Steps — Apne Parivaar ki Sampatti aur Wasiyat Plan Secure Karein",
    wizHint: "Shuru karne ke liye kisi bhi step par click karein →",
    wizStep1Title: "Family Tree Banayein",
    wizStep1Desc: "Parents, spouse, bete, betiyan aur coparceners ko family tree me jodein.",
    wizStep2Title: "Dukaan & Sampatti Darj Karein",
    wizStep2Desc: "Dukaan, plot, sona, bank accounts, FDs aur existing nominees list karein.",
    wizStep3Title: "Wasiyat Draft Taiyyar Karein",
    wizStep3Desc: "Tay karein kis waris ko kaunsi sampatti milegi; executor aur gawah chunein.",
    wizStep4Title: "Encrypted Locker me Rakhein",
    wizStep4Desc: "Registry kagaz, share certificate aur partnership pact AES-256 locker me secure karein.",
    // Legal Essentials
    legalTitle: "Family Business aur Joint Family ke liye 4 Zaroori Legal Rules:",
    legal1Title: "🏦 Bank Nominee ≠ Legal Owner",
    legal1Desc: "Supreme Court (Sarbati Devi) ke mutabiq nominee sirf temporary trustee hota hai. Asli legal malikana hak Wasiyat se milta hai.",
    legal2Title: "⚖️ Betiyon ka Barabar Janmsiddh Hak",
    legal2Desc: "2005 HSA amendment & Vineeta Sharma ruling ke mutabiq betiyon ka ancestral property me beto ke barabar coparcenary hak hai.",
    legal3Title: "🏢 Partnership Firm Protection",
    legal3Desc: "Partnership Act Sec 42(c) ke mutabiq partner ki death par firm automatically dissolve ho jati hai agar succession clause na ho.",
    legal4Title: "🏛️ Sub-Registrar (Tehsil) Registry",
    legal4Desc: "2 gavahon ke sath un-registered will bhi valid hai, lekin Tehsil me register karwane se jhoothe dispute rukte hain.",
    // Simulator
    simScenarioATitle: "Scenario A: Bina Will (Intestate Batwara)",
    simScenarioBTitle: "Scenario B: Vasiyat Ke Saath (Will Distribution)",
    simThIntestate: "Intestate Share (Bina Will)",
    simThTestate: "Will Share (Vasiyat Se)",
    // AI Advisor
    advInquiriesTitle: "Suggested Quick Inquiries:",
    advPill1Text: "⚠️ Nominee vs Wasiyat Waris",
    advPill1Query: "Indian law mein bank nominee aur will beneficiary mein kya farak hai?",
    advPill2Text: "👩‍👧 Ancestral Property me Betiyon ka Hak",
    advPill2Query: "Ancestral joint family property mein betiyon ka kya coparcenary right hai?",
    advPill3Text: "🏢 Business aur Dukaan ki Suraksha",
    advPill3Query: "Partnership firm aur dukaan ko partner ki death par dissolve hone se kaise bachayein?",
    advPill4Text: "📊 Readiness Score Kaise Badhayein",
    advPill4Query: "Humare parivaar ka succession readiness score kaise improve karein?",
    advPill5Text: "🏛️ Tehsil Will Registry Rules",
    advPill5Query: "Sub-Registrar office mein will register karwane ke kya rules aur process hain?",
    advPlaceholder: "Legal sawal poochein: jaise 'Betiyon ka hak', 'Nominee rules', 'Business continuity'...",
    advSendBtn: "Advisor Se Poochein",
    // Role Banners
    heirBannerTitle: "HEIR VIEW (Waris Mode)",
    heirBannerDesc: "Read-only estate visibility. Assets, family tree aur will me changes strictly locked hain.",
    advisorBannerTitle: "CA / ADVOCATE AUDIT VIEW",
    advisorBannerDesc: "Auditor access active hai. Asset titles, nominee gaps aur advisory review kar rahe hain.",
    // Toast validations
    errAgeMember: "Kripya family member ki sahi age darj karein",
    errAgeKarta: "Kripya sahi age darj karein"
  }
};

// Currency Formatter
function formatINR(amount) {
  if (amount === undefined || amount === null) return "₹0";
  const num = Math.abs(Number(amount));
  if (num >= 10000000) {
    return `₹${(amount / 10000000).toFixed(2)} Cr`;
  } else if (num >= 100000) {
    return `₹${(amount / 100000).toFixed(2)} Lakh`;
  } else {
    return `₹${Number(amount).toLocaleString('en-IN')}`;
  }
}

// Universal Modal Manager (WCAG Dialog & Light Dismiss)
function closeAllOpenModals() {
  const openModals = document.querySelectorAll("[role='dialog']:not(.hidden), [id$='-modal']:not(.hidden)");
  openModals.forEach(m => m.classList.add("hidden"));
}

// Global Keyboard Handler for Accessibility (Escape closes modals)
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeAllOpenModals();
  }
});

// Mobile Off-Canvas Drawer Navigation Toggle
function toggleMobileSidebar(forceState) {
  const sidebar = document.getElementById("main-sidebar");
  const backdrop = document.getElementById("mobile-sidebar-backdrop");
  const menuBtn = document.getElementById("mobile-menu-btn");
  if (!sidebar) return;

  const isHidden = sidebar.classList.contains("-translate-x-full");
  const shouldOpen = forceState !== undefined ? forceState : isHidden;

  if (shouldOpen) {
    sidebar.classList.remove("-translate-x-full");
    if (backdrop) backdrop.classList.remove("hidden");
    if (menuBtn) menuBtn.setAttribute("aria-expanded", "true");
  } else {
    sidebar.classList.add("-translate-x-full");
    if (backdrop) backdrop.classList.add("hidden");
    if (menuBtn) menuBtn.setAttribute("aria-expanded", "false");
  }
}

// HTML Escaper for XSS Prevention
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Accessible Toast Notification with Status/Alert roles & Dismiss action
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  const bg = type === "success" ? "bg-teal-700 text-white" : type === "error" ? "bg-rose-700 text-white" : "bg-amber-600 text-white";
  toast.setAttribute("role", type === "error" ? "alert" : "status");
  toast.className = `${bg} px-4 py-3 rounded-xl shadow-xl text-xs font-semibold flex items-center justify-between gap-3 transform transition-all duration-300 translate-y-2 opacity-0 z-50 pointer-events-auto min-w-[280px] max-w-sm border border-white/20`;
  toast.innerHTML = `
    <span class="flex-1">${escapeHtml(message)}</span>
    <button type="button" class="text-white/80 hover:text-white p-1 rounded-md text-sm font-bold cursor-pointer" aria-label="Dismiss notification">&times;</button>
  `;
  const closeBtn = toast.querySelector("button");
  if (closeBtn) {
    closeBtn.onclick = () => {
      toast.classList.add("opacity-0");
      setTimeout(() => toast.remove(), 250);
    };
  }
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.remove("translate-y-2", "opacity-0");
  }, 10);
  setTimeout(() => {
    if (toast.parentElement) {
      toast.classList.add("opacity-0");
      setTimeout(() => toast.remove(), 300);
    }
  }, 4500);
}

// Authenticated API Fetch Wrapper
async function apiFetch(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.authToken) {
    headers["Authorization"] = `Bearer ${state.authToken}`;
  }
  const res = await fetch(url, { ...options, headers });
  if (res.status === 401) {
    const data = await res.json().catch(() => ({}));
    const msg = data.detail || "Authentication required. Please log in.";
    showToast(msg, "error");
    throw new Error(msg);
  }
  if (res.status === 403) {
    const data = await res.json().catch(() => ({}));
    const msg = data.detail || "Action forbidden for your role";
    showToast(`Permission Denied: ${msg}`, "error");
    throw new Error(msg);
  }
  return res;
}

// -------------------------------------------------------------
// INITIALIZATION & SCENARIOS
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
  const savedLang = localStorage.getItem("waaris_lang");
  if (savedLang && ["en", "hi", "hinglish"].includes(savedLang)) {
    state.currentLang = savedLang;
  }
  initWalkingBanner();
  await loadScenarios();
  setupEventHandlers();
  updateLanguageUI();
  await initAuth();
});

// Load All Scenarios for Dropdown
async function loadScenarios() {
  try {
    const res = await fetch("/api/scenarios");
    state.scenarios = await res.json();
    const select = document.getElementById("scenario-select");
    if (select) {
      select.innerHTML = "";
      state.scenarios.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.innerText = `${s.karta_name} (${s.business_name} - ${s.city})`;
        select.appendChild(opt);
      });
    }
  } catch (err) {
    console.error("Failed to load scenarios:", err);
  }
}

// Switch Active Scenario (Strictly Gated by RBAC & Family Isolation)
async function switchScenario(profileId) {
  // 1. Unauthenticated Gate
  if (!state.currentUser) {
    showToast("Authentication required: Please sign in to view family estate records.", "error");
    openAuthLanding();
    return;
  }

  // 2. Cross-Family Security Gate
  // Only an authorized independent CA / Legal Advisor can audit multiple families.
  // Patriarch and Heir accounts are strictly isolated to their own family profile.
  if (state.currentUser.role !== "advisor" && state.currentUser.profile_id !== profileId) {
    showToast(`Access Restricted: Your account (${state.currentUser.username}) belongs to Estate #${state.currentUser.profile_id}. Please log in with an authorized account for Estate #${profileId} to view their records.`, "error");
    const select = document.getElementById("scenario-select");
    if (select) select.value = state.currentUser.profile_id;
    return;
  }

  state.currentProfileId = profileId;
  const select = document.getElementById("scenario-select");
  if (select) select.value = profileId;

  state.activeRole = state.currentUser.role;
  updateRoleSelectorUI();

  try {
    // 1. Fetch Profile
    const pRes = await apiFetch(`/api/profile/${profileId}`);
    state.currentProfile = await pRes.json();

    // 2. Refresh all core estate data
    await Promise.all([
      refreshFamily(),
      refreshAssets(),
      refreshAllocations(),
      refreshWillDraft(),
      refreshVault(),
      refreshAdvisorNotes(),
      refreshReminders(),
      refreshSimulation(),
      refreshReadiness(),
      refreshNominationTracker()
    ]);

    populateSimulatorSelects();
    renderActiveTab();
    showToast(`Loaded: ${state.currentProfile.karta_name} (${state.currentProfile.business_name})`, "success");
  } catch (err) {
    console.error("Error switching scenario:", err);
    showToast("Failed to switch scenario", "error");
  }
}

// -------------------------------------------------------------
// AUTHENTICATION & RBAC SUBSYSTEM
// -------------------------------------------------------------
async function initAuth() {
  const token = localStorage.getItem("virasat_token") || state.authToken;
  if (token) {
    state.authToken = token;
    try {
      const res = await apiFetch("/api/auth/me");
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated && data.user) {
          state.currentUser = data.user;
          state.activeRole = data.user.role;
          state.currentProfileId = data.user.profile_id;
          hideAuthLanding();
          updateRoleSelectorUI();
          await switchScenario(data.user.profile_id);
          return;
        }
      }
    } catch (e) {
      console.warn("Stored auth token invalid or expired:", e);
    }
  }

  // Fallback: Not authenticated. Keep private data locked, show Login & Registration Portal.
  // NEVER auto-login silently without user consent.
  state.authToken = null;
  state.currentUser = null;
  state.activeRole = "guest";
  localStorage.removeItem("virasat_token");
  openAuthLanding();
  updateRoleSelectorUI();
}

function openAuthLanding() {
  const landing = document.getElementById("auth-landing-view");
  if (landing) {
    landing.classList.remove("hidden");
  }
}

function hideAuthLanding() {
  const landing = document.getElementById("auth-landing-view");
  if (landing) {
    landing.classList.add("hidden");
  }
}

function showPortalAuthTab(tab) {
  const loginBtn = document.getElementById("portal-tab-login-btn");
  const regBtn = document.getElementById("portal-tab-reg-btn");
  const loginForm = document.getElementById("portal-login-form");
  const regForm = document.getElementById("portal-register-form");

  if (tab === "login") {
    if (loginBtn) loginBtn.className = "flex-1 py-2.5 text-center border-b-2 border-teal-700 text-teal-800 cursor-pointer font-bold";
    if (regBtn) regBtn.className = "flex-1 py-2.5 text-center border-b-2 border-transparent text-stone-500 hover:text-stone-800 cursor-pointer font-medium";
    if (loginForm) loginForm.classList.remove("hidden");
    if (regForm) regForm.classList.add("hidden");
  } else {
    if (regBtn) regBtn.className = "flex-1 py-2.5 text-center border-b-2 border-teal-700 text-teal-800 cursor-pointer font-bold";
    if (loginBtn) loginBtn.className = "flex-1 py-2.5 text-center border-b-2 border-transparent text-stone-500 hover:text-stone-800 cursor-pointer font-medium";
    if (regForm) regForm.classList.remove("hidden");
    if (loginForm) loginForm.classList.add("hidden");
  }
}

async function handlePortalLoginSubmit(event) {
  event.preventDefault();
  const u = document.getElementById("portal-login-username").value.trim();
  const p = document.getElementById("portal-login-password").value;
  const errEl = document.getElementById("portal-login-error");
  if (errEl) errEl.classList.add("hidden");

  try {
    await loginWithCredentials(u, p, true);
  } catch (e) {
    if (errEl) {
      errEl.innerText = e.message || "Invalid credentials";
      errEl.classList.remove("hidden");
    }
  }
}

async function handlePortalRegisterSubmit(event) {
  event.preventDefault();
  const fullName = document.getElementById("portal-reg-fullname").value.trim();
  const u = document.getElementById("portal-reg-username").value.trim();
  const r = document.getElementById("portal-reg-role").value;
  const profId = parseInt(document.getElementById("portal-reg-profile-id").value) || 1;
  const p = document.getElementById("portal-reg-password").value;
  const errEl = document.getElementById("portal-reg-error");
  if (errEl) errEl.classList.add("hidden");

  try {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: u,
        full_name: fullName,
        password: p,
        role: r,
        profile_id: profId
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed");
    }
    showToast(`Account registered for ${u}! Signing in...`, "success");
    await loginWithCredentials(u, p, true);
  } catch (err) {
    showToast(err.message, "error");
    if (errEl) {
      errEl.innerText = err.message;
      errEl.classList.remove("hidden");
    }
  }
}

async function quickPortalLogin(username, profileId) {
  try {
    state.currentProfileId = profileId;
    await loginWithCredentials(username, "Virasat@2026", true);
  } catch (e) {
    console.error("Quick portal login failed:", e);
  }
}

async function loginWithCredentials(username, password, showFeedback = true) {
  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Authentication failed: Invalid username or password");
    }
    const data = await res.json();
    state.authToken = data.token;
    state.currentUser = data.user;
    state.activeRole = data.user.role;
    state.currentProfileId = data.user.profile_id;
    localStorage.setItem("virasat_token", data.token);

    hideAuthLanding();
    closeAuthModal();
    updateRoleSelectorUI();

    await switchScenario(data.user.profile_id);

    if (showFeedback) {
      showToast(`Welcome ${data.user.full_name || data.user.username}! Signed in as ${data.user.role.toUpperCase()}`, "success");
    }
    return data;
  } catch (err) {
    if (showFeedback) {
      showToast(err.message, "error");
      const portalErr = document.getElementById("portal-login-error");
      if (portalErr) {
        portalErr.innerText = err.message;
        portalErr.classList.remove("hidden");
      }
      const modalErr = document.getElementById("auth-login-error");
      if (modalErr) {
        modalErr.innerText = err.message;
        modalErr.classList.remove("hidden");
      }
    }
    throw err;
  }
}

async function quickLoginRole(newRole) {
  const profileId = state.currentProfileId || 1;
  const userMap = scenarioRoleUserMap[profileId] || scenarioRoleUserMap[1];
  const targetUsername = userMap[newRole] || userMap.patriarch;
  await loginWithCredentials(targetUsername, "Virasat@2026", true);
}

async function switchRole(newRole) {
  await quickLoginRole(newRole);
}

async function logoutUser() {
  try {
    await fetch("/api/auth/logout", { method: "POST" });
  } catch (e) {}
  localStorage.removeItem("virasat_token");
  state.authToken = null;
  state.currentUser = null;
  state.activeRole = "guest";
  state.currentProfile = null;
  state.members = [];
  state.assets = [];
  state.allocations = [];
  state.vaultDocs = [];
  state.willDraft = null;
  state.advisorNotes = [];

  closeAuthModal();
  openAuthLanding();
  updateRoleSelectorUI();
  showToast("You have been signed out. Please authenticate to access family records.", "info");
}

function updateRoleSelectorUI() {
  const buttons = document.querySelectorAll(".role-btn");
  buttons.forEach(btn => {
    const r = btn.dataset.role;
    if (r === state.activeRole) {
      btn.className = "role-btn px-2.5 py-1 rounded-lg text-xs font-bold bg-teal-700 text-white shadow-sm transition";
    } else {
      btn.className = "role-btn px-2.5 py-1 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-200 transition";
    }
  });

  // Top header user session badge
  const headerUserDisplay = document.getElementById("header-username-display");
  const headerRoleBadge = document.getElementById("header-role-badge");
  if (headerUserDisplay && headerRoleBadge) {
    if (state.currentUser) {
      headerUserDisplay.innerText = state.currentUser.username;
      headerRoleBadge.innerText = state.currentUser.role.toUpperCase();
      headerRoleBadge.className = state.currentUser.role === "patriarch"
        ? "px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase bg-teal-700 text-white"
        : state.currentUser.role === "heir"
        ? "px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase bg-blue-700 text-white"
        : "px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase bg-amber-700 text-white";
    } else {
      headerUserDisplay.innerText = "Guest / Unauthenticated";
      headerRoleBadge.innerText = "GUEST";
      headerRoleBadge.className = "px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase bg-slate-500 text-white";
    }
  }

  // Header logout button visibility
  const logoutBtn = document.getElementById("header-logout-btn");
  if (logoutBtn) {
    if (state.currentUser) {
      logoutBtn.classList.remove("hidden");
    } else {
      logoutBtn.classList.add("hidden");
    }
  }

  // Update avatar initial in session pill
  const avatarEl = document.querySelector("#auth-session-pill div");
  if (avatarEl) {
    avatarEl.innerText = state.currentUser ? (state.currentUser.username[0] || "U").toUpperCase() : "G";
  }

  // Modal session displays
  const modalUser = document.getElementById("modal-current-user");
  const modalRole = document.getElementById("modal-current-role");
  if (modalUser && modalRole) {
    modalUser.innerText = state.currentUser ? state.currentUser.username : "None";
    modalRole.innerText = state.currentUser ? state.currentUser.role : "Guest";
  }

  // Global banner for Heir / Advisor notice
  const banner = document.getElementById("role-banner");
  if (banner) {
    const l = i18n[state.currentLang] || i18n.en;
    if (state.activeRole === "heir") {
      banner.classList.remove("hidden");
      const title = l.heirBannerTitle || "HEIR VIEW";
      const desc = l.heirBannerDesc || "Read-only estate visibility. Modifications to assets, family tree, and will clauses are strictly locked.";
      const username = state.currentUser ? state.currentUser.username : 'Heir';
      banner.innerHTML = `<div class="max-w-7xl mx-auto px-4 py-2 flex items-center justify-between"><span class="font-bold">${title} (Logged in as ${username}):</span> <span>${desc}</span></div>`;
      banner.className = "bg-blue-50 border-b border-blue-200 text-blue-900 text-xs";
    } else if (state.activeRole === "advisor") {
      banner.classList.remove("hidden");
      const title = l.advisorBannerTitle || "CA / ADVOCATE AUDIT VIEW";
      const desc = l.advisorBannerDesc || "You have auditor access. Reviewing asset titles, nominee discrepancies, and posting advisory notes.";
      const username = state.currentUser ? state.currentUser.username : 'Advisor';
      banner.innerHTML = `<div class="max-w-7xl mx-auto px-4 py-2 flex items-center justify-between"><span class="font-bold">${title} (Logged in as ${username}):</span> <span>${desc}</span></div>`;
      banner.className = "bg-amber-50 border-b border-amber-200 text-amber-900 text-xs";
    } else {
      banner.classList.add("hidden");
    }
  }
}

// Auth Modal Management
function openAuthModal() {
  const modal = document.getElementById("auth-modal");
  if (!modal) return;
  const regProfInput = document.getElementById("auth-reg-profile-id");
  if (regProfInput) regProfInput.value = state.currentProfileId;
  modal.classList.remove("hidden");
}

function closeAuthModal() {
  document.getElementById("auth-modal")?.classList.add("hidden");
  const loginErr = document.getElementById("auth-login-error");
  const regErr = document.getElementById("auth-reg-error");
  if (loginErr) loginErr.classList.add("hidden");
  if (regErr) regErr.classList.add("hidden");
}

function showAuthTab(tab) {
  const loginBtn = document.getElementById("auth-tab-login-btn");
  const regBtn = document.getElementById("auth-tab-reg-btn");
  const loginForm = document.getElementById("auth-login-form");
  const regForm = document.getElementById("auth-register-form");

  if (tab === "login") {
    loginBtn.className = "py-2 px-4 border-b-2 border-teal-600 font-bold text-teal-700 cursor-pointer";
    regBtn.className = "py-2 px-4 border-b-2 border-transparent text-slate-500 font-semibold hover:text-slate-700 cursor-pointer";
    loginForm.classList.remove("hidden");
    regForm.classList.add("hidden");
  } else {
    regBtn.className = "py-2 px-4 border-b-2 border-teal-600 font-bold text-teal-700 cursor-pointer";
    loginBtn.className = "py-2 px-4 border-b-2 border-transparent text-slate-500 font-semibold hover:text-slate-700 cursor-pointer";
    regForm.classList.remove("hidden");
    loginForm.classList.add("hidden");
  }
}

async function handleLoginFormSubmit(event) {
  event.preventDefault();
  const u = document.getElementById("auth-login-username").value.trim();
  const p = document.getElementById("auth-login-password").value;
  await loginWithCredentials(u, p, true);
}

async function handleRegisterFormSubmit(event) {
  event.preventDefault();
  const fullName = (document.getElementById("auth-reg-fullname")?.value || "").trim();
  const u = document.getElementById("auth-reg-username").value.trim();
  const r = document.getElementById("auth-reg-role").value;
  const profId = parseInt(document.getElementById("auth-reg-profile-id").value) || 1;
  const p = document.getElementById("auth-reg-password").value;

  try {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: u,
        full_name: fullName || u,
        password: p,
        role: r,
        profile_id: profId
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed");
    }
    showToast(`Account ${u} created! Authenticating...`, "success");
    await loginWithCredentials(u, p, true);
  } catch (err) {
    showToast(err.message, "error");
    const errEl = document.getElementById("auth-reg-error");
    if (errEl) {
      errEl.innerText = err.message;
      errEl.classList.remove("hidden");
    }
  }
}

// Language Switcher & Manager (English / Hindi / Hinglish)
function setLanguage(lang) {
  if (!['en', 'hi', 'hinglish'].includes(lang)) lang = 'en';
  state.currentLang = lang;
  try { localStorage.setItem('waaris_lang', lang); } catch (e) {}
  updateLanguageUI();
}

function toggleLanguage() {
  const order = ['en', 'hi', 'hinglish'];
  const nextIdx = (order.indexOf(state.currentLang) + 1) % order.length;
  setLanguage(order[nextIdx]);
}

function updateLanguageUI() {
  const l = i18n[state.currentLang] || i18n.en;
  const setTxt = (id, txt) => {
    const el = document.getElementById(id);
    if (el && txt !== undefined) el.innerText = txt;
  };

  // 1. Navigation Tabs
  setTxt("nav-dashboard-text", l.tabDashboard);
  setTxt("nav-family-text", l.tabFamily);
  setTxt("nav-assets-text", l.tabAssets);
  setTxt("nav-will-text", l.tabWill);
  setTxt("nav-vault-text", l.tabVault);
  setTxt("nav-simulator-text", l.tabSimulator);
  setTxt("nav-advisor-text", l.tabAdvisor);
  setTxt("nav-tracker-text", l.tabTracker);
  setTxt("nav-legacy-advisor-text", l.tabLegacyAdvisor);

  // 2. Hero Action Buttons
  setTxt("btn-create-plan-text", l.btnCreatePlan);
  setTxt("btn-edit-details-text", l.btnEditDetails);
  setTxt("btn-sro-guide-text", l.btnSroGuide);
  setTxt("btn-simulate-text", l.btnSimulate);

  // 3. Key Metric Card Labels
  setTxt("lbl-net-worth", l.netWorth);
  setTxt("lbl-gross-assets", l.assetsValue);
  setTxt("lbl-liabilities", l.liabilitiesValue);
  setTxt("lbl-dispute-risk", l.disputeRisk);

  // 4. Update segmented toggle active pills in header
  const btnEn = document.getElementById("lang-btn-en");
  const btnHi = document.getElementById("lang-btn-hi");
  const btnHinglish = document.getElementById("lang-btn-hinglish");
  [btnEn, btnHi, btnHinglish].forEach(b => {
    if (b) {
      b.className = "px-2.5 py-1 rounded-lg transition font-semibold text-stone-600 hover:text-stone-900 cursor-pointer";
    }
  });
  const activeBtn = state.currentLang === 'hi' ? btnHi : state.currentLang === 'hinglish' ? btnHinglish : btnEn;
  if (activeBtn) {
    activeBtn.className = "px-2.5 py-1 rounded-lg transition font-bold bg-white text-stone-900 shadow-2xs cursor-pointer";
  }

  // 5. Update legacy button if present
  const legacyBtn = document.getElementById("lang-toggle-btn");
  if (legacyBtn) {
    legacyBtn.innerText = state.currentLang === 'en' ? 'हिन्दी' : state.currentLang === 'hi' ? 'Hinglish' : 'English';
  }

  // 6. 4-Step Onboarding Wizard
  setTxt("wizard-title-text", l.wizTitle);
  setTxt("wizard-hint-text", l.wizHint);
  setTxt("wiz-step-1-title", l.wizStep1Title);
  setTxt("wiz-step-1-desc", l.wizStep1Desc);
  setTxt("wiz-step-2-title", l.wizStep2Title);
  setTxt("wiz-step-2-desc", l.wizStep2Desc);
  setTxt("wiz-step-3-title", l.wizStep3Title);
  setTxt("wiz-step-3-desc", l.wizStep3Desc);
  setTxt("wiz-step-4-title", l.wizStep4Title);
  setTxt("wiz-step-4-desc", l.wizStep4Desc);

  // 7. 4 Legal Essentials Cards
  setTxt("legal-rules-title-text", l.legalTitle);
  setTxt("legal-card-1-title", l.legal1Title);
  setTxt("legal-card-1-desc", l.legal1Desc);
  setTxt("legal-card-2-title", l.legal2Title);
  setTxt("legal-card-2-desc", l.legal2Desc);
  setTxt("legal-card-3-title", l.legal3Title);
  setTxt("legal-card-3-desc", l.legal3Desc);
  setTxt("legal-card-4-title", l.legal4Title);
  setTxt("legal-card-4-desc", l.legal4Desc);

  // 8. Simulator Scenario Titles and Table Headers
  setTxt("sim-scenario-a-title", l.simScenarioATitle);
  setTxt("sim-scenario-b-title", l.simScenarioBTitle);
  setTxt("sim-th-intestate", l.simThIntestate);
  setTxt("sim-th-testate", l.simThTestate);

  // 9. AI Family Legacy Advisor Quick Inquiries & Input
  setTxt("advisor-inquiries-title", l.advInquiriesTitle);
  const setupPill = (id, text, query) => {
    const el = document.getElementById(id);
    if (el) {
      if (text) el.innerText = text;
      if (query) {
        el.onclick = () => askAdvisorQuery(query);
      }
    }
  };
  setupPill("adv-pill-1", l.advPill1Text, l.advPill1Query);
  setupPill("adv-pill-2", l.advPill2Text, l.advPill2Query);
  setupPill("adv-pill-3", l.advPill3Text, l.advPill3Query);
  setupPill("adv-pill-4", l.advPill4Text, l.advPill4Query);
  setupPill("adv-pill-5", l.advPill5Text, l.advPill5Query);

  const advInput = document.getElementById("advisor-user-input");
  if (advInput && l.advPlaceholder) advInput.placeholder = l.advPlaceholder;
  setTxt("advisor-send-btn-text", l.advSendBtn);

  // 10. Update active role banner
  updateRoleSelectorUI();

  // 11. Refresh initial welcome chat message if user hasn't started a custom chat yet
  if (state.advisorChatMessages && state.advisorChatMessages.length === 1 && state.advisorChatMessages[0].role === "assistant") {
    state.advisorChatMessages = [];
    if (state.activeTab === "legacy-advisor") {
      renderLegacyAdvisorPane();
    }
  }
}

// -------------------------------------------------------------
// REFRESH DATA HELPERS
// -------------------------------------------------------------
async function refreshFamily() {
  const res = await apiFetch(`/api/family/${state.currentProfileId}`);
  const data = await res.json();
  state.members = data.members;
}

async function refreshAssets() {
  const res = await apiFetch(`/api/assets/${state.currentProfileId}`);
  const data = await res.json();
  state.assets = data.assets;
  state.assetsSummary = data.summary;
}

async function refreshAllocations() {
  const res = await apiFetch(`/api/allocations/${state.currentProfileId}`);
  state.allocations = await res.json();
}

async function refreshWillDraft() {
  const res = await apiFetch(`/api/will/${state.currentProfileId}`);
  state.willDraft = await res.json();
}

async function refreshVault() {
  const res = await apiFetch(`/api/vault/${state.currentProfileId}`);
  state.vaultDocs = await res.json();
}

async function refreshAdvisorNotes() {
  const res = await apiFetch(`/api/advisor-notes/${state.currentProfileId}`);
  state.advisorNotes = await res.json();
}

async function refreshReminders() {
  try {
    const res = await apiFetch(`/api/reminders/${state.currentProfileId}`);
    state.reminders = await res.json();
  } catch (e) {
    console.error("Failed to load reminders:", e);
  }
}

async function refreshSimulation() {
  const res = await apiFetch(`/api/simulation/${state.currentProfileId}`);
  state.simulationData = await res.json();
}

async function refreshReadiness() {
  try {
    const res = await apiFetch(`/api/readiness/${state.currentProfileId}`);
    state.readinessData = await res.json();
  } catch (e) {
    console.error("Failed to load readiness score:", e);
  }
}

async function refreshNominationTracker() {
  try {
    const res = await apiFetch(`/api/nomination-tracker/${state.currentProfileId}`);
    state.nominationTrackerData = await res.json();
    if (state.activeTab === 'tracker') {
      renderTrackerPane();
    }
  } catch (e) {
    console.error("Failed to load nomination tracker:", e);
  }
}

// Tab Switching
function selectTab(tabName) {
  state.activeTab = tabName;
  toggleMobileSidebar(false); // Seamlessly dismiss mobile drawer on navigation

  document.querySelectorAll(".nav-tab").forEach(t => {
    t.classList.remove("active", "border-teal-600", "text-teal-700");
    t.classList.add("text-slate-500");
  });
  const currentTabEl = document.getElementById(`nav-${tabName}`);
  if (currentTabEl) {
    currentTabEl.classList.add("active", "border-teal-600", "text-teal-700");
    currentTabEl.classList.remove("text-slate-500");
  }

  // Update Left Emerald Sidebar Active Navigation
  document.querySelectorAll(".side-nav-item").forEach(item => {
    item.classList.remove("active");
  });
  const sideNavEl = document.getElementById(`side-nav-${tabName}`);
  if (sideNavEl) {
    sideNavEl.classList.add("active");
  }

  document.querySelectorAll(".tab-pane").forEach(p => p.classList.add("hidden"));
  const pane = document.getElementById(`pane-${tabName}`);
  if (pane) pane.classList.remove("hidden");

  renderActiveTab();
}

function renderActiveTab() {
  switch (state.activeTab) {
    case 'dashboard':
      renderDashboard();
      break;
    case 'family':
      renderFamilyPane();
      break;
    case 'assets':
      renderAssetsPane();
      break;
    case 'will':
      renderWillPane();
      break;
    case 'vault':
      renderVaultPane();
      break;
    case 'simulator':
      renderSimulatorPane();
      break;
    case 'advisor':
      renderAdvisorPane();
      break;
    case 'tracker':
      renderTrackerPane();
      break;
    case 'legacy-advisor':
      renderLegacyAdvisorPane();
      break;
  }
}

// -------------------------------------------------------------
// PANE 1: DASHBOARD & REMINDERS (M3 Subsystem)
// -------------------------------------------------------------
function renderDashboard() {
  if (!state.currentProfile || !state.simulationData) return;

  // Header info
  document.getElementById("dash-karta-name").innerText = state.currentProfile.karta_name;
  document.getElementById("dash-biz-name").innerText = `${state.currentProfile.business_name} (${state.currentProfile.business_type}) • ${state.currentProfile.city}, ${state.currentProfile.state}`;
  document.getElementById("dash-gov-law").innerText = state.currentProfile.governing_law;

  // Render Reminders Banner (M3)
  renderDashboardReminders();

  // Stat Cards
  document.getElementById("dash-net-worth").innerText = formatINR(state.simulationData.net_worth_inr);
  document.getElementById("dash-gross-assets").innerText = formatINR(state.simulationData.total_asset_value_inr);
  document.getElementById("dash-liabilities").innerText = formatINR(state.simulationData.total_liabilities_inr);

  // Dispute Risk Meter
  const score = state.simulationData.dispute_risk_score;
  const level = state.simulationData.risk_level;

  const scoreEl = document.getElementById("dash-risk-score");
  scoreEl.innerText = `${score}/100`;
  const levelEl = document.getElementById("dash-risk-level");
  levelEl.innerText = level;

  const barEl = document.getElementById("dash-risk-bar");
  barEl.style.width = `${score}%`;
  barEl.className = `h-2.5 rounded-full transition-all duration-500 ${score > 70 ? 'bg-red-500' : score > 45 ? 'bg-amber-500' : 'bg-emerald-500'}`;

  // Mini Family Tree in Dashboard
  renderFamilyTree(state.members, "dash-family-tree-container", (member) => {
    showMemberDetailsModal(member);
  });

  // Recent Advisor Warnings
  const notesContainer = document.getElementById("dash-notes-container");
  if (notesContainer) {
    if (state.advisorNotes.length === 0) {
      notesContainer.innerHTML = `<div class="text-sm text-slate-400 py-4">No audit flags recorded. Everything looks orderly.</div>`;
    } else {
      notesContainer.innerHTML = state.advisorNotes.slice(0, 3).map(n => `
        <div class="p-3 rounded-lg border ${n.severity === 'critical' ? 'border-red-200 bg-red-50/50' : 'border-amber-200 bg-amber-50/50'} text-xs">
          <div class="flex items-center justify-between font-bold ${n.severity === 'critical' ? 'text-red-800' : 'text-amber-800'} mb-1">
            <span>${escapeHtml(n.author_name)} (${escapeHtml(n.author_role)})</span>
            <span class="uppercase text-[10px] px-1.5 py-0.5 rounded bg-white font-semibold">${n.severity}</span>
          </div>
          <p class="text-slate-700 leading-relaxed">${escapeHtml(n.note_text)}</p>
        </div>
      `).join("");
    }
  }

  // SRO Status Card
  const sroStatusEl = document.getElementById("dash-sro-status");
  if (sroStatusEl && state.willDraft) {
    const isReg = state.willDraft.status === "registered";
    const remDate = state.willDraft.sro_reminder_date || "Not set";
    sroStatusEl.innerHTML = `
      <div class="flex items-center justify-between">
        <div>
          <div class="font-bold text-slate-800 text-sm">${escapeHtml(state.willDraft.sub_registrar_office || "Sub-Registrar Office")}</div>
          <div class="text-xs text-slate-500 mt-0.5">
            Registration: <span class="font-semibold ${isReg ? 'text-emerald-700' : 'text-amber-700'}">${state.willDraft.status.toUpperCase()}</span>
            • SRO Target: <strong class="font-mono text-slate-700">${remDate}</strong>
          </div>
        </div>
        <button onclick="selectTab('vault')" class="px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold hover:bg-slate-50">
          View Guide & Vault
        </button>
      </div>
    `;
  }

  // Dynamic Succession Readiness Score & 4 Pillars
  if (state.readinessData) {
    const rd = state.readinessData;
    const badgeEl = document.getElementById("dash-readiness-badge");
    const percentEl = document.getElementById("dash-readiness-percent");
    const barEl = document.getElementById("dash-readiness-bar");
    const subtitleEl = document.getElementById("dash-readiness-subtitle");
    const checklistEl = document.getElementById("dash-readiness-checklist");

    if (badgeEl) {
      badgeEl.innerText = `${rd.grade.split(' ')[0]} • ${rd.overall_score}%`;
      badgeEl.className = rd.overall_score >= 80
        ? "px-2 py-0.5 rounded text-[10px] font-extrabold bg-emerald-100 text-emerald-900 border border-emerald-200"
        : rd.overall_score >= 60
        ? "px-2 py-0.5 rounded text-[10px] font-extrabold bg-teal-100 text-teal-900 border border-teal-200"
        : rd.overall_score >= 45
        ? "px-2 py-0.5 rounded text-[10px] font-extrabold bg-amber-100 text-amber-900 border border-amber-200"
        : "px-2 py-0.5 rounded text-[10px] font-extrabold bg-rose-100 text-rose-900 border border-rose-200";
    }

    if (percentEl) percentEl.innerText = `${rd.overall_score}%`;
    if (barEl) {
      barEl.style.width = `${rd.overall_score}%`;
      barEl.className = `h-2.5 rounded-full transition-all duration-700 ${
        rd.overall_score >= 75 ? 'bg-gradient-to-r from-teal-600 to-emerald-500' :
        rd.overall_score >= 50 ? 'bg-gradient-to-r from-amber-500 to-teal-600' :
        'bg-gradient-to-r from-rose-500 to-amber-500'
      }`;
    }

    if (subtitleEl) {
      subtitleEl.innerHTML = `
        <span class="w-2 h-2 rounded-full ${rd.overall_score >= 70 ? 'bg-emerald-500' : 'bg-amber-500'} animate-pulse"></span>
        <span>${escapeHtml(rd.status_label)}</span>
      `;
    }

    if (checklistEl) {
      const p = rd.pillars;
      const pillarRows = `
        <div class="grid grid-cols-2 gap-2 pb-2">
          <div class="p-2 rounded-lg bg-stone-50 border border-stone-200/80">
            <div class="flex justify-between items-center text-[10px] font-bold text-stone-600 mb-1">
              <span>📁 Title Deeds</span>
              <span class="font-mono text-teal-800">${p.documentation.score}/25</span>
            </div>
            <div class="w-full bg-stone-200 rounded-full h-1.5 overflow-hidden">
              <div class="bg-teal-600 h-1.5 rounded-full" style="width: ${p.documentation.percentage}%"></div>
            </div>
          </div>

          <div class="p-2 rounded-lg bg-stone-50 border border-stone-200/80">
            <div class="flex justify-between items-center text-[10px] font-bold text-stone-600 mb-1">
              <span>🏦 Nominees</span>
              <span class="font-mono text-teal-800">${p.nomination.score}/25</span>
            </div>
            <div class="w-full bg-stone-200 rounded-full h-1.5 overflow-hidden">
              <div class="bg-teal-600 h-1.5 rounded-full" style="width: ${p.nomination.percentage}%"></div>
            </div>
          </div>

          <div class="p-2 rounded-lg bg-stone-50 border border-stone-200/80">
            <div class="flex justify-between items-center text-[10px] font-bold text-stone-600 mb-1">
              <span>📜 Will Clarity</span>
              <span class="font-mono text-teal-800">${p.testamentary.score}/25</span>
            </div>
            <div class="w-full bg-stone-200 rounded-full h-1.5 overflow-hidden">
              <div class="bg-teal-600 h-1.5 rounded-full" style="width: ${p.testamentary.percentage}%"></div>
            </div>
          </div>

          <div class="p-2 rounded-lg bg-stone-50 border border-stone-200/80">
            <div class="flex justify-between items-center text-[10px] font-bold text-stone-600 mb-1">
              <span>⚖️ Legal Equity</span>
              <span class="font-mono text-teal-800">${p.statutory_equity.score}/25</span>
            </div>
            <div class="w-full bg-stone-200 rounded-full h-1.5 overflow-hidden">
              <div class="bg-teal-600 h-1.5 rounded-full" style="width: ${p.statutory_equity.percentage}%"></div>
            </div>
          </div>
        </div>
      `;

      let actionRows = "";
      if (rd.priority_actions && rd.priority_actions.length > 0) {
        actionRows = rd.priority_actions.slice(0, 3).map(a => `
          <div class="flex items-center justify-between p-2 rounded-lg border ${
            a.urgency === 'CRITICAL' ? 'border-rose-200 bg-rose-50/40 text-rose-900' : 'border-amber-200 bg-amber-50/30 text-amber-900'
          }">
            <div class="flex items-center gap-2 truncate">
              <span class="text-[10px] font-bold shrink-0">${a.urgency === 'CRITICAL' ? '⚠️' : '⚡'}</span>
              <span class="truncate font-medium text-[11px]">${escapeHtml(a.action)}</span>
            </div>
            <span class="text-[9px] font-extrabold px-1.5 py-0.5 rounded bg-white shrink-0 shadow-2xs font-mono">${escapeHtml(a.impact)}</span>
          </div>
        `).join("");
      } else {
        actionRows = `
          <div class="p-2 rounded-lg bg-emerald-50 text-emerald-800 text-[11px] font-semibold border border-emerald-200 flex items-center gap-2">
            <span>✓</span><span>All standard readiness criteria verified!</span>
          </div>
        `;
      }

      checklistEl.innerHTML = pillarRows + actionRows;
    }
  }

  // Render Asset Distribution Doughnut Chart
  renderAssetDistributionDonut();
}

function renderDashboardReminders() {
  const container = document.getElementById("reminders-list-container");
  if (!container || !state.reminders) return;

  const r = state.reminders;
  const cards = [];

  // 1. SRO Will Registration Card
  if (r.sro_will_registration) {
    const sro = r.sro_will_registration;
    const isOverdue = sro.days_remaining < 0;
    const badgeClass = isOverdue ? "bg-rose-100 text-rose-800" : sro.days_remaining <= 30 ? "bg-amber-100 text-amber-900" : "bg-teal-100 text-teal-800";
    cards.push(`
      <div class="p-3.5 rounded-xl border border-amber-200 bg-amber-50/40 text-xs space-y-1.5">
        <div class="flex items-center justify-between">
          <span class="font-bold text-amber-900 flex items-center gap-1.5">
            <span>🏛️</span><span>SRO Will Registration Target</span>
          </span>
          <span class="px-2 py-0.5 rounded text-[10px] font-extrabold ${badgeClass}">
            ${isOverdue ? `${Math.abs(sro.days_remaining)}d OVERDUE` : `Due in ${sro.days_remaining}d`}
          </span>
        </div>
        <div class="text-slate-600">
          Target Date: <strong class="font-mono text-slate-800">${sro.reminder_date}</strong>
        </div>
        <p class="text-[11px] text-slate-500 leading-snug">${sro.recommendation}</p>
        <div class="pt-1 flex justify-end">
          <button onclick="selectTab('vault')" class="text-teal-700 font-bold hover:underline text-[11px]">Manage at Vault &rarr;</button>
        </div>
      </div>
    `);
  }

  // 2. Vault Expiry Cards
  if (r.vault_expiries && r.vault_expiries.length > 0) {
    r.vault_expiries.forEach(v => {
      const isOverdue = v.days_remaining < 0;
      const badgeClass = isOverdue ? "bg-rose-100 text-rose-800" : v.days_remaining <= 30 ? "bg-amber-100 text-amber-900" : "bg-blue-100 text-blue-800";
      cards.push(`
        <div class="p-3.5 rounded-xl border border-slate-200 bg-white text-xs space-y-1.5 shadow-xs">
          <div class="flex items-center justify-between">
            <span class="font-bold text-slate-800 flex items-center gap-1.5">
              <span>📄</span><span class="truncate max-w-[150px]">${escapeHtml(v.reminder_title || v.file_name)}</span>
            </span>
            <span class="px-2 py-0.5 rounded text-[10px] font-extrabold ${badgeClass}">
              ${isOverdue ? `${Math.abs(v.days_remaining)}d OVERDUE` : `Due in ${v.days_remaining}d`}
            </span>
          </div>
          <div class="text-slate-600 text-[11px]">
            File: <strong>${escapeHtml(v.file_name)}</strong> • Category: <span class="capitalize">${v.category.replace('_', ' ')}</span>
          </div>
          <div class="text-slate-600 text-[11px]">
            Renewal Due: <strong class="font-mono text-slate-800">${v.expiry_or_renewal_date}</strong>
          </div>
          <div class="pt-1 flex justify-end">
            <button onclick="selectTab('vault')" class="text-teal-700 font-bold hover:underline text-[11px]">Open Vault &rarr;</button>
          </div>
        </div>
      `);
    });
  }

  if (cards.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-3 px-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500 flex items-center justify-between">
        <span>No immediate document expirations or SRO target dates set. Keep your estate compliant by scheduling renewals.</span>
        <button onclick="selectTab('vault')" class="px-2.5 py-1 rounded bg-teal-50 text-teal-800 font-bold hover:bg-teal-100">Set Targets in Vault</button>
      </div>
    `;
  } else {
    container.innerHTML = cards.join("");
  }
}

// -------------------------------------------------------------
// PANE 2: FAMILY TREE
// -------------------------------------------------------------
function renderFamilyPane() {
  const isHeir = state.activeRole === "heir";
  const addBtn = document.getElementById("add-member-btn");
  if (addBtn) addBtn.style.display = isHeir ? "none" : "inline-flex";

  renderFamilyTree(state.members, "main-family-tree-container", (member) => {
    showMemberDetailsModal(member);
  });

  const tbody = document.getElementById("family-table-body");
  if (!tbody) return;

  if (state.members.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="p-8 text-center">
          <div class="empty-state-card border-none bg-transparent">
            <span class="empty-icon" aria-hidden="true">🌳</span>
            <div class="font-bold text-slate-800 text-sm">No family members registered yet</div>
            <p class="text-xs text-slate-500 max-w-sm">Map out your family lineage, designate legal heirs, and protect coparceners.</p>
            ${!isHeir ? `<button onclick="openAddMemberModal()" class="mt-2 px-4 py-2 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs shadow-xs transition cursor-pointer">+ Add Family Member</button>` : ''}
          </div>
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = state.members.map(m => `
    <tr class="border-b border-slate-100 hover:bg-slate-50/70 transition">
      <td class="py-3 px-4 font-semibold text-slate-800">${escapeHtml(m.name)}</td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded-md text-xs font-medium ${m.relation.toLowerCase() === 'self' ? 'bg-teal-100 text-teal-800' : 'bg-slate-100 text-slate-700'}">
          ${escapeHtml(m.relation)}
        </span>
      </td>
      <td class="py-3 px-4 text-xs text-slate-600">${m.age} yrs ${m.is_minor ? '<span class="text-red-600 font-bold">(Minor)</span>' : ''}</td>
      <td class="py-3 px-4">
        ${m.is_class_1_heir ? '<span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">Class I Statutory</span>' : '<span class="text-xs text-slate-400">Class II / Non-heir</span>'}
      </td>
      <td class="py-3 px-4">
        ${m.is_coparcener ? '<span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">Birthright Coparcener</span>' : '<span class="text-xs text-slate-400">—</span>'}
      </td>
      <td class="py-3 px-4 text-right">
        ${!isHeir && m.relation.toLowerCase() !== 'self' ? `
          <button onclick="openEditMemberModal(${m.id})" class="text-xs text-teal-700 hover:text-teal-900 font-semibold mr-2.5">Edit</button>
          <button onclick="deleteMember(${m.id})" class="text-xs text-red-600 hover:text-red-800 font-medium">Remove</button>
        ` : !isHeir && m.relation.toLowerCase() === 'self' ? `
          <button onclick="openEditProfileModal()" class="text-xs text-teal-700 hover:text-teal-900 font-semibold">Edit Karta</button>
        ` : '<span class="text-xs text-slate-300">Protected</span>'}
      </td>
    </tr>
  `).join("");
}

// -------------------------------------------------------------
// PANE 3: ASSETS INVENTORY
// -------------------------------------------------------------
function renderAssetsPane() {
  const isHeir = state.activeRole === "heir";
  const addAssetBtn = document.getElementById("add-asset-btn");
  if (addAssetBtn) addAssetBtn.style.display = isHeir ? "none" : "inline-flex";

  const container = document.getElementById("assets-list-container");
  if (!container) return;

  if (state.assets.length === 0) {
    container.innerHTML = `
      <div class="col-span-full">
        <div class="empty-state-card">
          <span class="empty-icon" aria-hidden="true">🏪</span>
          <div class="font-bold text-slate-800 text-base">Your Asset Inventory is Empty</div>
          <p class="text-xs text-slate-500 max-w-md">Record your shops, residential homes, ancestral farmland, bank accounts, and business shares to prevent family disputes.</p>
          ${!isHeir ? `<button onclick="openAddAssetModal()" class="mt-2 px-4 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs shadow-sm transition cursor-pointer">+ Add New Asset</button>` : ''}
        </div>
      </div>
    `;
    return;
  }

  const categoryIcons = {
    commercial_shop: "🏪 Commercial Shop / Store",
    residential_property: "🏠 Residential Property",
    agricultural_land: "🌾 Agricultural Farmland",
    partnership_firm: "🤝 Business / Partnership Share",
    bank_fd: "🏦 Bank Fixed Deposit",
    savings_account: "💳 Savings Account",
    demat_stocks: "📈 Demat Shares & Mutual Funds",
    gold_jewellery: "🪙 Gold, Silver & Jewellery",
    vehicle: "🚚 Commercial Vehicle",
    liability_loan: "⚠️ Loan / Debt / Liability"
  };

  container.innerHTML = state.assets.map(a => {
    const isLiability = a.category === "liability_loan";
    const allocs = state.allocations.filter(al => al.asset_id === a.id);
    const allocatedPct = allocs.reduce((sum, al) => sum + al.share_percentage, 0);

    return `
      <div class="p-4 rounded-xl border ${isLiability ? 'border-red-200 bg-red-50/20' : 'border-slate-200 bg-white'} shadow-sm flex flex-col justify-between gap-3">
        <div>
          <div class="flex items-start justify-between gap-2">
            <div>
              <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">${categoryIcons[a.category] || a.category}</span>
              <h4 class="font-bold text-slate-800 text-base mt-0.5">${escapeHtml(a.title)}</h4>
            </div>
            <div class="text-right">
              <span class="font-extrabold text-base ${isLiability ? 'text-red-700' : 'text-teal-700'}">${formatINR(a.estimated_value_inr)}</span>
              <div class="text-[10px] text-slate-400 capitalize">${a.acquisition_type.replace('_', ' ')}</div>
            </div>
          </div>
          
          <p class="text-xs text-slate-600 mt-2 line-clamp-2 leading-relaxed">${escapeHtml(a.description || 'No description provided.')}</p>
          
          <div class="mt-3 pt-2 border-t border-slate-100 flex flex-wrap gap-2 text-xs">
            <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono text-[11px]">ID: ${escapeHtml(a.identifier_number || 'N/A')}</span>
            ${a.location_or_institution ? `<span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-medium">${escapeHtml(a.location_or_institution)}</span>` : ''}
          </div>

          ${a.has_nominee_discrepancy ? `
            <div class="mt-2.5 p-2 rounded bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center gap-1.5">
              <span>⚠️</span>
              <span><strong>Nominee Conflict:</strong> Nominee is <strong>${a.current_nominee_name}</strong> (${a.nominee_relationship}), which conflicts with will bequests!</span>
            </div>
          ` : a.current_nominee_name ? `
            <div class="mt-2 text-xs text-slate-500">
              Registered Nominee: <span class="font-medium text-slate-700">${a.current_nominee_name} (${a.nominee_relationship || 'Nominee'})</span>
            </div>
          ` : ''}
        </div>

        <div class="pt-3 border-t border-slate-100 flex items-center justify-between flex-wrap gap-2">
          <div class="text-xs">
            ${!isLiability ? `
              <span class="font-bold px-2 py-0.5 rounded-md text-[11px] ${allocatedPct > 100 ? 'bg-rose-100 text-rose-800 border border-rose-300' : allocatedPct === 100 ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-amber-100 text-amber-800 border border-amber-300'}">
                ${allocatedPct > 100 ? `⚠️ ${allocatedPct}% Overallocated` : allocatedPct === 100 ? `✅ 100% Bequeathed` : `⏳ ${allocatedPct}% Bequeathed (${100 - allocatedPct}% Left)`}
              </span>
            ` : '<span class="text-xs text-slate-400 font-medium">Payable from liquid estate</span>'}
          </div>

          <div class="flex items-center gap-2">
            ${!isLiability && !isHeir ? `
              <button onclick="openAllocationModal(${a.id})" class="px-2.5 py-1 rounded bg-teal-50 text-teal-700 hover:bg-teal-100 font-semibold text-xs border border-teal-200 cursor-pointer">
                Allocate / Bequeath
              </button>
            ` : ''}
            ${!isHeir ? `
              <button onclick="openEditAssetModal(${a.id})" class="px-2 py-1 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 font-semibold text-xs border border-slate-200 cursor-pointer" title="Edit Asset">
                Edit
              </button>
              <button onclick="deleteAsset(${a.id})" class="text-xs text-slate-400 hover:text-red-600 p-1 cursor-pointer" title="Delete Asset" aria-label="Delete asset ${a.title}">
                🗑️
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// -------------------------------------------------------------
// PANE 4: WILL & SUCCESSION DRAFT
// -------------------------------------------------------------
function renderWillPane() {
  if (!state.willDraft || !state.currentProfile) return;
  const isHeir = state.activeRole === "heir";

  document.getElementById("will-executor-name").value = state.willDraft.executor_name || "";
  document.getElementById("will-executor-rel").value = state.willDraft.executor_relationship || "";
  document.getElementById("will-alt-executor").value = state.willDraft.alternate_executor_name || "";
  document.getElementById("will-guardian").value = state.willDraft.guardian_minor_name || "";
  document.getElementById("will-witness1-name").value = state.willDraft.witness1_name || "";
  document.getElementById("will-witness1-addr").value = state.willDraft.witness1_address || "";
  document.getElementById("will-witness2-name").value = state.willDraft.witness2_name || "";
  document.getElementById("will-witness2-addr").value = state.willDraft.witness2_address || "";
  document.getElementById("will-doc-name").value = state.willDraft.doctor_name || "";
  document.getElementById("will-doc-reg").value = state.willDraft.doctor_reg_no || "";
  document.getElementById("will-vault-loc").value = state.willDraft.original_physical_location || "";
  document.getElementById("will-sro-office").value = state.willDraft.sub_registrar_office || "";

  const formFields = document.querySelectorAll("#will-form input, #will-form select");
  formFields.forEach(f => f.disabled = isHeir);
  const saveWillBtn = document.getElementById("save-will-btn");
  if (saveWillBtn) saveWillBtn.style.display = isHeir ? "none" : "inline-flex";

  const previewBox = document.getElementById("will-preview-summary");
  if (previewBox) {
    const totalAssets = state.assets.filter(a => a.category !== 'liability_loan').length;
    const allocCount = state.allocations.length;
    previewBox.innerHTML = `
      <div class="space-y-3 text-xs text-slate-700 leading-relaxed">
        <div class="p-3 bg-teal-50 border border-teal-200 rounded-lg">
          <div class="font-bold text-teal-900 text-sm">Legal Framework Verification</div>
          <div>Compliant with <strong>Indian Succession Act 1925</strong> & <strong>${state.currentProfile.governing_law}</strong></div>
          <div class="mt-1 text-slate-600">Total ${totalAssets} assets inventoried • ${allocCount} specific bequests executed</div>
        </div>

        <div class="border rounded-lg p-3 bg-white space-y-2">
          <div class="font-bold text-slate-800">Primary Clauses Generated:</div>
          <ul class="list-disc pl-4 space-y-1 text-slate-600">
            <li><strong>Sound Mind & Health Declaration:</strong> Doctor attestation by ${state.willDraft.doctor_name || 'Medical Practitioner'}.</li>
            <li><strong>Sole Executor Appointment:</strong> ${state.willDraft.executor_name} to administer distribution without surety bond.</li>
            <li><strong>Commercial Continuity Directives:</strong> Specific trader protections for ${state.currentProfile.business_name} trade licenses & debts.</li>
            <li><strong>Comprehensive Residuary Clause:</strong> Prevents non-inventoried properties from going into intestate litigation.</li>
            <li><strong>Two Independent Witnesses:</strong> Non-beneficiary attestation format under Section 63 of Indian Succession Act.</li>
          </ul>
        </div>
      </div>
    `;
  }

  // Render the full, authentic on-screen Will document
  renderWillDocumentPreview();
}

function switchWillViewMode(mode) {
  const docView = document.getElementById("will-document-view");
  const editView = document.getElementById("will-edit-view");
  const docBtn = document.getElementById("will-tab-doc-btn");
  const editBtn = document.getElementById("will-tab-edit-btn");

  if (mode === "doc") {
    if (docView) docView.classList.remove("hidden");
    if (editView) editView.classList.add("hidden");
    if (docBtn) docBtn.className = "px-3.5 py-1.5 rounded-lg transition font-bold bg-white text-stone-900 shadow-2xs cursor-pointer flex items-center gap-1.5";
    if (editBtn) editBtn.className = "px-3.5 py-1.5 rounded-lg transition font-semibold text-stone-600 hover:text-stone-900 cursor-pointer flex items-center gap-1.5";
  } else {
    if (docView) docView.classList.add("hidden");
    if (editView) editView.classList.remove("hidden");
    if (editBtn) editBtn.className = "px-3.5 py-1.5 rounded-lg transition font-bold bg-white text-stone-900 shadow-2xs cursor-pointer flex items-center gap-1.5";
    if (docBtn) docBtn.className = "px-3.5 py-1.5 rounded-lg transition font-semibold text-stone-600 hover:text-stone-900 cursor-pointer flex items-center gap-1.5";
  }
}

function renderWillDocumentPreview() {
  const container = document.getElementById("will-formal-doc-content");
  if (!container || !state.currentProfile || !state.willDraft) return;

  const p = state.currentProfile;
  const w = state.willDraft;
  const kartaName = escapeHtml(p.karta_name || "Karta");
  const cityName = escapeHtml(p.city || "New Delhi");
  const stateName = escapeHtml(p.state || "Delhi");
  const bizName = escapeHtml(p.business_name || "Trading Business");
  const bizType = escapeHtml(p.business_type || "Sole Proprietorship");
  const govLaw = escapeHtml(p.governing_law || "Hindu Succession Act, 1956");

  const executorName = escapeHtml(w.executor_name || "Designated Executor");
  const executorRel = escapeHtml(w.executor_relationship || "Family Member");
  const altExecutor = escapeHtml(w.alternate_executor_name || "Advocate / CA");
  const guardianName = escapeHtml(w.guardian_minor_name || "");
  const guardianRel = escapeHtml(w.guardian_relationship || "Guardian");

  const w1Name = escapeHtml(w.witness1_name || "______________________");
  const w1Addr = escapeHtml(w.witness1_address || "______________________");
  const w2Name = escapeHtml(w.witness2_name || "______________________");
  const w2Addr = escapeHtml(w.witness2_address || "______________________");

  const docName = escapeHtml(w.doctor_name || "______________________");
  const docReg = escapeHtml(w.doctor_reg_no || "______________________");
  const vaultLoc = escapeHtml(w.original_physical_location || "Physical Document Locker");
  const sroOffice = escapeHtml(w.sub_registrar_office || "Sub-Registrar Office");

  const memberMap = {};
  state.members.forEach(m => { memberMap[m.id] = m; });
  const assetMap = {};
  state.assets.forEach(a => { assetMap[a.id] = a; });

  const activeAssets = state.assets.filter(a => a.category !== 'liability_loan');
  const totalGross = activeAssets.reduce((sum, a) => sum + (a.estimated_value_inr || 0), 0);

  let bequestsTableRows = "";
  if (state.allocations.length === 0) {
    bequestsTableRows = `
      <tr class="border-b border-stone-200">
        <td class="py-2.5 px-3">All Inventoried Assets</td>
        <td class="py-2.5 px-3">General Estate</td>
        <td class="py-2.5 px-3"><strong>Surviving Class I Statutory Legal Heirs</strong></td>
        <td class="py-2.5 px-3 text-center">100.0%</td>
        <td class="py-2.5 px-3 text-right">Rs. ${totalGross.toLocaleString("en-IN")}</td>
      </tr>
    `;
  } else {
    bequestsTableRows = state.allocations.map(al => {
      const ast = assetMap[al.asset_id];
      const ben = memberMap[al.beneficiary_id];
      if (!ast || !ben) return "";
      const val = (al.share_percentage / 100.0) * (ast.estimated_value_inr || 0);
      return `
        <tr class="border-b border-stone-200 hover:bg-amber-50/50 transition text-xs">
          <td class="py-2.5 px-3 font-medium">
            <strong>${escapeHtml(ast.title)}</strong>
            ${ast.description ? `<br><span class="text-[10.5px] text-stone-500">${escapeHtml(ast.description.replace(/₹/g, 'Rs. '))}</span>` : ""}
          </td>
          <td class="py-2.5 px-3 text-stone-600">
            ${escapeHtml(ast.category.replace(/_/g, ' ').toUpperCase())}
            ${ast.identifier_number ? `<br><span class="text-[10px] text-stone-500 font-mono">ID: ${escapeHtml(ast.identifier_number)}</span>` : ""}
          </td>
          <td class="py-2.5 px-3">
            <strong class="text-teal-900">${escapeHtml(ben.name)}</strong>
            <span class="text-[10.5px] text-teal-700 ml-1">(${escapeHtml(ben.relation)})</span>
          </td>
          <td class="py-2.5 px-3 text-center font-bold text-stone-800">${al.share_percentage.toFixed(1)}%</td>
          <td class="py-2.5 px-3 text-right font-bold text-stone-900">Rs. ${Math.round(val).toLocaleString("en-IN")}</td>
        </tr>
      `;
    }).join("");
  }

  const todayStr = new Date().toLocaleDateString("en-IN", { day: 'numeric', month: 'long', year: 'numeric' });

  container.innerHTML = `
    <!-- Top Decorative Seal & Header -->
    <div class="text-center pb-6 border-b-2 border-stone-800 space-y-1">
      <div class="inline-flex items-center justify-center w-12 h-12 rounded-full border border-amber-600/60 bg-amber-50 text-xl mb-2 text-amber-800 shadow-xs">
        ⚖️
      </div>
      <h1 class="text-2xl sm:text-3xl font-black text-stone-950 tracking-wider uppercase font-serif">
        Last Will and Testament
      </h1>
      <div class="text-base font-bold text-stone-800">
        OF SHRI / SMT. ${kartaName.toUpperCase()}
      </div>
      <div class="text-xs text-stone-600">
        Resident of ${cityName}, ${stateName}, India • Governed by ${govLaw}
      </div>
    </div>

    <!-- Statutory Legal Banner -->
    <div class="p-3 bg-amber-50/80 border border-amber-300 rounded-xl text-xs text-amber-950 text-center font-sans">
      <strong>STATUTORY RECITALS:</strong> Executed in conformity with Section 63 of the Indian Succession Act, 1925. 
      Attested by two independent witnesses and recommended for Book 3 registration at Sub-Registrar Office (SRO).
    </div>

    <!-- Solemn Preamble -->
    <div class="space-y-3 text-sm text-stone-900 text-justify">
      <p>
        <strong>I, ${kartaName}</strong>, resident of ${cityName}, ${stateName}, India, 
        carrying on business under the name and commercial style of <strong>"${bizName}"</strong> (${bizType}), 
        by faith/religion Hindu, of sound physical health and disposing state of mind, memory, and understanding, 
        do hereby make, publish, and declare this as my <strong>LAST WILL AND TESTAMENT</strong>, 
        hereby revoking, canceling, and declaring null and void all former Wills, Codicils, Testaments, 
        and Testamentary Dispositions made by me at any time heretofore.
      </p>

      <!-- Clause I -->
      <div class="pt-2">
        <h3 class="font-bold text-stone-950 font-serif text-sm">CLAUSE I: DECLARATION OF SOUND MIND & FREE VOLITION</h3>
        <p class="text-xs text-stone-800 mt-1">
          I declare that I am executing this Will out of my own free will, volition, and desire, without any coercion, 
          compulsion, duress, undue influence, fraud, misrepresentation, or persuasion from any family member, associate, or stranger whatsoever. 
          I have thoroughly evaluated all my worldly assets, commercial properties, liabilities, and familial obligations.
        </p>
      </div>

      <!-- Clause II -->
      <div class="pt-2">
        <h3 class="font-bold text-stone-950 font-serif text-sm">CLAUSE II: APPOINTMENT OF EXECUTOR AND TRUSTEE</h3>
        <p class="text-xs text-stone-800 mt-1">
          I hereby nominate, constitute, and appoint my <strong>${executorRel}</strong>, <strong>${executorName}</strong>, 
          to be the sole and absolute Executor and Trustee of this my Last Will and Testament. 
          In the event that ${executorName} predeceases me or is unable to act, I appoint <strong>${altExecutor}</strong> 
          as Alternate Executor. I direct that no administration bond or court security shall be required from my Executor.
        </p>
      </div>

      ${guardianName ? `
      <!-- Clause III -->
      <div class="pt-2">
        <h3 class="font-bold text-stone-950 font-serif text-sm">CLAUSE III: TESTAMENTARY GUARDIAN FOR MINORS (Section 60 ISA)</h3>
        <p class="text-xs text-stone-800 mt-1">
          In the event of my demise prior to any of my children or grandchildren attaining majority (18 years), 
          I hereby appoint <strong>${guardianName}</strong> (${guardianRel}) as lawful Testamentary Guardian of their person and property.
        </p>
      </div>
      ` : ""}

      <!-- Clause IV -->
      <div class="pt-2">
        <h3 class="font-bold text-stone-950 font-serif text-sm">CLAUSE IV: DISCHARGE OF DEBTS, TAXES & FUNERAL EXPENSES</h3>
        <p class="text-xs text-stone-800 mt-1">
          I direct my Executor to first pay and satisfy all my just, lawful, and enforceable debts, trade liabilities, supplier dues, 
          outstanding taxes, and reasonable funeral expenses out of my liquid bank balances prior to distribution of specific bequests.
        </p>
      </div>

      <!-- Clause V: Specific Bequests Table -->
      <div class="pt-2">
        <h3 class="font-bold text-stone-950 font-serif text-sm mb-1.5">CLAUSE V: SCHEDULE OF SPECIFIC BEQUESTS & ALLOCATIONS</h3>
        <p class="text-xs text-stone-800 mb-2">
          Subject to the aforesaid payments, I hereby devise, bequeath, apportion, and assign my properties, businesses, 
          and assets as set forth hereunder:
        </p>
        
        <div class="overflow-x-auto border border-stone-300 rounded-xl bg-white shadow-2xs font-sans">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-stone-100 border-b border-stone-300 text-[11px] font-bold text-stone-700">
                <th class="py-2.5 px-3">Asset Title / Business</th>
                <th class="py-2.5 px-3">Category & Details</th>
                <th class="py-2.5 px-3">Designated Beneficiary</th>
                <th class="py-2.5 px-3 text-center">Share %</th>
                <th class="py-2.5 px-3 text-right">Estimated Value</th>
              </tr>
            </thead>
            <tbody>
              ${bequestsTableRows}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Clause VI -->
      <div class="pt-2">
        <h3 class="font-bold text-stone-950 font-serif text-sm">CLAUSE VI: COMMERCIAL ENTERPRISE CONTINUITY & GOODWILL</h3>
        <p class="text-xs text-stone-800 mt-1">
          Regarding my commercial concern <strong>"${bizName}"</strong>, I specifically direct that the goodwill, trade name, 
          GST registrations, tenancy rights, shop inventory, and ongoing trading agencies shall vest in the designated beneficiaries 
          without partition, disruption, or liquidation of the running business concern.
        </p>
      </div>

      <!-- Clause VII -->
      <div class="pt-2">
        <h3 class="font-bold text-stone-950 font-serif text-sm">CLAUSE VII: NOMINEE HARMONIZATION UNDER SARBATI DEVI JURISPRUDENCE</h3>
        <p class="text-xs text-stone-800 mt-1">
          I expressly declare that any bank nominations are made solely for institutional collection purposes under the Supreme Court 
          doctrine of <i>Sarbati Devi v. Usha Devi (1984)</i>. My nominees shall act as statutory trustees (Amanatdars) and immediately 
          transfer all proceeds to the designated beneficiaries named in this Will.
        </p>
      </div>

      <!-- Clause VIII -->
      <div class="pt-2">
        <h3 class="font-bold text-stone-950 font-serif text-sm">CLAUSE VIII: RESIDUARY ESTATE CLAUSE</h3>
        <p class="text-xs text-stone-800 mt-1">
          All the rest, residue, and remainder of my estate, whether real, personal, tangible, or intangible, including any properties 
          acquired after the date hereof, shall devolve equally upon my surviving Class I statutory legal heirs.
        </p>
      </div>

      <!-- Clause IX -->
      <div class="pt-2">
        <h3 class="font-bold text-stone-950 font-serif text-sm">CLAUSE IX: SOLEMN APPEAL FOR FAMILY HARMONY</h3>
        <p class="text-xs text-stone-800 mt-1">
          I earnestly counsel and enjoin all my heirs to accept this testamentary disposition in peace and goodwill, 
          preserving the honor, unity, and prosperity of our family across generations without recourse to litigation.
        </p>
      </div>

      <!-- Testimonium -->
      <div class="pt-4 border-t border-stone-300">
        <p class="text-xs text-stone-900">
          <strong>IN WITNESS WHEREOF</strong>, I, the said Testator, <strong>${kartaName}</strong>, have set and subscribed my hand 
          and signature to this my LAST WILL AND TESTAMENT on this <strong>${todayStr}</strong> at ${cityName}, ${stateName}, India, 
          in the joint presence of the two attesting witnesses signing below at my request.
        </p>
      </div>

      <!-- Signatures Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 font-sans text-xs">
        <div class="p-4 rounded-xl border border-stone-300 bg-stone-50/70">
          <div class="font-bold text-stone-900 mb-1">TESTATOR'S SIGNATURE:</div>
          <div class="h-12 border-b border-dashed border-stone-400 mb-2"></div>
          <div class="font-bold text-stone-800">${kartaName}</div>
          <div class="text-[11px] text-stone-500">(Testator)</div>
          <div class="text-[10px] text-stone-400 mt-2">Physical Custody: ${vaultLoc}</div>
        </div>

        <div class="p-4 rounded-xl border border-stone-300 bg-stone-50/70">
          <div class="font-bold text-stone-900 mb-1">INTENDED SRO JURISDICTION:</div>
          <div class="text-stone-700 font-semibold">${sroOffice}</div>
          <div class="text-[11px] text-stone-500 mt-1">Register: Book 3 (Wills & Adoptions)</div>
          <div class="text-[11px] text-stone-500">Stamp Duty: Nil (Zero across Indian States)</div>
        </div>
      </div>

      <!-- Attestation by Two Witnesses -->
      <div class="pt-4 font-sans text-xs">
        <div class="font-bold text-stone-900 font-serif text-sm mb-1">
          ATTESTATION BY TWO INDEPENDENT WITNESSES (Section 63, Indian Succession Act)
        </div>
        <p class="text-[11px] text-stone-600 mb-3">
          Signed, published, and declared by the Testator in our joint presence, who in their presence and at their request, 
          have hereunto subscribed our names as attesting witnesses confirming sound testamentary capacity.
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="p-4 rounded-xl border border-stone-300 bg-white">
            <div class="font-bold text-teal-900 mb-1">FIRST ATTESTING WITNESS:</div>
            <div class="h-10 border-b border-dashed border-stone-300 mb-2"></div>
            <div>Name: <strong>${w1Name}</strong></div>
            <div class="text-stone-500 text-[11px]">Address: ${w1Addr}</div>
            <div class="text-[10px] text-stone-400 mt-1">Identity: Independent Adult (Non-Beneficiary)</div>
          </div>

          <div class="p-4 rounded-xl border border-stone-300 bg-white">
            <div class="font-bold text-teal-900 mb-1">SECOND ATTESTING WITNESS:</div>
            <div class="h-10 border-b border-dashed border-stone-300 mb-2"></div>
            <div>Name: <strong>${w2Name}</strong></div>
            <div class="text-stone-500 text-[11px]">Address: ${w2Addr}</div>
            <div class="text-[10px] text-stone-400 mt-1">Identity: Independent Adult (Non-Beneficiary)</div>
          </div>
        </div>
      </div>

      <!-- Schedule I: Medical Fitness Certificate -->
      <div class="pt-4 font-sans text-xs">
        <div class="p-4 rounded-xl border border-teal-300 bg-teal-50/60">
          <div class="font-bold text-teal-950 font-serif text-sm mb-1">
            SCHEDULE I: REGISTERED MEDICAL PRACTITIONER'S FITNESS CERTIFICATE
          </div>
          <p class="text-[11px] text-teal-900 mb-2">
            I, <strong>Dr. ${docName}</strong> (MCI / State Medical Council Reg No. ${docReg}), hereby certify that I have examined 
            Shri / Smt. ${kartaName} on this date and certify that they are in sound mental and physical health, possessing full 
            cognitive faculties and an unclouded testamentary capacity to understand the nature, scope, and effect of this Will.
          </p>
          <div class="flex justify-between items-end pt-3 text-[11px] text-teal-800">
            <div>Date: ${todayStr}</div>
            <div class="text-right">Doctor's Signature & Stamp: ______________________</div>
          </div>
        </div>
      </div>

    </div>
  `;
}


// -------------------------------------------------------------
// PANE 5: ENCRYPTED DOCUMENT VAULT (Fernet AES-128-CBC + HMAC)
// -------------------------------------------------------------
function renderVaultPane() {
  const isHeir = state.activeRole === "heir";
  const uploadForm = document.getElementById("vault-upload-card");
  if (uploadForm) uploadForm.style.display = isHeir ? "none" : "block";

  // Update SRO Will Registration status card
  const sroDisplay = document.getElementById("vault-sro-date-display");
  const sroInput = document.getElementById("vault-sro-date-input");
  const sroTag = document.getElementById("vault-sro-status-tag");
  if (state.willDraft) {
    const d = state.willDraft.sro_reminder_date || "Not Scheduled";
    if (sroDisplay) sroDisplay.innerText = d;
    if (sroInput && state.willDraft.sro_reminder_date) sroInput.value = state.willDraft.sro_reminder_date;
    if (sroTag) {
      sroTag.innerText = state.willDraft.sro_reminder_date ? "Tracking Active" : "Date Pending";
      sroTag.className = state.willDraft.sro_reminder_date ? "px-2 py-0.5 rounded text-[10px] font-bold bg-amber-200 text-amber-900" : "px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-700";
    }
  }

  const listContainer = document.getElementById("vault-docs-list");
  if (!listContainer) return;

  if (state.vaultDocs.length === 0) {
    listContainer.innerHTML = `
      <div class="text-center py-8 text-slate-400 text-sm">
        No documents uploaded to the vault yet. Upload land registry, partnership deeds, and FDRs for encrypted safe-keeping.
      </div>
    `;
    return;
  }

  listContainer.innerHTML = state.vaultDocs.map(d => {
    let renewalBadge = "";
    let statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">🟢 Verified & Active</span>`;
    
    if (d.expiry_or_renewal_date) {
      try {
        const exp = new Date(d.expiry_or_renewal_date);
        const diffDays = Math.ceil((exp - new Date()) / (1000 * 60 * 60 * 24));
        if (diffDays < 0) {
          statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">🔴 Expired (${Math.abs(diffDays)}d overdue)</span>`;
        } else if (diffDays <= 30) {
          statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">🟡 Review Needed (${diffDays}d left)</span>`;
        }
      } catch (e) {}
      renewalBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-50 text-amber-800 border border-amber-200">Renewal: ${d.expiry_or_renewal_date}</span>`;
    }

    return `
      <div class="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 font-bold text-lg shrink-0">
            📄
          </div>
          <div>
            <div class="font-bold text-slate-800 text-sm flex items-center gap-2 flex-wrap">
              <span>${escapeHtml(d.file_name)}</span>
              ${statusBadge}
              ${d.reminder_title ? `<span class="text-xs font-normal text-slate-500">(${d.reminder_title})</span>` : ''}
              ${renewalBadge}
            </div>
            <div class="text-xs text-slate-500 flex items-center gap-2 mt-0.5 flex-wrap">
              <span class="px-1.5 py-0.5 rounded bg-slate-100 uppercase text-[10px] font-semibold">${d.category.replace('_', ' ')}</span>
              <span>${(d.file_size_bytes / 1024).toFixed(1)} KB</span>
              <span>•</span>
              <span class="text-emerald-700 font-semibold flex items-center gap-1">🔒 Fernet AES-128-CBC + HMAC</span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button onclick="downloadVaultDoc(${d.id})" class="px-3 py-1.5 rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 font-semibold text-xs border border-teal-200 flex items-center gap-1 cursor-pointer">
            <span>Decrypted Download</span>
          </button>
        </div>
      </div>
    `;
  }).join("");

  // Render Missing Documents Audit Section
  renderVaultMissingDocuments();
}

function renderVaultMissingDocuments() {
  const missingContainer = document.getElementById("vault-missing-docs-list");
  const countBadge = document.getElementById("vault-missing-docs-count");
  if (!missingContainer) return;

  const activeAssets = (state.assets || []).filter(a => a.category !== 'liability_loan');
  const vaultAssetIds = new Set((state.vaultDocs || []).map(d => d.asset_id).filter(Boolean));

  const missingAssets = activeAssets.filter(a => !vaultAssetIds.has(a.id) && !a.documents_available);

  if (countBadge) {
    countBadge.innerText = `${missingAssets.length} Assets Missing Title Deeds`;
    countBadge.className = missingAssets.length > 0
      ? "px-2 py-0.5 rounded text-[10px] font-extrabold bg-rose-100 text-rose-800"
      : "px-2 py-0.5 rounded text-[10px] font-extrabold bg-emerald-100 text-emerald-800";
  }

  if (missingAssets.length === 0) {
    missingContainer.innerHTML = `
      <div class="p-3 rounded-xl bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200 flex items-center gap-2">
        <span>✓</span><span>All inventoried estate properties have corresponding title deeds or receipts on record!</span>
      </div>
    `;
    return;
  }

  missingContainer.innerHTML = missingAssets.map(a => `
    <div class="p-3 rounded-xl border border-rose-200 bg-rose-50/40 flex items-center justify-between gap-3 text-xs">
      <div class="flex items-center gap-2.5 truncate">
        <span class="text-rose-600 font-bold">🔴</span>
        <div class="truncate">
          <div class="font-bold text-stone-900">${escapeHtml(a.title)}</div>
          <div class="text-[10px] text-stone-500">${escapeHtml(a.category.replace('_', ' '))} • Valuation: ${formatINR(a.estimated_value_inr)}</div>
        </div>
      </div>
      <button onclick="prefillUploadForAsset(${a.id}, '${escapeHtml(a.category)}', '${escapeHtml(a.title).replace(/'/g, "\\'")}')" class="px-3 py-1.5 rounded-lg bg-teal-800 hover:bg-teal-900 text-white font-bold text-xs shrink-0 cursor-pointer shadow-xs">
        + Upload Deed
      </button>
    </div>
  `).join("");
}

function prefillUploadForAsset(assetId, category, title) {
  const catSelect = document.getElementById("vault-category");
  const remInput = document.getElementById("vault-reminder-title");
  if (catSelect) {
    if (category.includes('shop') || category.includes('residential')) catSelect.value = 'registry_deed';
    else if (category.includes('partnership')) catSelect.value = 'partnership_deed';
    else if (category.includes('bank_fd')) catSelect.value = 'fd_receipt';
    else if (category.includes('gold')) catSelect.value = 'gold_valuation';
  }
  if (remInput) remInput.value = `Title Deed for ${title}`;
  document.getElementById("vault-upload-card")?.scrollIntoView({ behavior: 'smooth' });
  showToast(`Ready to upload document for: ${title}`, "info");
}

async function uploadVaultFile(event) {
  event.preventDefault();
  const fileInput = document.getElementById("vault-file-input");
  if (!fileInput.files || fileInput.files.length === 0) {
    showToast("Please choose a file to upload", "warning");
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);
  formData.append("category", document.getElementById("vault-category").value);
  const remTitle = document.getElementById("vault-reminder-title")?.value;
  const expDate = document.getElementById("vault-expiry-date")?.value;
  if (remTitle) formData.append("reminder_title", remTitle);
  if (expDate) formData.append("expiry_or_renewal_date", expDate);

  try {
    const res = await apiFetch(`/api/vault/${state.currentProfileId}/upload`, {
      method: "POST",
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload failed");
    }
    await refreshVault();
    await refreshReminders();
    fileInput.value = "";
    if (document.getElementById("vault-reminder-title")) document.getElementById("vault-reminder-title").value = "";
    if (document.getElementById("vault-expiry-date")) document.getElementById("vault-expiry-date").value = "";
    renderActiveTab();
    showToast(`File "${file.name}" encrypted with Fernet and vaulted!`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

function downloadVaultDoc(docId) {
  const tokenParam = state.authToken ? `?token=${encodeURIComponent(state.authToken)}` : '';
  window.open(`/api/vault/${state.currentProfileId}/download/${docId}${tokenParam}`, "_blank");
}

async function runVaultAudit() {
  try {
    const res = await apiFetch("/api/vault-security-audit");
    const data = await res.json();
    alert(`ENCRYPTED VAULT AUDIT:\nStatus: ${data.status}\nEncryption Standard: ${data.encryption_standard}\nTotal Files: ${data.total_files}\nVerified Healthy: ${data.verified_healthy_files}\nCorrupted: ${data.corrupted_or_tampered_files}\nKey Storage: ${data.key_storage}`);
  } catch (err) {
    showToast("Audit check failed", "error");
  }
}

async function saveSROReminderDate(event) {
  event.preventDefault();
  const dateInput = document.getElementById("vault-sro-date-input");
  if (!dateInput || !dateInput.value) return;

  try {
    const res = await apiFetch(`/api/reminders/${state.currentProfileId}/sro`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sro_reminder_date: dateInput.value })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to update SRO reminder");
    }
    await refreshWillDraft();
    await refreshReminders();
    renderActiveTab();
    showToast(`SRO Will Registration Target saved: ${dateInput.value}!`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// -------------------------------------------------------------
// PANE 6: 'WHAT HAPPENS IF...' SIMULATOR (M5 Subsystem)
// -------------------------------------------------------------
let intestateChartInstance = null;
let testateChartInstance = null;

function populateSimulatorSelects() {
  const childSelect = document.getElementById("sim-predeceased-child");
  const assetSelect = document.getElementById("sim-ademption-asset");

  if (childSelect) {
    childSelect.innerHTML = `<option value="">None (All Heirs Alive)</option>`;
    state.members.filter(m => m.relation === "Son" || m.relation === "Daughter").forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.innerText = `${c.name} (${c.relation})`;
      childSelect.appendChild(opt);
    });
  }

  if (assetSelect) {
    assetSelect.innerHTML = `<option value="">None (All Assets Intact)</option>`;
    state.assets.filter(a => a.category !== "liability_loan").forEach(a => {
      const opt = document.createElement("option");
      opt.value = a.id;
      opt.innerText = `${a.title} (${formatINR(a.estimated_value_inr)})`;
      assetSelect.appendChild(opt);
    });
  }
}

async function runInteractiveSimulation() {
  const childSelect = document.getElementById("sim-predeceased-child");
  const assetSelect = document.getElementById("sim-ademption-asset");
  const unregCheck = document.getElementById("sim-toggle-unregistered");
  const daughterCheck = document.getElementById("sim-toggle-exclude-daughter");

  const payload = {
    unregistered_will: unregCheck ? unregCheck.checked : false,
    exclude_daughter: daughterCheck ? daughterCheck.checked : false,
    predeceased_child_id: childSelect && childSelect.value ? parseInt(childSelect.value) : null,
    ademption_asset_id: assetSelect && assetSelect.value ? parseInt(assetSelect.value) : null
  };

  try {
    const res = await apiFetch(`/api/simulation/${state.currentProfileId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Simulation calculation failed");
    }
    state.simulationData = await res.json();
    renderSimulatorPane();
    showToast("⚡ Scenario simulated successfully!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function resetInteractiveSimulation() {
  const childSelect = document.getElementById("sim-predeceased-child");
  const assetSelect = document.getElementById("sim-ademption-asset");
  const unregCheck = document.getElementById("sim-toggle-unregistered");
  const daughterCheck = document.getElementById("sim-toggle-exclude-daughter");

  if (childSelect) childSelect.value = "";
  if (assetSelect) assetSelect.value = "";
  if (unregCheck) unregCheck.checked = false;
  if (daughterCheck) daughterCheck.checked = false;

  await refreshSimulation();
  renderSimulatorPane();
  showToast("Baseline succession scenario restored.", "info");
}

function renderSimulatorPane() {
  if (!state.simulationData) return;

  const sim = state.simulationData;

  document.getElementById("sim-networth").innerText = formatINR(sim.net_worth_inr);
  document.getElementById("sim-class1-count").innerText = `${sim.class_1_heirs_count} Heirs`;

  // Render Charts
  const ctxIntestate = document.getElementById("chart-intestate")?.getContext("2d");
  const ctxTestate = document.getElementById("chart-testate")?.getContext("2d");

  if (ctxIntestate) {
    if (intestateChartInstance) intestateChartInstance.destroy();
    const labels = sim.intestate_shares.map(s => `${s.name} (${s.relation})`);
    const values = sim.intestate_shares.map(s => s.share_pct);
    intestateChartInstance = new Chart(ctxIntestate, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: ["#3b82f6", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#64748b", "#06b6d4"]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
        }
      }
    });
  }

  if (ctxTestate) {
    if (testateChartInstance) testateChartInstance.destroy();
    const testateFiltered = sim.testate_shares.filter(s => s.share_pct > 0);
    const labels = testateFiltered.map(s => `${s.name} (${s.relation})`);
    const values = testateFiltered.map(s => s.share_pct);
    testateChartInstance = new Chart(ctxTestate, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: ["#0f766e", "#f97316", "#06b6d4", "#a855f7", "#84cc16", "#e11d48", "#4f46e5"]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
        }
      }
    });
  }

  // Side-by-side Table Comparison
  const simTableBody = document.getElementById("sim-comparison-table");
  if (simTableBody) {
    simTableBody.innerHTML = sim.testate_shares.map(ts => {
      const is = sim.intestate_shares.find(i => i.member_id === ts.member_id) || { share_pct: 0, estimated_inr: 0, heir_class: "N/A" };
      const diffPct = ts.share_pct - is.share_pct;

      return `
        <tr class="border-b border-slate-100 hover:bg-slate-50/70 text-xs">
          <td class="py-2.5 px-3 font-semibold text-slate-800">
            ${ts.name} <span class="text-[10px] text-slate-500 font-normal">(${ts.relation})</span>
          </td>
          <td class="py-2.5 px-3 font-medium text-blue-700">
            ${is.share_pct}% (${formatINR(is.estimated_inr)})
          </td>
          <td class="py-2.5 px-3 font-bold text-teal-800">
            ${ts.share_pct}% (${formatINR(ts.estimated_inr)})
          </td>
          <td class="py-2.5 px-3">
            <span class="px-2 py-0.5 rounded font-bold text-[11px] ${diffPct > 0 ? 'bg-emerald-50 text-emerald-700' : diffPct < 0 ? 'bg-amber-50 text-amber-800' : 'bg-slate-100 text-slate-600'}">
              ${diffPct > 0 ? `+${diffPct.toFixed(1)}%` : `${diffPct.toFixed(1)}%`}
            </span>
          </td>
        </tr>
      `;
    }).join("");
  }

  // Legal Pitfalls & Friction Points
  const pitfallsContainer = document.getElementById("sim-pitfalls-container");
  if (pitfallsContainer) {
    if (sim.pitfalls.length === 0) {
      pitfallsContainer.innerHTML = `<div class="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs font-semibold">Zero critical legal conflicts detected. Your succession plan is legally watertight!</div>`;
    } else {
      pitfallsContainer.innerHTML = sim.pitfalls.map(p => `
        <div class="p-3.5 rounded-xl border ${p.severity === 'CRITICAL' ? 'border-red-200 bg-red-50/40' : 'border-amber-200 bg-amber-50/40'} text-xs space-y-1.5">
          <div class="flex items-center justify-between font-bold ${p.severity === 'CRITICAL' ? 'text-red-900' : 'text-amber-900'}">
            <span>⚠️ ${escapeHtml(p.title)}</span>
            <span class="text-[10px] uppercase font-extrabold px-1.5 py-0.5 rounded bg-white">${p.severity}</span>
          </div>
          <p class="text-slate-700 leading-relaxed">${escapeHtml(p.description)}</p>
          <div class="pt-1 text-slate-800 font-medium">
            <span class="text-teal-800 font-bold">Recommended Legal Remedy:</span> ${escapeHtml(p.remedy)}
          </div>
        </div>
      `).join("");
    }
  }
}

// -------------------------------------------------------------
// PANE 7: CA & LEGAL ADVISOR PORTAL
// -------------------------------------------------------------
function renderAdvisorPane() {
  const noteList = document.getElementById("advisor-notes-list");
  if (!noteList) return;

  if (state.advisorNotes.length === 0) {
    noteList.innerHTML = `<div class="text-center py-8 text-slate-400 text-sm">No advisory audit notes recorded yet.</div>`;
    return;
  }

  noteList.innerHTML = state.advisorNotes.map(n => `
    <div class="p-4 rounded-xl border ${n.severity === 'critical' ? 'border-red-200 bg-red-50/30' : 'border-amber-200 bg-amber-50/30'} shadow-sm space-y-2">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-teal-100 text-teal-800 font-bold flex items-center justify-center text-xs">
            CA
          </div>
          <div>
            <div class="font-bold text-slate-800 text-xs">${escapeHtml(n.author_name)}</div>
            <div class="text-[10px] text-slate-500">${escapeHtml(n.author_role)} • ${new Date(n.created_at).toLocaleDateString()}</div>
          </div>
        </div>
        <span class="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${n.severity === 'critical' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}">
          ${n.severity}
        </span>
      </div>
      <p class="text-xs text-slate-700 leading-relaxed">${n.note_text}</p>
    </div>
  `).join("");
}

// -------------------------------------------------------------
// PANE 8: WILL & NOMINATION GAP TRACKER (Sarbati Devi Audit)
// -------------------------------------------------------------
function renderTrackerPane() {
  const tbody = document.getElementById("tracker-table-body");
  if (!tbody) return;

  const data = state.nominationTrackerData || [];

  // Update Summary Counts
  const alignedCount = data.filter(d => d.alignment_status === 'ALIGNED').length;
  const discCount = data.filter(d => d.alignment_status === 'DISCREPANCY').length;
  const missingNomCount = data.filter(d => d.alignment_status === 'MISSING_NOMINEE').length;
  const missingWillCount = data.filter(d => d.alignment_status === 'MISSING_WILL_BEQUEST' || d.alignment_status === 'UNPROTECTED').length;

  const elAligned = document.getElementById("tracker-stat-aligned");
  const elDisc = document.getElementById("tracker-stat-discrepancy");
  const elMissingNom = document.getElementById("tracker-stat-missing-nom");
  const elMissingWill = document.getElementById("tracker-stat-missing-will");

  if (elAligned) elAligned.innerText = alignedCount;
  if (elDisc) elDisc.innerText = discCount;
  if (elMissingNom) elMissingNom.innerText = missingNomCount;
  if (elMissingWill) elMissingWill.innerText = missingWillCount;

  // Filter items
  let filtered = data;
  if (state.trackerFilter && state.trackerFilter !== 'all') {
    filtered = data.filter(d => d.alignment_status === state.trackerFilter);
  }

  // Update filter buttons styling
  const filterBtns = [
    { key: 'all', id: 'tracker-filter-all' },
    { key: 'DISCREPANCY', id: 'tracker-filter-discrepancy' },
    { key: 'MISSING_NOMINEE', id: 'tracker-filter-missing-nom' },
    { key: 'MISSING_WILL_BEQUEST', id: 'tracker-filter-missing-will' },
    { key: 'ALIGNED', id: 'tracker-filter-aligned' }
  ];

  filterBtns.forEach(f => {
    const btn = document.getElementById(f.id);
    if (btn) {
      if ((state.trackerFilter || 'all') === f.key) {
        btn.className = "px-3 py-1.5 rounded-lg text-xs font-bold bg-teal-800 text-white cursor-pointer shadow-xs";
      } else {
        btn.className = "px-3 py-1.5 rounded-lg text-xs font-bold bg-stone-100 hover:bg-stone-200 text-stone-700 cursor-pointer";
      }
    }
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center py-8 text-stone-400">
          No estate assets found matching this filter criteria.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered.map(item => {
    let statusPill = "";
    if (item.alignment_status === "ALIGNED") {
      statusPill = `<span class="px-2 py-0.5 rounded text-[10px] font-extrabold bg-emerald-100 text-emerald-800 border border-emerald-200">✓ ALIGNED</span>`;
    } else if (item.alignment_status === "DISCREPANCY") {
      statusPill = `<span class="px-2 py-0.5 rounded text-[10px] font-extrabold bg-rose-100 text-rose-800 border border-rose-200">⚠️ CONFLICT</span>`;
    } else if (item.alignment_status === "MISSING_NOMINEE") {
      statusPill = `<span class="px-2 py-0.5 rounded text-[10px] font-extrabold bg-amber-100 text-amber-800 border border-amber-200">NO NOMINEE</span>`;
    } else if (item.alignment_status === "MISSING_WILL_BEQUEST") {
      statusPill = `<span class="px-2 py-0.5 rounded text-[10px] font-extrabold bg-blue-100 text-blue-800 border border-blue-200">NO WILL CLAUSE</span>`;
    } else {
      statusPill = `<span class="px-2 py-0.5 rounded text-[10px] font-extrabold bg-slate-100 text-slate-700">UNPROTECTED</span>`;
    }

    let vaultBadge = "";
    if (item.vault_document_status === "UPDATED") {
      vaultBadge = `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">🟢 Verified</span>`;
    } else if (item.vault_document_status === "REVIEW_REQUIRED") {
      vaultBadge = `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">🟡 Review</span>`;
    } else {
      vaultBadge = `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-800 border border-rose-200">🔴 Missing</span>`;
    }

    let willBeneList = item.beneficiaries && item.beneficiaries.length > 0
      ? item.beneficiaries.map(b => `<div class="font-bold text-teal-800">${escapeHtml(b.name)} <span class="text-[10px] font-normal text-stone-500">(${b.share_percentage}%)</span></div>`).join("")
      : `<span class="text-stone-400 italic">None Assigned</span>`;

    return `
      <tr class="hover:bg-stone-50/60 transition">
        <td class="p-3.5">
          <div class="font-bold text-stone-900">${escapeHtml(item.title)}</div>
          <div class="text-[10px] text-stone-500 uppercase">${escapeHtml(item.category.replace('_', ' '))} • ${escapeHtml(item.acquisition_type.replace('_', ' '))}</div>
        </td>
        <td class="p-3.5 font-bold font-mono text-stone-900 whitespace-nowrap">
          ${formatINR(item.estimated_value_inr)}
        </td>
        <td class="p-3.5">
          <div class="font-bold text-stone-800">${escapeHtml(item.current_nominee_name)}</div>
          <div class="text-[10px] text-stone-500">${escapeHtml(item.nominee_relationship)}</div>
        </td>
        <td class="p-3.5">
          ${willBeneList}
        </td>
        <td class="p-3.5 whitespace-nowrap">
          ${vaultBadge}
        </td>
        <td class="p-3.5">
          ${statusPill}
          <div class="text-[10px] text-stone-500 mt-0.5 max-w-[130px] leading-tight">${escapeHtml(item.status_desc)}</div>
        </td>
        <td class="p-3.5 max-w-xs">
          <p class="text-[11px] text-stone-700 leading-snug font-medium">${escapeHtml(item.remedy)}</p>
          <div class="text-[10px] text-rose-700/80 mt-1">${escapeHtml(item.legal_risk)}</div>
        </td>
      </tr>
    `;
  }).join("");
}

function filterTracker(filterType) {
  state.trackerFilter = filterType;
  renderTrackerPane();
}

// -------------------------------------------------------------
// PANE 9: AI FAMILY LEGACY ADVISOR CHAT & MARKDOWN PARSER
// -------------------------------------------------------------
function formatAdvisorMarkdown(text) {
  if (!text) return "";

  // Normalize whitespace & narrow spaces that sometimes come from LLMs
  let cleaned = text.replace(/[\u202f\u00a0]/g, " ").replace(/\r\n/g, "\n").replace(/\r/g, "\n");

  // 1. If marked.js is available (loaded via CDN), use it with GFM and line breaks
  if (typeof marked !== "undefined" && typeof marked.parse === "function") {
    try {
      marked.setOptions({
        gfm: true,
        breaks: true
      });
      let html = marked.parse(cleaned);
      // Ensure tables are wrapped in a responsive scrollable container
      html = html.replace(/<table>/g, '<div class="overflow-x-auto my-2.5"><table>').replace(/<\/table>/g, '</table></div>');
      return html;
    } catch (e) {
      console.warn("Marked parser failed, falling back to built-in parser:", e);
    }
  }

  // 2. Comprehensive built-in Markdown Parser
  // First, extract and format tables
  cleaned = cleaned.replace(/(?:^|\n)(\|.+?\|\n\|[-:| ]+?\|\n(?:\|.+?\|\n?)+)/g, function(match, tableBlock) {
    const lines = tableBlock.trim().split("\n");
    if (lines.length < 3) return match;
    const headerCells = lines[0].split("|").filter((c, i, a) => i > 0 && i < a.length - 1).map(c => c.trim());
    const rowLines = lines.slice(2);

    let html = '<div class="overflow-x-auto my-2.5"><table><thead><tr>';
    headerCells.forEach(h => { html += `<th>${formatInlineMarkdown(h)}</th>`; });
    html += '</tr></thead><tbody>';
    rowLines.forEach(r => {
      const cells = r.split("|").filter((c, i, a) => i > 0 && i < a.length - 1).map(c => c.trim());
      html += '<tr>';
      cells.forEach(c => { html += `<td>${formatInlineMarkdown(c)}</td>`; });
      html += '</tr>';
    });
    html += '</tbody></table></div>';
    return "\n" + html + "\n";
  });

  // Process line by line
  const lines = cleaned.split("\n");
  let out = [];
  let inUl = false;
  let inOl = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Already-generated HTML blocks (e.g. table)
    if (line.includes("<table") || line.includes("</table>") || line.includes("<tr>") || line.includes("<td>") || line.includes("<th>")) {
      if (inUl) { out.push("</ul>"); inUl = false; }
      if (inOl) { out.push("</ol>"); inOl = false; }
      out.push(line);
      continue;
    }

    // Unordered lists (- or * or •)
    let ulMatch = line.match(/^(\s*)[-*•]\s+(.+)$/);
    if (ulMatch) {
      if (inOl) { out.push("</ol>"); inOl = false; }
      if (!inUl) { out.push('<ul>'); inUl = true; }
      out.push(`<li>${formatInlineMarkdown(ulMatch[2])}</li>`);
      continue;
    }

    // Ordered lists (1. or 1))
    let olMatch = line.match(/^(\s*)\d+[.)]\s+(.+)$/);
    if (olMatch) {
      if (inUl) { out.push("</ul>"); inUl = false; }
      if (!inOl) { out.push('<ol>'); inOl = true; }
      out.push(`<li>${formatInlineMarkdown(olMatch[2])}</li>`);
      continue;
    }

    // Close any active lists
    if (inUl) { out.push("</ul>"); inUl = false; }
    if (inOl) { out.push("</ol>"); inOl = false; }

    let trimmed = line.trim();
    if (!trimmed) continue;

    // Headings
    if (trimmed.startsWith("#### ")) {
      out.push(`<h4>${formatInlineMarkdown(trimmed.substring(5))}</h4>`);
    } else if (trimmed.startsWith("### ")) {
      out.push(`<h3>${formatInlineMarkdown(trimmed.substring(4))}</h3>`);
    } else if (trimmed.startsWith("## ")) {
      out.push(`<h2>${formatInlineMarkdown(trimmed.substring(3))}</h2>`);
    } else if (trimmed.startsWith("# ")) {
      out.push(`<h1>${formatInlineMarkdown(trimmed.substring(2))}</h1>`);
    } else if (trimmed.startsWith("> ")) {
      out.push(`<blockquote>${formatInlineMarkdown(trimmed.substring(2))}</blockquote>`);
    } else if (trimmed === "---" || trimmed === "***") {
      out.push('<hr/>');
    } else {
      out.push(`<p>${formatInlineMarkdown(trimmed)}</p>`);
    }
  }

  if (inUl) out.push("</ul>");
  if (inOl) out.push("</ol>");

  return out.join("\n");
}

function formatInlineMarkdown(str) {
  if (!str) return "";
  return escapeHtml(str)
    .replace(/&lt;br\s*\/?&gt;/gi, '<br/>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

function renderLegacyAdvisorPane() {
  const stream = document.getElementById("advisor-chat-stream");
  if (!stream) return;

  if (!state.advisorChatMessages || state.advisorChatMessages.length === 0) {
    const kartaName = state.currentProfile ? state.currentProfile.karta_name : "User";
    const bizName = state.currentProfile ? state.currentProfile.business_name : "Your Business";
    state.advisorChatMessages = [{
      role: "assistant",
      content: `Namaste **${kartaName} ji**! I am your **AI Family Legacy & Succession Advisor**, specialized in Indian personal laws (*Hindu Succession Act 1956/2005*, *Shariat*, *Indian Succession Act 1925*, and *Indian Partnership Act 1932*).\n\nI have reviewed your active family estate (**${bizName}**, valued at **${state.simulationData ? formatINR(state.simulationData.total_asset_value_inr) : '₹0'}** with **${state.members ? state.members.length : 0} members**).\n\nClick any suggested query above or ask about your family's assets, nominees, daughter coparcenary shares, or SRO will registration!`,
      action_items: [
        "Audit existing bank nominees against your will draft",
        "Verify partnership deed continuation clause under Section 42(c)",
        "Schedule an SRO appointment for Book 3 will registration"
      ],
      suggested_followups: [
        "What are our nominee discrepancies and biggest gaps?",
        "What are the rights of daughters under Hindu coparcenary law?",
        "How do we protect our business from dissolving?"
      ]
    }];
  }

  stream.innerHTML = state.advisorChatMessages.map(msg => {
    const isUser = msg.role === "user";
    if (isUser) {
      return `
        <div class="flex justify-end">
          <div class="bg-teal-800 text-white rounded-2xl rounded-tr-xs px-4 py-2.5 max-w-lg text-xs shadow-xs font-medium">
            ${escapeHtml(msg.content)}
          </div>
        </div>
      `;
    } else {
      let formatted = formatAdvisorMarkdown(msg.content);

      let actionPills = "";
      if (msg.action_items && msg.action_items.length > 0) {
        actionPills = `
          <div class="mt-3.5 pt-2.5 border-t border-stone-200">
            <div class="text-[10px] font-bold uppercase tracking-wider text-teal-800 mb-1.5 flex items-center gap-1">
              <span>🎯</span><span>Actionable Next Steps:</span>
            </div>
            <div class="space-y-1.5">
              ${msg.action_items.map(a => `
                <div class="flex items-start gap-2 text-xs font-semibold text-teal-950 bg-teal-50/90 px-3 py-2 rounded-lg border border-teal-200/70 shadow-2xs">
                  <span class="text-teal-700 font-bold shrink-0 mt-0.5">✓</span>
                  <span class="leading-snug">${escapeHtml(a)}</span>
                </div>
              `).join("")}
            </div>
          </div>
        `;
      }

      let followupBtns = "";
      if (msg.suggested_followups && msg.suggested_followups.length > 0) {
        followupBtns = `
          <div class="mt-3.5 pt-2.5 border-t border-stone-100 flex items-center gap-1.5 flex-wrap">
            <span class="text-[10px] font-bold text-stone-400 uppercase tracking-wider">Ask Next:</span>
            ${msg.suggested_followups.map(f => `
              <button onclick="askAdvisorQuery('${escapeHtml(f).replace(/'/g, "\\'")}')" class="px-3 py-1 rounded-full bg-stone-100 hover:bg-teal-50 hover:text-teal-900 hover:border-teal-300 border border-stone-200 text-stone-700 text-[11px] font-semibold transition cursor-pointer shadow-2xs">
                ${escapeHtml(f)} &rarr;
              </button>
            `).join("")}
          </div>
        `;
      }

      let providerBadge = "";
      if (msg.ai_provider) {
        providerBadge = `<span class="text-[9px] px-2.5 py-0.5 rounded-full bg-teal-100 text-teal-800 font-bold border border-teal-300 shadow-2xs">⚡ ${escapeHtml(msg.ai_provider)}</span>`;
      }

      return `
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-amber-100 to-amber-200 text-amber-900 font-black flex items-center justify-center text-sm border border-amber-300 shadow-xs shrink-0 mt-0.5">
            ⚖️
          </div>
          <div class="bg-white border border-stone-200 rounded-2xl rounded-tl-xs p-4 sm:p-5 max-w-3xl w-full text-xs shadow-xs space-y-2">
            <div class="flex items-center justify-between pb-2 border-b border-stone-200/80">
              <span class="font-bold text-stone-800 text-[12px] flex items-center gap-1.5">
                <span>Waaris AI Legal Advisor</span>
              </span>
              ${providerBadge}
            </div>
            <div class="advisor-markdown text-stone-800 leading-relaxed">${formatted}</div>
            ${actionPills}
            ${followupBtns}
          </div>
        </div>
      `;
    }
  }).join("");

  stream.scrollTop = stream.scrollHeight;
}

async function askAdvisorQuery(question) {
  if (!question || !question.trim()) return;
  state.advisorChatMessages.push({ role: "user", content: question });
  renderLegacyAdvisorPane();

  const stream = document.getElementById("advisor-chat-stream");
  const loadingId = "advisor-loading-msg";
  if (stream) {
    const loadingEl = document.createElement("div");
    loadingEl.id = loadingId;
    loadingEl.className = "flex items-start gap-3";
    loadingEl.innerHTML = `
      <div class="w-8 h-8 rounded-full bg-amber-100 text-amber-900 font-bold flex items-center justify-center text-sm border border-amber-300 shrink-0">
        ⚖️
      </div>
      <div class="bg-stone-50 border border-stone-200 rounded-2xl p-3 text-xs text-stone-500 font-medium flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-teal-600 animate-ping"></span>
        <span>AI Advisor analyzing family records under Indian Succession Act...</span>
      </div>
    `;
    stream.appendChild(loadingEl);
    stream.scrollTop = stream.scrollHeight;
  }

  try {
    const res = await apiFetch(`/api/legacy-advisor/${state.currentProfileId}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: question })
    });
    const data = await res.json();
    document.getElementById(loadingId)?.remove();
    state.advisorChatMessages.push({
      role: "assistant",
      content: data.answer,
      action_items: data.action_items,
      suggested_followups: data.suggested_followups,
      ai_provider: data.ai_provider,
      api_key_note: data.api_key_note
    });
    renderLegacyAdvisorPane();
  } catch (err) {
    document.getElementById(loadingId)?.remove();
    state.advisorChatMessages.push({
      role: "assistant",
      content: `I encountered an issue analyzing your records: ${err.message}. Please check your connection or try again.`,
      action_items: [],
      suggested_followups: []
    });
    renderLegacyAdvisorPane();
  }
}

function handleAdvisorSubmit(e) {
  e.preventDefault();
  const input = document.getElementById("advisor-user-input");
  if (!input) return;
  const q = input.value.trim();
  if (q) {
    input.value = "";
    askAdvisorQuery(q);
  }
}

function clearAdvisorChat() {
  state.advisorChatMessages = [];
  renderLegacyAdvisorPane();
}

// -------------------------------------------------------------
// ACTIONS & MODALS
// -------------------------------------------------------------
function openAddMemberModal() {
  const form = document.getElementById("add-member-form");
  if (form) form.reset();
  const ageEl = document.getElementById("mem-age");
  if (ageEl) ageEl.value = "";
  document.getElementById("add-member-modal")?.classList.remove("hidden");
}

function closeAddMemberModal() {
  document.getElementById("add-member-modal")?.classList.add("hidden");
}

async function saveFamilyMember(event) {
  event.preventDefault();
  const ageVal = document.getElementById("mem-age").value;
  if (!ageVal || isNaN(parseInt(ageVal)) || parseInt(ageVal) < 0) {
    const l = i18n[state.currentLang] || i18n.en;
    showToast(l.errAgeMember || "Please enter a valid age for the family member", "error");
    document.getElementById("mem-age")?.focus();
    return;
  }
  const payload = {
    profile_id: state.currentProfileId,
    name: document.getElementById("mem-name").value,
    relation: document.getElementById("mem-relation").value,
    gender: document.getElementById("mem-gender").value,
    age: parseInt(ageVal),
    marital_status: document.getElementById("mem-marital").value,
    notes: document.getElementById("mem-notes").value
  };

  try {
    const res = await apiFetch(`/api/family/${state.currentProfileId}/member`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to add member");
    }
    await refreshFamily();
    await refreshSimulation();
    populateSimulatorSelects();
    closeAddMemberModal();
    renderActiveTab();
    showToast(`Family member ${payload.name} added successfully!`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteMember(memberId) {
  if (!confirm("Are you sure you want to remove this family member?")) return;
  try {
    const res = await apiFetch(`/api/family/${state.currentProfileId}/member/${memberId}`, {
      method: "DELETE"
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to delete");
    }
    await refreshFamily();
    await refreshSimulation();
    populateSimulatorSelects();
    renderActiveTab();
    showToast("Family member removed", "info");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Assets Handlers
function openAddAssetModal() {
  document.getElementById("add-asset-form")?.reset();
  document.getElementById("add-asset-modal")?.classList.remove("hidden");
}

function closeAddAssetModal() {
  document.getElementById("add-asset-modal")?.classList.add("hidden");
}

async function saveAsset(event) {
  event.preventDefault();
  const payload = {
    profile_id: state.currentProfileId,
    title: document.getElementById("ast-title").value,
    category: document.getElementById("ast-category").value,
    estimated_value_inr: parseFloat(document.getElementById("ast-value").value) || 0,
    identifier_number: document.getElementById("ast-identifier").value,
    location_or_institution: document.getElementById("ast-location").value,
    acquisition_type: document.getElementById("ast-acq").value,
    current_nominee_name: document.getElementById("ast-nominee").value,
    nominee_relationship: document.getElementById("ast-nominee-rel").value,
    description: document.getElementById("ast-desc").value
  };

  try {
    const res = await apiFetch(`/api/assets/${state.currentProfileId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to add asset");
    }
    await refreshAssets();
    await refreshSimulation();
    populateSimulatorSelects();
    closeAddAssetModal();
    renderActiveTab();
    showToast(`Asset "${payload.title}" recorded!`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteAsset(assetId) {
  if (!confirm("Are you sure you want to remove this asset?")) return;
  try {
    const res = await apiFetch(`/api/assets/${state.currentProfileId}/${assetId}`, {
      method: "DELETE"
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to delete asset");
    }
    await refreshAssets();
    await refreshSimulation();
    populateSimulatorSelects();
    renderActiveTab();
    showToast("Asset removed", "info");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Allocation Handlers
let currentAllocatingAssetId = null;

function openAllocationModal(assetId) {
  currentAllocatingAssetId = assetId;
  const asset = state.assets.find(a => a.id === assetId);
  if (!asset) return;

  document.getElementById("alloc-asset-title").innerText = asset.title;
  document.getElementById("alloc-asset-value").innerText = formatINR(asset.estimated_value_inr);

  const beneSelect = document.getElementById("alloc-beneficiary");
  beneSelect.innerHTML = "";
  state.members.filter(m => m.relation.toLowerCase() !== "self").forEach(m => {
    const opt = document.createElement("option");
    opt.value = m.id;
    opt.innerText = `${m.name} (${escapeHtml(m.relation)})`;
    beneSelect.appendChild(opt);
  });

  document.getElementById("alloc-share-pct").value = 100;
  document.getElementById("alloc-instructions").value = "";
  document.getElementById("allocation-modal")?.classList.remove("hidden");
}

function closeAllocationModal() {
  document.getElementById("allocation-modal")?.classList.add("hidden");
}

async function saveAllocation(event) {
  event.preventDefault();
  if (!currentAllocatingAssetId) return;

  const payload = {
    profile_id: state.currentProfileId,
    asset_id: currentAllocatingAssetId,
    beneficiary_id: parseInt(document.getElementById("alloc-beneficiary").value),
    share_percentage: parseFloat(document.getElementById("alloc-share-pct").value) || 100,
    special_instructions: document.getElementById("alloc-instructions").value
  };

  try {
    const res = await apiFetch(`/api/allocations/${state.currentProfileId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to save allocation");
    }
    await refreshAllocations();
    await refreshSimulation();
    closeAllocationModal();
    renderActiveTab();
    showToast("Bequest successfully assigned!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Will Draft Handlers
async function saveWillDraftData(event) {
  event.preventDefault();
  const payload = {
    profile_id: state.currentProfileId,
    executor_name: document.getElementById("will-executor-name").value,
    executor_relationship: document.getElementById("will-executor-rel").value,
    alternate_executor_name: document.getElementById("will-alt-executor").value,
    guardian_minor_name: document.getElementById("will-guardian").value,
    witness1_name: document.getElementById("will-witness1-name").value,
    witness1_address: document.getElementById("will-witness1-addr").value,
    witness2_name: document.getElementById("will-witness2-name").value,
    witness2_address: document.getElementById("will-witness2-addr").value,
    doctor_name: document.getElementById("will-doc-name").value,
    doctor_reg_no: document.getElementById("will-doc-reg").value,
    original_physical_location: document.getElementById("will-vault-loc").value,
    sub_registrar_office: document.getElementById("will-sro-office").value,
    status: "reviewed_by_ca"
  };

  try {
    const res = await apiFetch(`/api/will/${state.currentProfileId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to update will draft");
    }
    await refreshWillDraft();
    renderActiveTab();
    showToast("Will Draft details updated successfully!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

function downloadWillPDF() {
  const tokenParam = state.authToken ? `?token=${encodeURIComponent(state.authToken)}` : '';
  window.open(`/api/will/${state.currentProfileId}/pdf${tokenParam}`, "_blank");
  showToast("Generating formal legal PDF with ReportLab...", "info");
}

// SRO Guide Modal
async function openSROGuideModal() {
  try {
    const res = await fetch("/api/sro-guide");
    const data = await res.json();
    const content = document.getElementById("sro-modal-content");
    content.innerHTML = `
      <div class="space-y-4">
        <div class="grid grid-cols-2 gap-2 text-xs">
          ${data.key_facts.map(f => `
            <div class="p-2.5 rounded-lg bg-teal-50 border border-teal-100">
              <span class="font-bold text-teal-900 block">${f.label}</span>
              <span class="text-slate-600">${f.value}</span>
            </div>
          `).join("")}
        </div>

        <div class="font-bold text-slate-800 text-sm mt-3">Step-by-Step Procedure at Sub-Registrar Office:</div>
        <div class="space-y-2 text-xs">
          ${data.step_by_step_checklist.map(s => `
            <div class="p-3 rounded-lg border border-slate-200 bg-white">
              <div class="font-bold text-slate-800">Step ${s.step}: ${s.title}</div>
              <p class="text-slate-600 mt-1">${s.desc}</p>
            </div>
          `).join("")}
        </div>
      </div>
    `;
    document.getElementById("sro-modal")?.classList.remove("hidden");
  } catch (err) {
    console.error(err);
  }
}

function closeSROModal() {
  document.getElementById("sro-modal")?.classList.add("hidden");
}

// Member Details Modal (Rich Portfolio & Statutory Breakdown)
async function showMemberDetailsModal(member) {
  const modal = document.getElementById("member-details-modal");
  const content = document.getElementById("member-modal-content");
  if (!modal || !content) return;

  // Initial loader
  content.innerHTML = `
    <div class="py-8 text-center text-stone-500 text-xs flex items-center justify-center gap-2">
      <span class="w-3 h-3 rounded-full bg-teal-600 animate-ping"></span>
      <span>Loading statutory portfolio & rights for ${escapeHtml(member.name)}...</span>
    </div>
  `;
  modal.classList.remove("hidden");

  try {
    const res = await apiFetch(`/api/family/${state.currentProfileId}/member-detail/${member.id}`);
    const data = await res.json();
    const m = data.member;

    let bequestsHtml = "";
    if (data.assigned_bequests && data.assigned_bequests.length > 0) {
      bequestsHtml = `
        <ul class="space-y-1.5 mt-1">
          ${data.assigned_bequests.map(b => `
            <li class="p-2.5 rounded-lg bg-teal-50/60 border border-teal-200/80 flex items-center justify-between text-xs">
              <div>
                <strong class="text-stone-900">${escapeHtml(b.asset_title)}</strong>
                <span class="text-[10px] text-stone-500 block uppercase">${escapeHtml(b.category.replace('_', ' '))} • ${b.share_percentage}% allocation</span>
              </div>
              <span class="font-bold font-mono text-teal-800 text-xs">${formatINR(b.value_inr)}</span>
            </li>
          `).join("")}
        </ul>
      `;
    } else {
      bequestsHtml = `<div class="text-stone-400 italic text-xs py-1">No specific assets bequeathed in current will draft.</div>`;
    }

    let nominatedHtml = "";
    if (data.nominated_assets && data.nominated_assets.length > 0) {
      nominatedHtml = `
        <ul class="space-y-1.5 mt-1">
          ${data.nominated_assets.map(n => `
            <li class="p-2.5 rounded-lg bg-amber-50/60 border border-amber-200/80 flex items-center justify-between text-xs">
              <div>
                <strong class="text-stone-900">${escapeHtml(n.title)}</strong>
                <span class="text-[10px] text-stone-500 block uppercase">Recorded Nominee (${escapeHtml(n.nominee_relationship || 'Nominee')})</span>
              </div>
              <span class="font-bold font-mono text-amber-900 text-xs">${formatINR(n.estimated_value_inr)}</span>
            </li>
          `).join("")}
        </ul>
      `;
    } else {
      nominatedHtml = `<div class="text-stone-400 italic text-xs py-1">No bank accounts or assets directly nominate this member.</div>`;
    }

    content.innerHTML = `
      <div class="space-y-3.5 text-xs">
        <div class="flex items-center justify-between pb-3 border-b border-stone-100">
          <div>
            <div class="text-base font-bold text-stone-900">${escapeHtml(m.name)}</div>
            <div class="text-stone-500 text-xs">${escapeHtml(m.relation)} • ${escapeHtml(m.gender)} • ${m.age} yrs • ${escapeHtml(m.marital_status)}</div>
          </div>
          <span class="px-2.5 py-1 rounded-full text-[10px] font-extrabold ${m.is_class_1_heir ? 'bg-blue-100 text-blue-900 border border-blue-200' : 'bg-stone-100 text-stone-700'}">
            ${escapeHtml(data.statutory_class)}
          </span>
        </div>

        <!-- Statutory & Coparcenary Status Card -->
        <div class="p-3 rounded-xl bg-stone-50 border border-stone-200 text-stone-700 space-y-1 text-xs">
          <div><strong>Coparcenary Status:</strong> ${escapeHtml(data.coparcenary_rights)}</div>
          <div><strong>Statutory Intestate Share:</strong> <span class="font-bold text-stone-900">${data.statutory_intestate_share_pct}%</span> (~<span class="font-bold font-mono text-teal-800">${formatINR(data.statutory_intestate_inr)}</span> if intestate).</div>
          ${m.notes ? `<div><strong>Notes:</strong> ${escapeHtml(m.notes)}</div>` : ''}
        </div>

        <!-- Assigned Will Bequests -->
        <div>
          <div class="flex items-center justify-between font-bold text-stone-800 text-xs">
            <span>📜 Assigned Will Bequests</span>
            <span class="font-mono text-teal-800 font-bold">${formatINR(data.total_bequest_inr)}</span>
          </div>
          ${bequestsHtml}
        </div>

        <!-- Institutional Nominations -->
        <div>
          <div class="font-bold text-stone-800 text-xs">
            <span>🏦 Accounts Nominated To This Member</span>
          </div>
          ${nominatedHtml}
        </div>

        <!-- Action Footer -->
        <div class="pt-3 border-t border-stone-200 flex items-center justify-between">
          <button type="button" onclick="closeMemberDetailsModal()" class="px-3 py-1.5 rounded-xl border border-stone-300 text-stone-600 font-semibold hover:bg-stone-50 text-xs cursor-pointer">Close</button>
          ${state.activeRole !== 'heir' ? (m.relation.toLowerCase() === 'self' ? 
            `<button type="button" onclick="closeMemberDetailsModal(); openEditProfileModal();" class="px-3.5 py-1.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs flex items-center gap-1 cursor-pointer"><span>✏️</span> Edit Karta</button>` :
            `<button type="button" onclick="closeMemberDetailsModal(); openEditMemberModal(${m.id});" class="px-3.5 py-1.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs flex items-center gap-1 cursor-pointer"><span>✏️</span> Edit Member</button>`
          ) : ''}
        </div>
      </div>
    `;
  } catch (err) {
    content.innerHTML = `
      <div class="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs">
        Failed to load member portfolio details: ${escapeHtml(err.message)}
      </div>
    `;
  }
}

function closeMemberDetailsModal() {
  document.getElementById("member-details-modal")?.classList.add("hidden");
}

// Advisor Notes Modal
function openAddNoteModal() {
  document.getElementById("add-note-modal")?.classList.remove("hidden");
}

function closeAddNoteModal() {
  document.getElementById("add-note-modal")?.classList.add("hidden");
}

async function saveAdvisorNote(event) {
  event.preventDefault();
  const payload = {
    profile_id: state.currentProfileId,
    author_name: document.getElementById("note-author-name").value,
    author_role: document.getElementById("note-author-role").value,
    category: document.getElementById("note-category").value,
    severity: document.getElementById("note-severity").value,
    note_text: document.getElementById("note-text").value
  };

  try {
    const res = await apiFetch(`/api/advisor-notes/${state.currentProfileId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to add note");
    }
    await refreshAdvisorNotes();
    closeAddNoteModal();
    renderActiveTab();
    showToast("Advisor Audit Note recorded!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// New Profile (Create Custom Plan)
function openNewProfileModal() {
  document.getElementById("new-profile-form")?.reset();
  document.getElementById("new-profile-modal")?.classList.remove("hidden");
}

function closeNewProfileModal() {
  document.getElementById("new-profile-modal")?.classList.add("hidden");
}

async function saveNewProfile(event) {
  event.preventDefault();
  const kartaAgeVal = document.getElementById("new-profile-karta-age")?.value;
  if (!kartaAgeVal || isNaN(parseInt(kartaAgeVal)) || parseInt(kartaAgeVal) < 18) {
    showToast("Please enter a valid age (18 or older) for Head of Family / Karta", "error");
    document.getElementById("new-profile-karta-age")?.focus();
    return;
  }

  const payload = {
    name: document.getElementById("new-profile-title").value,
    karta_name: document.getElementById("new-profile-karta").value,
    karta_age: parseInt(kartaAgeVal),
    karta_gender: document.getElementById("new-profile-karta-gender")?.value || "Male",
    karta_marital_status: document.getElementById("new-profile-karta-marital")?.value || "Married",
    business_name: document.getElementById("new-profile-biz").value,
    business_type: document.getElementById("new-profile-biz-type").value,
    city: document.getElementById("new-profile-city").value,
    state: document.getElementById("new-profile-state").value,
    pan_or_gstin: document.getElementById("new-profile-gstin").value || null,
    governing_law: document.getElementById("new-profile-law").value
  };

  try {
    const res = await apiFetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create profile");
    }
    const created = await res.json();
    closeNewProfileModal();
    await loadScenarios();
    await switchScenario(created.id);
    selectTab("family");
    showToast(`Welcome ${created.karta_name}! Your custom estate plan is created. Add your family members below.`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Edit Existing Profile
function openEditProfileModal() {
  if (!state.currentProfile) return;
  document.getElementById("edit-profile-title").value = state.currentProfile.name || "";
  document.getElementById("edit-profile-karta").value = state.currentProfile.karta_name || "";
  const kartaMember = (state.members || []).find(m => (m.relation || "").toLowerCase() === "self");
  const ageEl = document.getElementById("edit-profile-karta-age");
  if (ageEl) ageEl.value = kartaMember ? kartaMember.age : "";
  document.getElementById("edit-profile-biz").value = state.currentProfile.business_name || "";
  document.getElementById("edit-profile-biz-type").value = state.currentProfile.business_type || "Sole Proprietorship";
  document.getElementById("edit-profile-city").value = state.currentProfile.city || "";
  document.getElementById("edit-profile-state").value = state.currentProfile.state || "";
  document.getElementById("edit-profile-gstin").value = state.currentProfile.pan_or_gstin || "";
  document.getElementById("edit-profile-modal")?.classList.remove("hidden");
}

function closeEditProfileModal() {
  document.getElementById("edit-profile-modal")?.classList.add("hidden");
}

async function saveEditProfile(event) {
  event.preventDefault();
  const kartaAgeVal = document.getElementById("edit-profile-karta-age")?.value;
  const payload = {
    name: document.getElementById("edit-profile-title").value,
    karta_name: document.getElementById("edit-profile-karta").value,
    karta_age: kartaAgeVal ? parseInt(kartaAgeVal) : null,
    business_name: document.getElementById("edit-profile-biz").value,
    business_type: document.getElementById("edit-profile-biz-type").value,
    city: document.getElementById("edit-profile-city").value,
    state: document.getElementById("edit-profile-state").value,
    pan_or_gstin: document.getElementById("edit-profile-gstin").value || null
  };

  try {
    const res = await apiFetch(`/api/profile/${state.currentProfileId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to update profile");
    }
    closeEditProfileModal();
    await loadScenarios();
    await switchScenario(state.currentProfileId);
    showToast("Estate details updated successfully!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteCurrentProfile() {
  if (!state.currentProfile) return;
  if (!confirm(`Are you sure you want to delete the plan: "${state.currentProfile.name}"?`)) return;

  try {
    const res = await apiFetch(`/api/profile/${state.currentProfileId}`, { method: "DELETE" });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Cannot delete this profile");
    }
    const data = await res.json();
    showToast("Estate profile deleted", "info");
    await loadScenarios();
    if (data.next_profile_id) {
      await switchScenario(data.next_profile_id);
    } else {
      await switchScenario(1);
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Quick Add Member / Edit Member
function quickAddMember(relation, gender) {
  openAddMemberModal();
  const relSelect = document.getElementById("mem-relation");
  const genSelect = document.getElementById("mem-gender");
  if (relSelect) relSelect.value = relation;
  if (genSelect) genSelect.value = gender;
  document.getElementById("mem-name")?.focus();
}

function openEditMemberModal(memberId) {
  const m = state.members.find(x => x.id === memberId);
  if (!m) return;
  document.getElementById("edit-mem-id").value = m.id;
  document.getElementById("edit-mem-name").value = m.name;
  document.getElementById("edit-mem-relation").value = m.relation;
  document.getElementById("edit-mem-gender").value = m.gender;
  document.getElementById("edit-mem-age").value = m.age;
  document.getElementById("edit-mem-marital").value = m.marital_status || "Married";
  document.getElementById("edit-mem-notes").value = m.notes || "";
  document.getElementById("edit-member-modal")?.classList.remove("hidden");
}

function closeEditMemberModal() {
  document.getElementById("edit-member-modal")?.classList.add("hidden");
}

async function saveEditMember(event) {
  event.preventDefault();
  const memId = parseInt(document.getElementById("edit-mem-id").value);
  const ageVal = document.getElementById("edit-mem-age").value;
  if (!ageVal || isNaN(parseInt(ageVal)) || parseInt(ageVal) < 0) {
    const l = i18n[state.currentLang] || i18n.en;
    showToast(l.errAgeKarta || "Please enter a valid age", "error");
    document.getElementById("edit-mem-age")?.focus();
    return;
  }
  const payload = {
    name: document.getElementById("edit-mem-name").value,
    relation: document.getElementById("edit-mem-relation").value,
    gender: document.getElementById("edit-mem-gender").value,
    age: parseInt(ageVal),
    marital_status: document.getElementById("edit-mem-marital").value,
    notes: document.getElementById("edit-mem-notes").value
  };

  try {
    const res = await apiFetch(`/api/family/${state.currentProfileId}/member/${memId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to update member");
    }
    await refreshFamily();
    await refreshSimulation();
    populateSimulatorSelects();
    closeEditMemberModal();
    renderActiveTab();
    showToast(`Member "${payload.name}" updated!`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Quick Add Asset / Edit Asset
function quickAddAsset(category) {
  openAddAssetModal();
  const catSelect = document.getElementById("ast-category");
  if (catSelect) catSelect.value = category;
  document.getElementById("ast-title")?.focus();
}

function openEditAssetModal(assetId) {
  const a = state.assets.find(x => x.id === assetId);
  if (!a) return;
  document.getElementById("edit-ast-id").value = a.id;
  document.getElementById("edit-ast-title").value = a.title;
  document.getElementById("edit-ast-category").value = a.category;
  document.getElementById("edit-ast-value").value = a.estimated_value_inr;
  document.getElementById("edit-ast-identifier").value = a.identifier_number || "";
  document.getElementById("edit-ast-location").value = a.location_or_institution || "";
  document.getElementById("edit-ast-acq").value = a.acquisition_type || "self_acquired";
  document.getElementById("edit-ast-nominee").value = a.current_nominee_name || "";
  document.getElementById("edit-ast-nominee-rel").value = a.nominee_relationship || "";
  document.getElementById("edit-ast-desc").value = a.description || "";
  document.getElementById("edit-asset-modal")?.classList.remove("hidden");
}

function closeEditAssetModal() {
  document.getElementById("edit-asset-modal")?.classList.add("hidden");
}

async function saveEditAsset(event) {
  event.preventDefault();
  const assetId = parseInt(document.getElementById("edit-ast-id").value);
  const payload = {
    title: document.getElementById("edit-ast-title").value,
    category: document.getElementById("edit-ast-category").value,
    estimated_value_inr: parseFloat(document.getElementById("edit-ast-value").value) || 0,
    identifier_number: document.getElementById("edit-ast-identifier").value,
    location_or_institution: document.getElementById("edit-ast-location").value,
    acquisition_type: document.getElementById("edit-ast-acq").value,
    current_nominee_name: document.getElementById("edit-ast-nominee").value,
    nominee_relationship: document.getElementById("edit-ast-nominee-rel").value,
    description: document.getElementById("edit-ast-desc").value
  };

  try {
    const res = await apiFetch(`/api/assets/${state.currentProfileId}/${assetId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to update asset");
    }
    await refreshAssets();
    await refreshSimulation();
    populateSimulatorSelects();
    closeEditAssetModal();
    renderActiveTab();
    showToast(`Asset "${payload.title}" updated!`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Event Handlers Setup
function setupEventHandlers() {
  const scenarioSelect = document.getElementById("scenario-select");
  if (scenarioSelect) {
    scenarioSelect.addEventListener("change", (e) => {
      switchScenario(parseInt(e.target.value));
    });
  }

  // Navigation tab clicks
  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      selectTab(tab.dataset.tab);
    });
  });

  // Role button clicks in top header
  document.querySelectorAll(".role-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      quickLoginRole(btn.dataset.role);
    });
  });

  // Forms submit
  document.getElementById("new-profile-form")?.addEventListener("submit", saveNewProfile);
  document.getElementById("edit-profile-form")?.addEventListener("submit", saveEditProfile);
  document.getElementById("edit-member-form")?.addEventListener("submit", saveEditMember);
  document.getElementById("edit-asset-form")?.addEventListener("submit", saveEditAsset);
  document.getElementById("add-member-form")?.addEventListener("submit", saveFamilyMember);
  document.getElementById("add-asset-form")?.addEventListener("submit", saveAsset);
  document.getElementById("allocation-form")?.addEventListener("submit", saveAllocation);
  document.getElementById("will-form")?.addEventListener("submit", saveWillDraftData);
  document.getElementById("vault-upload-form")?.addEventListener("submit", uploadVaultFile);
  document.getElementById("add-note-form")?.addEventListener("submit", saveAdvisorNote);
}

// =============================================================
// ASSET DISTRIBUTION DOUGHNUT CHART (DASHBOARD)
// =============================================================
let assetDonutChartInstance = null;

function renderAssetDistributionDonut() {
  const canvas = document.getElementById("asset-distribution-chart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // Use actual assets from state.assets
  const assets = (state.assets || []).filter(a => a.category !== 'liability_loan');
  
  const categoryMap = {
    commercial_shop: { name: "Commercial Shops & Stores", color: "#0f4b3d", value: 0 },
    residential_property: { name: "Residential Property", color: "#c59b27", value: 0 },
    agricultural_land: { name: "Farmland / Ancestral Land", color: "#166534", value: 0 },
    partnership_firm: { name: "Business & Partnership Shares", color: "#4f46e5", value: 0 },
    bank_fd: { name: "Bank Fixed Deposits", color: "#0d9488", value: 0 },
    savings_account: { name: "Savings & Liquid Funds", color: "#0284c7", value: 0 },
    demat_stocks: { name: "Demat & Mutual Funds", color: "#2563eb", value: 0 },
    demat_shares: { name: "Demat & Mutual Funds", color: "#2563eb", value: 0 },
    gold_jewellery: { name: "Gold & Jewellery", color: "#d97706", value: 0 },
    vehicle: { name: "Commercial & Personal Vehicles", color: "#64748b", value: 0 },
    other: { name: "Other Estate Assets", color: "#7c3aed", value: 0 }
  };

  let totalValue = 0;
  if (assets.length > 0) {
    assets.forEach(a => {
      const val = Number(a.estimated_value_inr) || 0;
      totalValue += val;
      if (categoryMap[a.category]) {
        categoryMap[a.category].value += val;
      } else {
        categoryMap.other.value += val;
      }
    });
  } else if (state.simulationData) {
    totalValue = state.simulationData.total_asset_value_inr || 0;
    categoryMap.commercial_shop.value = totalValue * 0.52;
    categoryMap.residential_property.value = totalValue * 0.24;
    categoryMap.gold_jewellery.value = totalValue * 0.12;
    categoryMap.bank_fd.value = totalValue * 0.08;
    categoryMap.vehicle.value = totalValue * 0.04;
  }

  const activeCategories = Object.values(categoryMap).filter(c => c.value > 0);
  const labels = activeCategories.map(c => c.name);
  const data = activeCategories.map(c => c.value);
  const colors = activeCategories.map(c => c.color);

  // Update center total text
  const centerEl = document.getElementById("dash-chart-center-total");
  if (centerEl) {
    centerEl.innerText = formatINR(totalValue);
  }

  // Populate dynamic asset breakdown legend
  const legendContainer = document.getElementById("dash-asset-legend-container");
  if (legendContainer) {
    if (activeCategories.length === 0) {
      legendContainer.innerHTML = `<div class="text-xs text-stone-400 py-4 text-center">No assets recorded yet.</div>`;
    } else {
      legendContainer.innerHTML = activeCategories.map(c => {
        const pct = totalValue > 0 ? ((c.value / totalValue) * 100).toFixed(1) : "0.0";
        return `
          <div class="flex items-center justify-between p-2 rounded-lg bg-stone-50/70 hover:bg-stone-100/80 transition border border-stone-100">
            <div class="flex items-center gap-2 min-w-0">
              <span class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: ${c.color}"></span>
              <span class="font-medium text-stone-800 truncate">${c.name}</span>
            </div>
            <div class="flex items-center gap-2 text-right flex-shrink-0 pl-2">
              <span class="font-mono font-semibold text-stone-700">${formatINR(c.value)}</span>
              <span class="text-[11px] font-bold text-stone-500 w-11 text-right">${pct}%</span>
            </div>
          </div>
        `;
      }).join("");
    }
  }

  if (assetDonutChartInstance) {
    assetDonutChartInstance.destroy();
  }

  assetDonutChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: "#ffffff",
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              const val = context.raw || 0;
              const pct = totalValue > 0 ? ((val / totalValue) * 100).toFixed(1) : 0;
              return ` ${context.label}: ${formatINR(val)} (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

// =============================================================
// PANORAMIC WALKING BANNER & 3D CHARACTER SPRITES ENGINE
// =============================================================
// Preload all 16 walk cycle frames into browser memory for 0ms instantaneous switching
const walkFrameAssets = {
  dada: [1, 2, 3, 4].map(n => { const i = new Image(); i.src = `/static/dada_walk_${n}.png`; return i; }),
  father: [1, 2, 3, 4].map(n => { const i = new Image(); i.src = `/static/father_walk_${n}.png`; return i; }),
  boy: [1, 2, 3, 4].map(n => { const i = new Image(); i.src = `/static/boy_walk_${n}.png`; return i; }),
  kid: [1, 2, 3, 4].map(n => { const i = new Image(); i.src = `/static/kid_walk_${n}.png`; return i; })
};

let walkingBannerState = {
  active: true,
  speedIndex: 0,
  speeds: [
    { label: "🚶 Normal Walk", mult: 1.0, moveSpeed: 0.026, cycleDuration: 1.10 },
    { label: "🏃 Brisk Stroll", mult: 1.45, moveSpeed: 0.040, cycleDuration: 0.80 }
  ],
  posPercent: 10.0,
  walkPhase: 0,
  currentWalkFrame: 1,
  wrapMinPos: -22.0, // smoothly enters from behind left banyan tree
  wrapMaxPos: 104.0, // smoothly exits behind right banyan tree
  bubbleTimer: null,
  animReqId: null,
  lastTime: null
};

const charDialogues = {
  dada: [
    "Puttar, parivaar ki virasat hi sabse badi daulat hai! 🌿",
    "Humne jo mehnat se banaya, use aage badhana tumhara farz hai.",
    "Bina vasiyat aur registry ke parivaar mein kalesh ho sakta hai, tayyari zaroori hai! 📜"
  ],
  father: [
    "Sharma Kirana ko 3 gunna expand karna hai, poori legal clarity ke sath! 💼",
    "Papa ji ke ashirwaad se sabhi assets ki registry aur nomination done hai. ✨",
    "Business aur parivaar dono ko transparent rakhna hi meri zimmedari hai."
  ],
  boy: [
    "Dada-ji, main dukan ko modern e-commerce aur AI se digitalize karunga! 🚀",
    "Family tree and estate distribution dekhkar main bohot proud hoon! 🌳",
    "Hamari dukan ab poore sheher mein sabse reliable banegi!"
  ],
  kid: [
    "Dada-ji dukan se mere liye kaju katli aur chocolate layenge! 🍬✨",
    "Main bhi bade hokar papa jaisa suit pehnunga! 🎈",
    "Ghar chalo, mujhe dukan ke baare mein stories sunni hain! 🪔"
  ],
  group: [
    "Char peedhiyan, ek atoot parivaar — VirasatPlanner ke sang! 🏛️",
    "Surakshit kal ki or naye kadam! 🌅",
    "Plan Today, Preserve Tomorrow! 🤝"
  ]
};

function initWalkingBanner() {
  const group = document.getElementById("walking-family-group");
  if (!group) return;

  group.style.left = `${walkingBannerState.posPercent}%`;

  if (walkingBannerState.animReqId) {
    cancelAnimationFrame(walkingBannerState.animReqId);
  }

  function loop(now) {
    if (!walkingBannerState.lastTime) walkingBannerState.lastTime = now;
    const dtSeconds = Math.min((now - walkingBannerState.lastTime) / 1000.0, 0.05);
    const dt = Math.min((now - walkingBannerState.lastTime) / 16.67, 2.5);
    walkingBannerState.lastTime = now;

    if (walkingBannerState.active) {
      const cfg = walkingBannerState.speeds[walkingBannerState.speedIndex];

      // 1. Advance horizontal position smoothly across stone promenade
      walkingBannerState.posPercent += cfg.moveSpeed * dt;
      if (walkingBannerState.posPercent >= walkingBannerState.wrapMaxPos) {
        walkingBannerState.posPercent = walkingBannerState.wrapMinPos;
      }
      group.style.left = `${walkingBannerState.posPercent}%`;

      // 2. Advance 4-frame walk cycle so legs physically alternate steps & bend knees
      const phaseDelta = (dtSeconds / cfg.cycleDuration) * 4;
      walkingBannerState.walkPhase = (walkingBannerState.walkPhase + phaseDelta) % 4;
      const frameIndex = Math.floor(walkingBannerState.walkPhase) + 1; // 1, 2, 3, or 4

      if (frameIndex !== walkingBannerState.currentWalkFrame) {
        walkingBannerState.currentWalkFrame = frameIndex;

        const dadaImg = document.getElementById("char-dada-img");
        const fatherImg = document.getElementById("char-father-img");
        const boyImg = document.getElementById("char-boy-img");
        const kidImg = document.getElementById("char-kid-img");

        if (dadaImg) dadaImg.src = `/static/dada_walk_${frameIndex}.png`;
        if (fatherImg) fatherImg.src = `/static/father_walk_${frameIndex}.png`;
        if (boyImg) boyImg.src = `/static/boy_walk_${frameIndex}.png`;
        if (kidImg) kidImg.src = `/static/kid_walk_${frameIndex}.png`;
      }
    }

    walkingBannerState.animReqId = requestAnimationFrame(loop);
  }

  walkingBannerState.animReqId = requestAnimationFrame(loop);
}

function toggleWalking() {
  const group = document.getElementById("walking-family-group");
  const banner = document.querySelector(".walking-banner-container");
  const icon = document.getElementById("walk-toggle-icon");
  const text = document.getElementById("walk-toggle-text");

  walkingBannerState.active = !walkingBannerState.active;

  if (walkingBannerState.active) {
    if (banner) banner.classList.remove("walking-paused");
    if (group) group.classList.remove("walking-paused");
    if (icon) icon.innerText = "⏸️";
    if (text) text.innerText = "Walking";
    showToast("Family stroll resumed 🌿", "success");
  } else {
    if (banner) banner.classList.add("walking-paused");
    if (group) group.classList.add("walking-paused");
    if (icon) icon.innerText = "▶️";
    if (text) text.innerText = "Paused";
    showToast("Walking paused", "info");
  }
}

function speedUpWalking() {
  walkingBannerState.speedIndex = (walkingBannerState.speedIndex + 1) % walkingBannerState.speeds.length;
  const cfg = walkingBannerState.speeds[walkingBannerState.speedIndex];

  // Update container CSS animation step durations to stay in lockstep
  const banner = document.querySelector(".walking-banner-container");
  if (banner) {
    banner.style.setProperty("--walk-cycle-dur", `${cfg.cycleDuration}s`);
  }

  // Update button label
  const btn = document.getElementById("walk-speed-btn") || document.querySelector("button[onclick='speedUpWalking()']");
  if (btn) {
    btn.innerText = cfg.label;
  }

  showToast(`Walk pace: ${cfg.label}`, "info");
}

function triggerCharReaction(charKey) {
  const bubble = document.getElementById("family-speech-bubble");
  const bubbleText = document.getElementById("speech-bubble-text");
  if (!bubble || !bubbleText) return;

  // Jump animation on sprite
  const walkerUnits = {
    dada: document.querySelector(".char-dada-anim"),
    father: document.querySelector(".char-father-anim"),
    boy: document.querySelector(".char-boy-anim"),
    kid: document.querySelector(".char-kid-anim")
  };

  const sprite = walkerUnits[charKey];
  if (sprite) {
    sprite.classList.remove("animate-char-jump");
    void sprite.offsetWidth; // trigger reflow
    sprite.classList.add("animate-char-jump");
    setTimeout(() => sprite.classList.remove("animate-char-jump"), 600);
  }

  // Select dialogue
  const quotes = charDialogues[charKey] || charDialogues.group;
  const quote = quotes[Math.floor(Math.random() * quotes.length)];
  bubbleText.innerText = quote;

  bubble.classList.remove("hidden", "bubble-pop");
  void bubble.offsetWidth;
  bubble.classList.add("bubble-pop");

  if (walkingBannerState.bubbleTimer) {
    clearTimeout(walkingBannerState.bubbleTimer);
  }
  walkingBannerState.bubbleTimer = setTimeout(() => {
    bubble.classList.add("hidden");
  }, 4000);
}
