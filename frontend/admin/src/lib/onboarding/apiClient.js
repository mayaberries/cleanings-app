import { el } from "./dom.js";
import { createApiClient } from "../apiClient.js";

export function apiBase() { return el("apiBaseInput").value.replace(/\/+$/, ""); }
export function isDemo() { return el("demoModeToggle").checked; }

export const { apiCall } = createApiClient({ getBaseUrl: apiBase, getIsDemo: isDemo });
