import { slugify } from "./dom.js";

function demoDelay(fn) {
    return new Promise((resolve) => setTimeout(() => resolve(fn()), 450 + Math.random() * 350));
}

export function demoRegisterUser() {
    return demoDelay(() => ({ ok: true, data: { access_token: { access_token: "demo.jwt.token" } } }));
}
export function demoCreateClinic(payload) {
    return demoDelay(() => ({
        ok: true,
        data: { id: "demo-clinic-id", name: payload.name, slug: payload.slug || slugify(payload.name),
            email: payload.email, phone_number: payload.phone_number, address: payload.address },
    }));
}
export function demoCreateService(payload) {
    return demoDelay(() => ({ ok: true, data: { id: "demo-service-" + Math.random().toString(36).slice(2, 8), ...payload } }));
}
export function demoCreateKey() {
    return demoDelay(() => ({
        ok: true,
        data: { public_key: "pk_live_demo_" + Math.random().toString(36).slice(2, 10), environment: "live" },
    }));
}