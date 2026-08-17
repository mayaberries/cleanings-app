import { el, setFieldError, slugify } from "./dom.js";
import { state } from "./state.js";

export function validateStep0() {
    let ok = true;
    state.account.email = el("acc_email").value.trim();
    state.account.username = el("acc_username").value.trim();
    state.account.password = el("acc_password").value;
    const password2 = el("acc_password2").value;

    setFieldError("acc_email", "");
    setFieldError("acc_username", "");
    setFieldError("acc_password", "");
    setFieldError("acc_password2", "");

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(state.account.email)) {
        setFieldError("acc_email", "Enter a valid email address."); ok = false;
    }
    if (state.account.username.length < 3 || !/^[A-Za-z0-9_-]+$/.test(state.account.username)) {
        setFieldError("acc_username", "3+ characters, letters/numbers/-/_ only."); ok = false;
    }
    if (state.account.password.length < 7) {
        setFieldError("acc_password", "Use at least 7 characters."); ok = false;
    }
    if (password2 !== state.account.password) {
        setFieldError("acc_password2", "Passwords don't match."); ok = false;
    }
    return ok;
}

export function validateStep1() {
    let ok = true;
    state.clinic.name = el("cl_name").value.trim();
    state.clinic.slug = slugify(el("cl_slug").value.trim());
    state.clinic.email = el("cl_email").value.trim();
    state.clinic.phone_number = el("cl_phone").value.trim();
    state.clinic.address = el("cl_address").value.trim();

    setFieldError("cl_name", "");
    setFieldError("cl_slug", "");

    if (!state.clinic.name) { setFieldError("cl_name", "Clinic name is required."); ok = false; }
    if (!state.clinic.slug) { setFieldError("cl_slug", "Slug must contain at least one letter or number."); ok = false; }
    return ok;
}

export function validateStep2() {
    let ok = true;
    state.services.forEach(function (svc) {
        const err = document.querySelector('.field-error[data-for="svc-' + svc._id + '"]');
        let msg = "";
        const finalCategory = svc.category || svc.customCategory;
        if (!svc.name.trim()) msg = "Name and price are required.";
        else if (svc.price === "" || isNaN(Number(svc.price)) || Number(svc.price) < 0) msg = "Enter a valid price.";
        else if (!finalCategory || !finalCategory.trim()) msg = "Pick a category or name a custom one.";
        if (msg) { ok = false; if (err) { err.textContent = msg; err.classList.add("show"); } }
        else if (err) { err.classList.remove("show"); err.textContent = ""; }
    });
    return ok;
}