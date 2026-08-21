document.addEventListener("DOMContentLoaded", () => {
  const state = boot("keys");
  if (!state) return;
  renderKeys(state);
});

function renderKeys(state) {
  const clinicId = state.me.clinic_id;
  const keys = state.keys;
  document.getElementById("view-content").innerHTML = `
    <div class="flex items-end justify-between mb-6">
      <h1 class="font-display font-700 text-2xl text-ink">API Keys</h1>
      <button onclick="createKey()" class="bg-gold hover:bg-[#d1922f] text-ink font-display font-600 text-xs px-4 py-2 rounded-full transition-colors">
        + New key
      </button>
    </div>
    <div class="grid gap-3">
      ${keys.map(k => `
        <div class="bg-surface border border-line rounded-xl p-4 flex items-center justify-between flex-wrap gap-3">
          <div>
            <p class="text-sm font-mono text-ink">${k.public_key}</p>
            <p class="text-xs text-inksoft">${k.label || "unlabeled"} · ${k.environment}</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="badge ${k.is_active ? "badge-ok" : "badge-off"}">${k.is_active ? "active" : "revoked"}</span>
            ${k.is_active ? `<button onclick="revokeKey('${clinicId}','${k.id}')" class="text-xs font-medium text-red-600 hover:underline">Revoke</button>` : ""}
          </div>
        </div>
      `).join("") || `<p class="text-sm text-inksoft">No API keys yet — create one to enable public booking and site generation.</p>`}
    </div>
  `;
}

function createKey() {
  const label = prompt("Label for this key (optional):", "Website widget") || undefined;
  const state = getState();
  const key = {
    id: uid("key"),
    public_key: `pk_live_${Math.random().toString(16).slice(2, 14)}`,
    label: label || null, environment: "live", is_active: true,
  };
  state.keys.push(key);
  setState(state);
  showToast("Key created.");
  renderKeys(state);
}

function revokeKey(clinicId, keyId) {
  if (!confirm("Revoke this key? Anything using it will stop working immediately.")) return;
  const state = getState();
  const key = state.keys.find(k => k.id === keyId);
  if (key) key.is_active = false;
  setState(state);
  showToast("Key revoked.");
  renderKeys(state);
}
