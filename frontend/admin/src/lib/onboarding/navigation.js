import { el } from "./dom.js";
import { state } from "./state.js";
import { renderServices } from "./servicesForm.js";
import { renderReview } from "./review.js";
import { renderStepper } from "./stepper.js";

export function showStep(n) {
    state.step = n;
    document.querySelectorAll(".step-panel").forEach(function (p) {
        p.classList.toggle("active", Number(p.getAttribute("data-step")) === n);
    });
    el("intro").style.display = n === 0 ? "" : "none";
    el("stepper").style.display = n === 4 ? "none" : "flex";
    el("navRow").style.display = n === 4 ? "none" : "flex";
    el("backBtn").style.visibility = n === 0 ? "hidden" : "visible";
    el("nextBtn").textContent = n === 3 ? "Launch clinic 🚀" : "Continue";
    if (n === 2) renderServices();
    if (n === 3) renderReview();
    renderStepper();
    window.scrollTo({ top: 0, behavior: "smooth" });
}