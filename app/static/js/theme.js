const root = document.documentElement;
const toggle = document.getElementById("themeToggle");
const themeIcon = document.getElementById("themeIcon");
const savedTheme = localStorage.getItem("resume_ai_theme") || "dark";

function applyTheme(mode) {
  root.setAttribute("data-theme", mode);
  root.setAttribute("data-bs-theme", mode);
  localStorage.setItem("resume_ai_theme", mode);
  if (themeIcon) {
    themeIcon.className = mode === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
  }
}

applyTheme(savedTheme);

if (toggle) {
  toggle.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    applyTheme(next);
  });
}
