const form = document.getElementById("screeningForm");
const responseDiv = document.getElementById("screeningResponse");
const weightSliders = document.querySelectorAll(".weight-slider");
const weightPreview = document.getElementById("weightPreview");
const totalWeightBadge = document.getElementById("totalWeight");
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("files");
const fileList = document.getElementById("fileList");

// --- Weight Preview ---
function renderWeightPreview() {
  if (!weightPreview || !weightSliders.length) return;
  const values = {};
  weightSliders.forEach((slider) => {
    const key = slider.name.replace("weight_", "");
    values[key] = Number(slider.value || 0);
    // Update per-slider label
    const label = document.getElementById("val_" + key);
    if (label) label.textContent = values[key] + "%";
  });
  const total = Object.values(values).reduce((a, b) => a + b, 0);

  weightPreview.textContent = `K: ${values.keyword || 0}% | S: ${values.semantic || 0}% | E: ${values.experience || 0}% | A: ${values.achievements || 0}%`;

  if (totalWeightBadge) {
    totalWeightBadge.textContent = `Total: ${total}%`;
    totalWeightBadge.className = total === 100 ? "badge bg-success rounded-pill" : "badge bg-warning text-dark rounded-pill";
  }
}

weightSliders.forEach((slider) => slider.addEventListener("input", renderWeightPreview));

// --- Presets ---
document.querySelectorAll(".preset-btn").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("weight_keyword").value = btn.dataset.keyword;
    document.getElementById("weight_semantic").value = btn.dataset.semantic;
    document.getElementById("weight_experience").value = btn.dataset.experience;
    document.getElementById("weight_achievements").value = btn.dataset.achievements;
    renderWeightPreview();
  });
});

// --- Drag & Drop ---
if (dropZone && fileInput) {
  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    fileInput.files = e.dataTransfer.files;
    updateFileList();
  });

  fileInput.addEventListener("change", updateFileList);
}

function getFileIcon(name) {
  const ext = name.split(".").pop().toLowerCase();
  const icons = { pdf: "bi-file-earmark-pdf", docx: "bi-file-earmark-word", csv: "bi-file-earmark-spreadsheet", txt: "bi-file-earmark-text" };
  return icons[ext] || "bi-file-earmark";
}

function updateFileList() {
  if (!fileInput || !fileList) return;
  const files = fileInput.files;
  fileList.innerHTML = Array.from(files)
    .map((f) => `<div class="file-item"><i class="bi ${getFileIcon(f.name)}"></i>${f.name} <span class="text-muted">(${(f.size / 1024).toFixed(1)} KB)</span></div>`)
    .join("");
}

// --- Tooltips ---
document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => new bootstrap.Tooltip(el));

renderWeightPreview();

// --- Toast ---
function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `custom-toast toast-${type}`;
  const icon = type === "success" ? "check-circle-fill" : "exclamation-triangle-fill";
  const color = type === "success" ? "var(--green)" : "var(--red)";
  toast.innerHTML = `<i class="bi bi-${icon}" style="color:${color}"></i><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

// --- AI Loader ---
const loader = {
  el: document.getElementById("aiLoader"),
  show() {
    if (!this.el) return;
    this.el.classList.add("active");
    this.runSteps();
  },
  hide() {
    if (!this.el) return;
    this.el.classList.remove("active");
    document.querySelectorAll(".step-item").forEach((s) => s.classList.remove("active"));
  },
  async runSteps() {
    const steps = ["step1", "step2", "step3", "step4"];
    for (const stepId of steps) {
      const el = document.getElementById(stepId);
      if (el) el.classList.add("active");
      await new Promise((r) => setTimeout(r, 900));
      if (stepId !== steps[steps.length - 1] && el) {
        el.classList.remove("active");
      }
    }
  },
};

// --- JD Insights ---
const jdInput = document.getElementById("jdInput");
const jdInsights = document.getElementById("jdInsights");

function updateJDInsights() {
  if (!jdInput || !jdInsights) return;
  const text = jdInput.value.trim();
  if (text.length < 10) {
    jdInsights.innerHTML = `
      <div class="text-center py-3 cursor-pointer" onclick="document.getElementById('jdInput').focus()">
          <i class="bi bi-clipboard-plus fs-3 d-block mb-2 text-primary"></i>
          <span>Paste a Job Description to see extracted insights</span>
      </div>`;
    return;
  }

  const skills = [
    "Python","React","Flask","AWS","SQL","Machine Learning","Docker","Java","Go",
    "Node.js","TypeScript","Kubernetes","Azure","GCP","TensorFlow","PyTorch",
    "Pandas","NumPy","Scikit-Learn","NLTK","FastAPI","Django","Vue","Angular",
    "Next.js","Redis","MongoDB","PostgreSQL","CI/CD","Jenkins","Git","C++",
    "C#","PHP","Laravel","Spring","Swift","Kotlin","Flutter","Ruby","Rails",
  ];
  const foundSkills = skills.filter((s) => new RegExp(`\\b${s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i").test(text));

  const expMatch = text.match(/(\d+)\+?\s*years?/i);
  const experience = expMatch ? `${expMatch[1]}+ years` : "Not specified";

  let category = "General";
  if (/data|machine learning|ai|nlp/i.test(text)) category = "🧠 AI / Data Science";
  else if (/web|frontend|backend|fullstack/i.test(text)) category = "🌐 Web Development";
  else if (/cloud|devops|aws|azure/i.test(text)) category = "☁️ Cloud & DevOps";
  else if (/mobile|android|ios|flutter/i.test(text)) category = "📱 Mobile Development";

  jdInsights.innerHTML = `
    <div class="mb-3">
      <label class="d-block x-small fw-bold text-uppercase text-muted mb-1">Detected Category</label>
      <div class="badge bg-primary bg-opacity-10 text-primary border">${category}</div>
    </div>
    <div class="mb-3">
      <label class="d-block x-small fw-bold text-uppercase text-muted mb-1">Target Experience</label>
      <div class="fw-bold small">${experience}</div>
    </div>
    <div>
      <label class="d-block x-small fw-bold text-uppercase text-muted mb-1">Key Requirements (${foundSkills.length})</label>
      <div class="d-flex flex-wrap gap-1 mt-1">
        ${foundSkills.length ? foundSkills.map((s) => `<span class="badge bg-light text-muted border x-small">${s}</span>`).join("") : '<span class="text-muted x-small">No specific skills detected yet</span>'}
      </div>
    </div>`;
}

if (jdInput && jdInsights) {
  jdInput.addEventListener("input", debounce(updateJDInsights, 300));
  jdInput.addEventListener("paste", () => setTimeout(updateJDInsights, 10));
  updateJDInsights();
}

// --- Form Submit ---
if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(form);

    loader.show();
    if (responseDiv) responseDiv.innerHTML = "";

    try {
      const response = await fetch("/api/screen", { method: "POST", body: formData });
      const result = await response.json();
      loader.hide();

      if (result.ok) {
        showToast(`Successfully screened ${result.processed || 0} candidates!`);
        setTimeout(() => (window.location.href = "/dashboard"), 1200);
      } else {
        showToast(result.error || "Screening failed", "danger");
      }
    } catch (err) {
      loader.hide();
      showToast("A server error occurred. Please try again.", "danger");
    }
  });
}

// --- Utilities ---
function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

document.querySelectorAll(".template-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const jdField = document.querySelector("textarea[name='jd']");
    if (jdField) {
      jdField.value = btn.dataset.jd || "";
      updateJDInsights();
      jdField.focus();
    }
  });
});
