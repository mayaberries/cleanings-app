document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("login-btn").addEventListener("click", handleLoginSubmit);
});

// No credential check against anything. The only validation is that both
// fields are filled in — matches the original single-file prototype.
function handleLoginSubmit() {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const errEl = document.getElementById("login-error");
  errEl.classList.add("hidden");

  if (!email || !password) {
    errEl.textContent = "Email and password are required.";
    errEl.classList.remove("hidden");
    return;
  }

  loginAs("clinic_admin", email);
}

function loginAs(role, email) {
  const state = seedData(role, email);
  location.href = firstPageFor(state.me);
}
