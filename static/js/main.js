const form = document.getElementById("screeningForm");
const progressWrap = document.getElementById("uploadProgressWrap");
const progressBar = document.getElementById("uploadProgressBar");
const responseDiv = document.getElementById("screeningResponse");
const weightSliders = document.querySelectorAll(".weight-slider");
const weightPreview = document.getElementById("weightPreview");
const totalWeightBadge = document.getElementById("totalWeight");
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("files");
const fileCount = document.getElementById("fileCount");
const fileList = document.getElementById("fileList");

function renderWeightPreview() {
  if (!weightPreview || !weightSliders.length) return;
  const values = Object.fromEntries(
    Array.from(weightSliders).map((slider) => [slider.name, Number(slider.value || 0)])
  );
  const total = Object.values(values).reduce((a, b) => a + b, 0);
  
  weightPreview.textContent = `Keyword ${values.weight_keyword}% | Semantic ${values.weight_semantic}% | Experience ${values.weight_experience}% | Achievements ${values.weight_achievements}%`;
  
  if (totalWeightBadge) {
    totalWeightBadge.textContent = `Total: ${total}%`;
    totalWeightBadge.className = total === 100 ? "badge bg-success" : "badge bg-warning text-dark";
  }
}

weightSliders.forEach((slider) => slider.addEventListener("input", renderWeightPreview));

// Preset handling
document.querySelectorAll(".preset-btn").forEach(btn => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("weight_keyword").value = btn.dataset.keyword;
    document.getElementById("weight_semantic").value = btn.dataset.semantic;
    document.getElementById("weight_experience").value = btn.dataset.experience;
    document.getElementById("weight_achievements").value = btn.dataset.achievements;
    renderWeightPreview();
  });
});

// Drag and drop handling
if (dropZone && fileInput) {
  dropZone.addEventListener("click", () => fileInput.click());
  
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("border-primary");
  });
  
  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("border-primary");
  });
  
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-primary");
    fileInput.files = e.dataTransfer.files;
    updateFileList();
  });
  
  fileInput.addEventListener("change", updateFileList);
}

function updateFileList() {
  const files = fileInput.files;
  fileCount.textContent = `${files.length} files selected`;
  fileList.innerHTML = Array.from(files).map(f => `<div class="file-item">${f.name} (${(f.size/1024).toFixed(1)} KB)</div>`).join("");
}

// Initialize tooltips
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl);
});

renderWeightPreview();

// Toast Helper
function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `custom-toast toast-${type}`;
  const icon = type === "success" ? "check-circle" : "exclamation-triangle";
  toast.innerHTML = `<i class="bi bi-${icon} text-${type}"></i><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

// AI Loader Controller
const loader = {
  el: document.getElementById("aiLoader"),
  show() {
    this.el.classList.add("active");
    this.runSteps();
  },
  hide() {
    this.el.classList.remove("active");
  },
  async runSteps() {
    const steps = ["step1", "step2", "step3", "step4"];
    for (const stepId of steps) {
      document.getElementById(stepId).classList.add("active");
      await new Promise(r => setTimeout(r, 800));
      if (stepId !== steps[steps.length - 1]) {
        document.getElementById(stepId).classList.remove("active");
      }
    }
  }
};

// JD Insights Panel Update
const jdInput = document.getElementById("jdInput");
const jdInsights = document.getElementById("jdInsights");

if (jdInput && jdInsights) {
  jdInput.addEventListener("input", debounce(() => {
    const text = jdInput.value.trim();
    if (text.length < 50) return;

    // Simple Extraction Logic
    const skills = ["Python", "React", "Flask", "AWS", "SQL", "Machine Learning", "Docker", "Java", "Go"];
    const foundSkills = skills.filter(s => new RegExp(`\\b${s}\\b`, 'i').test(text));
    
    let expMatch = text.match(/(\d+)\+?\s*years?/i);
    let experience = expMatch ? `${expMatch[1]}+ years` : "Not specified";

    let category = "General";
    if (/data|machine learning|ai|nlp/i.test(text)) category = "AI / Data Science";
    else if (/web|frontend|backend|fullstack/i.test(text)) category = "Web Development";
    else if (/cloud|devops|aws|azure/i.test(text)) category = "Cloud & DevOps";

    jdInsights.innerHTML = `
      <div class="mb-3">
        <label class="d-block x-small fw-bold text-uppercase text-muted mb-1">Detected Category</label>
        <div class="badge bg-primary-subtle text-primary border border-primary-subtle">${category}</div>
      </div>
      <div class="mb-3">
        <label class="d-block x-small fw-bold text-uppercase text-muted mb-1">Target Experience</label>
        <div class="text-main fw-bold">${experience}</div>
      </div>
      <div>
        <label class="d-block x-small fw-bold text-uppercase text-muted mb-1">Key Requirements</label>
        <div class="d-flex flex-wrap gap-1 mt-1">
          ${foundSkills.length ? foundSkills.map(s => `<span class="badge bg-light text-muted border">${s}</span>`).join("") : '<span class="text-muted">Analyzing...</span>'}
        </div>
      </div>
    `;
  }, 1000));
}

if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(form);

    loader.show();
    responseDiv.innerHTML = "";

    try {
      const response = await fetch("/api/screen", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      loader.hide();

      if (result.ok) {
        showToast(`Successfully screened ${result.candidates ? result.candidates.length : (result.processed || 0)} candidates!`);
        setTimeout(() => window.location.href = "/dashboard", 1000);
      } else {
        showToast(result.error || "Screening failed", "danger");
      }
    } catch (err) {
      loader.hide();
      showToast("A server error occurred. Please try again.", "danger");
    }
  });
}

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

document.querySelectorAll(".template-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const jdField = document.querySelector("textarea[name='jd']");
    jdField.value = btn.dataset.jd || "";
    jdField.focus();
  });
});
