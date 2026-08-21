document.addEventListener("DOMContentLoaded", () => {
  const state = boot("overview");
  if (!state) return;
  renderOverview(state);
});

function renderOverview(state) {
  const services = state.services;
  let totalAppointments = 0, requested = 0;
  for (const svc of services) {
    const appts = state.appointmentsByService[svc.id] || [];
    totalAppointments += appts.length;
    requested += appts.filter(a => a.status === "requested").length;
  }
  const keys = state.keys;

  document.getElementById("view-content").innerHTML = `
    <h1 class="font-display font-700 text-2xl text-ink mb-6">Overview</h1>
    <div class="grid sm:grid-cols-3 gap-4">
      ${statCard("Services", services.length)}
      ${statCard("Appointments (total)", totalAppointments)}
      ${statCard("Awaiting confirmation", requested)}
    </div>
    <div class="grid sm:grid-cols-2 gap-4 mt-4">
      ${statCard("Active API keys", keys.filter(k => k.is_active).length)}
      ${statCard("Clinic ID", state.me.clinic_id || "—", true)}
    </div>
  `;
}

function statCard(label, value, mono = false) {
  return `
    <div class="bg-surface border border-line rounded-2xl p-5">
      <p class="text-xs text-inksoft font-medium mb-1">${label}</p>
      <p class="${mono ? "font-mono text-sm" : "font-display font-700 text-2xl"} text-ink">${value}</p>
    </div>
  `;
}
