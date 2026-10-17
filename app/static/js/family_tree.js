/**
 * VirasatPlanner - Interactive Family Tree Graph Renderer
 * Visualizes multi-generational hierarchy with legal heir status
 * Fully sanitized against HTML injection (XSS safe)
 */

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function renderFamilyTree(members, containerId, onSelectMember) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = "";

  if (!members || members.length === 0) {
    container.innerHTML = `
      <div class="text-center py-12 text-slate-400">
        <p>No family members added yet.</p>
      </div>
    `;
    return;
  }

  // Group members by generation / tiers
  // Gen 0: Parents
  // Gen 1: Self & Spouse
  // Gen 2: Children (Sons, Daughters, DIL, SIL)
  // Gen 3: Grandchildren
  const gen0 = [];
  const gen1 = [];
  const gen2 = [];
  const gen3 = [];

  members.forEach(m => {
    const rel = (m.relation || "").toLowerCase();
    if (rel.includes("father") || rel.includes("mother") || rel.includes("parent")) {
      gen0.push(m);
    } else if (rel.includes("self") || rel.includes("spouse") || rel.includes("wife") || rel.includes("husband")) {
      gen1.push(m);
    } else if (rel.includes("son") || rel.includes("daughter") || rel.includes("dil") || rel.includes("sil")) {
      gen2.push(m);
    } else if (rel.includes("grand") || rel.includes("grandson") || rel.includes("granddaughter")) {
      gen3.push(m);
    } else {
      gen2.push(m);
    }
  });

  // Ensure Karta is first in Gen 1
  gen1.sort((a, b) => ((a.relation || "").toLowerCase() === "self" ? -1 : 1));

  const wrapper = document.createElement("div");
  wrapper.className = "flex flex-col items-center gap-8 py-6 w-full overflow-x-auto";

  // Tier builder helper
  function buildTierRow(tierMembers, tierLabel) {
    if (tierMembers.length === 0) return null;

    const rowContainer = document.createElement("div");
    rowContainer.className = "flex flex-col items-center w-full";

    const label = document.createElement("div");
    label.className = "text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3";
    label.textContent = tierLabel;
    rowContainer.appendChild(label);

    const cardsRow = document.createElement("div");
    cardsRow.className = "flex flex-wrap justify-center items-center gap-4 sm:gap-6";

    tierMembers.forEach(m => {
      const card = document.createElement("div");
      const rel = (m.relation || "").toLowerCase();
      const isSelf = rel === "self";
      const isSpouse = rel === "spouse" || rel === "wife";
      const isClass1 = Boolean(m.is_class_1_heir);

      let borderStyle = isSelf ? "border-teal-600 bg-teal-50/50 shadow-md ring-2 ring-teal-500/20" : "border-slate-200 bg-white";
      if (isSpouse) borderStyle = "border-amber-400 bg-amber-50/30";

      card.className = `tree-node rounded-xl border ${borderStyle} p-3.5 w-52 flex flex-col gap-1.5 shadow-sm transition hover:shadow-md cursor-pointer focus:outline-none focus:ring-2 focus:ring-amber-500`;
      card.setAttribute("tabindex", "0");
      card.setAttribute("role", "button");
      card.setAttribute("aria-label", `View details and legal rights for ${m.name || ''}, ${m.relation || ''}`);

      const gender = (m.gender || "male").toLowerCase();
      const genderIcon = gender === "female" ? "♀" : "♂";
      const genderColor = gender === "female" ? "text-pink-600" : "text-blue-600";

      const safeName = escapeHtml(m.name);
      const safeRel = escapeHtml(m.relation);
      const safeMarital = escapeHtml(m.marital_status || 'Married');

      card.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${isSelf ? 'bg-teal-600 text-white' : 'bg-slate-100 text-slate-700'}">
            ${safeRel}
          </span>
          <span class="text-sm font-bold ${genderColor}" aria-hidden="true">${genderIcon}</span>
        </div>
        <div class="font-bold text-slate-800 text-sm truncate" title="${safeName}">
          ${safeName}
        </div>
        <div class="text-xs text-slate-500 flex items-center justify-between">
          <span>Age: ${Number(m.age) || 0} ${m.is_minor ? '<span class="text-red-600 font-semibold">(Minor)</span>' : ''}</span>
          <span>${safeMarital}</span>
        </div>
        <div class="pt-1.5 border-t border-slate-100 flex items-center gap-1.5 flex-wrap">
          ${isClass1 ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-medium">Class I Heir</span>' : ''}
          ${m.is_coparcener ? '<span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">Coparcener</span>' : ''}
        </div>
      `;

      const triggerAction = () => {
        if (typeof onSelectMember === "function") {
          onSelectMember(m);
        }
      };

      card.onclick = triggerAction;
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          triggerAction();
        }
      });

      cardsRow.appendChild(card);
    });

    rowContainer.appendChild(cardsRow);
    return rowContainer;
  }

  // Build rows
  const row0 = buildTierRow(gen0, "Generation I — Parents & Elders");
  const row1 = buildTierRow(gen1, "Generation II — Karta & Spouse");
  const row2 = buildTierRow(gen2, "Generation III — Sons, Daughters & In-Laws");
  const row3 = buildTierRow(gen3, "Generation IV — Grandchildren (Next Gen)");

  function createConnector() {
    const conn = document.createElement("div");
    conn.className = "w-0.5 h-6 bg-slate-300 my-1";
    return conn;
  }

  if (row0) {
    wrapper.appendChild(row0);
    wrapper.appendChild(createConnector());
  }
  if (row1) {
    wrapper.appendChild(row1);
    if (row2 || row3) wrapper.appendChild(createConnector());
  }
  if (row2) {
    wrapper.appendChild(row2);
    if (row3) wrapper.appendChild(createConnector());
  }
  if (row3) {
    wrapper.appendChild(row3);
  }

  container.appendChild(wrapper);
}

window.renderFamilyTree = renderFamilyTree;
