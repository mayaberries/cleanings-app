document.addEventListener("DOMContentLoaded", () => {
  const state = boot("website");
  if (!state) return;
  renderWebsite(state);
});

function renderWebsite(state) {
  const clinicId = state.me.clinic_id;
  const status = state.sitesRegistry[clinicId] || { built: false };
  document.getElementById("view-content").innerHTML = `
    <h1 class="font-display font-700 text-2xl text-ink mb-6">Website</h1>
    <div class="bg-surface border border-line rounded-2xl p-6 max-w-xl">
      <div class="mb-4">
        <span class="badge ${status.built ? "badge-ok" : "badge-off"}">
          ${status.built ? "live · built " + new Date(status.last_built_at).toLocaleString() : "not built yet"}
        </span>
        ${status.site_url ? `<a href="${status.site_url}" target="_blank" class="ml-2 text-sm text-teal hover:underline">${status.site_url}</a>` : ""}
      </div>
      <div id="website-form"></div>
    </div>
  `;
  document.getElementById("website-form").innerHTML = launchFormHTML(clinicId);
}

// Completion hook for shared.js's launchSite() — re-render the whole panel
// (there's only ever one clinic here, unlike clinics.html's per-row badge).
function onSiteBuilt(state) {
  renderWebsite(state);
}
