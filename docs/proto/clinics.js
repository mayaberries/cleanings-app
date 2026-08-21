document.addEventListener("DOMContentLoaded", () => {
  const state = boot("clinics");
  if (!state) return;
  renderClinics(state);
});

function renderClinics(state) {
  const root = document.getElementById("view-content");
  root.innerHTML = `
    <div class="flex items-end justify-between mb-6">
      <h1 class="font-display font-700 text-2xl text-ink">Clinics</h1>
      <p class="text-sm text-inksoft font-mono">${state.clinics.length} total</p>
    </div>
    <div class="grid gap-4" id="clinics-list"></div>
  `;

  const list = document.getElementById("clinics-list");
  for (const clinic of state.clinics) {
    const card = document.createElement("div");
    card.className = "bg-surface border border-line rounded-2xl p-5";
    card.innerHTML = `
      <div class="flex items-center justify-between flex-wrap gap-3">
        <div>
          <p class="font-display font-600 text-ink">${clinic.name}</p>
          <p class="text-xs text-inksoft font-mono">${clinic.slug} · ${clinic.id}</p>
        </div>
        <div class="flex items-center gap-3">
          <span id="site-badge-${clinic.id}" class="badge badge-off"></span>
          <button onclick="openLaunchPanel('${clinic.id}')"
            class="bg-gold hover:bg-[#d1922f] text-ink font-display font-600 text-xs px-4 py-2 rounded-full transition-colors">
            Launch / rebuild site
          </button>
        </div>
      </div>
      <div id="launch-panel-${clinic.id}" class="hidden mt-4 pt-4 border-t border-line"></div>
    `;
    list.appendChild(card);
    refreshSiteBadge(state, clinic);
  }
}

function refreshSiteBadge(state, clinic) {
  const badge = document.getElementById(`site-badge-${clinic.id}`);
  if (!badge) return;
  const status = state.sitesRegistry[clinic.id] || { built: false };
  if (status.built) {
    badge.textContent = "live · built " + new Date(status.last_built_at).toLocaleString();
    badge.className = "badge badge-ok";
  } else {
    badge.textContent = "not built yet";
    badge.className = "badge badge-off";
  }
}

function openLaunchPanel(clinicId) {
  const panel = document.getElementById(`launch-panel-${clinicId}`);
  const wasOpen = !panel.classList.contains("hidden");
  document.querySelectorAll('[id^="launch-panel-"]').forEach(p => p.classList.add("hidden"));
  if (wasOpen) return;
  panel.classList.remove("hidden");
  panel.innerHTML = launchFormHTML(clinicId);
}

// Completion hook for shared.js's launchSite() — just refresh this clinic's badge.
function onSiteBuilt(state, clinicId) {
  const clinic = state.clinics.find(c => c.id === clinicId);
  if (clinic) refreshSiteBadge(state, clinic);
  const btn = document.getElementById(`launch-btn-${clinicId}`);
  if (btn) { btn.disabled = false; btn.textContent = "Build site"; }
}
