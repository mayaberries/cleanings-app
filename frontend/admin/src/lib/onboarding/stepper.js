import { el } from "./dom.js";
import { state } from "./state.js";
import { STEP_LABELS } from "./constants.js";

export function renderStepper() {
    const stepper = el("stepper");
    stepper.innerHTML = STEP_LABELS.map((label, i) => {
        const isDone = i < state.step;
        const isActive = i === state.step;
        const circleClasses = isDone
            ? "bg-teal text-white"
            : isActive
                ? "bg-gold text-ink"
                : "bg-panel text-inksoft border border-line";
        const lineClasses = i < STEP_LABELS.length - 1
            ? '<div class="flex-1 h-px ' + (isDone ? "bg-teal" : "bg-line") + ' mx-1"></div>'
            : "";
        return (
            '<li class="flex items-center flex-1 last:flex-none">' +
            '<div class="flex items-center gap-2 shrink-0">' +
            '<span class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-display font-600 ' + circleClasses + '">' +
            (isDone ? "✓" : i + 1) +
            '</span>' +
            '<span class="hidden sm:inline text-xs font-medium ' + (isActive ? "text-ink" : "text-inksoft") + '">' + label + '</span>' +
            '</div>' +
            lineClasses +
            '</li>'
        );
    }).join("");
}