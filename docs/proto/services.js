document.addEventListener("DOMContentLoaded", () => {
  const state = boot("services");
  if (!state) return;
  renderServices(state);
});

function renderServices(state) {
  const services = state.services;
  document.getElementById("view-content").innerHTML = `
    <h1 class="font-display font-700 text-2xl text-ink mb-6">Services</h1>
    <div class="grid sm:grid-cols-2 gap-4">
      ${services.map(s => `
        <div class="bg-surface border border-line rounded-2xl p-5">
          <p class="font-display font-600 text-ink">${s.name}</p>
          <p class="text-sm text-inksoft mt-1">${s.description || ""}</p>
          <p class="text-xs text-inksoft font-mono mt-2">${s.category} · ${s.duration_minutes || 30}min · $${s.price ?? "—"}</p>
        </div>
      `).join("") || `<p class="text-sm text-inksoft">No services yet.</p>`}
    </div>
  `;
}
