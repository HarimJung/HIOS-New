/* HiOS Control Center — vanilla JS frontend */
"use strict";

const $ = (id) => document.getElementById(id);

const TABS = [
  { id: "home", label: "홈" },
  { id: "board", label: "액션" },
  { id: "mail", label: "이메일" },
  { id: "work", label: "워크스페이스" },
  { id: "vault", label: "파일" },
  { id: "graph", label: "그래프" },
  { id: "engine", label: "엔진" },
  { id: "agenda", label: "캘린더" },
];

const CONTENT_PROJECT = "Visual-Climate";
const CONTENT_VIEWS = [
  ["digests", "다이제스트"],
  ["xhs", "XHS 초안"],
  ["ig", "IG 초안"],
  ["calendar", "콘텐츠 캘린더"],
];

const WORK_SUBS = [
  ["overview", "개요"],
  ["actions", "액션"],
  ["meetings", "미팅"],
  ["emails", "이메일"],
  ["files", "파일"],
  ["resources", "리소스"],
  ["accounts", "계정"],
  ["ai", "AI 요청"],
];

// job.refresh 값 → 결과가 보이는 새 탭
const REFRESH_TAB = {
  daily: "home", projects: "work",
  digests: "work", xhs: "work", ig: "work", calendar: "work",
};

const state = {
  tasks: [],
  jobs: [],
  jobStatusCache: {},   // job_id -> last seen status (completion detection)
  selectedJob: null,
  logOffset: 0,
  logLines: [],
  activeTab: "home",
  pollTimer: null,
  actions: [],
  actionsSig: "",       // avoid re-render while user types
  schedule: [],
  boardProject: "",     // "" = 전체
  boardShowDone: false,
  mailFilter: "",       // "" = 전체 프로젝트
  // workspace
  workProject: null,
  workSub: "overview",
  workMeeting: null,
  workTreeCache: {},    // project -> tree json
  workOpenDirs: {},     // project -> Set of open dir paths
  workFilePath: null,
  pendingHighlightActionId: null,
  contentView: "digests",
  contentFile: null,
  // home
  homeDaily: null,
  // editor
  editorDirty: false,
  // AI request live log
  aiJobId: null,
  aiOffset: 0,
  aiLines: [],
  aiTimer: null,
  // global ask drawer
  askJobId: null,
  askOffset: 0,
  askLines: [],
  askTimer: null,
  // vault file tab
  vaultTree: null,
  vaultOpenDirs: new Set(),
  vaultFilePath: null,
  uploadBatches: [],
  uploadPollTimer: null,
  // graph tab
  graphData: null,
  graphInstance: null,
  graphFilter: "",
  graphSearch: "",
  // calendar
  calMonth: null,       // "YYYY-MM"
  calSel: null,         // selected item key
  calItems: [],
  calEvents: [],
  calError: null,
  calJobId: null,
  calOffset: 0,
  calLines: [],
  calTimer: null,
};

/* ---------------------------------------------------------------- utils */

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// [[01-Projects/X/02-Meetings/note]] or [[path|display text]] — AI-generated
// notes (daily brief, _STATUS.md) reference other vault files this way.
// Matches against the already-escaped string, so captured text is HTML-safe
// to reinsert directly (no re-escaping, no injection risk).
const WIKI_LINK_RE = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;

function renderMarkdown(src) {
  // escape raw HTML first, then let marked render markdown syntax only
  const withWikiLinks = escapeHtml(src).replace(WIKI_LINK_RE, (whole, path, alias) => {
    const trimmed = path.trim();
    if (!trimmed.startsWith("01-Projects/") && !trimmed.startsWith("00-Inbox/")) {
      return whole; // not a recognized vault path — leave the literal text alone
    }
    const relPath = /\.[a-z0-9]+$/i.test(trimmed) ? trimmed : `${trimmed}.md`;
    const display = (alias || trimmed).trim();
    return `<a href="#" class="wiki-link" data-path="${relPath}">${display}</a>`;
  });
  return marked.parse(withWikiLinks, { breaks: true });
}

document.addEventListener("click", (e) => {
  const link = e.target.closest(".wiki-link");
  if (!link) return;
  e.preventDefault();
  fmOpenInWorkspace(link.dataset.path);
});

function fmtDate(ts) {
  const d = new Date(ts * 1000);
  return `${d.getMonth() + 1}/${d.getDate()} ${d.toTimeString().slice(0, 5)}`;
}

function fmtSize(n) {
  if (n == null) return "";
  if (n < 1024) return `${n}B`;
  if (n < 1048576) return `${(n / 1024).toFixed(1)}K`;
  return `${(n / 1048576).toFixed(1)}M`;
}

function encodeRel(rel) {
  return rel.split("/").map(encodeURIComponent).join("/");
}

function failHtml(e) {
  return `<div class="doc-empty">로드 실패: ${escapeHtml(e.message || String(e))}</div>`;
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(body.message || `HTTP ${res.status}`), { status: res.status, body });
  return body;
}

function postJson(path, payload) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function toast(msg, kind = "ok") {
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  const icon = kind === "ok" ? "✓" : kind === "err" ? "✕" : "!";
  el.innerHTML = `<span class="ticon">${icon}</span><span>${escapeHtml(msg)}</span>`;
  $("toasts").appendChild(el);
  setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 350); }, 4200);
}

/* dirty editor guard — every navigation goes through this */
function confirmLeave() {
  if (!state.editorDirty) return true;
  const ok = confirm("저장하지 않은 변경이 있습니다. 버리고 이동할까요?");
  if (ok) state.editorDirty = false;
  return ok;
}

window.addEventListener("beforeunload", (e) => {
  if (state.editorDirty) e.preventDefault();
});

/* ---------------------------------------------------------------- engine: tasks */

const STATUS_KO = {
  success: "성공", failed: "실패", running: "실행중", pending: "대기",
  queued: "대기열", cancelled: "취소됨", timeout: "타임아웃",
};

/* 202 응답 공통 토스트 — 대기열 여부에 따라 문구 분기 */
function startedToast(res, msg) {
  if (res && res.queued) toast(`${msg} — 대기열 등록, 자리 나면 자동 시작`, "warn");
  else toast(`${msg} 시작됨`, "ok");
}

function renderTasks() {
  const panel = $("run-panel");
  const cats = [...new Set(state.tasks.map((t) => t.category))];
  panel.innerHTML = "";
  for (const cat of cats) {
    const group = document.createElement("div");
    group.className = "task-group";
    group.dataset.cat = cat;
    group.innerHTML = `<div class="group-title">${escapeHtml(cat)}</div>`;
    for (const t of state.tasks.filter((x) => x.category === cat)) {
      if (t.topic) {
        const row = document.createElement("div");
        row.className = "topic-row";
        row.innerHTML = `<input type="text" id="topic-${t.id}" maxlength="500"
          placeholder="${escapeHtml(t.label_ko)} 주제 (선택)">`;
        group.appendChild(taskButton(t));
        group.appendChild(row);
      } else {
        group.appendChild(taskButton(t));
      }
    }
    panel.appendChild(group);
  }
}

function taskButton(t) {
  const btn = document.createElement("button");
  btn.className = "task-btn";
  btn.disabled = t.running || t.blocked;
  const glyph = t.running ? `<span class="spinner"></span>` : `<span class="glyph">▶</span>`;
  const badge = t.warning ? `<span class="badge">${escapeHtml(t.warning)}</span>` : "";
  btn.innerHTML = `${glyph}<span class="name">${escapeHtml(t.label_ko)}</span>${badge}`;
  btn.onclick = () => runTask(t);
  return btn;
}

async function runTask(t) {
  const payload = {};
  if (t.topic) {
    const input = $(`topic-${t.id}`);
    if (input && input.value.trim()) payload.topic = input.value.trim().slice(0, 500);
  }
  try {
    const res = await postJson(`/api/run/${t.id}`, payload);
    state.selectedJob = res.job_id;
    state.logOffset = 0;
    state.logLines = [];
    startedToast(res, t.label_ko);
    schedulePoll(0);
  } catch (e) {
    toast(`실행 실패: ${e.body?.message || e.message}`, "err");
  }
}

/* ---------------------------------------------------------------- action bar */

function renderActions() {
  const pending = state.actions.filter((a) => a.status === "pending");
  const sig = pending.map((a) => a.id).join(",");
  if (sig === state.actionsSig) return;   // no change — don't clobber user input
  state.actionsSig = sig;

  const bar = $("action-bar");
  const box = $("ab-cards");
  if (!pending.length) { bar.style.display = "none"; box.innerHTML = ""; return; }
  bar.style.display = "";
  box.innerHTML = "";

  for (const a of pending) {
    const card = document.createElement("div");
    card.className = "ab-card";
    let controls = "";
    if (a.kind === "choice") {
      controls = `<div class="ab-controls">` + a.options.map((o, i) =>
        `<button class="ab-btn" data-i="${i}">${escapeHtml(o)}</button>`).join("") + `</div>`;
    } else if (a.kind === "env") {
      controls = `<div class="ab-controls">` + a.fields.map((f) =>
        `<input class="ab-input" data-key="${escapeHtml(f.key)}"
          type="${f.secret ? "password" : "text"}" placeholder="${escapeHtml(f.label)}">`).join("") +
        `<button class="ab-btn primary" data-save="1">저장</button></div>`;
    } else if (a.kind === "text") {
      controls = `<div class="ab-controls">
        <input class="ab-input" data-key="text" type="text" placeholder="${escapeHtml(a.placeholder || "")}">
        <button class="ab-btn primary" data-save="1">제출</button></div>`;
    }
    card.innerHTML = `
      <div class="ab-title">${escapeHtml(a.title)}</div>
      <div class="ab-desc">${escapeHtml(a.desc)}</div>${controls}`;

    card.querySelectorAll(".ab-btn").forEach((btn) => {
      btn.onclick = () => {
        let payload;
        if (a.kind === "choice") {
          payload = { choice: a.options[Number(btn.dataset.i)] };
        } else if (a.kind === "env") {
          const values = {};
          card.querySelectorAll(".ab-input").forEach((inp) => { values[inp.dataset.key] = inp.value.trim(); });
          if (Object.values(values).some((v) => !v)) { toast("모든 값을 입력하세요", "warn"); return; }
          payload = { values };
        } else {
          const inp = card.querySelector(".ab-input");
          if (!inp.value.trim()) { toast("값을 입력하세요", "warn"); return; }
          payload = { text: inp.value.trim() };
        }
        resolveAction(a, payload);
      };
    });
    box.appendChild(card);
  }
  linkifyVaultPaths(box);
}

async function resolveAction(a, payload) {
  try {
    await postJson(`/api/actions/${a.id}/resolve`, payload);
    toast(`처리됨: ${a.title}`, "ok");
    state.actionsSig = "";   // force re-render
    schedulePoll(0);
  } catch (e) {
    toast(`실패: ${e.body?.message || e.message}`, "err");
  }
}

/* ---------------------------------------------------------------- engine: schedule */

function renderSchedule() {
  const box = $("sched");
  if (!state.schedule.length) { box.innerHTML = ""; return; }
  box.innerHTML = `<div class="sched-title">자동 스케줄</div>` +
    state.schedule.map((s) => `
      <div class="sched-row">
        <span class="sched-at">${escapeHtml(s.at)}</span>
        <span class="sched-name">${escapeHtml(s.label)}</span>
        <span class="sched-dot ${s.done_today ? "done" : "wait"}"
          title="${s.done_today ? "오늘 실행됨" : "대기 중"}"></span>
      </div>`).join("");
}

/* ---------------------------------------------------------------- request tray */

let trayOpen = false;

function fmtElapsed(sec) {
  sec = Math.max(0, Math.floor(sec));
  if (sec < 60) return `${sec}초`;
  const m = Math.floor(sec / 60);
  return m < 60 ? `${m}분` : `${Math.floor(m / 60)}시간 ${m % 60}분`;
}

function renderTray() {
  const active = state.jobs.filter((j) => !TERMINAL.has(j.status));
  const running = active.filter((j) => j.status !== "queued").length;
  const queued = active.length - running;
  const cnt = $("tray-cnt");
  cnt.style.display = active.length ? "" : "none";
  cnt.textContent = queued ? `${running}+${queued}` : `${running}`;
  $("tray-btn").classList.toggle("busy", active.length > 0);
  $("tray-ic").innerHTML = active.length ? `<span class="spinner"></span>` : "◎";
  if (!trayOpen) return;
  const now = Date.now() / 1000;
  const rows = state.jobs.slice(0, 10).map((j) => {
    const time = j.status === "running" || j.status === "pending"
      ? `${fmtElapsed(now - j.created)} 경과`
      : j.status === "queued" ? "차례 대기" : fmtDate(j.created);
    return `<div class="tray-row" data-j="${escapeHtml(j.id)}" title="클릭하면 엔진 탭에서 로그 보기">
      <span class="pill ${j.status}">${STATUS_KO[j.status] || j.status}</span>
      <span class="tray-name">${escapeHtml(j.label)}</span>
      <span class="tray-time">${escapeHtml(time)}</span>
    </div>`;
  }).join("");
  const panel = $("tray-panel");
  panel.innerHTML = rows || `<div class="ws-empty">최근 작업 없음</div>`;
  panel.querySelectorAll(".tray-row").forEach((r) => {
    r.onclick = () => {
      closeTray();
      state.selectedJob = r.dataset.j;
      state.logOffset = 0;
      state.logLines = [];
      switchTab("engine");
    };
  });
}

function closeTray() {
  trayOpen = false;
  $("tray-panel").style.display = "none";
}

$("tray-btn").onclick = (ev) => {
  ev.stopPropagation();
  trayOpen = !trayOpen;
  $("tray-panel").style.display = trayOpen ? "" : "none";
  if (trayOpen) renderTray();
};

document.addEventListener("click", (ev) => {
  if (trayOpen && !ev.target.closest("#tray")) closeTray();
});

/* ---------------------------------------------------------------- engine: jobs & log */

function renderJobs() {
  const box = $("job-history");
  if (!state.jobs.length) {
    box.innerHTML = `<div class="log-empty">아직 실행된 작업 없음</div>`;
    return;
  }
  box.innerHTML = "";
  for (const j of state.jobs) {
    const row = document.createElement("div");
    row.className = "job-row" + (j.id === state.selectedJob ? " selected" : "");
    row.innerHTML = `
      <span class="pill ${j.status}">${STATUS_KO[j.status] || j.status}</span>
      <span class="jlabel">${escapeHtml(j.label)}</span>
      <span class="jtime">${fmtDate(j.created)}</span>`;
    row.onclick = () => selectJob(j.id);
    box.appendChild(row);
  }
}

function selectJob(id) {
  if (state.selectedJob !== id) {
    state.selectedJob = id;
    state.logOffset = 0;
    state.logLines = [];
  }
  renderJobs();
  schedulePoll(0);
}

function renderLogHead(job) {
  $("log-title").textContent = job
    ? `${job.label} — ${job.id}` : "작업을 선택하세요";
  $("log-pill").innerHTML = job
    ? `<span class="pill ${job.status}">${STATUS_KO[job.status] || job.status}</span>` : "";
  $("btn-cancel").style.display =
    job && (job.status === "running" || job.status === "queued") ? "" : "none";
}

function logLinesHtml(lines) {
  return lines.map((l) => {
    const esc = escapeHtml(l);
    if (l.startsWith("[시스템]")) return `<span class="sys">${esc}</span>`;
    if (l.startsWith("…")) return `<span class="hb">${esc}</span>`;
    return esc;
  }).join("\n");
}

function renderLogLines() {
  const view = $("log-view");
  if (!state.logLines.length) {
    view.innerHTML = `<div class="log-empty">로그 없음</div>`;
    return;
  }
  const stick = view.scrollTop + view.clientHeight >= view.scrollHeight - 40;
  view.innerHTML = `<pre>${logLinesHtml(state.logLines)}</pre>`;
  if (stick) view.scrollTop = view.scrollHeight;
}

$("btn-cancel").onclick = async () => {
  if (!state.selectedJob) return;
  try {
    await api(`/api/jobs/${state.selectedJob}/cancel`, { method: "POST" });
    toast("취소 요청 전송됨", "warn");
  } catch (e) {
    toast(`취소 실패: ${e.message}`, "err");
  }
};

/* ---------------------------------------------------------------- tabs */

function renderTabs() {
  const box = $("tabs");
  box.innerHTML = "";
  for (const t of TABS) {
    const b = document.createElement("button");
    b.className = "tab" + (t.id === state.activeTab ? " active" : "");
    b.textContent = t.label;
    b.dataset.tab = t.id;
    b.onclick = () => {
      if (t.id === state.activeTab) return;
      if (!confirmLeave()) return;
      state.activeTab = t.id;
      localStorage.setItem("hios-tab", t.id);
      renderTabs();
      loadTab();
    };
    box.appendChild(b);
  }
}

function switchTab(id) {
  if (!confirmLeave()) return;
  state.activeTab = id;
  localStorage.setItem("hios-tab", id);
  renderTabs();
  loadTab();
}

async function loadTab() {
  stopAiPoll();
  stopCalPoll();
  stopUploadPoll();
  destroyGraph();
  const isEngine = state.activeTab === "engine";
  $("engine-view").style.display = isEngine ? "" : "none";
  $("output-body").style.display = isEngine ? "none" : "";
  if (isEngine) { schedulePoll(0); return; }
  const doc = $("doc-view");
  if (state.activeTab === "home") return loadHome();
  if (state.activeTab === "board") return renderBoardView(doc, null);
  if (state.activeTab === "mail") return loadMailTab();
  if (state.activeTab === "work") return loadWork();
  if (state.activeTab === "vault") return loadVaultTab();
  if (state.activeTab === "graph") return loadGraphTab(false);
  if (state.activeTab === "agenda") return loadAgenda(false);
}

function flashTab(tabId) {
  const el = document.querySelector(`.tab[data-tab="${tabId}"]`);
  if (el) { el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); }
}

/* ---------------------------------------------------------------- agenda */

function agendaHtml(events, emptyMsg) {
  if (!events.length) return `<div class="doc-empty">${escapeHtml(emptyMsg || "일정 없음")}</div>`;
  const days = {};
  for (const e of events) {
    const day = e.start.slice(0, 10);
    (days[day] = days[day] || []).push(e);
  }
  const dowKo = ["일", "월", "화", "수", "목", "금", "토"];
  const todayStr = localDateStr(0);
  return `<div class="agenda">` + Object.keys(days).sort().map((day) => {
    const d = new Date(day + "T00:00:00");
    const head = `${d.getMonth() + 1}/${d.getDate()} (${dowKo[d.getDay()]})` +
      (day === todayStr ? " · 오늘" : "");
    return `<div class="ag-day">
      <div class="ag-head${day === todayStr ? " today" : ""}">${head}</div>` +
      days[day].map((e) => `
        <div class="ag-ev">
          <span class="ag-time">${escapeHtml(e.start.slice(11))}–${escapeHtml(e.end.slice(11))}</span>
          <span class="ag-title">${escapeHtml(e.title)}</span>
          <span class="ag-cal">${escapeHtml(e.calendar)}</span>
        </div>`).join("") + `</div>`;
  }).join("") + `</div>`;
}

function localDateStr(offsetDays) {
  const n = new Date();
  n.setDate(n.getDate() + offsetDays);
  return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, "0")}-${String(n.getDate()).padStart(2, "0")}`;
}

async function loadAgenda(force) {
  stopCalPoll();
  const doc = $("doc-view");
  doc.innerHTML = `<div class="doc-empty">캘린더 불러오는 중…</div>`;
  try {
    const [cal, items] = await Promise.all([
      api(`/api/calendar${force ? "?refresh=1" : ""}`),
      api(`/api/work-items${force ? "?refresh=1" : ""}`),
    ]);
    state.calEvents = cal.events || [];
    state.calError = cal.error || null;
    state.calItems = items || [];
    if (!state.calMonth) state.calMonth = localDateStr(0).slice(0, 7);
    renderCalendar();
  } catch (e) {
    doc.innerHTML = `<div class="doc-empty">캘린더 로드 실패: ${escapeHtml(e.message)}</div>`;
  }
}

function calShiftMonth(delta) {
  const [y, m] = state.calMonth.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  state.calMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  renderCalendar();
}

function calItemKey(it) {
  return it.kind === "file" ? `f:${it.path}` : `a:${it.project}/${it.id}`;
}

function calFindItem(key) {
  return state.calItems.find((it) => calItemKey(it) === key) || null;
}

function calChipHtml(it) {
  const key = calItemKey(it);
  const cls = `cal-chip p-${it.priority || "med"}` +
    (it.status === "done" ? " done" : "") +
    (state.calSel === key ? " sel" : "");
  const proj = it.project ? `<span class="cal-proj">${escapeHtml(it.project)}</span>` : "";
  return `<button class="${cls}" data-key="${escapeHtml(key)}" title="${escapeHtml(it.title)}">${proj}${escapeHtml(it.title)}</button>`;
}

function renderCalendar() {
  const doc = $("doc-view");
  const [y, m] = state.calMonth.split("-").map(Number);
  const startDow = new Date(y, m - 1, 1).getDay();
  const daysInMonth = new Date(y, m, 0).getDate();
  const todayStr = localDateStr(0);

  const evByDay = {}, itByDay = {}, undated = [];
  for (const e of state.calEvents) {
    const d = e.start.slice(0, 10);
    (evByDay[d] = evByDay[d] || []).push(e);
  }
  for (const it of state.calItems) {
    if (it.due) (itByDay[it.due] = itByDay[it.due] || []).push(it);
    else if (it.status !== "done") undated.push(it);
  }

  const dowKo = ["일", "월", "화", "수", "목", "금", "토"];
  let cells = "";
  for (let i = 0; i < startDow; i++) cells += `<div class="cal-cell empty"></div>`;
  for (let d = 1; d <= daysInMonth; d++) {
    const ds = `${state.calMonth}-${String(d).padStart(2, "0")}`;
    const evs = (evByDay[ds] || []).map((e) =>
      `<div class="cal-ev" title="${escapeHtml(e.title)}"><span class="cal-time">${escapeHtml(e.start.slice(11))}</span>${escapeHtml(e.title)}</div>`).join("");
    const its = (itByDay[ds] || []).map(calChipHtml).join("");
    cells += `<div class="cal-cell${ds === todayStr ? " today" : ""}"><div class="cal-daynum">${d}</div>${evs}${its}</div>`;
  }

  doc.innerHTML = `
    <div class="cal-head">
      <button class="ab-btn" id="cal-prev">◀</button>
      <span class="cal-month">${y}년 ${m}월</span>
      <button class="ab-btn" id="cal-next">▶</button>
      <button class="ab-btn" id="cal-goto-today">오늘</button>
      <span class="spacer"></span>
      <button class="ab-btn" id="cal-refresh">새로고침</button>
    </div>
    ${state.calError ? `<div class="ag-error">${escapeHtml(state.calError)}</div>` : ""}
    <div class="cal-dow">${dowKo.map((d) => `<div>${d}</div>`).join("")}</div>
    <div class="cal-grid">${cells}</div>
    ${undated.length ? `<div class="cal-undated"><div class="cal-und-head">날짜 미지정 (${undated.length})</div>${undated.map(calChipHtml).join("")}</div>` : ""}
    <div class="cal-detail" id="cal-detail" style="display:none"></div>`;

  $("cal-prev").onclick = () => calShiftMonth(-1);
  $("cal-next").onclick = () => calShiftMonth(1);
  $("cal-goto-today").onclick = () => { state.calMonth = todayStr.slice(0, 7); renderCalendar(); };
  $("cal-refresh").onclick = () => loadAgenda(true);
  doc.querySelectorAll(".cal-chip[data-key]").forEach((b) => {
    b.onclick = () => {
      state.calSel = b.dataset.key;
      doc.querySelectorAll(".cal-chip").forEach((c) =>
        c.classList.toggle("sel", c.dataset.key === state.calSel));
      openCalItem(state.calSel);
    };
  });
  if (state.calSel) openCalItem(state.calSel);
}

async function openCalItem(key) {
  const box = $("cal-detail");
  if (!box) return;
  const it = calFindItem(key);
  if (!it) { box.style.display = "none"; return; }
  box.style.display = "";
  box.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;

  let bodyHtml = "", progressHtml = "", relatedHtml = "", openBtn = "";
  if (it.kind === "file") {
    let d;
    try { d = await api(`/api/work-item-detail?path=${encodeRel(it.path)}`); }
    catch (e) { box.innerHTML = failHtml(e); return; }
    if (d.total_boxes) {
      const pct = Math.round(100 * d.done_boxes / d.total_boxes);
      progressHtml = `<div class="cal-prog"><div class="cal-prog-bar" style="width:${pct}%"></div></div>
        <div class="cal-prog-label">진행 ${d.done_boxes}/${d.total_boxes} 항목 (${pct}%)</div>`;
    }
    bodyHtml = `<div class="md cal-md">${renderMarkdown(d.content)}</div>`;
    const links = (d.links || []).map((l) => `<span class="cal-rel wl">[[${escapeHtml(l)}]]</span>`).join("");
    const sibs = (d.siblings || []).map((s) => `<span class="cal-rel">${escapeHtml(s)}</span>`).join("");
    if (links || sibs) relatedHtml = `<div class="cal-related"><b>관련</b> ${links}${sibs}</div>`;
    openBtn = `<button class="ws-open-btn" id="cal-open-file">파일 열기</button>`;
  } else {
    bodyHtml =
      (it.detail ? `<div class="md cal-md">${renderMarkdown(it.detail)}</div>` : "") +
      (it.note ? `<div class="cal-note"><b>메모</b><div class="md">${renderMarkdown(it.note)}</div></div>` : "");
    if (!bodyHtml) bodyHtml = `<div class="doc-empty">상세 내용 없음</div>`;
  }

  const badges =
    (it.project ? `<span class="pill">${escapeHtml(it.project)}</span>` : "") +
    (it.due ? dueBadge(it.due) : "") +
    `<span class="pill ${escapeHtml(it.status || "")}">${escapeHtml(BI_STATUS_KO[it.status] || it.status || "")}</span>` +
    `<span class="pill">${escapeHtml(BI_PRIO_KO[it.priority] || it.priority || "")}</span>`;

  box.innerHTML = `
    <div class="cal-det-head">
      <span class="cal-det-title">${escapeHtml(it.title)}</span>
      ${badges}
      <span class="spacer"></span>
      ${openBtn}
      <button class="ws-open-btn" id="cal-det-close">닫기</button>
    </div>
    ${progressHtml}
    ${bodyHtml}
    ${relatedHtml}
    <div class="cal-memo-box">
      <textarea id="cal-memo" placeholder="메모 또는 요청 — 'AI 요청 → 엔진'을 누르면 엔진이 이 아이템에 바로 반영합니다" maxlength="2000"></textarea>
      <div class="cal-memo-btns">
        <button class="ab-btn" id="cal-memo-save">메모 저장</button>
        <button class="ab-btn cal-primary" id="cal-memo-ai">AI 요청 → 엔진</button>
      </div>
    </div>
    <div class="cal-log" id="cal-log" style="display:none">
      <div class="log-head"><span class="ltitle" id="cal-log-title"></span><span id="cal-log-pill"></span></div>
      <div class="log-view" id="cal-log-view"></div>
    </div>`;

  $("cal-det-close").onclick = () => {
    state.calSel = null;
    box.style.display = "none";
    document.querySelectorAll(".cal-chip.sel").forEach((c) => c.classList.remove("sel"));
  };
  const of = $("cal-open-file");
  if (of) of.onclick = () =>
    postJson("/api/open-path", { path: it.path, app: "vscode" }).catch((e) => toast(e.message, "err"));
  $("cal-memo-save").onclick = () => calMemoSend(it, "memo");
  $("cal-memo-ai").onclick = () => calMemoSend(it, "ai");
}

async function calMemoSend(it, mode) {
  const ta = $("cal-memo");
  const text = (ta && ta.value || "").trim();
  if (!text) { toast("내용을 입력하세요", "warn"); return; }
  try {
    if (it.kind === "file") {
      const res = await postJson("/api/work-item-memo", { path: it.path, text, mode });
      if (mode === "ai") { startCalPoll(res.job_id); startedToast(res, "AI 작업"); }
      else { toast("메모 저장됨 (## Log)"); openCalItem(calItemKey(it)); }
    } else if (mode === "ai") {
      const res = await postJson(`/api/projects/${encodeURIComponent(it.project)}/request`,
        { prompt: `[액션 아이템: ${it.title}]\n${text}` });
      startCalPoll(res.job_id);
      startedToast(res, "AI 작업");
    } else {
      const note = (it.note ? it.note + "\n" : "") + `**${localDateStr(0)}** ${text}`;
      await postJson(`/api/action-items/${encodeURIComponent(it.project)}/${encodeURIComponent(it.id)}`, { note });
      it.note = note;
      toast("메모 저장됨");
      openCalItem(calItemKey(it));
    }
    if (ta) ta.value = "";
  } catch (e) { toast(`실패: ${e.message}`, "err"); }
}

function stopCalPoll() {
  clearTimeout(state.calTimer);
  state.calTimer = null;
}

function startCalPoll(jobId) {
  state.calJobId = jobId;
  state.calOffset = 0;
  state.calLines = [];
  stopCalPoll();
  pollCal();
}

async function pollCal() {
  const box = $("cal-log");
  if (!box || !state.calJobId) { stopCalPoll(); return; }
  let d;
  try { d = await api(`/api/jobs/${state.calJobId}?offset=${state.calOffset}`); }
  catch { stopCalPoll(); return; }
  state.calLines.push(...d.lines);
  if (state.calLines.length > 2000) state.calLines = state.calLines.slice(-2000);
  state.calOffset = d.next_offset;
  box.style.display = "";
  $("cal-log-title").textContent = `${d.label} — ${d.id}`;
  $("cal-log-pill").innerHTML = `<span class="pill ${d.status}">${STATUS_KO[d.status] || d.status}</span>`;
  const view = $("cal-log-view");
  const stick = view.scrollTop + view.clientHeight >= view.scrollHeight - 40;
  view.innerHTML = `<pre>${logLinesHtml(state.calLines)}</pre>`;
  if (stick) view.scrollTop = view.scrollHeight;
  if (TERMINAL.has(d.status)) {
    stopCalPoll();
    if (d.status === "success" && state.activeTab === "agenda") {
      toast("AI 작업 완료 — 캘린더 새로고침");
      loadAgenda(true);
    }
    return;
  }
  state.calTimer = setTimeout(pollCal, 1500);
}

/* ---------------------------------------------------------------- action board */

const BI_STATUS = [
  ["open", "대기"], ["in_progress", "진행중"], ["blocked", "차단됨"], ["done", "완료"],
];
const BI_STATUS_KO = Object.fromEntries(BI_STATUS);
const BI_PRIO_KO = { high: "높음", med: "중간", low: "낮음" };
const BI_PRIO_W = { high: 0, med: 1, low: 2 };
const SRC_ICON = { gmail: "✉", granola: "▤", link: "↗" };

function dueBadge(due) {
  if (!due) return "";
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const d = new Date(due + "T00:00:00");
  const diff = Math.round((d - today) / 86400000);
  let cls = "ok", label;
  if (diff < 0) { cls = "over"; label = `${due} · ${-diff}일 지남`; }
  else if (diff === 0) { cls = "today"; label = `${due} · D-DAY`; }
  else { if (diff <= 3) cls = "soon"; label = `${due} · D-${diff}`; }
  return `<span class="bi-due ${cls}">${label}</span>`;
}

function dueDiff(due) {
  if (!due) return null;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return Math.round((new Date(due + "T00:00:00") - today) / 86400000);
}

function biSortKey(it) {
  // overdue/near due first, then priority, then no-due last
  const due = it.due ? new Date(it.due + "T00:00:00").getTime() : Infinity;
  return [due, BI_PRIO_W[it.priority] ?? 1];
}

function biCardHtml(p, it, deliverableSlugs) {
  const srcs = (it.sources || []).map((s) =>
    `<a class="src-chip ${s.kind}" href="${escapeHtml(s.url)}" target="_blank" rel="noopener">
      <span class="src-ic">${SRC_ICON[s.kind] || "↗"}</span>${escapeHtml(s.label)}</a>`).join("");
  const people = (it.people || []).map((x) => `<span class="bi-person">@${escapeHtml(x)}</span>`).join("");
  const statusBtns = BI_STATUS.map(([k, ko]) =>
    `<button class="bi-st ${k}${it.status === k ? " on" : ""}" data-st="${k}">${ko}</button>`).join("");
  const detail = it.detail
    ? `<div class="bi-detail md">${renderMarkdown(it.detail)}</div>` : "";
  const slugs = deliverableSlugs || [];
  const delivSelect = slugs.length
    ? `<select class="bi-deliv-select" title="이 액션과 연결된 딜리버블 폴더">
        <option value=""${it.deliverable ? "" : " selected"}>(프로젝트 전체)</option>
        ${slugs.map((s) =>
          `<option value="${escapeHtml(s)}"${s === it.deliverable ? " selected" : ""}>${escapeHtml(s)}</option>`).join("")}
      </select>` : "";
  const folderLabel = it.deliverable || "프로젝트 폴더";
  return `
  <div class="bi-card p-${escapeHtml(it.priority || "med")}${it.status === "done" ? " is-done" : ""}"
       data-p="${escapeHtml(p)}" data-id="${escapeHtml(it.id)}" data-deliverable="${escapeHtml(it.deliverable || "")}">
    <div class="bi-top">
      <span class="bi-proj">${escapeHtml(p)}</span>
      <select class="bi-prio-select ${escapeHtml(it.priority || "med")}" title="우선순위 변경">
        ${["high", "med", "low"].map((v) =>
          `<option value="${v}"${v === (it.priority || "med") ? " selected" : ""}>${BI_PRIO_KO[v]}</option>`).join("")}
      </select>
      ${dueBadge(it.due)}
      <span class="spacer"></span>
      <button class="bi-del" title="삭제">✕</button>
    </div>
    <div class="bi-title">${escapeHtml(it.title)}</div>
    ${detail}
    <div class="bi-meta">
      ${srcs}
      <button class="src-chip bi-open-folder" type="button"
        title="Finder에서 ${escapeHtml(folderLabel)} 폴더 열기">
        <span class="src-ic">📁</span>${escapeHtml(folderLabel)}</button>
      ${delivSelect}
      ${people}
    </div>
    <div class="bi-controls">${statusBtns}</div>
    <div class="bi-note">
      <textarea class="bi-note-in" placeholder="메모 — 진행상황, 막힌 것, 다음 스텝…">${escapeHtml(it.note || "")}</textarea>
      <button class="bi-note-save">메모 저장</button>
      <span class="bi-upd">upd ${escapeHtml(it.updated || "")}</span>
    </div>
  </div>`;
}

async function saveItem(project, id, payload, msg) {
  try {
    await postJson(`/api/action-items/${encodeURIComponent(project)}/${encodeURIComponent(id)}`, payload);
    if (msg) toast(msg, "ok");
    return true;
  } catch (e) { toast(`실패: ${e.body?.message || e.message}`, "err"); return false; }
}

function wireBiCards(container, reload) {
  container.querySelectorAll(".bi-card").forEach((card) => {
    const p = card.dataset.p, id = card.dataset.id;
    card.querySelectorAll(".bi-st").forEach((b) => {
      b.onclick = async () => {
        if (await saveItem(p, id, { status: b.dataset.st },
          `상태 변경: ${BI_STATUS_KO[b.dataset.st]}`)) reload();
      };
    });
    card.querySelector(".bi-note-save").onclick = async () => {
      const v = card.querySelector(".bi-note-in").value;
      await saveItem(p, id, { note: v }, "메모 저장됨 — _ACTIONS.json에 기록");
    };
    const prioSel = card.querySelector(".bi-prio-select");
    prioSel.onchange = async () => {
      const v = prioSel.value;
      prioSel.className = `bi-prio-select ${v}`;
      card.className = card.className.replace(/\bp-(high|med|low)\b/, `p-${v}`);
      if (!(await saveItem(p, id, { priority: v }, `우선순위: ${BI_PRIO_KO[v]}`))) reload();
    };
    card.querySelector(".bi-del").onclick = async () => {
      if (!confirm("이 액션을 삭제할까요?")) return;
      if (await saveItem(p, id, { delete: true }, "삭제됨")) reload();
    };
    card.querySelector(".bi-open-folder").onclick = async () => {
      const slug = card.dataset.deliverable;
      try {
        await postJson(`/api/projects/${encodeURIComponent(p)}/open`,
          slug ? { which: "deliverable", slug } : { which: "root" });
        toast(`Finder에서 ${slug || p} 폴더 열림`, "ok");
      } catch (e) { toast(`실패: ${e.body?.message || e.message}`, "err"); }
    };
    const delivSel = card.querySelector(".bi-deliv-select");
    if (delivSel) {
      delivSel.onchange = async () => {
        const v = delivSel.value;
        card.dataset.deliverable = v;
        const folderBtn = card.querySelector(".bi-open-folder");
        folderBtn.title = `Finder에서 ${v || p} 폴더 열기`;
        folderBtn.lastChild.textContent = v || "프로젝트 폴더";
        if (!(await saveItem(p, id, { deliverable: v },
          v ? `딜리버블 연결: ${v}` : "딜리버블 연결 해제"))) reload();
      };
    }
  });
}

/* board view — 전체 탭(fixedProject=null)과 워크스페이스 액션 서브탭(고정 필터) 공용 */
async function renderBoardView(container, fixedProject) {
  container.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;
  let groups;
  try { groups = await api("/api/action-items"); }
  catch (e) { container.innerHTML = failHtml(e); return; }
  const reload = () => renderBoardView(container, fixedProject);

  const openCnt = {};
  let totalOpen = 0;
  for (const g of groups) {
    openCnt[g.project] = g.items.filter((i) => i.status !== "done").length;
    totalOpen += openCnt[g.project];
  }

  let chips = "";
  if (!fixedProject) {
    chips = `<div class="proj-chips">
      <button class="proj-chip${state.boardProject === "" ? " active" : ""}" data-p="">
        전체${totalOpen ? `<span class="cnt">${totalOpen}</span>` : ""}</button>` +
      groups.map((g) => `
        <button class="proj-chip${g.project === state.boardProject ? " active" : ""}" data-p="${escapeHtml(g.project)}">
          ${escapeHtml(g.project)}${openCnt[g.project] ? `<span class="cnt">${openCnt[g.project]}</span>` : ""}
        </button>`).join("") + `</div>`;
  }

  const filter = fixedProject || state.boardProject;
  const visible = groups.filter((g) => !filter || g.project === filter);
  const flat = [];
  for (const g of visible) for (const it of g.items) flat.push([g.project, it]);
  const open = flat.filter(([, it]) => it.status !== "done")
    .sort((a, b) => { const x = biSortKey(a[1]), y = biSortKey(b[1]); return x[0] - y[0] || x[1] - y[1]; });
  const done = flat.filter(([, it]) => it.status === "done");

  const deliverableMap = {};
  await Promise.all(visible.map(async (g) => {
    deliverableMap[g.project] = await api(`/api/projects/${encodeURIComponent(g.project)}/deliverables`)
      .catch(() => []);
  }));

  const cards = open.map(([p, it]) => biCardHtml(p, it, deliverableMap[p])).join("")
    || `<div class="ws-empty">열린 액션 없음 🎉</div>`;
  let doneHtml = "";
  if (done.length) {
    doneHtml = `<button class="bi-done-toggle" id="bi-done-toggle">
        완료됨 ${done.length}건 ${state.boardShowDone ? "접기 ▲" : "보기 ▼"}</button>` +
      (state.boardShowDone ? done.map(([p, it]) => biCardHtml(p, it, deliverableMap[p])).join("") : "");
  }

  const defProj = fixedProject || state.boardProject || groups[0]?.project;
  const addProjSel = fixedProject
    ? `<input type="hidden" id="bi-add-proj" value="${escapeHtml(fixedProject)}">`
    : `<select class="ws-input bi-add-proj" id="bi-add-proj">` + groups.map((g) =>
      `<option value="${escapeHtml(g.project)}"${g.project === defProj ? " selected" : ""}>${escapeHtml(g.project)}</option>`).join("") + `</select>`;
  const addForm = `
    <div class="ws-section bi-add">
      <div class="ws-head"><span class="ws-title">새 액션 추가${fixedProject ? ` — ${escapeHtml(fixedProject)}` : ""}</span></div>
      <div class="ws-form">
        ${addProjSel}
        <input class="ws-input" id="bi-add-title" placeholder="제목" style="flex:2">
        <input class="ws-input" id="bi-add-due" type="date" title="마감일 (선택)">
        <select class="ws-input bi-add-proj" id="bi-add-prio">
          <option value="high">높음</option><option value="med" selected>중간</option><option value="low">낮음</option>
        </select>
      </div>
      <div class="ws-form">
        <input class="ws-input" id="bi-add-detail" placeholder="상세 설명 (선택)">
        <button class="ws-add-btn" id="bi-add-btn">추가</button>
      </div>
    </div>`;

  container.innerHTML = chips + `<div class="board-cards">${cards}${doneHtml}</div>` + addForm;

  if (!fixedProject) {
    container.querySelectorAll(".proj-chip").forEach((c) => {
      c.onclick = () => { state.boardProject = c.dataset.p; reload(); };
    });
  }
  const dt = container.querySelector("#bi-done-toggle");
  if (dt) dt.onclick = () => { state.boardShowDone = !state.boardShowDone; reload(); };

  wireBiCards(container, reload);

  if (state.pendingHighlightActionId) {
    const target = container.querySelector(`.bi-card[data-id="${state.pendingHighlightActionId}"]`);
    state.pendingHighlightActionId = null;
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "center" });
      target.classList.add("bi-flash");
      setTimeout(() => target.classList.remove("bi-flash"), 2200);
    }
  }

  container.querySelector("#bi-add-btn").onclick = async () => {
    const title = container.querySelector("#bi-add-title").value.trim();
    if (!title) { toast("제목을 입력하세요", "warn"); return; }
    try {
      await postJson(`/api/action-items/${encodeURIComponent(container.querySelector("#bi-add-proj").value)}`, {
        title,
        detail: container.querySelector("#bi-add-detail").value.trim(),
        due: container.querySelector("#bi-add-due").value,
        priority: container.querySelector("#bi-add-prio").value,
      });
      toast("액션 추가됨", "ok");
      reload();
    } catch (e) { toast(`실패: ${e.body?.message || e.message}`, "err"); }
  };
}

/* ---------------------------------------------------------------- home */

async function loadHome() {
  const doc = $("doc-view");
  doc.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;
  let projects, groups, cal, daily, mail;
  try {
    [projects, groups, cal, daily, mail] = await Promise.all([
      api("/api/projects"),
      api("/api/action-items"),
      api("/api/calendar").catch(() => ({ events: [], error: "캘린더 로드 실패" })),
      api("/api/files/daily").catch(() => []),
      api("/api/emails").catch(() => null),
    ]);
  } catch (e) { doc.innerHTML = failHtml(e); return; }

  // ① 오늘·내일 일정
  const near = new Set([localDateStr(0), localDateStr(1)]);
  const nearEvents = (cal.events || []).filter((e) => near.has(e.start.slice(0, 10)));

  // ② 마감 지남 / D-3 이내 열린 액션
  const urgent = [];
  for (const g of groups) {
    for (const it of g.items) {
      if (it.status === "done") continue;
      const d = dueDiff(it.due);
      if (d !== null && d <= 3) urgent.push([g.project, it]);
    }
  }
  urgent.sort((a, b) => { const x = biSortKey(a[1]), y = biSortKey(b[1]); return x[0] - y[0] || x[1] - y[1]; });
  const urgentHtml = urgent.length
    ? urgent.map(([p, it]) => biCardHtml(p, it)).join("")
    : `<div class="ws-empty">임박/지연 액션 없음 🎉</div>`;

  // ②-b 5일 이상 정체된 열린 액션 (놓친 것 찾기)
  const todayMs = new Date(localDateStr(0) + "T00:00:00").getTime();
  const stale = [];
  for (const g of groups) {
    for (const it of g.items) {
      if (it.status === "done") continue;
      const upd = it.updated || it.created;
      if (!upd) continue;
      const days = Math.floor((todayMs - new Date(upd + "T00:00:00").getTime()) / 86400000);
      if (days >= 5) stale.push([g.project, it, days]);
    }
  }
  stale.sort((a, b) => b[2] - a[2]);
  const staleHtml = stale.length
    ? stale.slice(0, 8).map(([p, it, days]) => `
      <div class="stale-row" data-sp="${escapeHtml(p)}" title="클릭하면 액션 보드로 이동">
        <span class="stale-days">${days}일째</span>
        <span class="stale-proj">${escapeHtml(p)}</span>
        <span class="stale-title">${escapeHtml(it.title)}</span>
      </div>`).join("")
    : "";

  // ②-c 이메일 수집 상태 스트립
  const mailStats = (mail && mail.stats) || {};
  const naCount = ((mail && mail.emails) || []).filter((e) => e.needs_action).length;
  let mailStrip = "";
  if (mail) {
    const upd = mail.updated ? `마지막 수집 ${fmtDate(mail.updated)}` : "아직 수집 안 됨";
    const err = mail.last_status === "error"
      ? `<span class="mail-err">⚠ 실패${mail.last_error ? ` — ${escapeHtml(mail.last_error)}` : ""}</span>`
      : (mail.missed && mail.missed.length
        ? `<span class="mail-err">⚠ 누락: ${escapeHtml(mail.missed.join(", "))}</span>` : "");
    const chips = Object.keys(mailStats).map((p) =>
      `<span class="pc-stat${mailStats[p] ? "" : " zero"}">${escapeHtml(p)} ${mailStats[p]}</span>`).join("");
    mailStrip = `
      <div class="home-strip">
        <span class="hs-title">이메일</span>
        <span class="em-updated">${escapeHtml(upd)}</span>${err}
        <button class="ws-open-btn${naCount ? " hot" : ""}" id="hs-goto-mail">${naCount ? `회신 필요 ${naCount}건 →` : "이메일 탭 →"}</button>
        <span class="spacer"></span>
        <span class="hs-chips">${chips}</span>
      </div>`;
  }

  // ③ 프로젝트 카드
  const projCards = projects.map((p) => `
    <div class="proj-card" data-p="${escapeHtml(p.name)}">
      <div class="pc-name">${escapeHtml(p.name)}</div>
      <div class="pc-client">${escapeHtml(p.client || "")}</div>
      <div class="pc-stats">
        <span class="pc-stat${p.open_actions ? " hot" : ""}">액션 ${p.open_actions || 0}</span>
        <span class="pc-stat">할 일 ${p.open_todos || 0}</span>
        <span class="pc-stat">미팅 ${p.meetings || 0}</span>
        ${mail ? `<span class="pc-stat">메일 ${mailStats[p.name] || 0}</span>` : ""}
      </div>
      ${p.latest_meeting
        ? `<div class="pc-meeting" title="${escapeHtml(p.latest_meeting)}">최근 미팅 · ${escapeHtml(p.latest_meeting)}</div>`
        : `<div class="pc-meeting none">미팅 노트 없음</div>`}
    </div>`).join("");

  // ④ 최근 데일리 노트 5개
  const dailyFiles = (daily || []).slice(0, 5);
  if (!state.homeDaily || !dailyFiles.some((f) => f.name === state.homeDaily)) {
    state.homeDaily = dailyFiles[0]?.name || null;
  }
  const dailyChips = dailyFiles.length
    ? dailyFiles.map((f) =>
      `<button class="file-chip${f.name === state.homeDaily ? " active" : ""}" data-d="${escapeHtml(f.name)}">${escapeHtml(f.name)}</button>`).join("")
    : `<div class="ws-empty">데일리 노트 없음</div>`;

  doc.innerHTML = `
    ${mailStrip}
    <div class="home">
      <div class="home-col">
        <div class="ws-section">
          <div class="ws-head"><span class="ws-title">오늘 · 내일 일정</span></div>
          ${cal.error ? `<div class="ag-error">${escapeHtml(cal.error)}</div>` : ""}
          ${agendaHtml(nearEvents, "오늘·내일 일정 없음")}
        </div>
        <div class="ws-section">
          <div class="ws-head"><span class="ws-title">임박 · 지연 액션</span>
            <span class="spacer"></span>
            <button class="ws-open-btn" id="home-goto-board">전체 보드 →</button></div>
          <div class="board-cards">${urgentHtml}</div>
        </div>
        ${staleHtml ? `
        <div class="ws-section">
          <div class="ws-head"><span class="ws-title">정체 중 — 5일 이상 손 안 댄 액션</span></div>
          <div class="stale-list">${staleHtml}</div>
        </div>` : ""}
      </div>
      <div class="home-col">
        <div class="ws-section">
          <div class="ws-head"><span class="ws-title">프로젝트</span>
            <span class="spacer"></span>
            <button class="ws-open-btn" id="home-refresh"
              title="Granola 회의 + Gmail 이메일 다시 수집 (매일 06:40 자동)">↻ 아침 리프레시</button></div>
          <div class="proj-grid">${projCards}</div>
        </div>
        <div class="ws-section">
          <div class="ws-head"><span class="ws-title">최근 데일리 노트</span></div>
          <div class="ws-files">${dailyChips}</div>
          <div class="meeting-doc" id="home-daily-doc" style="display:none"></div>
        </div>
      </div>
    </div>`;

  $("home-goto-board").onclick = () => switchTab("board");
  const gotoMail = $("hs-goto-mail");
  if (gotoMail) gotoMail.onclick = () => switchTab("mail");
  doc.querySelectorAll(".stale-row").forEach((r) => {
    r.onclick = () => { state.boardProject = r.dataset.sp; switchTab("board"); };
  });
  $("home-refresh").onclick = async () => {
    try {
      const res = await postJson("/api/run/morning_refresh", {});
      startedToast(res, "아침 리프레시");
    } catch (e) { toast(`실패: ${e.body?.message || e.message}`, "err"); }
  };
  wireBiCards(doc, loadHome);

  doc.querySelectorAll(".proj-card").forEach((c) => {
    c.onclick = () => {
      state.workProject = c.dataset.p;
      state.workSub = "overview";
      localStorage.setItem("hios-work-proj", c.dataset.p);
      switchTab("work");
    };
  });

  const showDaily = async (name) => {
    const box = $("home-daily-doc");
    if (!box) return;
    box.style.display = "";
    box.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;
    try {
      const f = await api(`/api/file/daily/${encodeURIComponent(name)}`);
      box.innerHTML = `<div class="md">${renderMarkdown(f.content)}</div>`;
    } catch (e) { box.innerHTML = failHtml(e); }
  };
  doc.querySelectorAll(".file-chip[data-d]").forEach((chip) => {
    chip.onclick = () => {
      state.homeDaily = chip.dataset.d;
      doc.querySelectorAll(".file-chip[data-d]").forEach((c) =>
        c.classList.toggle("active", c.dataset.d === state.homeDaily));
      showDaily(state.homeDaily);
    };
  });
  if (state.homeDaily) showDaily(state.homeDaily);
}

/* ---------------------------------------------------------------- unified mail tab */

function emailRowHtml(e, showProject) {
  const link = e.thread_id
    ? `https://mail.google.com/mail/u/0/#all/${encodeURIComponent(e.thread_id)}` : "";
  const subj = link
    ? `<a class="em-subject" href="${escapeHtml(link)}" target="_blank" rel="noopener">${escapeHtml(e.subject || "(제목 없음)")}</a>`
    : `<span class="em-subject">${escapeHtml(e.subject || "(제목 없음)")}</span>`;
  const tid = escapeHtml(e.thread_id || "");
  return `<div class="em-row${e.important ? " em-important-row" : ""}" data-tid="${tid}">
    <div class="em-line">
      <span class="em-date">${escapeHtml(e.date || "")}</span>
      ${showProject ? `<span class="em-proj">${escapeHtml(e.project)}</span>` : ""}
      ${e.needs_action ? `<span class="pill failed">액션</span>` : ""}
      ${subj}
      <span class="em-from">${escapeHtml(e.from || "")}</span>
      ${e.thread_id ? `
        <button class="em-star${e.important ? " active" : ""}" data-tid="${tid}"
          title="${e.important ? "중요 해제" : "중요 표시"}">${e.important ? "★" : "☆"}</button>
        <button class="em-dismiss" data-tid="${tid}" title="목록에서 지우기">✕</button>` : ""}
    </div>
    ${e.summary ? `<div class="em-summary">${escapeHtml(e.summary)}</div>` : ""}
    ${e.needs_action && e.suggested_action
      ? `<div class="em-suggest">→ ${escapeHtml(e.suggested_action)}</div>` : ""}
  </div>`;
}

document.addEventListener("click", async (e) => {
  const star = e.target.closest(".em-star");
  const dismiss = e.target.closest(".em-dismiss");
  const btn = star || dismiss;
  if (!btn) return;
  const tid = btn.dataset.tid;
  if (!tid) return;
  const row = btn.closest(".em-row");
  try {
    if (star) {
      const nowImportant = !star.classList.contains("active");
      await postJson("/api/emails/important", { thread_id: tid, important: nowImportant });
      star.classList.toggle("active", nowImportant);
      star.textContent = nowImportant ? "★" : "☆";
      star.title = nowImportant ? "중요 해제" : "중요 표시";
      if (row) row.classList.toggle("em-important-row", nowImportant);
    } else {
      await postJson("/api/emails/dismiss", { thread_id: tid });
      if (row) row.remove();
      toast("이메일 목록에서 지웠습니다");
    }
  } catch (err) {
    toast(`실패: ${err.body?.message || err.message}`, "err");
  }
});

async function loadMailTab() {
  const doc = $("doc-view");
  doc.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;
  let d;
  try { d = await api("/api/emails"); }
  catch (e) { doc.innerHTML = failHtml(e); return; }

  const emails = d.emails || [];
  const stats = d.stats || {};
  const projNames = Object.keys(stats).length
    ? Object.keys(stats)
    : [...new Set(emails.map((e) => e.project))];
  if (state.mailFilter && !projNames.includes(state.mailFilter)) state.mailFilter = "";

  const chips = [`<button class="proj-chip${!state.mailFilter ? " active" : ""}" data-mf="">전체<span class="cnt">${emails.length}</span></button>`]
    .concat(projNames.map((p) => {
      const n = stats[p] ?? emails.filter((e) => e.project === p).length;
      return `<button class="proj-chip${state.mailFilter === p ? " active" : ""}" data-mf="${escapeHtml(p)}">${escapeHtml(p)}<span class="cnt">${n}</span></button>`;
    })).join("");

  const visible = state.mailFilter ? emails.filter((e) => e.project === state.mailFilter) : emails;
  const na = visible.filter((e) => e.needs_action);
  const rest = visible.filter((e) => !e.needs_action);
  const showProj = !state.mailFilter;

  const upd = d.updated ? `마지막 수집 ${fmtDate(d.updated)}` : "아직 수집 안 됨";
  let health = "";
  if (d.last_status === "error") {
    health = `<span class="mail-err">⚠ 마지막 수집 실패${d.last_error ? ` — ${escapeHtml(d.last_error)}` : ""}</span>`;
  } else if (d.missed && d.missed.length) {
    health = `<span class="mail-err">⚠ 검색 누락: ${escapeHtml(d.missed.join(", "))}</span>`;
  }

  doc.innerHTML = `
    <div class="ws-section">
      <div class="ws-head"><span class="ws-title">이메일 — 전체 프로젝트</span>
        <span class="em-updated">${escapeHtml(upd)}</span>${health}<span class="spacer"></span>
        <button class="ws-open-btn" id="mail-refresh"
          title="Gmail 이메일 수집·분류 (매일 06:40 자동)">지금 수집</button></div>
      <div class="proj-chips">${chips}</div>
      ${na.length ? `
        <div class="mail-group-head na">회신·작업 필요 <span class="cnt">${na.length}</span></div>
        <div class="em-list">${na.map((e) => emailRowHtml(e, showProj)).join("")}</div>` : ""}
      <div class="mail-group-head">${na.length ? "나머지" : "수집된 이메일"}</div>
      <div class="em-list">${rest.length
        ? rest.map((e) => emailRowHtml(e, showProj)).join("")
        : `<div class="ws-empty">이메일 없음${emails.length ? "" : " — '지금 수집'을 누르거나 매일 06:40 자동 수집을 기다리세요"}</div>`}</div>
    </div>`;

  doc.querySelectorAll("[data-mf]").forEach((c) => {
    c.onclick = () => { state.mailFilter = c.dataset.mf; loadMailTab(); };
  });
  $("mail-refresh").onclick = async () => {
    try {
      const res = await postJson("/api/run/morning_refresh", {});
      startedToast(res, "이메일 수집·분류");
    } catch (e) { toast(`실패: ${e.body?.message || e.message}`, "err"); }
  };
}

/* ---------------------------------------------------------------- workspace shell */

async function loadWork() {
  stopAiPoll();
  const doc = $("doc-view");
  doc.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;
  let projects;
  try { projects = await api("/api/projects"); }
  catch (e) { doc.innerHTML = failHtml(e); return; }
  if (!projects.length) { doc.innerHTML = `<div class="doc-empty">프로젝트 없음</div>`; return; }

  if (!state.workProject) state.workProject = localStorage.getItem("hios-work-proj");
  if (!state.workProject || !projects.some((p) => p.name === state.workProject)) {
    state.workProject = projects[0].name;
  }

  const chips = `<div class="proj-chips">` + projects.map((p) => `
    <button class="proj-chip${p.name === state.workProject ? " active" : ""}" data-p="${escapeHtml(p.name)}">
      ${escapeHtml(p.name)}${p.open_actions ? `<span class="cnt">${p.open_actions}</span>` : ""}
    </button>`).join("") + `</div>`;

  const subs = WORK_SUBS.slice();
  if (state.workProject === CONTENT_PROJECT) subs.push(["content", "콘텐츠"]);
  if (!subs.some(([id]) => id === state.workSub)) state.workSub = "overview";
  const subTabs = `<div class="sub-tabs">` + subs.map(([id, ko]) =>
    `<button class="sub-tab${id === state.workSub ? " active" : ""}" data-s="${id}">${ko}</button>`).join("") + `</div>`;

  doc.innerHTML = chips + subTabs + `<div id="ws-body"><div class="doc-empty">불러오는 중…</div></div>`;

  doc.querySelectorAll(".proj-chip").forEach((c) => {
    c.onclick = () => {
      if (c.dataset.p === state.workProject) return;
      if (!confirmLeave()) return;
      state.workProject = c.dataset.p;
      state.workMeeting = null;
      state.workFilePath = null;
      localStorage.setItem("hios-work-proj", c.dataset.p);
      loadWork();
    };
  });
  doc.querySelectorAll(".sub-tab").forEach((b) => {
    b.onclick = () => {
      if (b.dataset.s === state.workSub) return;
      if (!confirmLeave()) return;
      state.workSub = b.dataset.s;
      loadWork();
    };
  });

  const body = $("ws-body");
  if (state.workSub === "overview") return loadWorkOverview(body);
  if (state.workSub === "actions") return renderBoardView(body, state.workProject);
  if (state.workSub === "meetings") return loadWorkMeetings(body);
  if (state.workSub === "emails") return loadWorkEmails(body);
  if (state.workSub === "files") return loadWorkFiles(body);
  if (state.workSub === "resources") return loadWorkResources(body);
  if (state.workSub === "accounts") return loadWorkAccounts(body);
  if (state.workSub === "ai") return loadWorkAi(body);
  if (state.workSub === "content") return loadWorkContent(body);
}

/* -------- workspace: 개요 -------- */

function priorityItemHtml(it) {
  return `<div class="pri-item" data-id="${escapeHtml(it.id)}">
    <div class="pri-top">
      <span class="bi-prio ${escapeHtml(it.priority || "med")}">${BI_PRIO_KO[it.priority] || "중간"}</span>
      ${dueBadge(it.due)}
    </div>
    <div class="pri-title">${escapeHtml(it.title)}</div>
  </div>`;
}

function priorityPanelHtml(items) {
  const open = items.filter((it) => it.status !== "done");
  const top = open.slice().sort((a, b) => {
    const x = biSortKey(a), y = biSortKey(b);
    return x[0] - y[0] || x[1] - y[1];
  }).slice(0, 8);
  return `
    <div class="ws-section ov-priority">
      <div class="ws-head"><span class="ws-title">⭐ 지금 중요한 것</span>
        <span class="spacer"></span><span class="em-updated">${open.length}건 열림</span></div>
      ${top.length
        ? `<div class="pri-list">${top.map(priorityItemHtml).join("")}</div>`
        : `<div class="ws-empty">열린 액션 없음 🎉</div>`}
    </div>`;
}

async function loadWorkOverview(box) {
  const name = state.workProject;
  let p;
  try { p = await api(`/api/projects/${encodeURIComponent(name)}`); }
  catch (e) { box.innerHTML = failHtml(e); return; }
  const briefRel = `01-Projects/${name}/_PROJECT-BRIEF.md`;
  const brief = await api(`/api/vault-file/${encodeRel(briefRel)}`).catch(() => null);
  const itemGroups = await api("/api/action-items").catch(() => []);
  const myItems = (itemGroups.find((g) => g.project === name) || {}).items || [];

  const todosHtml = p.todos.length
    ? p.todos.map((t) => `
      <div class="todo-row${t.done ? " done" : ""}" data-line="${t.line}">
        <span class="todo-check">${t.done ? "✓" : ""}</span>
        <span class="todo-text">${escapeHtml(t.text)}</span>
      </div>`).join("")
    : `<div class="ws-empty">할 일 없음</div>`;

  box.innerHTML = `
  <div class="ov-split">
    <div class="ov-main">
      <div class="ws-section ov-ask">
        <div class="ws-head"><span class="ws-title">엔진에게 바로 요청</span><span class="spacer"></span>
          <span class="ai-note-inline">Claude가 <code>01-Projects/${escapeHtml(name)}/</code> 범위로 실행 — 로그는 AI 요청 탭</span></div>
        <div class="ws-form">
          <input class="ws-input" id="ov-ask-input" maxlength="2000"
            placeholder="예: 최근 미팅노트 반영해서 _STATUS.md 업데이트해줘 (Enter로 실행)">
          <button class="ws-add-btn" id="ov-ask-run">엔진 실행</button>
        </div>
      </div>
      <div class="ws-section" id="ov-status">
        <div class="ws-head"><span class="ws-title">현황 — _STATUS.md</span><span class="spacer"></span>
          <button class="ws-open-btn" id="ov-status-edit">편집</button>
          <button class="ws-open-btn" data-open-folder="root">프로젝트 폴더</button></div>
        <div class="md">${renderMarkdown(p.status || "_STATUS.md 없음")}</div>
      </div>
      ${brief && !brief.binary ? `
      <div class="ws-section" id="ov-brief">
        <div class="ws-head"><span class="ws-title">브리프 — _PROJECT-BRIEF.md</span><span class="spacer"></span>
          <button class="ws-open-btn" id="ov-brief-edit">편집</button></div>
        <div class="md">${renderMarkdown(brief.content)}</div>
      </div>` : ""}
      <div class="ws-section">
        <div class="ws-head"><span class="ws-title">할 일 — _TODO.md</span></div>
        <div id="ws-todos">${todosHtml}</div>
        <div class="ws-form">
          <input class="ws-input" id="todo-new" placeholder="새 할 일 입력 후 Enter 또는 추가">
          <button class="ws-add-btn" id="todo-add">추가</button>
        </div>
      </div>
    </div>
    <div class="ov-side">${priorityPanelHtml(myItems)}</div>
  </div>`;

  const reload = () => loadWorkOverview(box);

  const ovAsk = async () => {
    const inp = $("ov-ask-input");
    const prompt = inp.value.trim();
    if (!prompt) { toast("요청 내용을 입력하세요", "warn"); return; }
    try {
      const res = await postJson(`/api/projects/${encodeURIComponent(name)}/request`, { prompt });
      startedToast(res, `엔진 요청 — ${name}`);
      inp.value = "";
      state.workSub = "ai";
      state.aiJobId = res.job_id;
      state.aiOffset = 0;
      state.aiLines = [];
      loadWork();
      schedulePoll(0);
    } catch (e) {
      toast(`실행 실패: ${e.body?.message || e.message}`, "err");
    }
  };
  $("ov-ask-run").onclick = ovAsk;
  $("ov-ask-input").onkeydown = (ev) => { if (ev.key === "Enter") ovAsk(); };

  const statusEditBtn = box.querySelector("#ov-status-edit");
  if (statusEditBtn) statusEditBtn.onclick = () =>
    openInlineEditor(box.querySelector("#ov-status"), `01-Projects/${name}/_STATUS.md`, reload);
  const briefEditBtn = box.querySelector("#ov-brief-edit");
  if (briefEditBtn) briefEditBtn.onclick = () =>
    openInlineEditor(box.querySelector("#ov-brief"), briefRel, reload);

  box.querySelectorAll("[data-open-folder]").forEach((b) => {
    b.onclick = () => postJson(`/api/projects/${encodeURIComponent(name)}/open`,
      { which: b.dataset.openFolder }).catch(() => {});
  });

  box.querySelectorAll(".todo-row").forEach((row) => {
    row.onclick = async () => {
      try {
        await postJson(`/api/projects/${encodeURIComponent(name)}/todos/toggle`,
          { line: Number(row.dataset.line) });
        reload();
      } catch (e) { toast(`실패: ${e.message}`, "err"); }
    };
  });
  const addTodo = async () => {
    const inp = $("todo-new");
    if (!inp.value.trim()) return;
    try {
      await postJson(`/api/projects/${encodeURIComponent(name)}/todos`, { text: inp.value.trim() });
      toast("할 일 추가됨 — _TODO.md에 기록", "ok");
      reload();
    } catch (e) { toast(`실패: ${e.message}`, "err"); }
  };
  $("todo-add").onclick = addTodo;
  $("todo-new").onkeydown = (ev) => { if (ev.key === "Enter") addTodo(); };

  box.querySelectorAll(".pri-item").forEach((row) => {
    row.onclick = () => {
      if (!confirmLeave()) return;
      state.pendingHighlightActionId = row.dataset.id;
      state.workSub = "actions";
      loadWork();
    };
  });
}

/* -------- workspace: 미팅 -------- */

async function loadWorkMeetings(box) {
  const name = state.workProject;
  let p;
  try { p = await api(`/api/projects/${encodeURIComponent(name)}`); }
  catch (e) { box.innerHTML = failHtml(e); return; }

  const meetingsHtml = p.meetings.length
    ? p.meetings.map((f) =>
      `<button class="file-chip${f.name === state.workMeeting ? " active" : ""}" data-m="${escapeHtml(f.name)}">${escapeHtml(f.name)}</button>`).join("")
    : `<div class="ws-empty">미팅 노트 없음 — Granola 동기화로 자동 생성됩니다</div>`;

  box.innerHTML = `
    <div class="ws-section">
      <div class="ws-head"><span class="ws-title">미팅 노트</span><span class="spacer"></span>
        <button class="ws-open-btn" id="meet-open">폴더 열기</button></div>
      <div class="ws-files">${meetingsHtml}</div>
      <div class="meeting-doc" id="meeting-doc" style="display:none"></div>
    </div>`;

  $("meet-open").onclick = () => postJson(`/api/projects/${encodeURIComponent(name)}/open`,
    { which: "meetings" }).catch(() => {});

  const showMeeting = async (fname) => {
    const md = $("meeting-doc");
    md.style.display = "";
    md.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;
    try {
      const f = await api(`/api/projects/${encodeURIComponent(name)}/meeting/${encodeURIComponent(fname)}`);
      md.innerHTML = `<div class="md">${renderMarkdown(f.content)}</div>`;
    } catch (e) { md.innerHTML = failHtml(e); }
  };
  box.querySelectorAll(".file-chip[data-m]").forEach((chip) => {
    chip.onclick = () => {
      state.workMeeting = chip.dataset.m;
      box.querySelectorAll(".file-chip[data-m]").forEach((c) =>
        c.classList.toggle("active", c.dataset.m === state.workMeeting));
      showMeeting(state.workMeeting);
    };
  });
  if (state.workMeeting && p.meetings.some((f) => f.name === state.workMeeting)) {
    showMeeting(state.workMeeting);
  }
}

/* -------- workspace: 이메일 -------- */

async function loadWorkEmails(box) {
  const name = state.workProject;
  let p;
  try { p = await api(`/api/projects/${encodeURIComponent(name)}/emails`); }
  catch (e) { box.innerHTML = failHtml(e); return; }

  const rows = p.emails.length
    ? p.emails.map((e) => emailRowHtml(e, false)).join("")
    : `<div class="ws-empty">수집된 이메일 없음 — '지금 수집'을 누르거나 매일 아침 06:40 자동 수집을 기다리세요</div>`;

  const upd = p.updated ? `마지막 수집 ${fmtDate(p.updated)}` : "아직 수집 안 됨";
  const health = p.last_status === "error"
    ? `<span class="mail-err">⚠ 마지막 수집 실패${p.last_error ? ` — ${escapeHtml(p.last_error)}` : ""}</span>` : "";

  box.innerHTML = `
    <div class="ws-section">
      <div class="ws-head"><span class="ws-title">이메일 — ${escapeHtml(name)}</span>
        <span class="em-updated">${escapeHtml(upd)}</span>${health}<span class="spacer"></span>
        <button class="ws-open-btn" id="em-refresh">지금 수집</button></div>
      <div class="em-list">${rows}</div>
    </div>`;

  $("em-refresh").onclick = async () => {
    try {
      const res = await postJson("/api/run/morning_refresh", {});
      startedToast(res, "이메일·미팅 수집");
    } catch (e) { toast(`실패: ${e.body?.message || e.message}`, "err"); }
  };
}

/* -------- workspace: 파일 (트리 + 뷰어/에디터) -------- */

async function loadWorkFiles(box) {
  const name = state.workProject;
  let tree = state.workTreeCache[name];
  if (!tree) {
    try { tree = await api(`/api/projects/${encodeURIComponent(name)}/tree`); }
    catch (e) { box.innerHTML = failHtml(e); return; }
    state.workTreeCache[name] = tree;
  }
  if (!state.workOpenDirs[name]) state.workOpenDirs[name] = new Set();
  const open = state.workOpenDirs[name];

  box.innerHTML = `
    <div class="files-wrap">
      <div class="file-tree">
        <div class="dropzone-strip">
          <span class="dz-ic">⇣</span> 파일을 여기로 드래그 — ${escapeHtml(name)} 안에서 AI가 정리합니다
        </div>
        <div id="upload-batches" data-project="${escapeHtml(name)}"></div>
        <div class="tree-toolbar">
          <span class="tree-root-name">${escapeHtml(tree.root)}</span>
          <span class="spacer"></span>
          ${tree.truncated ? `<span class="tree-trunc" title="깊이/개수 제한으로 일부만 표시">일부만 표시</span>` : ""}
          <button class="ws-open-btn" id="tree-newdir" title="새 폴더 생성">＋폴더</button>
          <button class="ws-open-btn" id="tree-newmd" title="새 마크다운 노트 생성">＋노트</button>
          <button class="ws-open-btn" id="tree-refresh">새로고침</button>
        </div>
        <div class="tree-body" id="tree-root"></div>
        <div class="file-open-row">
          <button class="ws-open-btn" data-open-root="finder">Finder에서 열기</button>
          <button class="ws-open-btn" data-open-root="vscode">VS Code로 열기</button>
        </div>
      </div>
      <div class="file-pane" id="file-pane"><div class="doc-empty">파일을 선택하세요</div></div>
    </div>`;

  $("tree-refresh").onclick = () => {
    if (!confirmLeave()) return;
    delete state.workTreeCache[name];
    loadWorkFiles(box);
  };

  const createInTree = async (isDir) => {
    if (!confirmLeave()) return;
    const kind = isDir ? "폴더" : "노트(.md)";
    const raw = prompt(`새 ${kind} 경로 — ${tree.root}/ 아래 상대 경로`,
      isDir ? "새폴더" : "새노트.md");
    if (raw === null) return;
    let rel = raw.trim().replace(/^\/+|\/+$/g, "");
    if (!rel) { toast("경로를 입력하세요", "warn"); return; }
    if (!isDir && !rel.endsWith(".md")) rel += ".md";
    const path = `${tree.root}/${rel}`;
    try {
      const res = await postJson("/api/vault-create", { path, dir: isDir });
      toast(`${kind} 생성됨 — ${res.path}`, "ok");
      delete state.workTreeCache[name];
      if (!isDir) state.workFilePath = res.path;
      // reopen parent dirs so the new node is visible
      const parts = res.path.split("/");
      for (let i = 3; i < parts.length; i += 1) open.add(parts.slice(0, i).join("/"));
      if (isDir) open.add(res.path);
      await loadWorkFiles(box);
      if (!isDir) {
        const pane = $("file-pane");
        if (pane) openInlineEditor(pane, res.path, () => openWorkFile(res.path));
      }
    } catch (e) {
      if (e.status === 409) toast("이미 존재하는 경로입니다", "warn");
      else toast(`생성 실패: ${e.body?.message || e.message}`, "err");
    }
  };
  $("tree-newdir").onclick = () => createInTree(true);
  $("tree-newmd").onclick = () => createInTree(false);
  box.querySelectorAll("[data-open-root]").forEach((b) => {
    b.onclick = () => postJson("/api/open-path", { path: tree.root, app: b.dataset.openRoot })
      .catch((e) => toast(`열기 실패: ${e.message}`, "err"));
  });

  const rootEl = $("tree-root");
  const rerender = () => renderTree(rootEl, tree.children, open, rerender);
  rerender();

  if (state.workFilePath && state.workFilePath.startsWith(tree.root + "/")) {
    openWorkFile(state.workFilePath);
  } else {
    state.workFilePath = null;
  }
  loadUploadBatches();
}

function renderTree(rootEl, children, open, rerender, opts) {
  const activePath = opts ? opts.activePath : state.workFilePath;
  const onFile = (opts && opts.onFile) || ((path) => {
    state.workFilePath = path;
    rerender();
    openWorkFile(path);
  });
  rootEl.innerHTML = "";
  const build = (nodes, depth) => {
    const wrap = document.createElement("div");
    for (const n of nodes) {
      const row = document.createElement("div");
      row.className = "tree-row" + (n.dir ? " dir" : "") +
        (!n.dir && n.path === activePath ? " active" : "");
      row.style.paddingLeft = `${depth * 14 + 8}px`;
      if (n.dir) {
        const isOpen = open.has(n.path);
        row.innerHTML = `<span class="tree-caret">${isOpen ? "▾" : "▸"}</span>
          <span class="tree-name">${escapeHtml(n.name)}</span>`;
        row.onclick = () => {
          if (open.has(n.path)) open.delete(n.path); else open.add(n.path);
          rerender();
        };
        wrap.appendChild(row);
        if (isOpen && n.children && n.children.length) {
          wrap.appendChild(build(n.children, depth + 1));
        } else if (isOpen) {
          const empty = document.createElement("div");
          empty.className = "tree-empty";
          empty.style.paddingLeft = `${(depth + 1) * 14 + 8}px`;
          empty.textContent = "비어 있음";
          wrap.appendChild(empty);
        }
      } else {
        row.innerHTML = `<span class="tree-ic">${n.editable ? "▤" : "·"}</span>
          <span class="tree-name">${escapeHtml(n.name)}</span>
          <span class="tree-size">${fmtSize(n.size)}</span>`;
        row.onclick = () => {
          if (!confirmLeave()) return;
          onFile(n.path);
        };
        wrap.appendChild(row);
      }
    }
    return wrap;
  };
  rootEl.appendChild(build(children, 0));
}

async function openWorkFile(rel) {
  const pane = $("file-pane");
  if (!pane) return;
  pane.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;
  let f;
  try { f = await api(`/api/vault-file/${encodeRel(rel)}`); }
  catch (e) { pane.innerHTML = failHtml(e); return; }
  renderFilePane(pane, rel, f);
}

function openButtonsHtml() {
  return `<div class="file-open-row">
    <button class="ws-open-btn" data-open="finder">Finder에서 열기</button>
    <button class="ws-open-btn" data-open="vscode">VS Code로 열기</button>
  </div>`;
}

function wireOpenButtons(container, rel) {
  container.querySelectorAll("[data-open]").forEach((b) => {
    b.onclick = () => postJson("/api/open-path", { path: rel, app: b.dataset.open })
      .catch((e) => toast(`열기 실패: ${e.message}`, "err"));
  });
}

function renderFilePane(pane, rel, f, reopen) {
  let body;
  if (f.binary) {
    body = `<div class="bin-card">
      <div class="bin-name">${escapeHtml(f.name)}</div>
      <div class="bin-meta">${escapeHtml(f.ext || "파일")} · ${fmtSize(f.size)} — 브라우저 미리보기 불가, 앱으로 여세요</div>
    </div>`;
  } else if (f.ext === ".md") {
    body = `<div class="file-head">
        <span class="editor-path">${escapeHtml(rel)}</span><span class="spacer"></span>
        <button class="ws-add-btn" id="file-edit">편집</button></div>
      <div class="md">${renderMarkdown(f.content)}</div>`;
  } else {
    body = `<div class="file-head"><span class="editor-path">${escapeHtml(rel)}</span></div>
      <pre class="code-view">${escapeHtml(f.content)}</pre>`;
  }
  pane.innerHTML = body + openButtonsHtml();
  wireOpenButtons(pane, rel);
  const md = pane.querySelector(".md");
  if (md) linkifyVaultPaths(md);
  const eb = pane.querySelector("#file-edit");
  const again = reopen || openWorkFile;
  if (eb) eb.onclick = () => openInlineEditor(pane, rel, () => again(rel));
}

/* -------- markdown editor + 409 conflict UX -------- */

async function openInlineEditor(container, rel, afterClose) {
  let f;
  try { f = await api(`/api/vault-file/${encodeRel(rel)}`); }
  catch (e) { toast(`로드 실패: ${e.message}`, "err"); return; }
  if (f.binary || !f.editable) { toast(".md 파일만 편집할 수 있습니다", "warn"); return; }
  renderEditor(container, rel, f, afterClose);
}

function renderEditor(container, rel, f, afterClose) {
  state.editorDirty = false;
  container.innerHTML = `
    <div class="editor">
      <div class="editor-head">
        <span class="editor-path">${escapeHtml(rel)}</span>
        <span class="editor-dirty" id="ed-dirty" style="visibility:hidden">● 수정됨</span>
        <span class="spacer"></span>
        <button class="ws-add-btn" id="ed-save">저장</button>
        <button class="ws-open-btn" id="ed-cancel">닫기</button>
      </div>
      <div class="editor-conflict" id="ed-conflict" style="display:none"></div>
      <textarea class="editor-ta" id="ed-ta" spellcheck="false"></textarea>
    </div>`;

  const ta = container.querySelector("#ed-ta");
  const dirtyEl = container.querySelector("#ed-dirty");
  const conflictBox = container.querySelector("#ed-conflict");
  ta.value = f.content;
  let mtime = f.mtime;

  ta.oninput = () => {
    state.editorDirty = true;
    dirtyEl.style.visibility = "visible";
  };
  ta.onkeydown = (ev) => {
    if ((ev.metaKey || ev.ctrlKey) && ev.key === "s") { ev.preventDefault(); save(false); }
  };

  container.querySelector("#ed-cancel").onclick = () => {
    if (!confirmLeave()) return;
    afterClose();
  };

  const clean = () => {
    state.editorDirty = false;
    dirtyEl.style.visibility = "hidden";
    conflictBox.style.display = "none";
  };

  const save = async (force) => {
    try {
      const res = await postJson(`/api/vault-file/${encodeRel(rel)}`,
        { content: ta.value, mtime, force: !!force });
      mtime = res.mtime;
      clean();
      toast("저장됨", "ok");
      afterClose();
    } catch (e) {
      if (e.status === 409) {
        conflictBox.style.display = "";
        conflictBox.innerHTML = `
          <span class="conflict-msg">⚠ 다른 곳에서 수정됨 (Obsidian?)</span>
          <button class="ab-btn" id="ed-reload">다시 불러오기 (내 변경 버림)</button>
          <button class="ab-btn" id="ed-force">그래도 저장 (덮어쓰기)</button>`;
        conflictBox.querySelector("#ed-reload").onclick = async () => {
          try {
            const nf = await api(`/api/vault-file/${encodeRel(rel)}`);
            ta.value = nf.content;
            mtime = nf.mtime;
            clean();
            toast("다시 불러옴 — 내 변경은 버려짐", "warn");
          } catch (e2) { toast(`다시 불러오기 실패: ${e2.message}`, "err"); }
        };
        conflictBox.querySelector("#ed-force").onclick = () => save(true);
      } else {
        toast(`저장 실패: ${e.body?.message || e.message}`, "err");
      }
    }
  };
  container.querySelector("#ed-save").onclick = () => save(false);
}

/* ---------------------------------------------------------------- vault file tab (파일) */
/* Whole-vault explorer + upload dropzone + AI classification batches. */

async function loadVaultTab() {
  const doc = $("doc-view");
  doc.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;
  let tree = state.vaultTree;
  if (!tree) {
    try { tree = await api("/api/vault-tree"); }
    catch (e) { doc.innerHTML = failHtml(e); return; }
    state.vaultTree = tree;
  }
  const open = state.vaultOpenDirs;

  doc.innerHTML = `
    <div class="files-wrap vault-wrap">
      <div class="file-tree">
        <div class="dropzone-strip" id="vault-dropzone">
          <span class="dz-ic">⇣</span> 파일을 여기로 드래그 — AI가 자동 분류합니다
        </div>
        <div id="upload-batches"></div>
        <div class="tree-toolbar">
          <span class="tree-root-name">vault</span>
          <span class="spacer"></span>
          ${tree.truncated ? `<span class="tree-trunc" title="깊이/개수 제한으로 일부만 표시">일부만 표시</span>` : ""}
          <button class="ws-open-btn" id="vault-tree-refresh">새로고침</button>
        </div>
        <div class="tree-body" id="vault-tree-root"></div>
      </div>
      <div class="file-pane" id="vault-file-pane"><div class="doc-empty">파일을 선택하세요</div></div>
    </div>`;

  $("vault-tree-refresh").onclick = () => {
    if (!confirmLeave()) return;
    state.vaultTree = null;
    loadVaultTab();
  };

  const rootEl = $("vault-tree-root");
  const rerender = () => renderTree(rootEl, tree.children, open, rerender, {
    activePath: state.vaultFilePath,
    onFile: (path) => {
      state.vaultFilePath = path;
      rerender();
      openVaultFile(path);
    },
  });
  rerender();

  if (state.vaultFilePath) openVaultFile(state.vaultFilePath);
  loadUploadBatches();
}

async function openVaultFile(rel) {
  const pane = $("vault-file-pane");
  if (!pane) return;
  pane.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;
  let f;
  try { f = await api(`/api/vault-file/${encodeRel(rel)}`); }
  catch (e) { pane.innerHTML = failHtml(e); return; }
  renderFilePane(pane, rel, f, openVaultFile);
}

function revealVaultDir(dir) {
  const parts = dir.split("/");
  for (let i = 1; i <= parts.length; i += 1) {
    state.vaultOpenDirs.add(parts.slice(0, i).join("/"));
  }
  if (state.activeTab === "vault") loadVaultTab();
  else switchTab("vault");
}

/* -------- uploads: global dropzone + AI classification batches -------- */

const UB_STATUS_KO = {
  staged: "대기", classifying: "분류 중", filed: "완료", failed: "실패",
};
const UB_SUBFOLDERS = [
  ["06-Documents", "문서"], ["02-Meetings", "회의록"],
  ["05-References", "참고"], ["01-Deliverables", "산출물"],
];

let dragDepth = 0;

// while on a workspace project, drops are scoped to that project
const dropProject = () => (state.activeTab === "work" && state.workProject) || "";

document.addEventListener("dragenter", (ev) => {
  if (![...(ev.dataTransfer?.types || [])].includes("Files")) return;
  ev.preventDefault();
  dragDepth += 1;
  const proj = dropProject();
  const msg = document.querySelector("#drop-overlay .drop-overlay-msg");
  if (msg) msg.textContent = proj
    ? `여기에 놓으면 ${proj} 안으로 업로드 — AI가 폴더를 정리합니다`
    : "여기에 놓으면 업로드 — AI가 자동 분류합니다";
  $("drop-overlay").style.display = "";
});
document.addEventListener("dragover", (ev) => {
  if (![...(ev.dataTransfer?.types || [])].includes("Files")) return;
  ev.preventDefault();
});
document.addEventListener("dragleave", (ev) => {
  if (![...(ev.dataTransfer?.types || [])].includes("Files")) return;
  dragDepth = Math.max(0, dragDepth - 1);
  if (dragDepth === 0) $("drop-overlay").style.display = "none";
});
document.addEventListener("drop", (ev) => {
  if (![...(ev.dataTransfer?.types || [])].includes("Files")) return;
  ev.preventDefault();
  dragDepth = 0;
  $("drop-overlay").style.display = "none";
  const files = [...ev.dataTransfer.files];
  if (files.length) uploadFiles(files, dropProject());
});

async function uploadFiles(files, project) {
  const fd = new FormData();
  if (project) fd.append("project", project);
  for (const f of files) fd.append("files", f, f.name);
  toast(`${files.length}개 업로드 중…`, "ok");
  let res;
  try {
    const r = await fetch("/api/upload", { method: "POST", body: fd });
    res = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(res.message || `HTTP ${r.status}`);
  } catch (e) {
    toast(`업로드 실패: ${e.message}`, "err");
    return;
  }
  if (res.conflict) {
    toast(`${res.count}개 업로드됨 — 다른 AI 작업 종료 후 분류 버튼을 누르세요`, "warn");
  } else {
    toast(`${res.count}개 업로드됨 — AI 분류 시작`, "ok");
  }
  state.vaultTree = null;   // staging dir appeared under 00-Inbox
  if (project) {
    delete state.workTreeCache[project];
    state.workSub = "files";
    if (state.activeTab === "work") loadWork();
    else switchTab("work");
  } else if (state.activeTab === "vault") loadVaultTab();
  else switchTab("vault");
}

function stopUploadPoll() {
  clearTimeout(state.uploadPollTimer);
  state.uploadPollTimer = null;
}

async function loadUploadBatches() {
  stopUploadPoll();
  const box = $("upload-batches");
  if (!box) return;
  try { state.uploadBatches = await api("/api/uploads"); }
  catch { return; }
  renderUploadBatches(box);
  if (state.uploadBatches.some((b) => b.status === "classifying")) {
    state.uploadPollTimer = setTimeout(() => {
      const stillHere = $("upload-batches");
      if (stillHere) {
        const before = JSON.stringify(state.uploadBatches);
        api("/api/uploads").then((bs) => {
          const done = state.uploadBatches.some((b) => b.status === "classifying")
            && !bs.some((b) => b.status === "classifying");
          state.uploadBatches = bs;
          if (JSON.stringify(bs) !== before) {
            renderUploadBatches(stillHere);
            if (done) {
              toast("업로드 분류 완료", "ok");
              state.vaultTree = null;
              if (state.activeTab === "work") {
                delete state.workTreeCache[state.workProject];
                loadWork();
              } else if (state.activeTab === "vault") loadVaultTab();
              return;
            }
          }
          if (bs.some((b) => b.status === "classifying")) loadUploadBatches();
        }).catch(() => {});
      }
    }, 3000);
  }
}

function ubDestOptions(current) {
  const projects = (state.vaultTree ? state.vaultTree.children : [])
    .filter((c) => c.dir && c.path === "01-Projects")
    .flatMap((c) => (c.children || []).filter((x) => x.dir).map((x) => x.name));
  const opts = [`<option value="">재분류…</option>`,
    `<option value="00-Inbox/unsorted">00-Inbox/unsorted</option>`];
  for (const p of projects) {
    for (const [sub, ko] of UB_SUBFOLDERS) {
      const v = `01-Projects/${p}/${sub}`;
      opts.push(`<option value="${escapeHtml(v)}"${v === current ? " selected" : ""}>${escapeHtml(p)} · ${ko}</option>`);
    }
  }
  return opts.join("");
}

function renderUploadBatches(box) {
  let batches = state.uploadBatches || [];
  const scope = box.dataset.project || "";
  if (scope) batches = batches.filter((b) => b.project === scope);
  if (!batches.length) { box.innerHTML = ""; box.className = "upload-batches"; return; }
  box.className = "upload-batches";
  box.innerHTML = batches.map((b) => {
    const t = fmtDate(b.created);
    const pill = `<span class="pill ${b.status === "filed" ? "success" : b.status === "failed" ? "failed" : "running"}">${UB_STATUS_KO[b.status] || b.status}</span>`;
    const retry = (b.status === "failed" || b.status === "staged")
      ? `<button class="ws-open-btn" data-ub-retry="${escapeHtml(b.id)}">분류 ${b.status === "failed" ? "재시도" : "시작"}</button>` : "";
    const failNote = b.status === "failed"
      ? `<div class="ub-fail">분류 실패 — 파일은 ${escapeHtml(b.staging)}에 그대로 있습니다</div>` : "";
    // destination summary: group filed files by folder
    const groups = {};
    for (const f of b.files) {
      if (f.status !== "filed" || !f.dest) continue;
      const dir = f.dest.split("/").slice(0, -1).join("/");
      (groups[dir] = groups[dir] || []).push(f);
    }
    const dests = Object.keys(groups).sort().map((dir) =>
      `<div class="ub-dest-row">└ <a class="ub-dest-dir" data-dir="${escapeHtml(dir)}" href="#">${escapeHtml(dir)}</a>
       <b>${groups[dir].length}개</b></div>`).join("");
    const destBox = dests ? `<div class="ub-dests">${dests}</div>` : "";
    const rows = b.files.map((f) => {
      const where = f.status === "filed" && f.dest
        ? `→ <a class="vault-link" data-path="${escapeHtml(f.dest)}" href="#">${escapeHtml(f.dest)}</a>`
        : `<span class="ub-label">(${escapeHtml(UB_STATUS_KO[f.status] || f.status)})</span>`;
      const desc = (f.label ? `<span class="ub-label">${escapeHtml(f.label)}</span>` : "")
        + (f.summary ? ` <span class="ub-summary">"${escapeHtml(f.summary)}"</span>` : "");
      const resel = `<select class="ub-resel" data-ub-b="${escapeHtml(b.id)}" data-ub-f="${escapeHtml(f.name)}">${ubDestOptions("")}</select>`;
      return `<div class="ub-file"><span class="tree-ic">▤</span>
        <span class="ub-name">${escapeHtml(f.name)}</span> ${desc} ${where} ${resel}</div>`;
    }).join("");
    return `<div class="ub-card">
      <div class="ub-head">${pill}<span>${t} · ${b.files.length}개</span><span class="spacer"></span>${retry}</div>
      ${destBox}${failNote}${rows}
    </div>`;
  }).join("");

  box.querySelectorAll(".ub-dest-dir").forEach((a) => {
    a.onclick = (ev) => {
      ev.preventDefault();
      const dir = a.dataset.dir;
      const parts = dir.split("/");
      if (state.activeTab === "work" && parts[0] === "01-Projects"
          && parts[1] === state.workProject) {
        // expand inside the workspace tree instead of jumping to the vault tab
        const open = state.workOpenDirs[parts[1]]
          || (state.workOpenDirs[parts[1]] = new Set());
        for (let i = 3; i <= parts.length; i += 1) {
          open.add(parts.slice(0, i).join("/"));
        }
        loadWork();
      } else {
        revealVaultDir(dir);
      }
    };
  });
  box.querySelectorAll("[data-ub-retry]").forEach((btn) => {
    btn.onclick = async () => {
      try {
        await postJson(`/api/uploads/${encodeURIComponent(btn.dataset.ubRetry)}/classify`, {});
        toast("분류 시작됨", "ok");
        loadUploadBatches();
        schedulePoll(0);
      } catch (e) { toast(`실패: ${e.body?.message || e.message}`, "err"); }
    };
  });
  box.querySelectorAll(".ub-resel").forEach((sel) => {
    sel.onchange = async () => {
      if (!sel.value) return;
      try {
        const res = await postJson(`/api/uploads/${encodeURIComponent(sel.dataset.ubB)}/reclassify`,
          { name: sel.dataset.ubF, dest: sel.value });
        toast(`이동됨 → ${res.dest}`, "ok");
        state.vaultTree = null;
        if (state.activeTab === "work") {
          delete state.workTreeCache[state.workProject];
          loadWork();
        } else {
          loadVaultTab();
        }
      } catch (e) {
        toast(`재분류 실패: ${e.body?.message || e.message}`, "err");
        sel.value = "";
      }
    };
  });
}

/* ---------------------------------------------------------------- graph tab (F4) */

const GRAPH_PALETTE = [
  "#e05d5d", "#5d8fe0", "#5dbf7a", "#c98add",
  "#e0a54f", "#4fc3c9", "#a3b356", "#d97ba4",
];

function destroyGraph() {
  if (state.graphInstance) {
    try { state.graphInstance._destructor(); } catch (e) { /* noop */ }
    state.graphInstance = null;
  }
}

async function loadGraphTab(refresh) {
  const doc = $("doc-view");
  destroyGraph();
  doc.innerHTML = `<div class="doc-empty">그래프 불러오는 중…</div>`;
  let g;
  try { g = await api("/api/graph" + (refresh ? "?refresh=1" : "")); }
  catch (e) { doc.innerHTML = failHtml(e); return; }
  if (state.activeTab !== "graph") return;
  state.graphData = g;
  if (state.graphFilter && !g.projects.includes(state.graphFilter)) state.graphFilter = "";

  doc.innerHTML = `
    <div class="graph-toolbar">
      <select class="ws-input" id="graph-filter">
        <option value="">전체</option>
        ${g.projects.map((p) =>
          `<option value="${escapeHtml(p)}"${p === state.graphFilter ? " selected" : ""}>${escapeHtml(p)}</option>`).join("")}
      </select>
      <input class="ws-input" id="graph-search" placeholder="노드 검색…" value="${escapeHtml(state.graphSearch)}">
      <button class="ws-open-btn" id="graph-refresh">새로고침</button>
      <span class="spacer"></span>
      <span class="graph-meta" id="graph-meta"></span>
    </div>
    <div class="graph-box" id="graph-box"></div>`;

  $("graph-refresh").onclick = () => loadGraphTab(true);
  $("graph-filter").onchange = (ev) => { state.graphFilter = ev.target.value; renderGraph(); };
  $("graph-search").oninput = (ev) => {
    state.graphSearch = ev.target.value.trim().toLowerCase();
    const fg = state.graphInstance;
    if (fg) fg.nodeColor(fg.nodeColor());  // re-evaluate accessor → dim non-matching
  };
  renderGraph();
}

function renderGraph() {
  const g = state.graphData;
  const box = $("graph-box");
  if (!g || !box || typeof ForceGraph === "undefined") {
    if (box) box.innerHTML = `<div class="doc-empty">그래프 라이브러리 로드 실패</div>`;
    return;
  }
  destroyGraph();

  const idOf = (x) => (typeof x === "object" && x !== null ? x.id : x);
  let nodes = g.nodes, links = g.links;
  if (state.graphFilter) {
    const keep = new Set();
    for (const n of g.nodes) {
      if (n.group === state.graphFilter || n.id === `project:${state.graphFilter}`) keep.add(n.id);
    }
    nodes = g.nodes.filter((n) => keep.has(n.id));
    links = g.links.filter((l) => keep.has(idOf(l.source)) && keep.has(idOf(l.target)));
  }
  // fresh copies — force-graph mutates node/link objects (x, y, source refs)
  const data = {
    nodes: nodes.map((n) => ({ ...n })),
    links: links.map((l) => ({ source: idOf(l.source), target: idOf(l.target) })),
  };

  const meta = $("graph-meta");
  if (meta) meta.textContent = `노드 ${data.nodes.length} · 링크 ${data.links.length}`;

  const groups = [...new Set(g.nodes.map((n) => n.group))].sort();
  const colorOf = (grp) => GRAPH_PALETTE[Math.max(0, groups.indexOf(grp)) % GRAPH_PALETTE.length];
  const cs = getComputedStyle(document.body);
  const textColor = cs.getPropertyValue("--text2").trim() || "#888";
  const linkColor = (cs.getPropertyValue("--border").trim() || "#888") + "cc";

  const height = Math.max(420, window.innerHeight - box.getBoundingClientRect().top - 32);
  const fg = ForceGraph()(box)
    .width(box.clientWidth || 800)
    .height(height)
    .graphData(data)
    .nodeId("id")
    .nodeVal("val")
    .nodeLabel((n) => (n.type === "project" ? `프로젝트: ${escapeHtml(n.name)}` : escapeHtml(n.id)))
    .nodeColor((n) => {
      const c = colorOf(n.group);
      const q = state.graphSearch;
      return q && !n.name.toLowerCase().includes(q) ? c + "22" : c;
    })
    .linkColor(() => linkColor)
    .linkWidth(1)
    .nodeCanvasObjectMode(() => "after")
    .nodeCanvasObject((n, ctx, scale) => {
      // labels: project hubs always, files only when zoomed in
      if (n.type !== "project" && scale < 1.4) return;
      const q = state.graphSearch;
      if (q && !n.name.toLowerCase().includes(q)) return;
      const size = n.type === "project" ? 12 / scale : 10 / scale;
      ctx.font = `${n.type === "project" ? "600 " : ""}${size}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillStyle = textColor;
      ctx.fillText(n.name, n.x, n.y + Math.sqrt(n.val || 1) * 2 + 2 / scale);
    })
    .onNodeClick((n) => {
      if (n.type === "project") {
        state.graphFilter = state.graphFilter === n.name ? "" : n.name;
        const sel = $("graph-filter");
        if (sel) sel.value = state.graphFilter;
        renderGraph();
      } else {
        openFileModal(n.id);
      }
    });
  state.graphInstance = fg;
}

/* -------- workspace: 리소스 -------- */

async function loadWorkResources(box) {
  const name = state.workProject;
  let p;
  try { p = await api(`/api/projects/${encodeURIComponent(name)}`); }
  catch (e) { box.innerHTML = failHtml(e); return; }

  box.innerHTML = `
    <div class="ws-section">
      <div class="ws-head"><span class="ws-title">리소스 링크 — _RESOURCES.md</span></div>
      <div class="md">${renderMarkdown(p.resources || "_아직 리소스 없음_")}</div>
      <div class="ws-form">
        <input class="ws-input" id="res-title" placeholder="제목">
        <input class="ws-input" id="res-url" placeholder="https:// 링크 (선택)">
        <input class="ws-input" id="res-note" placeholder="메모 (선택)">
        <button class="ws-add-btn" id="res-add">저장</button>
      </div>
    </div>`;

  $("res-add").onclick = async () => {
    const title = $("res-title").value.trim();
    if (!title) { toast("제목을 입력하세요", "warn"); return; }
    try {
      await postJson(`/api/projects/${encodeURIComponent(name)}/resources`,
        { title, url: $("res-url").value.trim(), note: $("res-note").value.trim() });
      toast("리소스 저장됨 — _RESOURCES.md에 기록", "ok");
      loadWorkResources(box);
    } catch (e) { toast(`실패: ${e.body?.message || e.message}`, "err"); }
  };
}

/* -------- workspace: 계정 -------- */
/* SECURITY: real passwords are never stored — only a pointer (pw_hint)
   to where the password lives (Keychain, 1Password, etc). */

async function loadWorkAccounts(box) {
  const name = state.workProject;
  let accounts = [];
  try { accounts = await api(`/api/projects/${encodeURIComponent(name)}/accounts`); }
  catch (e) { box.innerHTML = failHtml(e); return; }

  const rows = accounts.length
    ? accounts.map((a) => `
      <div class="acct-row" data-id="${escapeHtml(a.id)}">
        <div class="acct-main">
          <span class="acct-service">${escapeHtml(a.service || "—")}</span>
          <span class="acct-account">${escapeHtml(a.account || "")}</span>
          ${a.url ? `<a class="acct-url" href="${escapeHtml(a.url)}" target="_blank" rel="noopener noreferrer">열기 ↗</a>` : ""}
        </div>
        <div class="acct-sub">
          ${a.pw_hint ? `<span class="acct-hint" title="비밀번호가 저장된 위치">🔑 ${escapeHtml(a.pw_hint)}</span>` : ""}
          ${a.note ? `<span class="acct-note">${escapeHtml(a.note)}</span>` : ""}
          ${a.updated ? `<span class="jtime">${escapeHtml(a.updated)}</span>` : ""}
        </div>
        <button class="ws-open-btn acct-del" data-del="${escapeHtml(a.id)}">삭제</button>
      </div>`).join("")
    : `<div class="ws-empty">등록된 계정 없음</div>`;

  box.innerHTML = `
    <div class="ws-section">
      <div class="ws-head"><span class="ws-title">계정 — ${escapeHtml(name)}</span><span class="spacer"></span>
        <button class="ws-open-btn" id="acct-collect">AI로 기존 노트에서 수집</button></div>
      <div class="ai-note">⚠ 실제 비밀번호는 절대 입력하지 마세요 — 여기엔 <b>비번이 저장된 위치</b>만 적습니다
        (예: "macOS 키체인", "1Password — UNFPA"). 볼트 보안 규칙.</div>
      <div id="acct-list">${rows}</div>
      <div class="ws-form acct-form">
        <input class="ws-input" id="acct-service" placeholder="서비스 (예: UNFPA Gemini)">
        <input class="ws-input" id="acct-user" placeholder="계정 (이메일/아이디)">
        <input class="ws-input" id="acct-url" placeholder="https:// 로그인 링크 (선택)">
        <input class="ws-input" id="acct-hint" placeholder="비번 위치 (포인터 — 비번 자체 금지)">
        <input class="ws-input" id="acct-note" placeholder="메모 (선택)">
        <button class="ws-add-btn" id="acct-add">추가</button>
      </div>
    </div>`;

  const reload = () => loadWorkAccounts(box);

  $("acct-add").onclick = async () => {
    const item = {
      service: $("acct-service").value.trim(),
      account: $("acct-user").value.trim(),
      url: $("acct-url").value.trim(),
      pw_hint: $("acct-hint").value.trim(),
      note: $("acct-note").value.trim(),
    };
    if (!item.service && !item.account) { toast("서비스 또는 계정을 입력하세요", "warn"); return; }
    try {
      await postJson(`/api/projects/${encodeURIComponent(name)}/accounts`, { op: "add", item });
      toast("계정 저장됨 — _ACCOUNTS.json", "ok");
      reload();
    } catch (e) { toast(`실패: ${e.body?.message || e.message}`, "err"); }
  };

  box.querySelectorAll("[data-del]").forEach((b) => {
    b.onclick = async () => {
      if (!confirm("이 계정 항목을 삭제할까요?")) return;
      try {
        await postJson(`/api/projects/${encodeURIComponent(name)}/accounts`,
          { op: "delete", id: b.dataset.del });
        toast("삭제됨", "ok");
        reload();
      } catch (e) { toast(`실패: ${e.body?.message || e.message}`, "err"); }
    };
  });

  $("acct-collect").onclick = async () => {
    if (!confirm(`${name} 프로젝트 노트에서 계정/링크 정보를 AI가 수집해 _ACCOUNTS.json에 정리합니다. 실행할까요?`)) return;
    const prompt =
      "프로젝트 폴더의 노트(미팅노트, _STATUS.md, _RESOURCES.md 등)를 훑어서 " +
      "계정/로그인/포털/플랫폼 관련 정보를 찾아 _ACCOUNTS.json에 정리해줘. " +
      "형식: JSON 배열, 각 항목 {id: 8자리 hex, service, account, url, pw_hint, note, updated: YYYY-MM-DD}. " +
      "기존 항목은 유지하고 새 항목만 추가. " +
      "절대 규칙: 실제 비밀번호/토큰은 어떤 경우에도 기록 금지 — pw_hint에는 비번이 있을 만한 위치만 적어.";
    try {
      const res = await postJson(`/api/projects/${encodeURIComponent(name)}/request`, { prompt });
      startedToast(res, "AI 계정 수집");
      state.workSub = "ai";
      state.aiJobId = res.job_id;
      state.aiOffset = 0;
      state.aiLines = [];
      loadWork();
      schedulePoll(0);
    } catch (e) {
      toast(`실행 실패: ${e.body?.message || e.message}`, "err");
    }
  };
}

/* -------- workspace: AI 요청 -------- */

async function loadWorkAi(box) {
  const name = state.workProject;
  let hist = [];
  try { hist = await api(`/api/projects/${encodeURIComponent(name)}/requests`); } catch { /* empty */ }

  const jobById = Object.fromEntries(state.jobs.map((j) => [j.id, j]));
  const histHtml = hist.length
    ? hist.map((h) => {
      const j = jobById[h.job_id];
      const pill = j
        ? `<span class="pill ${j.status}">${STATUS_KO[j.status] || j.status}</span>`
        : `<span class="pill cancelled">기록</span>`;
      return `<div class="req-row" data-j="${escapeHtml(h.job_id)}" title="클릭하면 로그 보기">
        ${pill}
        <span class="req-prompt">${escapeHtml(h.prompt)}</span>
        <span class="jtime">${fmtDate(h.created)}</span>
      </div>`;
    }).join("")
    : `<div class="ws-empty">아직 요청 없음</div>`;

  box.innerHTML = `
    <div class="ws-section">
      <div class="ws-head"><span class="ws-title">AI 요청 — ${escapeHtml(name)}</span></div>
      <div class="ai-note">Claude 엔진이 <code>01-Projects/${escapeHtml(name)}/</code> 범위로 실행됩니다
        (Read·Write·Edit·Glob·Grep — Bash/MCP 없음)</div>
      <textarea class="ai-ta" id="ai-prompt" maxlength="2000"
        placeholder="예: 최근 미팅노트를 반영해서 _STATUS.md를 업데이트해줘"></textarea>
      <div class="ws-form ai-form">
        <span class="ai-count" id="ai-count">0 / 2000</span>
        <span class="spacer"></span>
        <button class="ws-add-btn" id="ai-run">실행</button>
      </div>
      <div class="ai-log" id="ai-log" style="display:none">
        <div class="ai-log-head">
          <span class="ltitle" id="ai-log-title"></span>
          <span id="ai-log-pill"></span>
          <span class="spacer"></span>
          <button class="btn-cancel" id="ai-cancel" style="display:none">중단</button>
        </div>
        <div class="log-view ai-log-view" id="ai-log-view"></div>
      </div>
    </div>
    <div class="ws-section">
      <div class="ws-head"><span class="ws-title">요청 히스토리 (최근 30건)</span></div>
      <div id="ai-hist">${histHtml}</div>
    </div>`;

  const ta = $("ai-prompt");
  ta.oninput = () => { $("ai-count").textContent = `${ta.value.length} / 2000`; };

  $("ai-run").onclick = async () => {
    const prompt = ta.value.trim();
    if (!prompt) { toast("요청 내용을 입력하세요", "warn"); return; }
    try {
      const res = await postJson(`/api/projects/${encodeURIComponent(name)}/request`, { prompt });
      startedToast(res, `AI 요청 — ${name}`);
      ta.value = "";
      $("ai-count").textContent = "0 / 2000";
      startAiJobView(res.job_id);
      schedulePoll(0);
    } catch (e) {
      toast(`실행 실패: ${e.body?.message || e.message}`, "err");
    }
  };

  $("ai-cancel").onclick = async () => {
    if (!state.aiJobId) return;
    try {
      await api(`/api/jobs/${state.aiJobId}/cancel`, { method: "POST" });
      toast("취소 요청 전송됨", "warn");
    } catch (e) { toast(`취소 실패: ${e.message}`, "err"); }
  };

  box.querySelectorAll(".req-row").forEach((row) => {
    row.onclick = () => startAiJobView(row.dataset.j);
  });

  // 진행 중이던 요청 로그 이어보기
  if (state.aiJobId) startAiJobView(state.aiJobId);
}

function startAiJobView(jobId) {
  state.aiJobId = jobId;
  state.aiOffset = 0;
  state.aiLines = [];
  stopAiPoll();
  pollAi();
}

function stopAiPoll() {
  clearTimeout(state.aiTimer);
  state.aiTimer = null;
}

async function pollAi() {
  const box = $("ai-log");
  if (!box || !state.aiJobId) { stopAiPoll(); return; }
  let d;
  try {
    d = await api(`/api/jobs/${state.aiJobId}?offset=${state.aiOffset}`);
  } catch {
    box.style.display = "";
    $("ai-log-title").textContent = "로그 만료됨 (작업 기록이 정리됨)";
    $("ai-log-pill").innerHTML = "";
    $("ai-cancel").style.display = "none";
    $("ai-log-view").innerHTML = "";
    stopAiPoll();
    return;
  }
  if (state.aiOffset === 0) state.aiLines = [];
  state.aiLines.push(...d.lines);
  if (state.aiLines.length > 2000) state.aiLines = state.aiLines.slice(-2000);
  state.aiOffset = d.next_offset;

  box.style.display = "";
  $("ai-log-title").textContent = `${d.label} — ${d.id}`;
  $("ai-log-pill").innerHTML = `<span class="pill ${d.status}">${STATUS_KO[d.status] || d.status}</span>`;
  $("ai-cancel").style.display = d.status === "running" ? "" : "none";
  const view = $("ai-log-view");
  const stick = view.scrollTop + view.clientHeight >= view.scrollHeight - 40;
  view.innerHTML = `<pre>${logLinesHtml(state.aiLines)}</pre>`;
  if (stick) view.scrollTop = view.scrollHeight;

  if (TERMINAL.has(d.status)) { stopAiPoll(); return; }
  state.aiTimer = setTimeout(pollAi, 1500);
}

/* -------- workspace: 콘텐츠 (Visual-Climate 전용) -------- */

async function loadWorkContent(box) {
  const viewChips = `<div class="sub-tabs content-views">` + CONTENT_VIEWS.map(([id, ko]) =>
    `<button class="sub-tab${id === state.contentView ? " active" : ""}" data-v="${id}">${ko}</button>`).join("") + `</div>`;

  box.innerHTML = `<div class="ws-section">
    <div class="ws-head"><span class="ws-title">콘텐츠 산출물</span></div>
    ${viewChips}
    <div class="ws-files" id="content-files"></div>
    <div class="meeting-doc" id="content-doc" style="display:none"></div>
  </div>`;

  box.querySelectorAll(".sub-tab[data-v]").forEach((b) => {
    b.onclick = () => {
      state.contentView = b.dataset.v;
      state.contentFile = null;
      loadWorkContent(box);
    };
  });

  const filesBox = $("content-files");
  let files;
  try { files = await api(`/api/files/${state.contentView}`); }
  catch (e) { filesBox.innerHTML = failHtml(e); return; }
  if (!files.length) {
    filesBox.innerHTML = `<div class="ws-empty">아직 생성된 파일이 없습니다</div>`;
    return;
  }
  if (!state.contentFile || !files.some((f) => f.name === state.contentFile)) {
    state.contentFile = files[0].name;
  }
  filesBox.innerHTML = files.map((f) =>
    `<button class="file-chip${f.name === state.contentFile ? " active" : ""}" data-f="${escapeHtml(f.name)}">${escapeHtml(f.name)}</button>`).join("");

  const showFile = async (fname) => {
    const docBox = $("content-doc");
    docBox.style.display = "";
    docBox.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;
    try {
      const f = await api(`/api/file/${state.contentView}/${encodeURIComponent(fname)}`);
      docBox.innerHTML = `<div class="md">${renderMarkdown(f.content)}</div>`;
    } catch (e) { docBox.innerHTML = failHtml(e); }
  };
  filesBox.querySelectorAll(".file-chip[data-f]").forEach((chip) => {
    chip.onclick = () => {
      state.contentFile = chip.dataset.f;
      filesBox.querySelectorAll(".file-chip[data-f]").forEach((c) =>
        c.classList.toggle("active", c.dataset.f === state.contentFile));
      showFile(state.contentFile);
    };
  });
  showFile(state.contentFile);
}

/* ---------------------------------------------------------------- polling */

const TERMINAL = new Set(["success", "failed", "cancelled", "timeout"]);

async function poll() {
  try {
    const [tasks, jobs, actions, schedule] = await Promise.all([
      api("/api/tasks"), api("/api/jobs"), api("/api/actions"), api("/api/schedule"),
    ]);
    state.tasks = tasks;
    state.jobs = jobs;
    state.actions = actions;
    state.schedule = schedule;
    $("health").classList.remove("down");
    $("health-text").textContent = "온라인";

    // completion detection → toast + auto-refresh related tab
    for (const j of jobs) {
      const prev = state.jobStatusCache[j.id];
      if (prev && !TERMINAL.has(prev) && TERMINAL.has(j.status)) {
        const ok = j.status === "success";
        toast(`${j.label} — ${STATUS_KO[j.status]}`, ok ? "ok" : j.status === "failed" ? "err" : "warn");
        if (ok && j.refresh) {
          const tab = REFRESH_TAB[j.refresh];
          if (tab) {
            flashTab(tab);
            // 홈만 자동 새로고침 — 워크스페이스는 입력/편집 클로버 방지 위해 플래시만
            if (tab === "home" && state.activeTab === "home" && !state.editorDirty) loadTab();
          }
          // 이메일·프로젝트 수집 완료 → 이메일/홈 탭 자동 갱신
          if (j.refresh === "projects") {
            flashTab("mail");
            if ((state.activeTab === "mail" || state.activeTab === "home") && !state.editorDirty) loadTab();
          }
        }
      }
      state.jobStatusCache[j.id] = j.status;
    }

    renderTasks();
    renderJobs();
    renderActions();
    renderSchedule();
    renderTray();

    // auto-select most recent job if none selected
    if (!state.selectedJob && jobs.length) state.selectedJob = jobs[0].id;

    if (state.selectedJob) {
      try {
        const d = await api(`/api/jobs/${state.selectedJob}?offset=${state.logOffset}`);
        if (state.logOffset === 0) state.logLines = [];
        state.logLines.push(...d.lines);
        if (state.logLines.length > 2000) state.logLines = state.logLines.slice(-2000);
        state.logOffset = d.next_offset;
        renderLogHead(d);
        renderLogLines();
      } catch { /* job may have been trimmed */ }
    }
  } catch {
    $("health").classList.add("down");
    $("health-text").textContent = "오프라인";
  }
  const active = state.jobs.some((j) => !TERMINAL.has(j.status));
  schedulePoll(active ? 2000 : 8000);
}

function schedulePoll(delay) {
  clearTimeout(state.pollTimer);
  state.pollTimer = setTimeout(poll, delay);
}

/* ---------------------------------------------------------------- file modal + clickable vault paths */
/* Any rendered text containing a vault-relative path becomes a .vault-link;
   one delegated click handler opens the global viewer modal on every tab. */

const VAULT_PATH_RE = /(?:0[0-7]-[\w-]+|Templates)\/[^\s`"'<>|*?]+?\.[A-Za-z0-9]{1,6}|\d{4}-\d{2}-\d{2}\.md/g;

function linkifyVaultPaths(container) {
  if (!container) return;
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const p = node.parentElement;
      if (!p || p.closest("a, textarea, input, .vault-link")) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const targets = [];
  let n;
  while ((n = walker.nextNode())) {
    VAULT_PATH_RE.lastIndex = 0;
    if (VAULT_PATH_RE.test(n.nodeValue)) targets.push(n);
  }
  for (const node of targets) {
    const text = node.nodeValue;
    const frag = document.createDocumentFragment();
    let last = 0;
    VAULT_PATH_RE.lastIndex = 0;
    let m;
    while ((m = VAULT_PATH_RE.exec(text))) {
      if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
      const a = document.createElement("a");
      a.className = "vault-link";
      a.dataset.path = m[0];
      a.href = "#";
      a.textContent = m[0];
      frag.appendChild(a);
      last = m.index + m[0].length;
    }
    if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
    node.parentNode.replaceChild(frag, node);
  }
}

document.addEventListener("click", (ev) => {
  const a = ev.target.closest(".vault-link");
  if (!a) return;
  ev.preventDefault();
  openFileModal(a.dataset.path);
});

function closeFileModal() {
  $("file-modal-backdrop").style.display = "none";
}

function fmOpenInWorkspace(rel) {
  closeFileModal();
  if (rel.startsWith("01-Projects/")) {
    const parts = rel.split("/");
    state.workProject = parts[1];
    state.workSub = "files";
    state.workFilePath = rel;
    localStorage.setItem("hios-work-proj", parts[1]);
    if (!state.workOpenDirs[parts[1]]) state.workOpenDirs[parts[1]] = new Set();
    for (let i = 3; i < parts.length; i += 1) {
      state.workOpenDirs[parts[1]].add(parts.slice(0, i).join("/"));
    }
    switchTab("work");
  } else {
    state.vaultFilePath = rel;
    const parts = rel.split("/");
    for (let i = 1; i < parts.length; i += 1) {
      state.vaultOpenDirs.add(parts.slice(0, i).join("/"));
    }
    switchTab("vault");
  }
}

async function openFileModal(rel) {
  const backdrop = $("file-modal-backdrop");
  const body = $("fm-body");
  backdrop.style.display = "";
  $("fm-path").textContent = rel;
  body.innerHTML = `<div class="doc-empty">불러오는 중…</div>`;

  $("fm-close").onclick = closeFileModal;
  $("fm-workspace").onclick = () => fmOpenInWorkspace(rel);
  $("fm-folder").onclick = () => {
    const parent = rel.includes("/") ? rel.slice(0, rel.lastIndexOf("/")) : null;
    // root files have no parent inside the vault → reveal the file instead
    postJson("/api/open-path", parent
      ? { path: parent, app: "finder" }
      : { path: rel, app: "finder" })
      .catch((e) => toast(`열기 실패: ${e.message}`, "err"));
  };

  let f;
  try {
    f = await api(`/api/vault-file/${encodeRel(rel)}`);
  } catch (e) {
    body.innerHTML = `<div class="doc-empty">${e.status === 404
      ? "파일 없음 — 경로가 오래되었거나 이동되었습니다"
      : `로드 실패: ${escapeHtml(e.message)}`}</div>`;
    return;
  }
  if (f.binary) {
    body.innerHTML = `<div class="bin-card">
      <div class="bin-name">${escapeHtml(f.name)}</div>
      <div class="bin-meta">${escapeHtml(f.ext || "파일")} · ${fmtSize(f.size)} — 브라우저 미리보기 불가</div>
      <div class="file-open-row">
        <button class="ws-open-btn" data-fm-open="finder">Finder에서 열기</button>
        <button class="ws-open-btn" data-fm-open="default">앱으로 열기</button>
      </div>
    </div>`;
    body.querySelectorAll("[data-fm-open]").forEach((b) => {
      b.onclick = () => postJson("/api/open-path", { path: rel, app: b.dataset.fmOpen })
        .catch((e) => toast(`열기 실패: ${e.message}`, "err"));
    });
  } else if (f.ext === ".md") {
    body.innerHTML = `<div class="md">${renderMarkdown(f.content)}</div>`;
    linkifyVaultPaths(body);
  } else {
    body.innerHTML = `<pre class="code-view">${escapeHtml(f.content)}</pre>`;
  }
}

$("file-modal-backdrop").addEventListener("click", (ev) => {
  if (ev.target === $("file-modal-backdrop")) closeFileModal();
});
document.addEventListener("keydown", (ev) => {
  if (ev.key === "Escape" && $("file-modal-backdrop").style.display !== "none") closeFileModal();
});

/* ---------------------------------------------------------------- quickbar (질문 + 메모) + ask drawer */
/* Drawer is global — its poller is NOT stopped on tab switches. */

function stopAskPoll() {
  clearTimeout(state.askTimer);
  state.askTimer = null;
}

function openAskDrawer(question, jobId) {
  state.askJobId = jobId;
  state.askOffset = 0;
  state.askLines = [];
  stopAskPoll();
  $("ask-drawer").style.display = "";
  $("ask-q").textContent = question;
  $("ask-title").textContent = "질문";
  $("ask-pill").innerHTML = "";
  $("ask-view").innerHTML = `<div class="log-empty">답변 준비 중…</div>`;
  pollAsk();
}

async function pollAsk() {
  if (!state.askJobId) { stopAskPoll(); return; }
  let d;
  try {
    d = await api(`/api/jobs/${state.askJobId}?offset=${state.askOffset}`);
  } catch {
    $("ask-title").textContent = "로그 만료됨";
    $("ask-pill").innerHTML = "";
    $("ask-cancel").style.display = "none";
    stopAskPoll();
    return;
  }
  if (state.askOffset === 0) state.askLines = [];
  state.askLines.push(...d.lines);
  if (state.askLines.length > 2000) state.askLines = state.askLines.slice(-2000);
  state.askOffset = d.next_offset;

  $("ask-pill").innerHTML = `<span class="pill ${d.status}">${STATUS_KO[d.status] || d.status}</span>`;
  $("ask-cancel").style.display = d.status === "running" ? "" : "none";
  const view = $("ask-view");
  const stick = view.scrollTop + view.clientHeight >= view.scrollHeight - 40;
  if (TERMINAL.has(d.status) && d.status === "success") {
    // finished: render the answer as markdown, dropping system/heartbeat lines
    const answer = state.askLines
      .filter((l) => !l.startsWith("[시스템]") && !/^… ?실행 중/.test(l))
      .join("\n").trim();
    view.innerHTML = `<div class="md">${renderMarkdown(answer || "(빈 응답)")}</div>`;
    linkifyVaultPaths(view);
  } else {
    view.innerHTML = `<pre>${logLinesHtml(state.askLines)}</pre>`;
  }
  if (stick) view.scrollTop = view.scrollHeight;

  if (TERMINAL.has(d.status)) { stopAskPoll(); return; }
  state.askTimer = setTimeout(pollAsk, 1500);
}

async function submitAsk() {
  const input = $("qb-input");
  const q = input.value.trim();
  if (!q) { toast("질문을 입력하세요", "warn"); return; }
  try {
    const res = await postJson("/api/ask", { q });
    input.value = "";
    if (res.queued) toast("질문이 대기열에 등록됨 — 자리 나면 자동 시작", "warn");
    openAskDrawer(q, res.job_id);
    schedulePoll(0);
  } catch (e) {
    toast(`질문 실패: ${e.body?.message || e.message}`, "err");
  }
}

async function submitMemo() {
  const input = $("qb-input");
  const text = input.value.trim();
  if (!text) { toast("메모를 입력하세요", "warn"); return; }
  try {
    const res = await postJson("/api/quick-memo", { text });
    input.value = "";
    toast(`메모 저장됨 — ${res.file}`, "ok");
  } catch (e) { toast(`메모 실패: ${e.body?.message || e.message}`, "err"); }
}

$("qb-ask").onclick = submitAsk;
$("qb-memo").onclick = submitMemo;
$("qb-input").onkeydown = (ev) => {
  if (ev.key === "Enter") { ev.preventDefault(); submitAsk(); }
};

$("ask-close").onclick = () => {
  stopAskPoll();
  state.askJobId = null;
  $("ask-drawer").style.display = "none";
};

$("ask-cancel").onclick = async () => {
  if (!state.askJobId) return;
  try {
    await api(`/api/jobs/${state.askJobId}/cancel`, { method: "POST" });
    toast("취소 요청 전송됨", "warn");
  } catch (e) { toast(`취소 실패: ${e.message}`, "err"); }
};

/* ---------------------------------------------------------------- clock */

setInterval(() => {
  const d = new Date();
  $("clock").textContent = d.toLocaleDateString("ko-KR", {
    month: "2-digit", day: "2-digit", weekday: "short",
  }) + " " + d.toTimeString().slice(0, 8);
}, 1000);

/* ---------------------------------------------------------------- theme */

function applyTheme(mode) {
  document.body.classList.toggle("dark", mode === "dark");
  $("theme-btn").textContent = mode === "dark" ? "라이트" : "다크";
  localStorage.setItem("hios-theme", mode);
}

$("theme-btn").onclick = () =>
  applyTheme(document.body.classList.contains("dark") ? "light" : "dark");

applyTheme(localStorage.getItem("hios-theme") || "light");

/* ---------------------------------------------------------------- boot */

// 옛 탭 id(daily/digests/xhs/ig/calendar/status/projects…)는 홈으로 폴백
const savedTab = localStorage.getItem("hios-tab");
state.activeTab = TABS.some((t) => t.id === savedTab) ? savedTab : "home";

renderTabs();
loadTab();
poll();
