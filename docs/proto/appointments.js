document.addEventListener("DOMContentLoaded", () => {
  const state = boot("appointments");
  if (!state) return;
  renderAppointments(state);
});

function renderAppointments(state) {
  const services = state.services;
  const root = document.getElementById("view-content");

  if (!services.length) {
    root.innerHTML = `
      <h1 class="font-display font-700 text-2xl text-ink mb-6">Appointments</h1>
      <p class="text-sm text-inksoft">No services yet — create one in the Services tab first.</p>
    `;
    return;
  }

  root.innerHTML = `
    <h1 class="font-display font-700 text-2xl text-ink mb-6">Appointments</h1>
    <select id="appt-service-select" class="rounded-lg border border-line px-3 py-2 text-sm mb-4">
      ${services.map(s => `<option value="${s.id}">${s.name}</option>`).join("")}
    </select>
    <div id="appt-list" class="grid gap-3"></div>
  `;
  document.getElementById("appt-service-select").addEventListener("change", (e) => loadAppointmentsFor(e.target.value));
  loadAppointmentsFor(services[0].id);
}

function loadAppointmentsFor(serviceId) {
  const state = getState();
  const list = document.getElementById("appt-list");
  const appts = state.appointmentsByService[serviceId] || [];
  if (!appts.length) {
    list.innerHTML = `<p class="text-sm text-inksoft">No appointments for this service yet.</p>`;
    return;
  }
  list.innerHTML = appts.map(a => appointmentCardHTML(a, serviceId)).join("");
}

function appointmentCardHTML(a, serviceId) {
  const badgeClass = a.status === "confirmed" ? "badge-ok" : a.status === "cancelled" ? "badge-off" : "badge-warn";
  return `
    <div class="bg-surface border border-line rounded-xl p-4 flex items-center justify-between flex-wrap gap-3">
      <div>
        <p class="text-sm font-medium text-ink">${new Date(a.start_time).toLocaleString()}</p>
        <p class="text-xs text-inksoft">appointment ${a.id}</p>
      </div>
      <div class="flex items-center gap-2">
        <span class="badge ${badgeClass}">${a.status}</span>
        ${a.status === "requested" ? `<button onclick="confirmAppt('${serviceId}','${a.id}')" class="text-xs font-medium text-teal hover:underline">Confirm</button>` : ""}
        ${a.status === "confirmed" ? `<button onclick="cancelAppt('${serviceId}','${a.id}')" class="text-xs font-medium text-red-600 hover:underline">Cancel</button>` : ""}
      </div>
    </div>
  `;
}

function confirmAppt(serviceId, apptId) {
  const state = getState();
  const appt = (state.appointmentsByService[serviceId] || []).find(a => a.id === apptId);
  if (appt) appt.status = "confirmed";
  setState(state);
  showToast("Appointment confirmed.");
  loadAppointmentsFor(serviceId);
}

function cancelAppt(serviceId, apptId) {
  const state = getState();
  const appt = (state.appointmentsByService[serviceId] || []).find(a => a.id === apptId);
  if (appt) appt.status = "cancelled";
  setState(state);
  showToast("Appointment cancelled.");
  loadAppointmentsFor(serviceId);
}
