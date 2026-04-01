function parseJSONFromTag(id) {
  const el = document.getElementById(id);
  return el ? JSON.parse(el.textContent || "{}") : {};
}

const candidates = parseJSONFromTag("candidatesData") || [];
const skillFrequency = parseJSONFromTag("skillFrequencyData") || {};
const candidatesById = Object.fromEntries(candidates.map((c) => [String(c.id), c]));

function renderCharts() {
  const top = [...candidates].sort((a, b) => b.final_score - a.final_score).slice(0, 7);
  new Chart(document.getElementById("topScoresChart"), {
    type: "bar",
    data: {
      labels: top.map((c) => c.name),
      datasets: [{ 
        label: "Final Score", 
        data: top.map((c) => c.final_score), 
        backgroundColor: "#6366f1",
        borderRadius: 8
      }],
    },
    options: { 
      indexAxis: 'y',
      plugins: { legend: { display: false } }, 
      scales: { x: { min: 0, max: 100 } } 
    },
  });

  const skills = Object.entries(skillFrequency).sort((a, b) => b[1] - a[1]).slice(0, 8);
  new Chart(document.getElementById("skillsChart"), {
    type: "pie",
    data: {
      labels: skills.map((x) => x[0]),
      datasets: [{ 
        data: skills.map((x) => x[1]), 
        backgroundColor: ["#0ea5e9", "#6366f1", "#14b8a6", "#f59e0b", "#f43f5e", "#8b5cf6", "#22c55e", "#ef4444"],
        borderWidth: 0
      }],
    },
    options: { plugins: { legend: { position: 'bottom' } } },
  });

  // Score Distribution Chart
  const scoreBuckets = { "0-40": 0, "41-60": 0, "61-80": 0, "81-100": 0 };
  candidates.forEach(c => {
    const s = c.final_score;
    if (s <= 40) scoreBuckets["0-40"]++;
    else if (s <= 60) scoreBuckets["41-60"]++;
    else if (s <= 80) scoreBuckets["61-80"]++;
    else scoreBuckets["81-100"]++;
  });
  
  new Chart(document.getElementById("gapChart"), {
    type: "bar",
    data: { 
      labels: Object.keys(scoreBuckets), 
      datasets: [{ 
        label: "Candidate Count",
        data: Object.values(scoreBuckets),
        backgroundColor: 'rgba(99, 102, 241, 0.6)',
        borderRadius: 6
      }] 
    },
    options: { plugins: { legend: { display: false } } },
  });

  // Trends over time (Batch)
  const trends = candidates.slice(-10).map((c, i) => ({ x: i, y: c.final_score }));
  new Chart(document.getElementById("trendsChart"), {
    type: "line",
    data: {
      labels: trends.map(t => `C${t.x + 1}`),
      datasets: [{
        label: "Score Trend",
        data: trends.map(t => t.y),
        borderColor: "#10b981",
        backgroundColor: "rgba(16, 185, 129, 0.1)",
        fill: true,
        tension: 0.4
      }]
    },
    options: { 
      plugins: { legend: { display: false } },
      scales: { y: { min: 0, max: 100 } }
    }
  });

  // Experience Distribution
  const expRanges = { "0-2": 0, "2-5": 0, "5-10": 0, "10+": 0 };
  candidates.forEach(c => {
    const y = c.years_experience || 0;
    if (y < 2) expRanges["0-2"]++;
    else if (y < 5) expRanges["2-5"]++;
    else if (y < 10) expRanges["5-10"]++;
    else expRanges["10+"]++;
  });
  new Chart(document.getElementById("expDistChart"), {
    type: "radar",
    data: {
      labels: Object.keys(expRanges),
      datasets: [{
        label: "Experience Breakdown",
        data: Object.values(expRanges),
        backgroundColor: "rgba(245, 158, 11, 0.2)",
        borderColor: "#f59e0b",
        pointBackgroundColor: "#f59e0b"
      }]
    },
    options: { plugins: { legend: { display: false } } }
  });
}

function applyFilters() {
  const name = (document.getElementById("filterName").value || "").toLowerCase();
  const status = document.getElementById("filterStatus").value;
  const minScore = Number(document.getElementById("filterScore").value || 0);

  document.querySelectorAll("#candidatesTable tbody tr").forEach((row) => {
    const rowName = row.dataset.name || "";
    const rowStatus = row.dataset.status || "";
    const rowScore = Number(row.dataset.score || 0);
    const visible = rowName.includes(name) && (!status || rowStatus === status) && rowScore >= minScore;
    row.style.display = visible ? "" : "none";
  });
}

function applySort() {
  const tableBody = document.querySelector("#candidatesTable tbody");
  if (!tableBody) return;
  const mode = document.getElementById("sortBy")?.value || "rank_asc";
  const rows = Array.from(tableBody.querySelectorAll("tr"));
  rows.sort((a, b) => {
    if (mode === "score_desc") return Number(b.dataset.score || 0) - Number(a.dataset.score || 0);
    if (mode === "score_asc") return Number(a.dataset.score || 0) - Number(b.dataset.score || 0);
    if (mode === "name_asc") return (a.dataset.name || "").localeCompare(b.dataset.name || "");
    return Number(a.dataset.rank || 0) - Number(b.dataset.rank || 0);
  });
  rows.forEach((row) => tableBody.appendChild(row));
}

function wireActions() {
  document.querySelectorAll("#filterName,#filterStatus,#filterScore").forEach((el) => el.addEventListener("input", applyFilters));
  const sortEl = document.getElementById("sortBy");
  if (sortEl) sortEl.addEventListener("change", applySort);

  // Selection & Comparison
  const selectAll = document.getElementById("selectAll");
  const compareBtn = document.getElementById("compareBtn");
  const checkboxes = document.querySelectorAll(".candidate-select");

  if (selectAll) {
    selectAll.addEventListener("change", () => {
      checkboxes.forEach(cb => cb.checked = selectAll.checked);
      updateCompareBtn();
    });
  }

  checkboxes.forEach(cb => cb.addEventListener("change", updateCompareBtn));

  function updateCompareBtn() {
    const selected = Array.from(checkboxes).filter(cb => cb.checked);
    compareBtn.disabled = selected.length < 2 || selected.length > 3;
    compareBtn.textContent = selected.length > 3 ? "Select Max 3" : (selected.length < 2 ? "Compare" : `Compare (${selected.length})`);
  }

  compareBtn.addEventListener("click", () => {
    const selectedIds = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.dataset.id);
    const tableDiv = document.getElementById("comparisonTable");
    const candidates = selectedIds.map(id => candidatesById[id]);

    let html = `<table class="table table-bordered align-middle">
      <thead>
        <tr>
          <th class="bg-light">Criteria</th>
          ${candidates.map(c => `<th class="text-center bg-light">${c.name}</th>`).join("")}
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><b>Final Score</b></td>
          ${candidates.map(c => `<td class="text-center"><span class="badge score-badge ${c.final_score >= 80 ? 'score-high' : 'score-mid'}">${c.final_score}%</span></td>`).join("")}
        </tr>
        <tr>
          <td><b>Key Strengths</b></td>
          ${candidates.map(c => `<td><ul class="x-small mb-0">${(c.strengths || []).map(s => `<li>${s}</li>`).join("")}</ul></td>`).join("")}
        </tr>
        <tr>
          <td><b>Missing Skills</b></td>
          ${candidates.map(c => `<td><ul class="x-small mb-0 text-danger">${(c.missing_skills || []).map(s => `<li>${s}</li>`).join("")}</ul></td>`).join("")}
        </tr>
        <tr>
          <td><b>Experience</b></td>
          ${candidates.map(c => `<td class="text-center">${c.years_experience} years</td>`).join("")}
        </tr>
      </tbody>
    </table>`;
    tableDiv.innerHTML = html;
  });

  // AI Assistant
  const aiBtn = document.getElementById("aiAssistantBtn");
  const aiPanel = document.getElementById("aiAssistantPanel");
  const aiClose = document.getElementById("closeAiAssistant");
  const aiInput = document.getElementById("aiChatInput");
  const aiSend = document.getElementById("sendAiChat");
  const aiMessages = document.getElementById("aiChatMessages");

  aiBtn.addEventListener("click", () => aiPanel.classList.remove("d-none"));
  aiClose.addEventListener("click", () => aiPanel.classList.add("d-none"));

  async function sendAiMessage() {
    const text = aiInput.value.trim();
    if (!text) return;
    
    aiMessages.innerHTML += `<div class="mb-2 text-end"><b>You:</b> ${text}</div>`;
    aiInput.value = "";
    
    // Simple mock response logic
    let response = "I'm analyzing that for you...";
    if (text.toLowerCase().includes("top")) {
      response = `The top candidate is ${candidates[0]?.name} with a score of ${candidates[0]?.final_score}%.`;
    } else if (text.toLowerCase().includes("skills")) {
      response = "Common skills across candidates include: " + Object.keys(skillFrequency).slice(0, 5).join(", ");
    } else {
      response = "I recommend checking the 'Skill Gap Analyzer' to see what's missing in your top picks.";
    }
    
    setTimeout(() => {
      aiMessages.innerHTML += `<div class="mb-2"><b>AI:</b> ${response}</div>`;
      aiMessages.scrollTop = aiMessages.scrollHeight;
    }, 600);
  }

  aiSend.addEventListener("click", sendAiMessage);
  aiInput.addEventListener("keypress", (e) => { if (e.key === "Enter") sendAiMessage(); });

  // Original actions
  document.querySelectorAll(".status-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const candidateId = btn.dataset.id;
      const status = btn.dataset.status;
      await fetch(`/update-status/${candidateId}`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ status }),
      });
      window.location.reload();
    });
  });

  const modal = new bootstrap.Modal(document.getElementById("resumeModal"));
  document.querySelectorAll(".preview-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const candidate = candidatesById[String(btn.dataset.id)];
      if (!candidate) return;
      document.getElementById("resumeModalTitle").textContent = candidate.name || "Resume";
      
      const matchedEl = document.getElementById("matchedSkills");
      matchedEl.innerHTML = (candidate.matched_skills || []).map(s => `<span class="badge bg-success-subtle text-success border border-success-subtle x-small">${s}</span>`).join("");
      
      const missingEl = document.getElementById("missingSkills");
      missingEl.innerHTML = (candidate.missing_skills || []).map(s => `<span class="badge bg-danger-subtle text-danger border border-danger-subtle x-small">${s}</span>`).join("");
      
      document.getElementById("aiExplanation").textContent = candidate.ai_explanation || "No explanation available.";
      
      const strengthsEl = document.getElementById("aiStrengths");
      strengthsEl.innerHTML = (candidate.strengths || []).map(s => `<li>${s}</li>`).join("");
      
      const weaknessesEl = document.getElementById("aiWeaknesses");
      weaknessesEl.innerHTML = (candidate.weaknesses || []).map(s => `<li>${s}</li>`).join("");
      
      const rejectionAlert = document.getElementById("rejectionAlert");
      const rejectionText = document.getElementById("rejectionText");
      if (candidate.rejection_reason) {
        rejectionAlert.classList.remove("d-none");
        rejectionText.textContent = candidate.rejection_reason;
      } else {
        rejectionAlert.classList.add("d-none");
      }
      
      // Simple frontend highlighting
      let resumeText = candidate.resume_text || "";
      (candidate.matched_skills || []).forEach(skill => {
        const regex = new RegExp(`\\b(${skill})\\b`, 'gi');
        resumeText = resumeText.replace(regex, '<mark class="bg-success text-white px-1 rounded">$1</mark>');
      });
      document.getElementById("resumePreview").innerHTML = resumeText;
      modal.show();
    });
  });

  // Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

if (candidates.length) {
  renderCharts();
}
wireActions();
applySort();
