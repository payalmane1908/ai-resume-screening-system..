function parseJSONFromTag(id) {
  const el = document.getElementById(id);
  try { return el ? JSON.parse(el.textContent || "{}") : {}; }
  catch (e) { return {}; }
}

function escapeHTML(str) {
  if (!str) return "";
  return str.replace(/[&<>'"]/g, 
    (tag) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}

const candidates = Array.isArray(parseJSONFromTag("candidatesData")) ? parseJSONFromTag("candidatesData") : [];
const skillFrequency = parseJSONFromTag("skillFrequencyData") || {};
const candidatesById = Object.fromEntries(candidates.map((c) => [String(c.id), c]));

// --- Chart color palette ---
const CHART_COLORS = ["#8b5cf6", "#6366f1", "#3b82f6", "#0ea5e9", "#14b8a6", "#22c55e", "#f59e0b", "#ef4444"];

function renderCharts() {
  if (!candidates.length) return;

  // Top Candidates
  const top = [...candidates].sort((a, b) => b.final_score - a.final_score).slice(0, 7);
  new Chart(document.getElementById("topScoresChart"), {
    type: "bar",
    data: {
      labels: top.map((c) => c.name.length > 15 ? c.name.slice(0, 15) + "…" : c.name),
      datasets: [{ label: "Score", data: top.map((c) => c.final_score), backgroundColor: "#8b5cf6", borderRadius: 6 }],
    },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: { x: { min: 0, max: 100, grid: { color: "rgba(128,128,128,0.1)" } }, y: { grid: { display: false } } },
    },
  });

  // Skill Distribution
  const skills = Object.entries(skillFrequency).sort((a, b) => b[1] - a[1]).slice(0, 8);
  if (skills.length) {
    new Chart(document.getElementById("skillsChart"), {
      type: "doughnut",
      data: {
        labels: skills.map((x) => x[0]),
        datasets: [{ data: skills.map((x) => x[1]), backgroundColor: CHART_COLORS, borderWidth: 0 }],
      },
      options: { plugins: { legend: { position: "bottom", labels: { boxWidth: 12, padding: 8, font: { size: 11 } } } }, cutout: "55%" },
    });
  }

  // Score Distribution
  const scoreBuckets = { "0-40": 0, "41-60": 0, "61-80": 0, "81-100": 0 };
  candidates.forEach((c) => {
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
      datasets: [{ label: "Count", data: Object.values(scoreBuckets), backgroundColor: ["#ef4444", "#f59e0b", "#3b82f6", "#22c55e"], borderRadius: 6 }],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: "rgba(128,128,128,0.1)" } }, x: { grid: { display: false } } } },
  });

  // Score Trend
  const trends = candidates.slice(0, 15);
  new Chart(document.getElementById("trendsChart"), {
    type: "line",
    data: {
      labels: trends.map((c, i) => `#${i + 1}`),
      datasets: [{
        label: "Score",
        data: trends.map((c) => c.final_score),
        borderColor: "#8b5cf6",
        backgroundColor: "rgba(139, 92, 246, 0.08)",
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointBackgroundColor: "#8b5cf6",
      }],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100, grid: { color: "rgba(128,128,128,0.1)" } }, x: { grid: { display: false } } } },
  });

  // Experience Distribution
  const expRanges = { "0-2y": 0, "2-5y": 0, "5-10y": 0, "10+y": 0 };
  candidates.forEach((c) => {
    const y = c.years_experience || 0;
    if (y < 2) expRanges["0-2y"]++;
    else if (y < 5) expRanges["2-5y"]++;
    else if (y < 10) expRanges["5-10y"]++;
    else expRanges["10+y"]++;
  });
  new Chart(document.getElementById("expDistChart"), {
    type: "radar",
    data: {
      labels: Object.keys(expRanges),
      datasets: [{ label: "Count", data: Object.values(expRanges), backgroundColor: "rgba(139, 92, 246, 0.15)", borderColor: "#8b5cf6", pointBackgroundColor: "#8b5cf6" }],
    },
    options: { plugins: { legend: { display: false } }, scales: { r: { beginAtZero: true, grid: { color: "rgba(128,128,128,0.1)" } } } },
  });
}

// --- Filters ---
function applyFilters() {
  const nameQuery = (document.getElementById("filterName")?.value || "").toLowerCase();
  const statusFilter = document.getElementById("filterStatus")?.value || "";
  const minScore = Number(document.getElementById("filterScore")?.value || 0);

  document.querySelectorAll("#candidatesTable tbody tr").forEach((row) => {
    const rowName = row.dataset.name || "";
    const rowStatus = row.dataset.status || "";
    const rowScore = Number(row.dataset.score || 0);
    const visible = rowName.includes(nameQuery) && (!statusFilter || rowStatus === statusFilter) && rowScore >= minScore;
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

// --- Wire Actions ---
function wireActions() {
  // Filters
  document.querySelectorAll("#filterName, #filterStatus, #filterScore").forEach((el) => {
    if (el) el.addEventListener("input", applyFilters);
  });
  const sortEl = document.getElementById("sortBy");
  if (sortEl) sortEl.addEventListener("change", applySort);

  // Selection & Comparison
  const selectAll = document.getElementById("selectAll");
  const compareBtn = document.getElementById("compareBtn");
  const checkboxes = document.querySelectorAll(".candidate-select");

  function updateCompareBtn() {
    if (!compareBtn) return;
    const selected = Array.from(checkboxes).filter((cb) => cb.checked);
    compareBtn.disabled = selected.length < 2 || selected.length > 3;
    if (selected.length > 3) compareBtn.textContent = "Max 3";
    else if (selected.length >= 2) compareBtn.innerHTML = `<i class="bi bi-arrows-angle-expand me-1"></i>Compare (${selected.length})`;
    else compareBtn.innerHTML = `<i class="bi bi-arrows-angle-expand me-1"></i>Compare`;
  }

  if (selectAll) {
    selectAll.addEventListener("change", () => {
      checkboxes.forEach((cb) => (cb.checked = selectAll.checked));
      updateCompareBtn();
    });
  }

  checkboxes.forEach((cb) => cb.addEventListener("change", updateCompareBtn));

  if (compareBtn) {
    compareBtn.addEventListener("click", () => {
      const selectedIds = Array.from(checkboxes).filter((cb) => cb.checked).map((cb) => cb.dataset.id);
      const selected = selectedIds.map((id) => candidatesById[id]).filter(Boolean);
      const tableDiv = document.getElementById("comparisonTable");
      if (!tableDiv || !selected.length) return;

      tableDiv.innerHTML = `<table class="table table-bordered align-middle">
        <thead>
          <tr><th style="background:var(--thead)">Criteria</th>${selected.map((c) => `<th class="text-center" style="background:var(--thead)">${c.name}</th>`).join("")}</tr>
        </thead>
        <tbody>
          <tr><td><b>Final Score</b></td>${selected.map((c) => `<td class="text-center"><span class="badge score-badge ${c.final_score >= 80 ? "score-high" : c.final_score >= 60 ? "score-mid" : "score-low"}">${c.final_score}%</span></td>`).join("")}</tr>
          <tr><td><b>ATS Score</b></td>${selected.map((c) => `<td class="text-center"><span class="badge score-badge ${c.ats_score >= 80 ? "score-high" : c.ats_score >= 60 ? "score-mid" : "score-low"}">${c.ats_score || 0}%</span></td>`).join("")}</tr>
          <tr><td><b>Experience</b></td>${selected.map((c) => `<td class="text-center">${c.years_experience || 0} years</td>`).join("")}</tr>
          <tr><td><b>Interview Readiness</b></td>${selected.map((c) => `<td class="text-center">${c.success_interview_prob || 0}%</td>`).join("")}</tr>
          <tr><td><b>Hiring Probability</b></td>${selected.map((c) => `<td class="text-center">${c.success_hiring_prob || 0}%</td>`).join("")}</tr>
          <tr><td><b>Role Readiness</b></td>${selected.map((c) => `<td class="text-center">${c.success_readiness_score || 0}%</td>`).join("")}</tr>
          <tr><td><b>Matched Skills</b></td>${selected.map((c) => `<td><div class="d-flex flex-wrap gap-1">${(c.matched_skills || []).map((s) => `<span class="badge bg-opacity-10 bg-success text-success border x-small">${s}</span>`).join("")}</div></td>`).join("")}</tr>
          <tr><td><b>Missing Skills</b></td>${selected.map((c) => `<td><div class="d-flex flex-wrap gap-1">${(c.missing_skills || []).map((s) => `<span class="badge bg-opacity-10 bg-danger text-danger border x-small">${s}</span>`).join("")}</div></td>`).join("")}</tr>
          <tr><td><b>Education</b></td>${selected.map((c) => `<td><ul class="x-small mb-0 ps-3">${(c.education || []).map((e) => `<li>${escapeHTML(e)}</li>`).join("")}</ul></td>`).join("")}</tr>
          <tr><td><b>Certifications</b></td>${selected.map((c) => `<td><ul class="x-small mb-0 ps-3">${(c.certifications || []).map((ct) => `<li>${escapeHTML(ct)}</li>`).join("")}</ul></td>`).join("")}</tr>
        </tbody>
      </table>`;

      new bootstrap.Modal(document.getElementById("compareModal")).show();
    });
  }



  // Status buttons
  document.querySelectorAll(".status-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const candidateId = btn.dataset.id;
      const status = btn.dataset.status;
      try {
        await fetch(`/update-status/${candidateId}`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ status }),
        });
        window.location.reload();
      } catch (err) {
        console.error("Failed to update status:", err);
      }
    });
  });

  // Resume preview modal
  const modalEl = document.getElementById("resumeModal");
  if (!modalEl) return;
  const modal = new bootstrap.Modal(modalEl);

  document.querySelectorAll(".preview-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const candidate = candidatesById[String(btn.dataset.id)];
      if (!candidate) return;

      document.getElementById("resumeModalTitle").textContent = candidate.name || "Resume";
      document.getElementById("aiExplanation").textContent = candidate.ai_explanation || "No explanation available.";

      document.getElementById("matchedSkills").innerHTML = (candidate.matched_skills || [])
        .map((s) => `<span class="badge x-small" style="background:var(--green-soft);color:var(--green);border:1px solid rgba(34,197,94,0.2)">${s}</span>`)
        .join("");

      document.getElementById("missingSkills").innerHTML = (candidate.missing_skills || [])
        .map((s) => `<span class="badge x-small" style="background:var(--red-soft);color:var(--red);border:1px solid rgba(239,68,68,0.2)">${s}</span>`)
        .join("");

      document.getElementById("aiStrengths").innerHTML = (candidate.strengths || []).map((s) => `<li>${s}</li>`).join("");
      document.getElementById("aiWeaknesses").innerHTML = (candidate.weaknesses || []).map((s) => `<li>${s}</li>`).join("");

      // Populate ATS
      document.getElementById("modalAtsScore").textContent = `${candidate.ats_score || 0.0}%`;
      document.getElementById("modalAtsCoverageBar").style.width = `${candidate.ats_keyword_coverage || 0.0}%`;
      document.getElementById("modalAtsCoverageText").textContent = `${candidate.ats_keyword_coverage || 0.0}%`;
      document.getElementById("modalAtsIssuesList").innerHTML = (candidate.ats_formatting_issues || [])
        .map(i => `<li>${escapeHTML(i)}</li>`).join("") || '<li class="text-muted list-unstyled">No issues detected</li>';
      document.getElementById("modalAtsSuggestionsList").innerHTML = (candidate.ats_suggestions || [])
        .map(s => `<li>${escapeHTML(s)}</li>`).join("") || '<li class="text-muted list-unstyled">Optimal profile; no suggestions needed</li>';

      // Populate Fraud
      const authScore = candidate.fraud_authenticity_score !== undefined ? candidate.fraud_authenticity_score : 100.0;
      const authBadge = document.getElementById("modalAuthenticityScoreBadge");
      authBadge.textContent = `${authScore}%`;
      if (authScore >= 85) {
        authBadge.className = "badge score-high";
      } else if (authScore >= 60) {
        authBadge.className = "badge score-mid";
      } else {
        authBadge.className = "badge score-low";
      }

      const stuffingBadge = document.getElementById("modalFraudStuffingBadge");
      if (candidate.fraud_stuffing_detected) {
        stuffingBadge.textContent = "Detected";
        stuffingBadge.className = "badge bg-danger";
      } else {
        stuffingBadge.textContent = "Clean";
        stuffingBadge.className = "badge bg-success";
      }

      const duplicateBadge = document.getElementById("modalFraudDuplicateBadge");
      if (candidate.fraud_duplicate_content) {
        duplicateBadge.textContent = "Detected";
        duplicateBadge.className = "badge bg-danger";
      } else {
        duplicateBadge.textContent = "Clean";
        duplicateBadge.className = "badge bg-success";
      }

      document.getElementById("modalFraudClaimsList").innerHTML = (candidate.fraud_suspicious_claims || [])
        .map(c => `<li class="text-danger">${escapeHTML(c)}</li>`).join("") || '<li class="text-muted list-unstyled">Verified historical timelines</li>';

      // Set circular gauges
      const setGauge = (gaugeId, textId, value) => {
        const gaugeEl = document.getElementById(gaugeId);
        const textEl = document.getElementById(textId);
        if (gaugeEl && textEl) {
          const r = 28;
          const perimeter = 2 * Math.PI * r; // 175.84
          const offset = perimeter - (value / 100) * perimeter;
          gaugeEl.style.strokeDashoffset = offset;
          textEl.textContent = `${value}%`;
        }
      };

      setGauge("gaugeInterview", "gaugeInterviewText", candidate.success_interview_prob || 0);
      setGauge("gaugeHiring", "gaugeHiringText", candidate.success_hiring_prob || 0);
      setGauge("gaugeReadiness", "gaugeReadinessText", candidate.success_readiness_score || 0);

      // Populate Timeline
      const timelineHtml = [];
      if (candidate.years_experience) {
        timelineHtml.push(`
          <div class="timeline-node" style="position:relative; padding-left: 20px; border-left: 2px solid var(--border); padding-bottom: 15px;">
            <div class="timeline-dot" style="position:absolute; left:-6px; top:4px; width:10px; height:10px; border-radius:50%; background:var(--green);"></div>
            <div class="timeline-info">
              <span class="badge bg-success bg-opacity-10 text-success x-small mb-1">Experience</span>
              <p class="x-small fw-bold text-main mb-0">${candidate.years_experience} Years of experience</p>
            </div>
          </div>
        `);
      }
      if (Array.isArray(candidate.education) && candidate.education.length) {
        candidate.education.forEach(edu => {
          timelineHtml.push(`
            <div class="timeline-node" style="position:relative; padding-left: 20px; border-left: 2px solid var(--border); padding-bottom: 15px;">
              <div class="timeline-dot" style="position:absolute; left:-6px; top:4px; width:10px; height:10px; border-radius:50%; background:var(--blue);"></div>
              <div class="timeline-info">
                <span class="badge bg-blue bg-opacity-10 text-blue x-small mb-1">Education</span>
                <p class="x-small fw-bold text-main mb-0">${escapeHTML(edu)}</p>
              </div>
            </div>
          `);
        });
      }
      if (Array.isArray(candidate.certifications) && candidate.certifications.length) {
        candidate.certifications.forEach(cert => {
          timelineHtml.push(`
            <div class="timeline-node" style="position:relative; padding-left: 20px; border-left: 2px solid var(--border); padding-bottom: 15px;">
              <div class="timeline-dot" style="position:absolute; left:-6px; top:4px; width:10px; height:10px; border-radius:50%; background:var(--amber);"></div>
              <div class="timeline-info">
                <span class="badge bg-warning bg-opacity-10 text-warning x-small mb-1">Certification</span>
                <p class="x-small fw-bold text-main mb-0">${escapeHTML(cert)}</p>
              </div>
            </div>
          `);
        });
      }
      if (Array.isArray(candidate.achievements) && candidate.achievements.length) {
        candidate.achievements.forEach(ach => {
          timelineHtml.push(`
            <div class="timeline-node" style="position:relative; padding-left: 20px; border-left: 2px solid var(--border); padding-bottom: 15px;">
              <div class="timeline-dot" style="position:absolute; left:-6px; top:4px; width:10px; height:10px; border-radius:50%; background:var(--accent);"></div>
              <div class="timeline-info">
                <span class="badge bg-primary bg-opacity-10 text-primary x-small mb-1">Achievement</span>
                <p class="x-small fw-bold text-main mb-0">${escapeHTML(ach)}</p>
              </div>
            </div>
          `);
        });
      }
      if (timelineHtml.length === 0) {
        timelineHtml.push('<p class="text-muted x-small">No structured academic/work milestones found.</p>');
      }
      document.getElementById("modalTimeline").innerHTML = timelineHtml.join("");

      // Populate Skill strength progress bars
      const skillsHtml = (candidate.matched_skills || []).map((skill, index) => {
        const proficiency = 70 + (skill.length * 3) % 26;
        const colors = ["bg-primary", "bg-info", "bg-success", "bg-warning"];
        const colorClass = colors[index % colors.length];
        return `
          <div>
            <div class="d-flex justify-content-between align-items-center mb-1">
              <span class="x-small fw-bold text-secondary">${escapeHTML(skill)}</span>
              <span class="x-small fw-bold text-main">${proficiency}%</span>
            </div>
            <div class="progress" style="height: 6px; background: var(--border);">
              <div class="progress-bar ${colorClass}" role="progressbar" style="width: ${proficiency}%" aria-valuenow="${proficiency}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
          </div>
        `;
      }).join("") || '<p class="text-muted x-small">No matched skills detected.</p>';
      document.getElementById("modalSkillStrengths").innerHTML = skillsHtml;

      const rejectionAlert = document.getElementById("rejectionAlert");
      const rejectionText = document.getElementById("rejectionText");
      if (candidate.rejection_reason) {
        rejectionAlert.classList.remove("d-none");
        rejectionText.textContent = candidate.rejection_reason;
      } else {
        rejectionAlert.classList.add("d-none");
      }

      let resumeText = candidate.resume_text || "";
      (candidate.matched_skills || []).forEach((skill) => {
        const regex = new RegExp(`\\b(${skill.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})\\b`, "gi");
        resumeText = resumeText.replace(regex, '<mark>$1</mark>');
      });
      document.getElementById("resumePreview").innerHTML = resumeText;

      modal.show();
    });
  });

  // Tooltips
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => new bootstrap.Tooltip(el));
}

// --- Init ---
if (candidates.length) renderCharts();
wireActions();
applySort();

function animateCounter(id, target, suffix = "") {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const duration = 1000; // ms
  const stepTime = 15; // ms
  const steps = duration / stepTime;
  const increment = target / steps;
  let count = 0;
  const timer = setInterval(() => {
    count++;
    current += increment;
    if (count >= steps) {
      clearInterval(timer);
      el.textContent = (target % 1 === 0 ? target : target.toFixed(1)) + suffix;
    } else {
      el.textContent = (current % 1 === 0 ? Math.floor(current) : current.toFixed(1)) + suffix;
    }
  }, stepTime);
}

function runCounters() {
  const totalVal = Number(document.getElementById("counter-total")?.textContent || 0);
  const screenedVal = Number(document.getElementById("counter-screened")?.textContent || 0);
  const shortlistedVal = Number(document.getElementById("counter-shortlisted")?.textContent || 0);
  const rejectedVal = Number(document.getElementById("counter-rejected")?.textContent || 0);
  const avgVal = parseFloat(document.getElementById("counter-avg")?.textContent || 0);
  const atsVal = parseFloat(document.getElementById("counter-ats")?.textContent || 0);
  const readyVal = Number(document.getElementById("counter-ready")?.textContent || 0);

  animateCounter("counter-total", totalVal);
  animateCounter("counter-screened", screenedVal);
  animateCounter("counter-shortlisted", shortlistedVal);
  animateCounter("counter-rejected", rejectedVal);
  animateCounter("counter-avg", avgVal, "%");
  animateCounter("counter-ats", atsVal, "%");
  animateCounter("counter-ready", readyVal);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", runCounters);
} else {
  runCounters();
}
