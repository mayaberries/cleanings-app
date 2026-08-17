// frontend/admin/src/lib/onboarding/review.js
import { el, escapeHtml } from "./dom.js";
import { state } from "./state.js";
import { CATEGORY_LABELS } from "./constants.js";

export function renderReview() {
    const finalServices = state.services.map(function (s) {
        return {
            name: s.name,
            category: s.category || s.customCategory,
            price: s.price,
            duration_minutes: s.duration_minutes,
            description: s.description,
        };
    });

    el("reviewBlock").innerHTML =
        '<div class="border border-line rounded-xl p-4">' +
        '<p class="text-xs font-mono uppercase tracking-wider text-teal mb-2">Account</p>' +
        '<p class="text-sm text-ink">' + escapeHtml(state.account.username) + ' · ' + escapeHtml(state.account.email) + '</p>' +
        '</div>' +
        '<div class="border border-line rounded-xl p-4">' +
        '<p class="text-xs font-mono uppercase tracking-wider text-teal mb-2">Clinic</p>' +
        '<p class="text-sm text-ink font-medium">' + escapeHtml(state.clinic.name) + '</p>' +
        '<p class="text-xs text-inksoft font-mono mt-0.5">/sites/' + escapeHtml(state.clinic.slug) + '</p>' +
        (state.clinic.email || state.clinic.phone_number
            ? '<p class="text-xs text-inksoft mt-1">' + [state.clinic.email, state.clinic.phone_number].filter(Boolean).map(escapeHtml).join(" · ") + '</p>'
            : "") +
        '</div>' +
        '<div class="border border-line rounded-xl p-4">' +
        '<p class="text-xs font-mono uppercase tracking-wider text-teal mb-2">Services (' + finalServices.length + ')</p>' +
        '<ul class="space-y-1.5">' +
        finalServices.map(function (s) {
            return '<li class="text-sm text-ink flex items-center justify-between gap-2">' +
                '<span>' + escapeHtml(s.name) + ' <span class="text-inksoft">— ' + escapeHtml(CATEGORY_LABELS[s.category] || s.category) + '</span></span>' +
                '<span class="text-inksoft font-mono text-xs shrink-0">$' + escapeHtml(s.price) + (s.duration_minutes ? " · " + escapeHtml(s.duration_minutes) + "min" : "") + '</span>' +
                '</li>';
        }).join("") +
        '</ul>' +
        '</div>';

    el("launchTasks").classList.add("hidden");
    el("launchTasks").innerHTML = "";
    el("launchError").classList.add("hidden");
    el("nextBtn").disabled = false;
}