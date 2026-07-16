/* HiOS Control Center — vanilla JS frontend */
"use strict";

const $ = (id) => document.getElementById(id);

const TABS = [
  { id: "home", label: "홈" },
  { id: "board", label: "액션" },
  { id: "work", label: "워크스페이스" },
  { id: "engine", label: "엔진" },
  { id: "agenda", label: "일정" },
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
  // workspace
  workProject: null,
  workSub: "overview",
  workMeeting: null,
  workTreeCache: {},    // project -> tree json
  workOpenDirs: {},     // project -> Set of open dir paths
  workFilePath: null,
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
};

/* ---------------------------------------------------------------- utils */

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function renderMarkdown(src) {
  // escape raw HTML first, then let marked render markdown syntax only
  return marked.parse(escapeHtml(src), { breaks: true });
}

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
  cancelled: "취소됨", timeout: "타임아웃",
};

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
    toast(`${t.label_ko} 시작됨`, "ok");
    schedulePoll(0);
  } catch (e) {
    if (e.status === 409) toast(e.body.message || "이미 실행 중인 작업과 충돌", "warn");
    else toast(`실행 실패: ${e.message}`, "err");
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
  $("btn-cancel").style.display = job && job.status === "running" ? "" : "none";
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
  const isEngine = state.activeTab === "engine";
  $("engine-view").style.display = isEngine ? "" : "none";
  $("output-body").style.display = isEngine ? "none" : "";
  if (isEngine) { schedulePoll(0); return; }
  const doc = $("doc-view");
  if (state.activeTab === "home") return loadHome();
  if (state.activeTab === "board") return renderBoardView(doc, null);
  if (state.activeTab === "work") return loadWork();
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
  const doc = $("doc-view");
  doc.innerHTML = `<div class="doc-empty">캘린더 불러오는 중…</div>`;
  try {
    const res = await api(`/api/calendar${force ? "?refresh=1" : ""}`);
    let html = "";
    if (res.error) html += `<div class="ag-error">${escapeHtml(res.error)}</div>`;
    html += agendaHtml(res.events || [], "4일 내 일정 없음");
    html += `<button class="ab-btn ag-refresh" id="ag-refresh">새로고침</button>`;
    doc.innerHTML = html;
    $("ag-refresh").onclick = () => loadAgenda(true);
  } catch (e) {
    doc.innerHTML = `<div class="doc-empty">캘린더 로드 실패: ${escapeHtml(e.message)}</div>`;
  }
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

function biCardHtml(p, it) {
  const srcs = (it.sources || []).map((s) =>
    `<a class="src-chip ${s.kind}" href="${escapeHtml(s.url)}" target="_blank" rel="noopener">
      <span class="src-ic">${SRC_ICON[s.kind] || "↗"}</span>${escapeHtml(s.label)}</a>`).join("");
  const people = (it.people || []).map((x) => `<span class="bi-person">@${escapeHtml(x)}</span>`).join("");
  const statusBtns = BI_STATUS.map(([k, ko]) =>
    `<button class="bi-st ${k}${it.status === k ? " on" : ""}" data-st="${k}">${ko}</button>`).join("");
  const detail = it.detail
    ? `<div class="bi-detail">${escapeHtml(it.detail).replace(/\n/g, "<br>")}</div>` : "";
  return `
  <div class="bi-card p-${escapeHtml(it.priority || "med")}${it.status === "done" ? " is-done" : ""}"
       data-p="${escapeHtml(p)}" data-id="${escapeHtml(it.id)}">
    <div class="bi-top">
      <span class="bi-proj">${escapeHtml(p)}</span>
      <span class="bi-prio ${escapeHtml(it.priority || "med")}">${BI_PRIO_KO[it.priority] || "중간"}</span>
      ${dueBadge(it.due)}
      <span class="spacer"></span>
      <button class="bi-del" title="삭제">✕</button>
    </div>
    <div class="bi-title">${escapeHtml(it.title)}</div>
    ${detail}
    ${(srcs || people) ? `<div class="bi-meta">${srcs}${people}</div>` : ""}
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
    card.querySelector(".bi-del").onclick = async () => {
      if (!confirm("이 액션을 삭제할까요?")) return;
      if (await saveItem(p, id, { delete: true }, "삭제됨")) reload();
    };
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

  const cards = open.map(([p, it]) => biCardHtml(p, it)).join("")
    || `<div class="ws-empty">열린 액션 없음 🎉</div>`;
  let doneHtml = "";
  if (done.length) {
    doneHtml = `<button class="bi-done-toggle" id="bi-done-toggle">
        완료됨 ${done.length}건 ${state.boardShowDone ? "접기 ▲" : "보기 ▼"}</button>` +
      (state.boardShowDone ? done.map(([p, it]) => biCardHtml(p, it)).join("") : "");
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
  let projects, groups, cal, daily;
  try {
    [projects, groups, cal, daily] = await Promise.all([
      api("/api/projects"),
      api("/api/action-items"),
      api("/api/calendar").catch(() => ({ events: [], error: "캘린더 로드 실패" })),
      api("/api/files/daily").catch(() => []),
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

  // ③ 프로젝트 카드
  const projCards = projects.map((p) => `
    <div class="proj-card" data-p="${escapeHtml(p.name)}">
      <div class="pc-name">${escapeHtml(p.name)}</div>
      <div class="pc-client">${escapeHtml(p.client || "")}</div>
      <div class="pc-stats">
        <span class="pc-stat${p.open_actions ? " hot" : ""}">액션 ${p.open_actions || 0}</span>
        <span class="pc-stat">할 일 ${p.open_todos || 0}</span>
        <span class="pc-stat">미팅 ${p.meetings || 0}</span>
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
      </div>
      <div class="home-col">
        <div class="ws-section">
          <div class="ws-head"><span class="ws-title">프로젝트</span></div>
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
  if (state.workSub === "files") return loadWorkFiles(body);
  if (state.workSub === "resources") return loadWorkResources(body);
  if (state.workSub === "accounts") return loadWorkAccounts(body);
  if (state.workSub === "ai") return loadWorkAi(body);
  if (state.workSub === "content") return loadWorkContent(body);
}

/* -------- workspace: 개요 -------- */

async function loadWorkOverview(box) {
  const name = state.workProject;
  let p;
  try { p = await api(`/api/projects/${encodeURIComponent(name)}`); }
  catch (e) { box.innerHTML = failHtml(e); return; }
  const briefRel = `01-Projects/${name}/_PROJECT-BRIEF.md`;
  const brief = await api(`/api/vault-file/${encodeRel(briefRel)}`).catch(() => null);

  const todosHtml = p.todos.length
    ? p.todos.map((t) => `
      <div class="todo-row${t.done ? " done" : ""}" data-line="${t.line}">
        <span class="todo-check">${t.done ? "✓" : ""}</span>
        <span class="todo-text">${escapeHtml(t.text)}</span>
      </div>`).join("")
    : `<div class="ws-empty">할 일 없음</div>`;

  box.innerHTML = `
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
    </div>`;

  const reload = () => loadWorkOverview(box);

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
}

function renderTree(rootEl, children, open, rerender) {
  rootEl.innerHTML = "";
  const build = (nodes, depth) => {
    const wrap = document.createElement("div");
    for (const n of nodes) {
      const row = document.createElement("div");
      row.className = "tree-row" + (n.dir ? " dir" : "") +
        (!n.dir && n.path === state.workFilePath ? " active" : "");
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
          state.workFilePath = n.path;
          rerender();
          openWorkFile(n.path);
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

function renderFilePane(pane, rel, f) {
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
  const eb = pane.querySelector("#file-edit");
  if (eb) eb.onclick = () => openInlineEditor(pane, rel, () => openWorkFile(rel));
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
      toast("AI 수집 시작 — AI 요청 탭에서 로그 확인", "ok");
      state.workSub = "ai";
      state.aiJobId = res.job_id;
      state.aiOffset = 0;
      state.aiLines = [];
      loadWork();
      schedulePoll(0);
    } catch (e) {
      if (e.status === 409) toast(e.body.message || "이미 실행 중인 Claude 작업과 충돌", "warn");
      else toast(`실행 실패: ${e.body?.message || e.message}`, "err");
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
      <div class="ai-note">Claude Code 엔진이 <code>01-Projects/${escapeHtml(name)}/</code> 범위로 실행됩니다
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
      toast(`AI 요청 시작됨 — ${name}`, "ok");
      ta.value = "";
      $("ai-count").textContent = "0 / 2000";
      startAiJobView(res.job_id);
      schedulePoll(0);
    } catch (e) {
      if (e.status === 409) toast(e.body.message || "이미 실행 중인 Claude 작업과 충돌", "warn");
      else toast(`실행 실패: ${e.body?.message || e.message}`, "err");
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
        }
      }
      state.jobStatusCache[j.id] = j.status;
    }

    renderTasks();
    renderJobs();
    renderActions();
    renderSchedule();

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
    openAskDrawer(q, res.job_id);
    schedulePoll(0);
  } catch (e) {
    if (e.status === 409) toast(e.body?.message || "이미 실행 중인 Claude 작업과 충돌", "warn");
    else toast(`질문 실패: ${e.body?.message || e.message}`, "err");
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
