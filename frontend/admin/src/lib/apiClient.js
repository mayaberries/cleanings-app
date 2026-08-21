export function createApiClient({getBaseUrl, getIsDemo} = {}) {
    async function apiCall(path, options) {
        if (getIsDemo && getIsDemo()) return null; // callers branch on isDemo() themselves
        const base = getBaseUrl ? getBaseUrl() : "";
        try {
            const res = await fetch(base + path, options);
            let data = null;
            try {
                data = await res.json();
            } catch (e) { /* no body */
            }
            if (!res.ok) {
                const detail = (data && (data.detail || data.message)) || (res.status + " " + res.statusText);
                return {
                    ok: false,
                    status: res.status,
                    detail: typeof detail === "string" ? detail : JSON.stringify(detail)
                };
            }
            return {ok: true, data};
        } catch (err) {
            return {
                ok: false,
                status: 0,
                detail: "Could not reach " + base + " — check the API base URL and that the backend is running (and CORS-enabled) for this origin."
            };
        }
    }

    return {apiCall};
}
