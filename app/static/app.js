const form = document.getElementById("analyze-form");
const fileInput = document.getElementById("file-input");
const fileName = document.getElementById("file-name");
const dropzone = document.getElementById("dropzone");
const clearButton = document.getElementById("clear-button");
const analyzeButton = document.getElementById("analyze-button");
const titleInput = document.getElementById("title-input");
const abstractInput = document.getElementById("abstract-input");
const summaryText = document.getElementById("summary-text");
const scoreValue = document.getElementById("score-value");
const riskBadge = document.getElementById("risk-badge");
const matchesGrid = document.getElementById("matches-grid");
const allMatchesBadge = document.getElementById("all-matches-badge");
const highRiskCountBadge = document.getElementById("high-risk-count-badge");
const systemStatus = document.getElementById("system-status");

const initialSummary =
  "Upload a Word document or paste a project title and abstract to generate similarity matches, risk level, and uniqueness score.";

fileInput.addEventListener("change", () => {
  updateFileName();
});

["dragenter", "dragover"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragging");
  });
});

dropzone.addEventListener("drop", (event) => {
  const [file] = event.dataTransfer.files;
  if (!file) {
    return;
  }

  const transfer = new DataTransfer();
  transfer.items.add(file);
  fileInput.files = transfer.files;
  updateFileName();
});

clearButton.addEventListener("click", () => {
  form.reset();
  fileInput.value = "";
  updateFileName();
  resetResults();
  setSystemStatus("ready", "SYSTEM READY");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const hasFile = fileInput.files.length > 0;
  const hasText = titleInput.value.trim() || abstractInput.value.trim();

  if (!hasFile && !hasText) {
    setSystemStatus("error", "INPUT REQUIRED");
    summaryText.textContent = "Add a Word document or enter a project title or abstract before running similarity analysis.";
    return;
  }

  analyzeButton.disabled = true;
  analyzeButton.textContent = "Analyzing...";
  setSystemStatus("loading", "ANALYZING");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: buildRequestBody(hasFile),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Analysis failed.");
    }

    renderResults(payload);
    setSystemStatus("ready", "ANALYSIS COMPLETE");
  } catch (error) {
    resetResults();
    setSystemStatus("error", "SYSTEM ERROR");
    summaryText.textContent = error.message || "Unable to analyze the project right now.";
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.textContent = "Check Similarity";
  }
});

function buildRequestBody(hasFile) {
  const formData = new FormData();

  if (titleInput.value.trim()) {
    formData.append("title", titleInput.value.trim());
  }

  if (abstractInput.value.trim()) {
    formData.append("abstract", abstractInput.value.trim());
  }

  if (hasFile) {
    formData.append("file", fileInput.files[0]);
  }

  return formData;
}

function updateFileName() {
  fileName.textContent = fileInput.files.length ? fileInput.files[0].name : "No file selected";
}

function renderResults(payload) {
  const uniqueness = Number(payload.uniqueness_score || 0).toFixed(1);
  const risk = (payload.risk_level || "Low").toLowerCase();
  const matches = Array.isArray(payload.similar_projects) ? payload.similar_projects : [];
  const highRiskCount = matches.filter((match) => Number(match.similarity) >= 60).length;

  scoreValue.textContent = `${trimTrailingZero(uniqueness)}%`;
  scoreValue.style.color = riskColor(risk);
  summaryText.textContent = payload.summary || initialSummary;

  riskBadge.textContent = riskLabel(risk);
  riskBadge.className = `risk-pill ${risk}`;

  allMatchesBadge.textContent = `All Matches (${matches.length})`;
  highRiskCountBadge.textContent = `High Risk (${highRiskCount})`;

  if (!matches.length) {
    matchesGrid.innerHTML = emptyStateMarkup();
    return;
  }

  matchesGrid.innerHTML = matches.map((match) => createMatchCard(match)).join("");
}

function createMatchCard(match) {
  const similarity = Number(match.similarity || 0);
  const cardRisk = similarity >= 60 ? "high" : similarity >= 30 ? "medium" : "low";
  const description = buildMatchDescription(match);
  const year = match.year && match.year > 0 ? match.year : "Archive";

  return `
    <article class="match-card ${cardRisk}">
      <div class="match-head">
        <div>
          <h3>${escapeHtml(match.title || "Untitled Project")}</h3>
          <span class="domain-badge">${escapeHtml((match.domain || "General").replace("/", " | "))}</span>
        </div>
        <div class="match-score">${trimTrailingZero(similarity.toFixed(1))}%</div>
      </div>
      <p class="match-description">${escapeHtml(description)}</p>
      <div class="match-footer">
        <span class="footer-link">Project Match Reference</span>
        <span>MATCHED: ${escapeHtml(String(year))}</span>
      </div>
    </article>
  `;
}

function buildMatchDescription(match) {
  const similarity = Number(match.similarity || 0);
  if (similarity >= 70) {
    return `Strong structural and thematic overlap detected with the archived ${match.domain || "project"} submission. Review title, scope, and core workflow before final submission.`;
  }
  if (similarity >= 40) {
    return `Noticeable similarity exists in the problem framing or implementation direction. Consider differentiating the feature set, domain depth, or technical approach.`;
  }
  return "Only limited overlap was found with this archived project. The concept appears directionally related, but the overall solution space remains distinct.";
}

function resetResults() {
  scoreValue.textContent = "--%";
  scoreValue.style.color = "var(--green)";
  summaryText.textContent = initialSummary;
  riskBadge.textContent = "Awaiting Input";
  riskBadge.className = "risk-pill neutral";
  allMatchesBadge.textContent = "All Matches (0)";
  highRiskCountBadge.textContent = "High Risk (0)";
  matchesGrid.innerHTML = emptyStateMarkup();
}

function emptyStateMarkup() {
  return `
    <article class="match-card empty-state">
      <h3>No analysis yet</h3>
      <p>Run a similarity check to see matched projects, domains, and duplication risk indicators.</p>
    </article>
  `;
}

function setSystemStatus(mode, label) {
  systemStatus.className = `system-status ${mode}`;
  systemStatus.querySelector("span:last-child").textContent = label;
}

function riskLabel(risk) {
  if (risk === "high") return "Reject";
  if (risk === "medium") return "Review";
  return "Accept";
}

function riskColor(risk) {
  if (risk === "high") return "var(--red)";
  if (risk === "medium") return "var(--amber)";
  return "var(--green)";
}

function trimTrailingZero(value) {
  return String(value).replace(/\.0$/, "");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
