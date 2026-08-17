import { el, escapeHtml } from "./dom.js";
import { state } from "./state.js";
import { SUGGESTED_CATEGORIES, CATEGORY_LABELS } from "./constants.js";

export function renderServices() {
    const wrap = el("servicesList");
    wrap.innerHTML = state.services.map(function (svc) {
        const isCustom = !SUGGESTED_CATEGORIES.includes(svc.category);
        const options = SUGGESTED_CATEGORIES.map(function (c) {
            return '<option value="' + c + '"' + (svc.category === c ? " selected" : "") + '>' + CATEGORY_LABELS[c] + '</option>';
        }).join("") + '<option value="__custom__"' + (isCustom ? " selected" : "") + '>Other…</option>';

        return (
            '<div class="relative border border-line rounded-xl p-4 bg-panel/50" data-svc="' + svc._id + '">' +
            (state.services.length > 1
                ? '<button type="button" class="remove-svc absolute top-3 right-3 text-inksoft hover:text-danger transition-colors" data-svc="' + svc._id + '" title="Remove service">' +
                '<svg viewBox="0 0 24 24" class="w-4 h-4 fill-none stroke-current stroke-2"><path d="M18 6 6 18M6 6l12 12"/></svg></button>'
                : "") +
            '<div class="grid sm:grid-cols-2 gap-3">' +
            '<div>' +
            '<label class="block text-xs font-medium text-ink mb-1">Service name</label>' +
            '<input type="text" class="svc-name w-full px-3 py-2 rounded-lg border border-line bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-teal" placeholder="Annual wellness exam" value="' + escapeHtml(svc.name) + '" data-svc="' + svc._id + '" />' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-ink mb-1">Category</label>' +
            '<select class="svc-category w-full px-3 py-2 rounded-lg border border-line bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-teal" data-svc="' + svc._id + '">' + options + '</select>' +
            '</div>' +
            '</div>' +
            (isCustom
                ? '<div class="mt-3"><label class="block text-xs font-medium text-ink mb-1">Custom category name</label>' +
                '<input type="text" class="svc-custom-category w-full px-3 py-2 rounded-lg border border-line bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-teal" placeholder="e.g. behavior-consult" value="' + escapeHtml(svc.customCategory) + '" data-svc="' + svc._id + '" /></div>'
                : "") +
            '<div class="grid sm:grid-cols-2 gap-3 mt-3">' +
            '<div>' +
            '<label class="block text-xs font-medium text-ink mb-1">Price (MXN)</label>' +
            '<input type="number" min="0" step="0.01" class="svc-price w-full px-3 py-2 rounded-lg border border-line bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-teal" placeholder="450.00" value="' + escapeHtml(svc.price) + '" data-svc="' + svc._id + '" />' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-ink mb-1">Duration (minutes)</label>' +
            '<input type="number" min="5" step="5" class="svc-duration w-full px-3 py-2 rounded-lg border border-line bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-teal" placeholder="30" value="' + escapeHtml(svc.duration_minutes) + '" data-svc="' + svc._id + '" />' +
            '</div>' +
            '</div>' +
            '<div class="mt-3">' +
            '<label class="block text-xs font-medium text-ink mb-1">Description <span class="text-inksoft font-normal">(optional)</span></label>' +
            '<textarea rows="2" class="svc-description w-full px-3 py-2 rounded-lg border border-line bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-teal" placeholder="What\'s included, what to bring…" data-svc="' + svc._id + '">' + escapeHtml(svc.description) + '</textarea>' +
            '</div>' +
            '<p class="field-error text-xs text-danger mt-2" data-for="svc-' + svc._id + '"></p>' +
            '</div>'
        );
    }).join("");

    wrap.querySelectorAll(".svc-name").forEach(function (i) { i.addEventListener("input", onServiceInput); });
    wrap.querySelectorAll(".svc-category").forEach(function (i) { i.addEventListener("change", onServiceInput); });
    wrap.querySelectorAll(".svc-custom-category").forEach(function (i) { i.addEventListener("input", onServiceInput); });
    wrap.querySelectorAll(".svc-price").forEach(function (i) { i.addEventListener("input", onServiceInput); });
    wrap.querySelectorAll(".svc-duration").forEach(function (i) { i.addEventListener("input", onServiceInput); });
    wrap.querySelectorAll(".svc-description").forEach(function (i) { i.addEventListener("input", onServiceInput); });
    wrap.querySelectorAll(".remove-svc").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const id = Number(btn.getAttribute("data-svc"));
            state.services = state.services.filter(function (s) { return s._id !== id; });
            renderServices();
        });
    });
}

function onServiceInput(e) {
    const id = Number(e.target.getAttribute("data-svc"));
    const svc = state.services.find(function (s) { return s._id === id; });
    if (!svc) return;
    const needsRerender = e.target.classList.contains("svc-category");
    if (e.target.classList.contains("svc-name")) svc.name = e.target.value;
    if (e.target.classList.contains("svc-category")) {
        svc.category = e.target.value === "__custom__" ? "" : e.target.value;
    }
    if (e.target.classList.contains("svc-custom-category")) svc.customCategory = e.target.value;
    if (e.target.classList.contains("svc-price")) svc.price = e.target.value;
    if (e.target.classList.contains("svc-duration")) svc.duration_minutes = e.target.value;
    if (e.target.classList.contains("svc-description")) svc.description = e.target.value;
    if (needsRerender) renderServices();
}