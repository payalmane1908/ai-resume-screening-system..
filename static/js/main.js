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

if (form) {
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    data.set("replace_existing", document.getElementById("replaceExisting").checked ? "true" : "false");

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/screen", true);

    progressWrap.classList.remove("d-none");
    progressBar.style.width = "0%";
    progressBar.textContent = "0%";
    responseDiv.innerHTML = "";

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100);
        progressBar.style.width = `${percent}%`;
        progressBar.textContent = `${percent}%`;
      }
    };

    xhr.onload = () => {
      const contentType = xhr.getResponseHeader("Content-Type") || "";
      try {
        const payload = contentType.includes("application/json")
          ? JSON.parse(xhr.responseText)
          : { ok: false, error: xhr.responseText || "Server returned non-JSON response." };
        if (xhr.status >= 200 && xhr.status < 300 && payload.ok) {
          const errors = (payload.errors || []).map((x) => `<li>${x}</li>`).join("");
          responseDiv.innerHTML = `
            <div class="alert alert-success">
              Processed <b>${payload.processed}</b> resumes. Top match: <b>${payload.top_candidate || "-"}</b>.
            </div>
            ${errors ? `<div class="alert alert-warning"><b>Warnings</b><ul class="mb-0">${errors}</ul></div>` : ""}
            <a href="/dashboard" class="btn btn-dark btn-sm">View Dashboard</a>
          `;
        } else {
          responseDiv.innerHTML = `<div class="alert alert-danger">${payload.error || "Screening failed"}</div>`;
        }
      } catch (_error) {
        const fallback = (xhr.responseText || "").slice(0, 350);
        responseDiv.innerHTML = `<div class="alert alert-danger">Unexpected server response. ${fallback}</div>`;
      }
    };

    xhr.onerror = () => {
      responseDiv.innerHTML = `<div class="alert alert-danger">Network error during upload.</div>`;
    };

    xhr.send(data);
  });
}

document.querySelectorAll(".template-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const jdField = document.querySelector("textarea[name='jd']");
    jdField.value = btn.dataset.jd || "";
    jdField.focus();
  });
});
