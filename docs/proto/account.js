document.addEventListener("DOMContentLoaded", () => {
  const state = boot("account");
  if (!state) return;
  renderAccount(state);
});

// Updates the signed-in user's own profile. Nothing here is sent anywhere;
// it just edits state.me in place (via getState()/setState()). Only checks
// that the required fields aren't empty, and that the two password fields
// match — same as the original single-file prototype.
function renderAccount(state) {
  const me = state.me;
  document.getElementById("view-content").innerHTML = `
    <h1 class="font-display font-700 text-2xl text-ink mb-6">Account</h1>
    <div class="bg-surface border border-line rounded-2xl p-6 max-w-lg">
      <label class="block text-xs font-medium text-inksoft mb-1.5">Display name</label>
      <input id="account-name" type="text" value="${me.username || ""}"
        class="w-full rounded-lg border border-line px-3.5 py-2.5 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary" />

      <label class="block text-xs font-medium text-inksoft mb-1.5">Email</label>
      <input id="account-email" type="email" value="${me.email || ""}"
        class="w-full rounded-lg border border-line px-3.5 py-2.5 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary" />

      <div class="h-px bg-line my-5"></div>

      <p class="text-xs font-medium text-inksoft mb-3">Change password <span class="text-inksoft/70 font-normal">(optional)</span></p>

      <label class="block text-xs font-medium text-inksoft mb-1.5">New password</label>
      <input id="account-password" type="password" autocomplete="new-password"
        class="w-full rounded-lg border border-line px-3.5 py-2.5 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary" />

      <label class="block text-xs font-medium text-inksoft mb-1.5">Confirm new password</label>
      <input id="account-password-confirm" type="password" autocomplete="new-password"
        class="w-full rounded-lg border border-line px-3.5 py-2.5 text-sm mb-5 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary" />

      <p id="account-error" class="text-sm text-red-600 mb-3 hidden"></p>

      <button onclick="saveAccount()"
        class="bg-ink hover:bg-[#0f211d] text-white font-display font-600 text-sm px-5 py-2.5 rounded-full transition-colors">
        Save changes
      </button>
    </div>
  `;
}

function saveAccount() {
  const name = document.getElementById("account-name").value.trim();
  const email = document.getElementById("account-email").value.trim();
  const password = document.getElementById("account-password").value;
  const passwordConfirm = document.getElementById("account-password-confirm").value;
  const errEl = document.getElementById("account-error");
  errEl.classList.add("hidden");

  if (!name || !email) {
    errEl.textContent = "Display name and email are required.";
    errEl.classList.remove("hidden");
    return;
  }
  if (password || passwordConfirm) {
    if (password !== passwordConfirm) {
      errEl.textContent = "New password and confirmation don't match.";
      errEl.classList.remove("hidden");
      return;
    }
  }

  const state = getState();
  state.me.username = name;
  state.me.email = email;
  setState(state);

  document.getElementById("user-email").textContent = email;
  document.getElementById("account-password").value = "";
  document.getElementById("account-password-confirm").value = "";
  showToast(password ? "Account and password updated." : "Account updated.");
}
