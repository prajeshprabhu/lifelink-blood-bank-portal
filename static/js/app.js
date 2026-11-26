async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  let data;
  try { data = await response.json(); } catch (_) { data = {}; }
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

function notify(message, isError = false) {
  const old = document.querySelector(".runtime-alert");
  if (old) old.remove();
  const alert = document.createElement("div");
  alert.className = `alert runtime-alert ${isError ? "alert-error" : "alert-success"}`;
  alert.textContent = message;
  document.querySelector(".content").prepend(alert);
  setTimeout(() => alert.remove(), 5000);
}

document.addEventListener("DOMContentLoaded", () => {
  if (window.renderIcons) renderIcons();
  document.getElementById("mobileMenu")?.addEventListener("click", () => {
    document.getElementById("sidebar").classList.toggle("open");
  });
  document.getElementById("logout")?.addEventListener("click", async (event) => {
    event.preventEvent?.();
    event.preventDefault();
    await fetch("/api/auth/logout", { method: "POST" });
    location.href = "/login";
  });
});
