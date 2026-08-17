export function el(id) {
    const node = document.getElementById(id);
    if (!node) throw new Error(`onboarding: expected #${id} to exist`);
    return node;
}

export function slugify(value) {
    return (value || "")
        .toLowerCase()
        .normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
        .replace(/[^\w\s-]/g, "")
        .trim()
        .replace(/[-\s]+/g, "-");
}

export function escapeHtml(v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
}

export function setFieldError(id, message) {
    const input = el(id);
    const err = document.querySelector('.field-error[data-for="' + id + '"]');
    if (message) {
        if (input) input.classList.add("field-invalid");
        if (err) { err.textContent = message; err.classList.add("show"); }
    } else {
        if (input) input.classList.remove("field-invalid");
        if (err) { err.classList.remove("show"); err.textContent = ""; }
    }
}