const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const clearBtn = document.getElementById("clearBtn");
const topicInput = document.getElementById("topicInput");
const taskBoard = document.getElementById("taskBoard");
const activityList = document.getElementById("activityList");
const reportRendered = document.getElementById("reportRendered");
const reportRaw = document.getElementById("reportRaw");
const reportMeta = document.getElementById("reportMeta");
const statusLine = document.getElementById("statusLine");
const statusBadge = document.getElementById("statusBadge");
const elapsedText = document.getElementById("elapsedText");
const progressText = document.getElementById("progressText");
const taskCountText = document.getElementById("taskCountText");
const lastUpdateText = document.getElementById("lastUpdateText");
const progressFill = document.getElementById("progressFill");
const toggleRawBtn = document.getElementById("toggleRawBtn");
const copyReportBtn = document.getElementById("copyReportBtn");
const downloadReportBtn = document.getElementById("downloadReportBtn");
const toggleAutoScrollBtn = document.getElementById("toggleAutoScrollBtn");

let activeStream = null;
let runStartedAt = null;
let elapsedTimer = null;
let autoScroll = true;
let showRawReport = false;
let reportMarkdown = "";
const tasks = new Map();
const summaryBuffers = new Map();

function nowTime() {
  return new Date().toLocaleTimeString();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function setStatus(text, kind = "idle") {
  statusLine.textContent = text;
  statusBadge.textContent = kind === "running" ? "Running" : kind === "done" ? "Done" : kind === "error" ? "Error" : "Idle";
  statusBadge.className = `status-pill ${kind}`;
  lastUpdateText.textContent = nowTime();
}

function appendActivity(message, kind = "info") {
  const li = document.createElement("li");
  li.className = `activity-item ${kind === "error" ? "error" : ""}`;
  li.innerHTML = `<time>${nowTime()}</time>${escapeHtml(message)}`;
  activityList.appendChild(li);
  if (autoScroll) {
    activityList.scrollTop = activityList.scrollHeight;
  }
}

function formatDuration(ms) {
  const total = Math.floor(ms / 1000);
  const m = String(Math.floor(total / 60)).padStart(2, "0");
  const s = String(total % 60).padStart(2, "0");
  return `${m}:${s}`;
}

function startElapsedTimer() {
  runStartedAt = Date.now();
  elapsedText.textContent = "00:00";
  if (elapsedTimer) {
    clearInterval(elapsedTimer);
  }
  elapsedTimer = setInterval(() => {
    if (!runStartedAt) {
      return;
    }
    elapsedText.textContent = formatDuration(Date.now() - runStartedAt);
  }, 500);
}

function stopElapsedTimer() {
  if (elapsedTimer) {
    clearInterval(elapsedTimer);
    elapsedTimer = null;
  }
}

function ensureTask(taskId) {
  if (!tasks.has(taskId)) {
    tasks.set(taskId, { id: taskId, status: "pending", title: `Task ${taskId}` });
  }
  return tasks.get(taskId);
}

function computeProgress() {
  const list = [...tasks.values()];
  const total = list.length;
  const done = list.filter((x) => x.status === "completed").length;
  progressText.textContent = `${done} / ${total}`;
  taskCountText.textContent = total === 0 ? "No tasks" : `${total} tasks`;
  const ratio = total === 0 ? 0 : Math.round((done / total) * 100);
  progressFill.style.width = `${ratio}%`;
}

function renderTasks() {
  const items = [...tasks.values()].sort((a, b) => a.id - b.id);
  if (items.length === 0) {
    taskBoard.innerHTML = `<p class="muted small">Tasks appear after planning.</p>`;
    computeProgress();
    return;
  }

  taskBoard.innerHTML = items
    .map((task) => {
      const summary = task.summary || "";
      const sources = task.sources_summary || "";
      const rounds = Array.isArray(task.round_queries) ? task.round_queries.join("\n") : "";
      return `
        <article class="task-card">
          <div class="task-head">
            <h3 class="task-title">${task.id}. ${escapeHtml(task.title || "Untitled")}</h3>
            <span class="badge ${task.status || "pending"}">${task.status || "pending"}</span>
          </div>
          <div class="task-meta">Intent: ${escapeHtml(task.intent || "")}</div>
          <div class="task-meta">Query: ${escapeHtml(task.query || "")}</div>
          ${rounds ? `<div class="task-block"><strong>Round queries</strong>\n${escapeHtml(rounds)}</div>` : ""}
          ${sources ? `<div class="task-block"><strong>Sources</strong>\n${escapeHtml(sources)}</div>` : ""}
          ${summary ? `<div class="task-block"><strong>Summary</strong>\n${escapeHtml(summary)}</div>` : ""}
        </article>
      `;
    })
    .join("");
  computeProgress();
}

function mdInline(text) {
  return text
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function renderMarkdown(md) {
  if (typeof marked !== 'undefined') {
    return marked.parse(md);
  }
  // Fallback if marked fails to load
  const lines = md.split(/\r?\n/);
  const html = [];
  let inList = false;
  let inCode = false;

  const closeList = () => {
    if (inList) {
      html.push("</ul>");
      inList = false;
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();

    if (line.startsWith("```")) {
      closeList();
      if (!inCode) {
        html.push("<pre><code>");
        inCode = true;
      } else {
        html.push("</code></pre>");
        inCode = false;
      }
      continue;
    }

    if (inCode) {
      html.push(`${escapeHtml(rawLine)}\n`);
      continue;
    }

    if (/^###\s+/.test(line)) {
      closeList();
      html.push(`<h3>${mdInline(escapeHtml(line.replace(/^###\s+/, "")))}</h3>`);
      continue;
    }
    if (/^##\s+/.test(line)) {
      closeList();
      html.push(`<h2>${mdInline(escapeHtml(line.replace(/^##\s+/, "")))}</h2>`);
      continue;
    }
    if (/^#\s+/.test(line)) {
      closeList();
      html.push(`<h1>${mdInline(escapeHtml(line.replace(/^#\s+/, "")))}</h1>`);
      continue;
    }
    if (/^[-*]\s+/.test(line)) {
      if (!inList) {
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${mdInline(escapeHtml(line.replace(/^[-*]\s+/, "")))}</li>`);
      continue;
    }

    closeList();
    if (line === "") {
      html.push("<p></p>");
    } else {
      html.push(`<p>${mdInline(escapeHtml(line))}</p>`);
    }
  }
  closeList();
  if (inCode) {
    html.push("</code></pre>");
  }
  return html.join("");
}

function renderReport() {
  if (!reportMarkdown) {
    reportRendered.classList.add("empty");
    reportRendered.textContent = "Report will appear here after completion.";
    reportRaw.textContent = "";
    reportMeta.textContent = "No report generated yet.";
    return;
  }
  reportRendered.classList.remove("empty");
  reportRendered.innerHTML = renderMarkdown(reportMarkdown);
  reportRaw.textContent = reportMarkdown;
  reportMeta.textContent = `Updated at ${nowTime()}`;
}

function setRunningState(running) {
  startBtn.disabled = running;
  stopBtn.disabled = !running;
  topicInput.disabled = running;
}

function resetRunState({ clearTopic = false } = {}) {
  if (activeStream) {
    activeStream.close();
    activeStream = null;
  }
  stopElapsedTimer();
  runStartedAt = null;
  elapsedText.textContent = "00:00";
  tasks.clear();
  summaryBuffers.clear();
  if (clearTopic) {
    topicInput.value = "";
  }
  reportMarkdown = "";
  renderTasks();
  renderReport();
  activityList.innerHTML = "";
  setRunningState(false);
  setStatus("Ready. Press Ctrl + Enter to run.", "idle");
}

function finishRun(statusKind, statusMessage) {
  if (activeStream) {
    activeStream.close();
    activeStream = null;
  }
  stopElapsedTimer();
  setRunningState(false);
  setStatus(statusMessage, statusKind);
}

function handleEvent(event) {
  const type = event.type;

  if (type === "status") {
    setStatus(event.message || "Running...", "running");
    appendActivity(event.message || "Status update");
    return;
  }

  if (type === "todo_list") {
    const incoming = Array.isArray(event.tasks) ? event.tasks : [];
    for (const item of incoming) {
      tasks.set(item.id, { ...item, status: item.status || "pending" });
    }
    renderTasks();
    appendActivity(`Planner generated ${incoming.length} tasks.`);
    return;
  }

  if (type === "task_status") {
    const task = ensureTask(event.task_id);
    Object.assign(task, event);
    if (!task.summary && summaryBuffers.has(task.id)) {
      task.summary = summaryBuffers.get(task.id);
    }
    renderTasks();
    appendActivity(`Task ${task.id} is ${task.status}.`);
    return;
  }

  if (type === "sources") {
    const task = ensureTask(event.task_id);
    task.sources_summary = event.sources_summary || "";
    task.round_queries = event.round_queries || [];
    renderTasks();
    appendActivity(`Task ${task.id}: sources collected.`);
    return;
  }

  if (type === "task_summary_chunk") {
    const task = ensureTask(event.task_id);
    const prev = summaryBuffers.get(task.id) || "";
    const next = prev + (event.content || "");
    summaryBuffers.set(task.id, next);
    task.summary = next;
    renderTasks();
    return;
  }

  if (type === "final_report") {
    reportMarkdown = event.report || "";
    renderReport();
    appendActivity("Final report generated.");
    return;
  }

  if (type === "error") {
    appendActivity(`Error: ${event.detail || "Unknown error"}`, "error");
    finishRun("error", "Research failed.");
    return;
  }

  if (type === "done") {
    finishRun("done", "Research completed.");
  }
}

function startResearch() {
  const topic = topicInput.value.trim();
  if (!topic) {
    setStatus("Please enter a topic first.", "error");
    return;
  }

  resetRunState();
  setRunningState(true);
  startElapsedTimer();
  setStatus("Starting research workflow...", "running");
  appendActivity("Connecting to stream...");

  const query = new URLSearchParams({ topic, search_api: "duckduckgo" }).toString();
  activeStream = new EventSource(`/research/stream/get?${query}`);

  activeStream.onmessage = (msg) => {
    try {
      const payload = JSON.parse(msg.data);
      handleEvent(payload);
    } catch (error) {
      appendActivity(`Parse error: ${error.message}`, "error");
    }
  };

  activeStream.onerror = () => {
    appendActivity("Stream disconnected unexpectedly.", "error");
    finishRun("error", "Disconnected.");
  };
}

function stopResearch() {
  appendActivity("Stopped by user.");
  finishRun("idle", "Stopped.");
}

function copyReport() {
  if (!reportMarkdown) {
    appendActivity("No report to copy.");
    return;
  }
  navigator.clipboard
    .writeText(reportMarkdown)
    .then(() => appendActivity("Report copied to clipboard."))
    .catch((err) => appendActivity(`Copy failed: ${err.message}`, "error"));
}

function downloadReport() {
  if (!reportMarkdown) {
    appendActivity("No report to download.");
    return;
  }
  const blob = new Blob([reportMarkdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  const safeName = (topicInput.value.trim() || "research-report").replace(/[^a-z0-9]+/gi, "-").toLowerCase();
  a.href = url;
  a.download = `${safeName}-report.md`;
  a.click();
  URL.revokeObjectURL(url);
  appendActivity("Report downloaded.");
}

function toggleRaw() {
  showRawReport = !showRawReport;
  reportRendered.classList.toggle("hidden", showRawReport);
  reportRaw.classList.toggle("hidden", !showRawReport);
  toggleRawBtn.textContent = showRawReport ? "Rendered" : "Raw";
}

function bindPresets() {
  for (const btn of document.querySelectorAll(".chip[data-topic]")) {
    btn.addEventListener("click", () => {
      topicInput.value = btn.getAttribute("data-topic") || "";
      topicInput.focus();
    });
  }
}

function bindShortcuts() {
  window.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.key === "Enter") {
      event.preventDefault();
      if (!startBtn.disabled) {
        startResearch();
      }
    }
    if (event.key === "Escape" && !stopBtn.disabled) {
      event.preventDefault();
      stopResearch();
    }
  });
}

startBtn.addEventListener("click", startResearch);
stopBtn.addEventListener("click", stopResearch);
clearBtn.addEventListener("click", () => resetRunState({ clearTopic: true }));
copyReportBtn.addEventListener("click", copyReport);
downloadReportBtn.addEventListener("click", downloadReport);
toggleRawBtn.addEventListener("click", toggleRaw);
toggleAutoScrollBtn.addEventListener("click", () => {
  autoScroll = !autoScroll;
  toggleAutoScrollBtn.textContent = `Auto-scroll: ${autoScroll ? "On" : "Off"}`;
});

bindPresets();
bindShortcuts();
resetRunState();

