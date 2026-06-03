// --- Global AI Advisor Controller with Speech-to-Text & Smooth Hash Navigation ---

document.addEventListener("DOMContentLoaded", () => {
  const aiBtn = document.getElementById("aiAssistantBtn");
  const aiPanel = document.getElementById("aiAssistantPanel");
  const aiClose = document.getElementById("closeAiAssistant");
  const aiInput = document.getElementById("aiChatInput");
  const aiSend = document.getElementById("sendAiChat");
  const aiMessages = document.getElementById("aiChatMessages");
  const micBtn = document.getElementById("micBtn");

  // 1. Toggle AI Advisor Panel
  if (aiBtn && aiPanel) {
    aiBtn.addEventListener("click", () => {
      aiPanel.classList.toggle("d-none");
      if (!aiPanel.classList.contains("d-none") && aiInput) {
        aiInput.focus();
      }
    });
  }
  if (aiClose && aiPanel) {
    aiClose.addEventListener("click", () => aiPanel.classList.add("d-none"));
  }

  // 2. Chat Query API Call
  async function sendAiMessage() {
    if (!aiInput || !aiMessages) return;
    const text = aiInput.value.trim();
    if (!text) return;

    // Display user message
    aiMessages.innerHTML += `<div class="chat-msg user">${escapeHTML(text)}</div>`;
    aiInput.value = "";
    aiMessages.scrollTop = aiMessages.scrollHeight;

    // Loading indicator
    const loadingId = "msg-load-" + Date.now();
    aiMessages.innerHTML += `<div class="chat-msg bot" id="${loadingId}"><i class="bi bi-three-dots animate-pulse"></i> Thinking...</div>`;
    aiMessages.scrollTop = aiMessages.scrollHeight;

    try {
      const response = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const result = await response.json();
      
      // Remove loading indicator
      const loaderEl = document.getElementById(loadingId);
      if (loaderEl) loaderEl.remove();

      const reply = result.ok ? formatMarkdown(result.response) : "I encountered an error trying to process your request. Please try again.";
      aiMessages.innerHTML += `<div class="chat-msg bot">${reply}</div>`;
    } catch (err) {
      const loaderEl = document.getElementById(loadingId);
      if (loaderEl) loaderEl.remove();
      aiMessages.innerHTML += `<div class="chat-msg bot">Could not connect to the AI service. Make sure your server is online.</div>`;
    }
    aiMessages.scrollTop = aiMessages.scrollHeight;
  }

  if (aiSend) aiSend.addEventListener("click", sendAiMessage);
  if (aiInput) {
    aiInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") sendAiMessage();
    });
  }

  // 3. Speech-to-Text (Voice Recognition)
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition && micBtn && aiInput) {
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = "en-US";
    recognition.interimResults = false;

    let isRecording = false;

    recognition.onstart = () => {
      isRecording = true;
      micBtn.innerHTML = '<i class="bi bi-mic-mute-fill"></i>';
      micBtn.classList.remove("btn-outline-primary");
      micBtn.classList.add("btn-danger");
      aiInput.placeholder = "Listening to your voice...";
    };

    recognition.onend = () => {
      isRecording = false;
      micBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
      micBtn.classList.add("btn-outline-primary");
      micBtn.classList.remove("btn-danger");
      aiInput.placeholder = "Ask AI advisor...";
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      aiInput.value = transcript;
      aiInput.focus();
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
    };

    micBtn.addEventListener("click", () => {
      if (isRecording) {
        recognition.stop();
      } else {
        recognition.start();
      }
    });
  } else if (micBtn) {
    // Hide mic button or display helper if browser doesn't support Web Speech API
    micBtn.style.opacity = "0.5";
    micBtn.title = "Voice search not supported in this browser";
  }

  // 4. Tabbed Content Switcher & Navigation
  const validTabs = ["dashboard", "candidates", "analytics", "reports", "copilot", "interview", "skillgap"];

  function switchTab(tabId) {
    const panes = document.querySelectorAll(".tab-pane-custom");
    const navLinks = document.querySelectorAll(".sidebar-nav .nav-link-custom");
    if (!panes.length) return;

    // Toggle d-none on all custom panes
    panes.forEach((p) => p.classList.add("d-none"));
    const activePane = document.getElementById(tabId);
    if (activePane) activePane.classList.remove("d-none");

    // Update active highlight classes in the sidebar navigation
    const targetHash = "#" + tabId.replace("tab-", "");
    navLinks.forEach((link) => {
      link.classList.remove("active");
      const url = new URL(link.href, window.location.origin);
      if (url.hash === targetHash) {
        link.classList.add("active");
      }
    });
  }

  // Handle URL hash routing on initial page load
  window.addEventListener("load", () => {
    // If on the dashboard page, load weights history list dynamically
    if (document.getElementById("presetHistoryLogs")) {
      loadWeightsHistory();
      initAdvancedTabs();
    }

    const currentHash = window.location.hash.replace("#", "");
    if (validTabs.includes(currentHash)) {
      switchTab("tab-" + currentHash);
    } else if (document.getElementById("tab-dashboard")) {
      switchTab("tab-dashboard");
    }
  });

  // Handle hash changes on-the-fly (e.g. clicking sidebar links)
  window.addEventListener("hashchange", () => {
    const hash = window.location.hash.replace("#", "");
    if (validTabs.includes(hash)) {
      switchTab("tab-" + hash);
    }
  });

  // Load weights presets history list from backend
  async function loadWeightsHistory() {
    const logsContainer = document.getElementById("presetHistoryLogs");
    if (!logsContainer) return;
    try {
      const response = await fetch("/api/weights/history");
      const result = await response.json();
      if (result.ok && result.history.length) {
        logsContainer.innerHTML = result.history.map(h => {
          const date = new Date(h.created_at).toLocaleString();
          return `
            <div class="p-2 border rounded mb-2" style="background:var(--input-bg); border-color:var(--border) !important;">
              <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="x-small fw-bold text-main">Screening Run</span>
                <span class="x-small text-muted">${date}</span>
              </div>
              <div class="x-small text-muted">
                Skills: ${h.keyword_weight}% | Experience: ${h.semantic_weight}% | Education: ${h.experience_weight}% | Projects: ${h.achievements_weight}%
              </div>
            </div>`;
        }).join("");
      } else {
        logsContainer.innerHTML = '<div class="text-center py-3 text-muted x-small">No weight presets history logs available</div>';
      }
    } catch (e) {
      logsContainer.innerHTML = '<div class="text-center py-3 text-danger x-small">Failed to load preset logs</div>';
    }
  }

  // Initialize Advanced Workspace Tabs (Copilot, Interview Assistant, Skill Gap)
  function initAdvancedTabs() {
    const candidatesEl = document.getElementById("candidatesData");
    let poolCandidates = [];
    if (candidatesEl) {
      try { poolCandidates = JSON.parse(candidatesEl.textContent || "[]"); }
      catch (e) { poolCandidates = []; }
    }

    if (!poolCandidates.length) return;

    // --- 1. Interview Assistant ---
    const interviewSelect = document.getElementById("interviewCandidateSelect");
    if (interviewSelect) {
      interviewSelect.addEventListener("change", (e) => {
        renderInterviewQuestions(e.target.value, poolCandidates);
      });
      renderInterviewQuestions(poolCandidates[0].id, poolCandidates);
    }

    // --- 2. Skill Gap Analysis ---
    const skillGapSelect = document.getElementById("skillGapCandidateSelect");
    let gapGaugeChart = null;

    if (skillGapSelect) {
      skillGapSelect.addEventListener("change", (e) => {
        gapGaugeChart = renderSkillGap(e.target.value, poolCandidates, gapGaugeChart);
      });
      gapGaugeChart = renderSkillGap(poolCandidates[0].id, poolCandidates, gapGaugeChart);
    }

    // --- 3. AI Copilot Chat Pane ---
    const copilotSend = document.getElementById("sendCopilotChat");
    const copilotInput = document.getElementById("copilotChatInput");
    const copilotMessages = document.getElementById("copilotChatMessages");
    const copilotMicBtn = document.getElementById("copilotMicBtn");

    async function sendCopilotMessage() {
      if (!copilotInput || !copilotMessages) return;
      const text = copilotInput.value.trim();
      if (!text) return;

      copilotMessages.innerHTML += `<div class="chat-msg user">${escapeHTML(text)}</div>`;
      copilotInput.value = "";
      copilotMessages.scrollTop = copilotMessages.scrollHeight;

      const loadingId = "copilot-load-" + Date.now();
      copilotMessages.innerHTML += `<div class="chat-msg bot" id="${loadingId}"><i class="bi bi-three-dots animate-pulse"></i> Thinking...</div>`;
      copilotMessages.scrollTop = copilotMessages.scrollHeight;

      try {
        const response = await fetch("/api/ai/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text }),
        });
        const result = await response.json();
        
        const loaderEl = document.getElementById(loadingId);
        if (loaderEl) loaderEl.remove();

        const reply = result.ok ? formatMarkdown(result.response) : "I encountered an error. Please try again.";
        copilotMessages.innerHTML += `<div class="chat-msg bot">${reply}</div>`;
      } catch (err) {
        const loaderEl = document.getElementById(loadingId);
        if (loaderEl) loaderEl.remove();
        copilotMessages.innerHTML += `<div class="chat-msg bot">Connection error.</div>`;
      }
      copilotMessages.scrollTop = copilotMessages.scrollHeight;
    }

    if (copilotSend) copilotSend.addEventListener("click", sendCopilotMessage);
    if (copilotInput) {
      copilotInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendCopilotMessage();
      });
    }

    if (SpeechRecognition && copilotMicBtn && copilotInput) {
      const copilotRec = new SpeechRecognition();
      copilotRec.continuous = false;
      copilotRec.lang = "en-US";
      copilotRec.interimResults = false;

      let isCopilotRecording = false;

      copilotRec.onstart = () => {
        isCopilotRecording = true;
        copilotMicBtn.innerHTML = '<i class="bi bi-mic-mute-fill"></i>';
        copilotMicBtn.classList.remove("btn-outline-primary");
        copilotMicBtn.classList.add("btn-danger");
        copilotInput.placeholder = "Listening to your voice...";
      };

      copilotRec.onend = () => {
        isCopilotRecording = false;
        copilotMicBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
        copilotMicBtn.classList.add("btn-outline-primary");
        copilotMicBtn.classList.remove("btn-danger");
        copilotInput.placeholder = "Ask Copilot about your candidates...";
      };

      copilotRec.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        copilotInput.value = transcript;
        copilotInput.focus();
      };

      copilotMicBtn.addEventListener("click", () => {
        if (isCopilotRecording) {
          copilotRec.stop();
        } else {
          copilotRec.start();
        }
      });
    } else if (copilotMicBtn) {
      copilotMicBtn.style.opacity = "0.5";
      copilotMicBtn.title = "Voice search not supported";
    }
  }

  function renderInterviewQuestions(candidateId, poolCandidates) {
    const cand = poolCandidates.find(c => String(c.id) === String(candidateId));
    if (!cand) return;

    let tech = cand.questions_technical;
    let proj = cand.questions_project;
    let behav = cand.questions_behavioral;
    let hr = cand.questions_hr;

    // Fallback if null (for pre-existing screened candidates)
    if (!tech || !tech.length) {
      tech = [];
      const skills = cand.matched_skills || [];
      const hasSkill = (s) => skills.some(sk => sk.toLowerCase().includes(s.toLowerCase()));
      
      if (hasSkill("python")) {
        tech.push("Explain the memory management model and GIL limitations in Python.");
      }
      if (hasSkill("react") || hasSkill("javascript") || hasSkill("frontend")) {
        tech.push("What are React concurrent rendering features and how do you handle state?");
      }
      if (hasSkill("machine learning") || hasSkill("data science") || hasSkill("ml")) {
        tech.push("How do you select loss functions and avoid overfitting in neural networks?");
      }
      if (!tech.length) {
        const primary = skills[0] || "software engineering";
        tech.push(`Walk me through the system architecture and best practices using ${primary}.`);
        tech.push(`How do you handle testing, debugging, and caching for ${primary} systems?`);
      }
      tech.push("Explain standard scalability strategies and how you optimize slow database operations.");
    }

    if (!proj || !proj.length) {
      proj = [
        "What was the most challenging technical bottleneck in your projects, and how did you resolve it?",
        "How did you design the schema, data flow, and services integration for your portfolio systems?"
      ];
    }

    if (!behav || !behav.length) {
      behav = [
        "Tell me about a time you had to deliver a high-stakes feature under a tight launch deadline.",
        "How do you handle design disagreements or code review disputes within your development team?"
      ];
    }

    if (!hr || !hr.length) {
      const exp = cand.years_experience || 0;
      hr = [
        "Why does this company and the target role match your career aspirations at this point?",
        `How do your ${exp} years of technical experience prepare you for this role's responsibilities?`
      ];
    }
    
    const buildList = (list) => (list || [])
      .map(q => `
        <div class="p-3 border rounded" style="background:var(--input-bg); border-color:var(--border) !important; transition: all 0.2s var(--transition);">
          <div class="d-flex justify-content-between align-items-start gap-2">
            <span class="small text-main" style="line-height: 1.5;">${escapeHTML(q)}</span>
            <button class="btn btn-link btn-sm text-primary p-0 shadow-none border-0 text-decoration-none copy-q-btn" data-text="${q.replace(/"/g, '&quot;')}"><i class="bi bi-copy"></i></button>
          </div>
        </div>`).join("") || '<div class="text-muted small">No questions generated.</div>';

    document.getElementById("techQuestionsList").innerHTML = buildList(tech);
    document.getElementById("projectQuestionsList").innerHTML = buildList(proj);
    document.getElementById("behavioralQuestionsList").innerHTML = buildList(behav);
    document.getElementById("hrQuestionsList").innerHTML = buildList(hr);

    // Copy handlers
    document.querySelectorAll(".copy-q-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        navigator.clipboard.writeText(btn.dataset.text);
        const icon = btn.querySelector("i");
        icon.className = "bi bi-check text-success";
        setTimeout(() => { icon.className = "bi bi-copy"; }, 1500);
      });
    });
  }

  function renderSkillGap(candidateId, poolCandidates, gapGaugeChart) {
    const cand = poolCandidates.find(c => String(c.id) === String(candidateId));
    if (!cand) return gapGaugeChart;

    document.getElementById("gapKeywordScore").textContent = `${cand.keyword_score}%`;
    document.getElementById("gapSemanticScore").textContent = `${cand.semantic_score}%`;
    document.getElementById("gapAtsScore").textContent = `${cand.ats_score || 0}%`;

    document.getElementById("gapMatchedSkillsList").innerHTML = (cand.matched_skills || [])
      .map(s => `<span class="badge bg-success bg-opacity-10 text-success border px-2 py-1 x-small">${escapeHTML(s)}</span>`)
      .join("") || '<span class="text-muted small">No matched skills.</span>';

    document.getElementById("gapMissingSkillsList").innerHTML = (cand.missing_skills || [])
      .map(s => `<span class="badge bg-danger bg-opacity-10 text-danger border px-2 py-1 x-small">${escapeHTML(s)}</span>`)
      .join("") || '<span class="text-muted small">No gaps detected.</span>';

    const canvas = document.getElementById("gapEvolutionGaugeChart");
    if (!canvas) return gapGaugeChart;

    if (gapGaugeChart) {
      gapGaugeChart.destroy();
    }

    const newChart = new Chart(canvas, {
      type: "bar",
      data: {
        labels: ["Keyword Match", "Semantic Alignment", "ATS Optimization", "Overall Fit"],
        datasets: [
          {
            label: "Score Metric %",
            data: [cand.keyword_score, cand.semantic_score, cand.ats_score || 0, cand.final_score],
            backgroundColor: ["#3b82f6", "#8b5cf6", "#7c3aed", "#22c55e"],
            borderRadius: 6
          }
        ]
      },
      options: {
        indexAxis: "y",
        plugins: { legend: { display: false } },
        scales: {
          x: { min: 0, max: 100, grid: { color: "rgba(128,128,128,0.1)" } },
          y: { grid: { display: false } }
        }
      }
    });

    return newChart;
  }

  // Custom handler to enable settings scroll from other pages
  document.querySelectorAll('a[href*="#"]').forEach((link) => {
    link.addEventListener("click", (e) => {
      const url = new URL(link.href);
      if (url.pathname === window.location.pathname) {
        const hash = url.hash.replace("#", "");
        if (validTabs.includes(hash)) {
          e.preventDefault();
          window.location.hash = url.hash;
        } else {
          const target = document.querySelector(url.hash);
          if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        }
      }
    });
  });

  // Utility to escape HTML
  function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
      (tag) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
  }

  // Basic markdown formatting helper for bot responses
  function formatMarkdown(text) {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/### (.*?)\n/g, '<h5>$1</h5>')
      .replace(/## (.*?)\n/g, '<h4>$1</h4>')
      .replace(/- (.*?)\n/g, '<li>$1</li>')
      .replace(/\n/g, '<br>');
  }
});
