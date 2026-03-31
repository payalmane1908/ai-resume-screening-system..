const root = document.documentElement;
const toggle = document.getElementById("themeToggle");
const savedTheme = localStorage.getItem("resume_ai_theme") || "dark";

function applyTheme(mode) {
  root.setAttribute("data-theme", mode);
  localStorage.setItem("resume_ai_theme", mode);
  if (toggle) {
    toggle.textContent = mode === "dark" ? "Light" : "Dark";
  }
}

applyTheme(savedTheme);

if (toggle) {
  toggle.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    applyTheme(next);
  });
}
