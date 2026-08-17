import { el, escapeHtml } from "./dom.js";
import { state } from "./state.js";
import { TASKS } from "./constants.js";
import { isDemo, apiCall } from "./apiClient.js";
import { demoRegisterUser, demoCreateClinic, demoCreateService, demoCreateKey } from "./demoBackend.js";
import { showStep } from "./navigation.js";

export function renderTasks(statusMap) {
    const box = el("launchTasks");
    box.classList.remove("hidden");
    box.innerHTML = TASKS.map(function (t) {
        const status = statusMap[t.key] || "pending";
        let icon;
        if (status === "done") icon = '<span class="task-icon w-5 h-5 rounded-full bg-teal text-white text-xs flex items-center justify-center">✓</span>';
        else if (status === "active") icon = '<span class="task-icon w-5 h-5 rounded-full border-2 border-gold border-t-transparent animate-spin"></span>';
        else if (status === "error") icon = '<span class="task-icon w-5 h-5 rounded-full bg-danger text-white text-xs flex items-center justify-center">!</span>';
        else icon = '<span class="task-icon w-5 h-5 rounded-full border-2 border-line"></span>';
        const textClass = status === "pending" ? "text-inksoft" : "text-ink";
        return '<div class="task-row flex items-center gap-3">' + icon + '<span class="text-sm ' + textClass + '">' + t.label + '</span></div>';
    }).join("");
}

export async function launch() {
    el("nextBtn").disabled = true;
    el("backBtn").style.pointerEvents = "none";
    el("launchError").classList.add("hidden");

    const status = { account: "active", clinic: "pending", services: "pending", key: "pending" };
    renderTasks(status);

    // 1. Account
    let regResult;
    if (isDemo()) regResult = await demoRegisterUser();
    else regResult = await apiCall("/users/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: state.account.email, username: state.account.username, password: state.account.password }),
    });

    if (!regResult.ok) return fail("account", status, regResult.detail);
    state.token = regResult.data.access_token.access_token;
    status.account = "done"; status.clinic = "active"; renderTasks(status);

    // 2. Clinic
    const clinicPayload = {
        name: state.clinic.name, slug: state.clinic.slug,
        email: state.clinic.email || undefined, phone_number: state.clinic.phone_number || undefined,
        address: state.clinic.address || undefined,
    };
    let clinicResult;
    if (isDemo()) clinicResult = await demoCreateClinic(clinicPayload);
    else clinicResult = await apiCall("/clinics/", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: "Bearer " + state.token },
        body: JSON.stringify(clinicPayload),
    });

    if (!clinicResult.ok) {
        const knownGap = /clinic admin/i.test(clinicResult.detail || "");
        return fail("clinic", status, clinicResult.detail, knownGap);
    }
    state.createdClinic = clinicResult.data;
    status.clinic = "done"; status.services = "active"; renderTasks(status);

    // 3. Services (sequential — keeps task UI honest about progress)
    state.createdServices = [];
    for (const svc of state.services) {
        const payload = {
            name: svc.name,
            description: svc.description || undefined,
            price: Number(svc.price),
            category: svc.category || svc.customCategory,
            duration_minutes: svc.duration_minutes ? Number(svc.duration_minutes) : undefined,
        };
        let svcResult;
        if (isDemo()) svcResult = await demoCreateService(payload);
        else svcResult = await apiCall("/services/", {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: "Bearer " + state.token },
            body: JSON.stringify(payload),
        });
        if (!svcResult.ok) return fail("services", status, svcResult.detail);
        state.createdServices.push(svcResult.data);
    }
    status.services = "done"; status.key = "active"; renderTasks(status);

    // 4. Public API key
    let keyResult;
    if (isDemo()) keyResult = await demoCreateKey();
    else keyResult = await apiCall("/clinics/" + state.createdClinic.id + "/api-keys/", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: "Bearer " + state.token },
        body: JSON.stringify({ label: "Onboarding widget key", environment: "live" }),
    });
    if (!keyResult.ok) return fail("key", status, keyResult.detail);
    state.apiKey = keyResult.data;
    status.key = "done"; renderTasks(status);

    el("backBtn").style.pointerEvents = "";
    renderSuccess();
    showStep(4);
}

function fail(taskKey, status, detail, knownGap) {
    status[taskKey] = "error";
    renderTasks(status);
    el("backBtn").style.pointerEvents = "";
    el("nextBtn").disabled = false;
    const box = el("launchError");
    box.classList.remove("hidden");
    box.innerHTML =
        '<p class="font-medium mb-1">Couldn\'t finish that step.</p>' +
        '<p class="font-mono text-xs opacity-90">' + escapeHtml(detail) + '</p>' +
        (knownGap
            ? '<p class="mt-2 text-xs">This is a known gap in the current backend: <code class="font-mono">POST /users/</code> always registers a <code class="font-mono">client</code>-role account, and clinic creation requires <code class="font-mono">clinic_admin</code>. There\'s no self-service HTTP path yet to register as a clinic admin — see the note at the bottom of this page. Try demo mode to preview the rest of the flow, or promote the account via the CLI/DB in the meantime.</p>'
            : "");
}

function renderSuccess() {
    const key = state.apiKey ? state.apiKey.public_key : "";
    const slug = state.createdClinic ? state.createdClinic.slug : state.clinic.slug;
    el("successBlock").innerHTML =
        '<div class="border border-line rounded-xl p-4 bg-panel">' +
        '<p class="text-xs font-mono uppercase tracking-wider text-teal mb-2">Public booking key</p>' +
        '<div class="flex items-center gap-2">' +
        '<code id="keyText" class="flex-1 text-sm font-mono bg-surface border border-line rounded-lg px-3 py-2 overflow-x-auto whitespace-nowrap">' + escapeHtml(key) + '</code>' +
        '<button id="copyKeyBtn" type="button" class="shrink-0 text-xs font-medium px-3 py-2 rounded-lg border border-line hover:border-teal text-ink transition-colors">Copy</button>' +
        '</div>' +
        '<p class="text-xs text-inksoft mt-2">Safe to use client-side. Scoped to this clinic only — you can revoke or rotate it later without downtime.</p>' +
        '</div>' +
        '<div class="border border-line rounded-xl p-4">' +
        '<p class="text-xs font-mono uppercase tracking-wider text-teal mb-2">Embed on your own site</p>' +
        '<pre class="text-xs font-mono bg-panel border border-line rounded-lg p-3 overflow-x-auto">&lt;iframe\n  src="https://sites.yourdomain.com/' + escapeHtml(slug) + '/"\n  style="width:100%;border:0;min-height:640px"\n&gt;&lt;/iframe&gt;</pre>' +
        '<p class="text-xs text-inksoft mt-2">Or build the standalone static site from this clinic via the admin CLI:</p>' +
        '<pre class="text-xs font-mono bg-panel border border-line rounded-lg p-3 mt-1 overflow-x-auto">sites generate ' + escapeHtml(state.createdClinic ? state.createdClinic.id : "&lt;clinic_id&gt;") + ' --public-api-url https://api.yourdomain.com/api</pre>' +
        '</div>' +
        '<div class="flex flex-wrap gap-3 pt-2">' +
        '<button id="restartBtn" type="button" class="text-sm font-medium text-inksoft hover:text-ink px-4 py-2.5 border border-line rounded-full transition-colors">Set up another clinic</button>' +
        '</div>';

    el("copyKeyBtn").addEventListener("click", function () {
        navigator.clipboard.writeText(key).then(function () {
            el("copyKeyBtn").textContent = "Copied";
            setTimeout(function () { el("copyKeyBtn").textContent = "Copy"; }, 1500);
        });
    });
    el("restartBtn").addEventListener("click", function () { window.location.reload(); });
}