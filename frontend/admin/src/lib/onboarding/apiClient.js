import { el } from "./dom.js";

export function apiBase() { return el("apiBaseInput").value.replace(/\/+$/, ""); }
export function isDemo() { return el("demoModeToggle").checked; }

export async function apiCall(path, options) {
    if (isDemo()) return null; // callers branch on isDemo() themselves
    try {
        const res = await fetch(apiBase() + path, options);
        let data = null;
        try { data = await res.json(); } catch (e) { /* no body */ }
        if (!res.ok) {
            const detail = (data && (data.detail || data.message)) || (res.status + " " + res.statusText);
            return { ok: false, status: res.status, detail: typeof detail === "string" ? detail : JSON.stringify(detail) };
        }
        return { ok: true, data };
    } catch (err) {
        return { ok: false, status: 0, detail: "Could not reach " + apiBase() + " — check the API base URL and that the backend is running (and CORS-enabled) for this origin." };
    }
}