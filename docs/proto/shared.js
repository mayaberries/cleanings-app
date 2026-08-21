/* =============================================================================
   shared.js — loaded by every page in this prototype.

   Holds everything that isn't specific to one tab: state storage, the login
   guard + role/tab access guard + header/nav rendering ("boot"), and the two
   bits reused by more than one view (the site "launch" panel, used by both
   clinics.html — one per clinic row — and website.html — the clinic admin's
   own clinic).

   Same no-backend spirit as the original single-file version of this
   prototype (docs/dashboard.html): nothing here is fetch()ed, all data is
   hardcoded below. The one deviation is sessionStorage — the original kept
   state in a plain JS object because every "tab" was an innerHTML swap on one
   page. Splitting into one real page per tab means a real navigation now
   happens between them, so state has to survive that hop. sessionStorage
   still clears the moment the tab closes, so it's the same "resets easily,
   nothing is really saved" spirit — just carried across a click instead of
   only a refresh.
   ============================================================================= */

const STORAGE_KEY = "petsadmin-proto-state";

function getState() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : { me: null };
  } catch (e) {
    return { me: null };
  }
}

function setState(state) {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function uid(prefix) {
  return `${prefix}-${Math.random().toString(36).slice(2, 8)}`;
}

/* =============================================================================
   HARDCODED DATA
   ============================================================================= */
function seedData(role, email) {
  const now = Date.now();
  const inHours = (h) => new Date(now + h * 3600_000).toISOString();
  const state = { me: null, clinics: [], services: [], keys: [], sitesRegistry: {}, appointmentsByService: {} };

  if (role === "superadmin") {
    state.me = {
      email: email || "superadmin@petsadmin.dev", username: "superadmin",
      is_superuser: true, role: null, clinic_id: null,
    };
    state.clinics = [
      { id: "demo-clinic-1", name: "Acme Vet Clinic", slug: "acme-vet", email: "hi@acmevet.dev", phone_number: "555-0100", created_at: inHours(-800) },
      { id: "demo-clinic-2", name: "Northside Animal Hospital", slug: "northside-animal", email: "hello@northside.dev", phone_number: "555-0142", created_at: inHours(-300) },
      { id: "demo-clinic-3", name: "Furry Friends Pet Care", slug: "furry-friends", email: "contact@furryfriends.dev", phone_number: "555-0177", created_at: inHours(-40) },
    ];
    state.sitesRegistry = {
      "demo-clinic-1": { built: true, last_built_at: inHours(-20), site_url: "https://acme-vet.example.com" },
      "demo-clinic-2": { built: false },
      "demo-clinic-3": { built: false },
    };
  } else {
    const svc1 = uid("svc"), svc2 = uid("svc");
    state.me = {
      email: email || "admin@acmevet.dev", username: "clinic-admin",
      is_superuser: false, role: "clinic_admin", clinic_id: "demo-clinic-1",
    };
    state.services = [
      { id: svc1, name: "Wellness Exam", description: "Annual checkup and vaccinations.", category: "wellness_exam", duration_minutes: 30, price: 65 },
      { id: svc2, name: "Nail Trim", description: "Quick nail trim, walk-ins welcome.", category: "nail_trim", duration_minutes: 15, price: 20 },
    ];
    state.appointmentsByService = {
      [svc1]: [
        { id: uid("appt"), start_time: inHours(2), status: "requested" },
        { id: uid("appt"), start_time: inHours(26), status: "confirmed" },
        { id: uid("appt"), start_time: inHours(-30), status: "cancelled" },
      ],
      [svc2]: [
        { id: uid("appt"), start_time: inHours(4), status: "requested" },
      ],
    };
    state.keys = [
      { id: uid("key"), public_key: "pk_live_5f8a2c9d1e3b", label: "Website widget", environment: "live", is_active: true },
      { id: uid("key"), public_key: "pk_test_a1b2c3d4e5f6", label: "Local testing", environment: "test", is_active: false },
    ];
    state.sitesRegistry = { "demo-clinic-1": { built: false } };
  }

  setState(state);
  return state;
}

/* =============================================================================
   TOAST
   ============================================================================= */
function showToast(msg, kind = "ok") {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.className = "mb-4 text-sm rounded-lg px-4 py-3 border " +
    (kind === "ok" ? "bg-[#DCEFE0] border-[#1E6B3A]/20 text-[#1E6B3A]" : "bg-red-50 border-red-200 text-red-700");
  el.classList.remove("hidden");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => el.classList.add("hidden"), 5000);
}

/* =============================================================================
   TABS / PAGES — one file per tab now, so "switching tabs" is a real
   navigation instead of an innerHTML swap. `role` controls both who sees the
   link in nav and who's allowed to land on the page directly (see boot()).
   ============================================================================= */
const PAGES = {
  clinics:      { label: "Clinics",      href: "clinics.html",      role: "superadmin" },
  overview:     { label: "Overview",     href: "overview.html",     role: "clinic_admin" },
  appointments: { label: "Appointments", href: "appointments.html", role: "clinic_admin" },
  services:     { label: "Services",     href: "services.html",     role: "clinic_admin" },
  keys:         { label: "API Keys",     href: "api-keys.html",     role: "clinic_admin" },
  website:      { label: "Website",      href: "website.html",      role: "clinic_admin" },
  account:      { label: "Account",      href: "account.html",      role: "both" },
};

function roleOf(me) { return me.is_superuser ? "superadmin" : "clinic_admin"; }

function tabsForRole(me) {
  const role = roleOf(me);
  return Object.entries(PAGES).filter(([, page]) => page.role === "both" || page.role === role);
}

function firstPageFor(me) {
  return roleOf(me) === "superadmin" ? PAGES.clinics.href : PAGES.overview.href;
}

/* =============================================================================
   AUTH / ACCESS GUARD + SHELL

   Every view page calls boot("<its tab id>") on load. It:
     1. bounces to login.html if nobody's "signed in" (no state.me),
     2. bounces to this role's landing tab if the current page doesn't belong
        to it (mirrors the original single-file renderTab()'s superadmin
        special-case — e.g. a clinic_admin who lands on clinics.html gets
        sent to overview.html instead),
     3. renders the shared role badge / email / sign-out button / tab nav
        into the page's static header markup.

   Returns the state, or null if it redirected — callers should bail out
   (`if (!state) return;`) when they get null; the redirect is already in
   flight via location.href.
   ============================================================================= */
function boot(tabId) {
  const state = getState();
  if (!state.me) {
    location.href = "login.html";
    return null;
  }
  const page = PAGES[tabId];
  if (page.role !== "both" && page.role !== roleOf(state.me)) {
    location.href = firstPageFor(state.me);
    return null;
  }
  renderShell(state, tabId);
  return state;
}

function renderShell(state, activeTab) {
  const me = state.me;
  document.getElementById("user-email").textContent = me.email;

  const roleBadge = document.getElementById("role-badge");
  if (me.is_superuser) {
    roleBadge.textContent = "Superadmin";
    roleBadge.className = "badge badge-warn ml-2";
  } else {
    roleBadge.textContent = me.role || "staff";
    roleBadge.className = "badge badge-ok ml-2";
  }

  const nav = document.getElementById("tab-nav");
  nav.innerHTML = tabsForRole(me).map(([id, page]) => {
    const active = id === activeTab;
    const stateClasses = active
      ? "border-teal text-ink font-semibold"
      : "border-transparent text-inksoft hover:text-ink";
    return `<a href="${page.href}" class="py-3 border-b-2 ${stateClasses} transition-colors">${page.label}</a>`;
  }).join("");

  document.getElementById("signout-btn").addEventListener("click", logout);
}

function logout() {
  sessionStorage.removeItem(STORAGE_KEY);
  location.href = "login.html";
}

/* =============================================================================
   SITE "LAUNCH" PANEL — shared by clinics.html (superadmin, one per clinic
   row) and website.html (clinic admin, their own clinic only). Each of those
   pages defines a top-level `onSiteBuilt(state, clinicId)` function; this is
   the (simulated) build's completion hook, so each page can decide what
   "done" means for it — clinics.html just refreshes that row's badge,
   website.html re-renders its single panel.
   ============================================================================= */
function launchFormHTML(clinicId) {
  return `
    <div class="grid sm:grid-cols-2 gap-3">
      <div>
        <label class="block text-xs font-medium text-inksoft mb-1">Site URL (optional, where it'll be hosted)</label>
        <input id="launch-siteurl-${clinicId}" placeholder="https://acme-vet.example.com" class="w-full rounded-lg border border-line px-3 py-2 text-sm" />
      </div>
      <div>
        <label class="block text-xs font-medium text-inksoft mb-1">Brand color (optional)</label>
        <input id="launch-color-${clinicId}" placeholder="#3F7377" class="w-full rounded-lg border border-line px-3 py-2 text-sm" />
      </div>
      <div>
        <label class="block text-xs font-medium text-inksoft mb-1">Logo URL (optional)</label>
        <input id="launch-logo-${clinicId}" class="w-full rounded-lg border border-line px-3 py-2 text-sm" />
      </div>
    </div>
    <button onclick="launchSite('${clinicId}', 'launch-btn-${clinicId}')" id="launch-btn-${clinicId}"
      class="mt-4 bg-ink hover:bg-[#0f211d] text-white font-display font-600 text-sm px-5 py-2.5 rounded-full transition-colors">
      Build site
    </button>
  `;
}

function launchSite(clinicId, buttonId) {
  const btn = document.getElementById(buttonId);
  btn.disabled = true;
  btn.textContent = "Building… (this can take a minute)";
  // Purely cosmetic delay so the interaction still feels like a build step.
  setTimeout(() => {
    const state = getState();
    const urlInput = document.getElementById(`launch-siteurl-${clinicId}`);
    const siteUrl = (urlInput ? urlInput.value.trim() : "") || `https://${clinicId}.example.com`;
    state.sitesRegistry[clinicId] = { built: true, last_built_at: new Date().toISOString(), site_url: siteUrl };
    setState(state);
    showToast("Site built successfully.");
    if (typeof onSiteBuilt === "function") onSiteBuilt(state, clinicId);
  }, 900);
}
