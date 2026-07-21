#!/usr/bin/env python3
"""HiOS Control Center — local web dashboard.

Single-file Flask server: task registry + job manager + file browsing API.
Binds to 127.0.0.1 only. All subprocesses use argv lists (shell=False).
"""

import hashlib
import html
import json
import os
import re
import traceback
import shutil
import signal
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

# ---------------------------------------------------------------- paths

APP_DIR = Path(__file__).resolve().parent          # .hios/app
VAULT = APP_DIR.parents[1]                          # vault root
ENGINE = VAULT / "01-Projects/Visual-Climate/06-Content-Engine"
SCRIPTS = ENGINE / "scripts"
HIOS_SCRIPTS = VAULT / ".hios/scripts"
LOG_DIR = VAULT / ".hios/logs/app"
LOG_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR = VAULT / ".hios/state"
STATE_DIR.mkdir(parents=True, exist_ok=True)
ENV_FILE = VAULT / ".hios/.env"
ACTIONS_FILE = STATE_DIR / "actions.json"
SCHED_STATE_FILE = STATE_DIR / "scheduler.json"
QUEUE_DIR = VAULT / "07-Queue"

PYTHON_BIN = sys.executable or "python3"


def _find_claude_bin():
    """Locate the Claude Code CLI for both interactive shells and minimal launchd PATHs."""
    configured = os.environ.get("HIOS_CLAUDE_BIN", "").strip()
    if configured:
        return configured
    found = shutil.which("claude")
    if found:
        return found
    return "claude"


CLAUDE_BIN = _find_claude_bin()
AI_PROVIDER = "claude"


def _find_gws_bin():
    """Locate the Google Workspace CLI used only for its encrypted OAuth store."""
    configured = os.environ.get("HIOS_GWS_BIN", "").strip()
    if configured:
        return configured
    found = shutil.which("gws")
    if found:
        return found
    candidate = Path.home() / ".npm-global/bin/gws"
    if candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate)
    return "gws"


GWS_BIN = _find_gws_bin()


def _gmail_config_dir():
    configured = os.environ.get("GOOGLE_WORKSPACE_CLI_CONFIG_DIR", "").strip()
    return Path(configured).expanduser() if configured else Path.home() / ".config/gws"


def _gmail_auth_ready():
    """Cheap readiness check; the live API call remains the source of truth."""
    binary_ok = bool(shutil.which(GWS_BIN)) if not Path(GWS_BIN).is_absolute() else (
        Path(GWS_BIN).is_file() and os.access(GWS_BIN, os.X_OK)
    )
    return binary_ok and (_gmail_config_dir() / "credentials.enc").is_file()

# ---------------------------------------------------------------- env & json state

ENV_KEYS = {"REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "X_BEARER_TOKEN"}


def _read_env_file():
    out = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


def _load_env():
    for k, v in _read_env_file().items():
        os.environ.setdefault(k, v)


def _save_env(values):
    current = _read_env_file()
    current.update(values)
    ENV_FILE.write_text(
        "".join(f"{k}={v}\n" for k, v in current.items()), encoding="utf-8"
    )
    os.chmod(ENV_FILE, 0o600)
    os.environ.update(values)


def _read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write_json(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)

app = Flask(__name__, static_folder=str(APP_DIR / "static"), static_url_path="/static")

# ---------------------------------------------------------------- task registry
# Every task is a pre-defined argv list. shell is never used.
# User input is included only in the prompt sent over stdin to Claude Code.

AI_TIMEOUT = 600
COLLECTOR_TIMEOUT = 120
TOPIC_MAX = 500
AI_PREAMBLE = (
    "HiOS 자동 작업입니다. 현재 저장소 안에서만 작업하세요. "
    "phase0-wip.patch는 백업이므로 열거나 실행하거나 수정하지 마세요. "
    "git commit/push 및 서버 재시작은 금지입니다. "
    "Gmail/Granola 커넥터는 작업 지시에 명시된 경우에만 사용하세요.\n\n"
)


def _claude_argv():
    """Non-interactive Claude Code worker; prompt arrives over stdin."""
    return [
        CLAUDE_BIN, "--print", "--verbose",
        "--permission-mode", "acceptEdits",
        "--allowedTools", "Read,Write,Edit,Glob,Grep,Bash",
        "--max-turns", "50",
    ]




def _topic(params):
    raw = str(params.get("topic", "") or "")
    # strip control chars, cap length — becomes part of a single argv element only
    clean = "".join(ch for ch in raw if ch == "\n" or ch >= " ")
    return clean.strip()[:TOPIC_MAX]


# Concurrency groups.
# - static set: vault-wide writers serialize among themselves ("ai")
# - callable(params) -> set: per-project scope ("proj:<name>") so jobs on
#   DIFFERENT projects run in parallel; same project stays serial.
# - empty set: read-only jobs never conflict (still capped by MAX_AI_CONCURRENT)
def _project_groups(p):
    name = str(p.get("project", "") or "")
    return {f"proj:{name}"} if name else {"ai"}


def _item_request_groups(p):
    parts = str(p.get("path", "") or "").split("/")
    if len(parts) > 2 and parts[0] == "01-Projects":
        return {f"proj:{parts[1]}"}
    return {"ai"}


def _reddit_env_warning():
    if not (os.environ.get("REDDIT_CLIENT_ID") and os.environ.get("REDDIT_CLIENT_SECRET")):
        return "env 미설정"
    return None


TASKS = {
    "rss": {
        "label_ko": "RSS 수집",
        "category": "수집",
        "groups": {"collectors"},
        "timeout": COLLECTOR_TIMEOUT,
        "heartbeat": False,
        "refresh": "digests",
        "argv": lambda p: [PYTHON_BIN, str(SCRIPTS / "rss_collector.py")],
    },
    "reddit": {
        "label_ko": "Reddit 수집",
        "category": "수집",
        "groups": {"collectors"},
        "timeout": COLLECTOR_TIMEOUT,
        "heartbeat": False,
        "refresh": "digests",
        "warning": _reddit_env_warning,
        "argv": lambda p: [
            PYTHON_BIN, str(SCRIPTS / "reddit_collector.py"),
            "--sort", "hot", "--timeframe", "day", "--limit", "15",
        ],
    },
    "x": {
        "label_ko": "X 수집",
        "category": "수집",
        "groups": {"collectors"},
        "timeout": COLLECTOR_TIMEOUT,
        "heartbeat": False,
        "refresh": "digests",
        "argv": lambda p: (
            [PYTHON_BIN, str(SCRIPTS / "x_collector.py")]
            + (["--mode", "api"] if os.environ.get("X_BEARER_TOKEN") else [])
        ),
    },
    # "granola" (granola-sync.sh) removed 2026-07-17 — replaced by morning_refresh
    # (Granola + Gmail app connectors via Claude Code), registered near the emails
    # section below.
    "daily_brief": {
        "label_ko": "데일리 브리프",
        "category": "브리핑",
        "groups": {"ai"},
        "ai": True,
        "timeout": AI_TIMEOUT,
        "heartbeat": True,
        "refresh": "daily",
        "argv": lambda p: _claude_argv(),
        "stdin": lambda p: (
            "Run /today. Generate the daily note for today. Read all project "
            "STATUS files, check the inbox, and create the daily brief."
        ),
    },
    "xhs_draft": {
        "label_ko": "XHS 초안",
        "category": "콘텐츠",
        "groups": {"ai"},
        "ai": True,
        "timeout": AI_TIMEOUT,
        "heartbeat": True,
        "refresh": "xhs",
        "topic": True,
        "argv": lambda p: _claude_argv(),
        "stdin": lambda p: (
            ("/xhs-draft " + _topic(p)) if _topic(p) else
            "/xhs-draft\n\nHeadless mode — do not ask questions. Pick the "
            "highest-potential topic yourself from the latest digest and "
            "generate the draft files."
        ),
    },
    "ig_draft": {
        "label_ko": "IG 초안",
        "category": "콘텐츠",
        "groups": {"ai"},
        "ai": True,
        "timeout": AI_TIMEOUT,
        "heartbeat": True,
        "refresh": "ig",
        "topic": True,
        "argv": lambda p: _claude_argv(),
        "stdin": lambda p: (
            ("/ig-draft " + _topic(p)) if _topic(p) else
            "/ig-draft\n\nHeadless mode — do not ask questions. Pick the "
            "highest-potential topic yourself from the latest digest and "
            "generate the draft files."
        ),
    },
    "collect_full": {
        "label_ko": "전체 파이프라인",
        "category": "수집",
        "groups": {"ai", "collectors"},
        "ai": True,
        "timeout": AI_TIMEOUT,
        "heartbeat": True,
        "refresh": "digests",
        "argv": lambda p: _claude_argv(),
        "stdin": lambda p: "/collect",
    },
    "project_request": {
        "label_ko": "AI 요청",
        "category": "AI",
        "groups": _project_groups,       # per-project → parallel across projects
        "ai": True,
        "timeout": AI_TIMEOUT,
        "heartbeat": True,
        "internal": True,   # hidden from /api/tasks, blocked in /api/run
        "argv": lambda p: _claude_argv(),
        "stdin": lambda p: (
            f"프로젝트 폴더 01-Projects/{p['project']}/ 범위에서만 작업하세요. "
            f"01-Projects/{p['project']}/CLAUDE.md(있다면)와 볼트 루트 CLAUDE.md 규칙을 준수하세요. "
            "Headless mode — 질문하지 말고 바로 실행하세요.\n\n"
            "요청:\n" + p["prompt"]
        ),
    },
    "vault_ask": {
        "label_ko": "질문",
        "category": "AI",
        "groups": set(),                 # read-only → never conflicts
        "ai": True,
        "timeout": AI_TIMEOUT,
        "heartbeat": True,
        "internal": True,   # hidden from /api/tasks, blocked in /api/run
        "argv": lambda p: _claude_argv(),
        "stdin": lambda p: (
            "볼트 전체에서 검색해서 아래 질문에 답하세요. 읽기 전용입니다 — "
            "파일을 만들거나 수정하지 마세요. 답은 간결하게, 근거가 된 파일 경로를 "
            "함께 인용하세요. Headless mode — 되묻지 말고 바로 답하세요.\n\n"
            "질문:\n" + p["prompt"]
        ),
    },
    "item_request": {
        "label_ko": "아이템 AI 요청",
        "category": "AI",
        "groups": _item_request_groups,  # per-project → parallel across projects
        "ai": True,
        "timeout": AI_TIMEOUT,
        "heartbeat": True,
        "internal": True,   # started only via /api/work-item-memo
        "argv": lambda p: _claude_argv(),
        "stdin": lambda p: (
            f"작업 아이템 파일: {p['path']}\n"
            "이 파일이 속한 프로젝트 폴더 범위에서만 작업하세요. 볼트 루트 CLAUDE.md와 "
            "해당 프로젝트 CLAUDE.md(있다면) 규칙을 준수하세요. 기존 내용을 지우지 말고 "
            "업데이트/추가만 하세요. 작업 완료 후 반드시 해당 파일 하단 '## Log' 섹션에 "
            f"'- {time.strftime('%Y-%m-%d %H:%M')} [AI] <한 줄 요약>' 형식으로 기록하세요. "
            "Headless mode — 질문하지 말고 바로 실행하세요.\n\n"
            "요청:\n" + p["prompt"]
        ),
    },
    "queue_process": {
        "label_ko": "큐 자동 처리",
        "category": "AI",
        "groups": {"ai"},
        "ai": True,
        "timeout": AI_TIMEOUT,
        "heartbeat": True,
        "internal": True,   # started only by the queue watcher thread
        "argv": lambda p: _claude_argv(),
        "stdin": lambda p: (
            f"07-Queue 요청 파일: {p['path']}\n"
            "볼트 루트 CLAUDE.md 규칙을 준수하며 아래 요청을 처리하세요. "
            "Headless mode — 질문하지 말고 바로 실행하세요. 처리 결과 요약을 "
            "요청 파일 하단에 '## 처리 결과' 섹션으로 덧붙이세요. "
            "요청 파일을 삭제하거나 이동하지 마세요 (서버가 아카이브합니다).\n\n"
            "요청 내용:\n" + p["content"]
        ),
    },
}

# ---------------------------------------------------------------- job manager

LOCK = threading.Lock()
JOBS = {}                 # job_id -> job dict
JOB_ORDER = []            # oldest first, trimmed to 50
ACTIVE_GROUPS = set()
MAX_JOBS = 50
LOG_CAP = 2000
HEARTBEAT_SEC = 15
MAX_AI_CONCURRENT = 3       # max simultaneous non-interactive Claude workers

# ---- Phase 0 usage guard: idempotency + cooldown + usage-limit breaker ----
# Design: docs in 01-Projects — collection stays cheap, duplicates never run,
# and a provider "out of usage" message pauses ALL AI dispatch (jobs stay
# queued) until the stated reset time instead of burning the remaining quota.

HEALTH_FILE = STATE_DIR / "health.json"
USAGE_FILE = STATE_DIR / "usage.json"
TASK_RUNS_FILE = STATE_DIR / "task_runs.json"
AI_LIMIT_RE = re.compile(
    r"out of extra usage|usage limit reached|you(?:['\u2019]ve| have) hit your (?:usage )?limit"
    r"|rate.?limit|too many requests|\b429\b|quota exceeded",
    re.I,
)
AI_LIMIT_RESET_RE = re.compile(
    r"resets?\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)", re.I
)
AI_LIMIT_BACKOFF = 1800        # fallback hold when the reset time can't be parsed
HEALTH_LOCK = threading.Lock()
USAGE_LOCK = threading.Lock()
TASK_RUNS_LOCK = threading.Lock()


def _load_ai_health(path, now=None):
    """Restore an unexpired breaker; expired/malformed state starts healthy."""
    current = time.time() if now is None else now
    out = {"limited_until": 0.0, "since": None, "detected_at": None}
    saved = _read_json(path, {})
    if not isinstance(saved, dict):
        return out
    # A stale breaker from a different provider must not block the current one.
    if saved.get("provider") != AI_PROVIDER:
        return out
    until = saved.get("limited_until")
    if not isinstance(until, (int, float)) or until <= current:
        return out
    since = saved.get("since")
    detected = saved.get("detected_at")
    out["limited_until"] = float(until)
    out["since"] = float(since) if isinstance(since, (int, float)) else current
    out["detected_at"] = (
        float(detected) if isinstance(detected, (int, float)) else out["since"]
    )
    return out


AI_HEALTH = _load_ai_health(HEALTH_FILE)   # guarded by LOCK


def _idem_key(task_id, params):
    try:
        blob = json.dumps(params, sort_keys=True, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        blob = repr(params)
    return f"{task_id}:{hashlib.sha1(blob.encode('utf-8', 'replace')).hexdigest()[:16]}"


def _ai_limited_locked():
    """Caller must hold LOCK."""
    return time.time() < AI_HEALTH["limited_until"]


def _parse_limit_reset(text):
    """'resets 10:30pm (...)'/'resets 1am' → next epoch, or None."""
    m = AI_LIMIT_RESET_RE.search(text or "")
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        return None
    hh = hour % 12 + (12 if m.group(3).lower() == "pm" else 0)
    now = time.localtime()
    target = time.mktime((now.tm_year, now.tm_mon, now.tm_mday,
                          hh, minute, 0, 0, 0, -1))
    if target <= time.time():
        target += 86400
    return target + 120        # small buffer past the reset


def _note_ai_limit(job, line):
    """Log a provider limit line and engage the breaker atomically."""
    until = _parse_limit_reset(line) or (time.time() + AI_LIMIT_BACKOFF)
    with LOCK:
        _append_log(job, line)
        detected_at = time.time()
        AI_HEALTH["limited_until"] = max(AI_HEALTH["limited_until"], until)
        AI_HEALTH["since"] = AI_HEALTH["since"] or detected_at
        AI_HEALTH["detected_at"] = detected_at
        hint = time.strftime("%H:%M", time.localtime(AI_HEALTH["limited_until"]))
        _append_log(job, f"[시스템] ⛔ Claude 사용량 한도 감지 — {hint}까지 "
                         "AI 작업 일시정지 (대기열 유지, 자동 재개)")
        health = {
            "ai": "limited", "since": AI_HEALTH["since"],
            "detected_at": AI_HEALTH["detected_at"],
            "limited_until": AI_HEALTH["limited_until"], "detected": line[:200],
            "provider": AI_PROVIDER,
        }
    try:
        with HEALTH_LOCK:
            _write_json(HEALTH_FILE, health)
    except OSError as exc:
        with LOCK:
            _append_log(job, f"[시스템] health.json 저장 실패: {exc}")


def _clear_ai_limit(job):
    """Clear an old breaker only after a post-limit probe job succeeds."""
    with LOCK:
        detected_at = AI_HEALTH["detected_at"]
        # Jobs already running when another worker detected the limit are not
        # proof that the provider recovered, even if they finish successfully.
        if detected_at is None or (job.get("started") or 0) <= detected_at:
            return
        was = AI_HEALTH["limited_until"]
        AI_HEALTH.update(limited_until=0.0, since=None, detected_at=None)
        _dispatch_locked()
    if was:
        try:
            with HEALTH_LOCK:
                _write_json(HEALTH_FILE, {
                    "ai": "ok", "since": None, "detected_at": None,
                    "limited_until": 0, "provider": AI_PROVIDER,
                })
        except OSError as exc:
            with LOCK:
                _append_log(job, f"[시스템] health.json 저장 실패: {exc}")


def _record_usage(task_id, status, limited=False):
    day = time.strftime("%Y-%m-%d")
    with USAGE_LOCK:
        data = _read_json(USAGE_FILE, {})
        if not isinstance(data, dict):
            data = {}
        d = data.setdefault(day, {})
        if not isinstance(d, dict):
            d = data[day] = {}
        for key in ("ai_jobs", "success", "failed", "limited_hits"):
            if not isinstance(d.get(key), int):
                d[key] = 0
        if not isinstance(d.get("by_task"), dict):
            d["by_task"] = {}
        d["ai_jobs"] += 1
        d["provider"] = AI_PROVIDER
        d["success" if status == "success" else "failed"] += 1
        if limited:
            d["limited_hits"] += 1
        task_count = d["by_task"].get(task_id)
        d["by_task"][task_id] = (task_count if isinstance(task_count, int) else 0) + 1
        for k in sorted(data)[:-60]:      # keep 60 days
            del data[k]
        _write_json(USAGE_FILE, data)


def _record_task_success(task_id):
    with TASK_RUNS_LOCK:
        data = _read_json(TASK_RUNS_FILE, {})
        if not isinstance(data, dict):
            data = {}
        data[task_id] = time.time()
        _write_json(TASK_RUNS_FILE, data)


def _last_task_success(task_id):
    with TASK_RUNS_LOCK:
        data = _read_json(TASK_RUNS_FILE, {})
        v = data.get(task_id) if isinstance(data, dict) else None
    return float(v) if isinstance(v, (int, float)) else None


def _job_summary(job):
    return {
        "id": job["id"],
        "task_id": job["task_id"],
        "label": job["label"],
        "status": job["status"],
        "created": job["created"],
        "started": job.get("started"),
        "finished": job.get("finished"),
        "returncode": job.get("returncode"),
        "refresh": job.get("refresh"),
        "log_len": job["log_total"],
    }


def _append_log(job, line):
    """Caller must hold LOCK."""
    job["log"].append(line)
    job["log_total"] += 1


def _kill_group(proc):
    """SIGTERM the whole process group, escalate to SIGKILL after 5s."""
    try:
        pgid = os.getpgid(proc.pid)
    except (ProcessLookupError, OSError):
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except (ProcessLookupError, OSError):
        return
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except (ProcessLookupError, OSError):
            pass


def _watchdog(job, proc, timeout):
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        with LOCK:
            if job["status"] == "running":
                job["timed_out"] = True
                _append_log(job, f"[시스템] 타임아웃 ({timeout}초 초과) — 프로세스 그룹 종료")
        _kill_group(proc)


def _heartbeat(job, proc):
    start = time.time()
    while True:
        time.sleep(HEARTBEAT_SEC)
        if proc.poll() is not None:
            return
        elapsed = int(time.time() - start)
        with LOCK:
            if job["status"] != "running":
                return
            _append_log(job, f"… 실행 중 (경과 {elapsed}초)")


def _runner(job, task, params):
    log_path = LOG_DIR / f"{job['id']}.log"
    argv = task["argv"](params)
    stdin_text = task["stdin"](params) if "stdin" in task else None
    if job.get("ai") and stdin_text is not None:
        stdin_text = AI_PREAMBLE + stdin_text

    def run_finalize():
        # generic post-job hook (e.g. upload classification → server-side move);
        # failures are logged only, never raised.
        fin = task.get("finalize")
        if fin is None:
            return
        try:
            fin(job, params)
        except Exception as exc:
            with LOCK:
                _append_log(job, f"[시스템] finalize 오류: {exc}")

    try:
        proc = subprocess.Popen(
            argv,
            cwd=str(VAULT),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            start_new_session=True,
        )
        if stdin_text is not None:
            proc.stdin.write(stdin_text)
        proc.stdin.close()
    except OSError as exc:
        with LOCK:
            job["status"] = "failed"
            job["finished"] = time.time()
            _append_log(job, f"[시스템] 실행 실패: {exc}")
            ACTIVE_GROUPS.difference_update(job["groups"])
            _dispatch_locked()
        run_finalize()
        return

    with LOCK:
        job["status"] = "running"
        job["started"] = time.time()
        job["proc"] = proc
        _append_log(job, f"[시스템] 시작: {' '.join(argv[:3])} … (pid {proc.pid})")

    threading.Thread(target=_watchdog, args=(job, proc, task["timeout"]), daemon=True).start()
    if task.get("heartbeat"):
        threading.Thread(target=_heartbeat, args=(job, proc), daemon=True).start()

    limited_line = None
    with open(log_path, "w", encoding="utf-8") as lf:
        for line in proc.stdout:
            line = line.rstrip("\n")
            lf.write(line + "\n")
            lf.flush()
            if job.get("ai") and limited_line is None and AI_LIMIT_RE.search(line):
                limited_line = line
                # Set the global breaker before any concurrently finishing
                # worker gets a chance to dispatch more AI jobs.
                _note_ai_limit(job, line)
            else:
                with LOCK:
                    _append_log(job, line)
        rc = proc.wait()
        with LOCK:
            if job.get("cancel_requested"):
                job["status"] = "cancelled"
            elif job.get("timed_out"):
                job["status"] = "timeout"
            elif limited_line:
                # Some AI CLIs report the provider limit with rc=0.
                # It is not a successful run and must never trigger finalize
                # success-only hooks from persisting AI-produced state.
                job["status"] = "failed"
            elif rc == 0:
                job["status"] = "success"
            else:
                job["status"] = "failed"
            job["returncode"] = rc
            job["finished"] = time.time()
            _append_log(job, f"[시스템] 종료 — 상태: {job['status']} (rc={rc})")
            ACTIVE_GROUPS.difference_update(job["groups"])
            _dispatch_locked()
        lf.write(f"[system] finished status={job['status']} rc={rc}\n")
    if job.get("ai"):
        try:
            _record_usage(job["task_id"], job["status"], limited=bool(limited_line))
        except Exception as exc:
            with LOCK:
                _append_log(job, f"[시스템] usage.json 저장 실패: {exc}")
        if job["status"] == "success":
            try:
                _record_task_success(job["task_id"])
            except Exception as exc:
                with LOCK:
                    _append_log(job, f"[시스템] task_runs.json 저장 실패: {exc}")
            try:
                _clear_ai_limit(job)
            except Exception as exc:
                with LOCK:
                    _append_log(job, f"[시스템] AI 한도 해제 실패: {exc}")
    run_finalize()


def _trim_jobs():
    """Caller must hold LOCK. Drop oldest terminal jobs beyond MAX_JOBS."""
    terminal = {"success", "failed", "cancelled", "timeout"}
    while len(JOB_ORDER) > MAX_JOBS:
        for jid in JOB_ORDER:
            if JOBS[jid]["status"] in terminal:
                JOB_ORDER.remove(jid)
                del JOBS[jid]
                break
        else:
            break

# ---------------------------------------------------------------- file views
# Whitelisted views only. Triple defense against path traversal:
# 1) filename regex  2) resolve() + is_relative_to()  3) .md enforced

FILENAME_RE = re.compile(r"^[\w\-. ]+\.md$", re.UNICODE)
DAILY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")

VIEWS = {
    "digests": {"dir": ENGINE / "sources", "label": "다이제스트"},
    "xhs": {"dir": VAULT / "01-Projects/Visual-Climate/02-Xiaohongshu/drafts", "label": "XHS 초안"},
    "ig": {"dir": VAULT / "01-Projects/Visual-Climate/04-Social/instagram", "label": "IG 초안"},
    "daily": {"dir": VAULT, "label": "데일리 노트", "pattern": DAILY_RE},
    "calendar": {
        "dir": VAULT / "01-Projects/Visual-Climate",
        "label": "콘텐츠 캘린더",
        "fixed": "_CONTENT-CALENDAR.md",
    },
}


def _view_files(view):
    base = view["dir"]
    if not base.is_dir():
        return []
    if "fixed" in view:
        names = [view["fixed"]]
    else:
        names = [p.name for p in base.iterdir() if p.is_file() and p.suffix == ".md"]
    out = []
    for name in names:
        if not FILENAME_RE.match(name):
            continue
        if "pattern" in view and not view["pattern"].match(name):
            continue
        p = base / name
        if not p.is_file():
            continue
        st = p.stat()
        out.append({"name": name, "mtime": st.st_mtime, "size": st.st_size})
    out.sort(key=lambda f: f["mtime"], reverse=True)
    return out


def _safe_read(view, name):
    if not FILENAME_RE.match(name) or not name.endswith(".md"):
        abort(400)
    if "pattern" in view and not view["pattern"].match(name):
        abort(400)
    if "fixed" in view and name != view["fixed"]:
        abort(400)
    base = view["dir"].resolve()
    target = (base / name).resolve()
    if not target.is_relative_to(base):
        abort(400)
    if target.suffix != ".md" or not target.is_file():
        abort(404)
    return target.read_text(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------- vault files
# Browser file explorer + markdown editing. Same triple defense as _safe_read:
# segment validation → resolve() → is_relative_to(VAULT). Writes are .md only.

TEXT_EXTS = {
    ".md", ".txt", ".json", ".py", ".js", ".ts", ".csv", ".tsv", ".yaml", ".yml",
    ".html", ".css", ".sh", ".toml", ".xml", ".sql", ".ini", ".cfg", ".log",
}
FILE_MAX = 2 * 1024 * 1024          # 2MB read/write cap
TREE_MAX_DEPTH = 6
TREE_MAX_ENTRIES = 500
PROMPT_MAX = 2000
EDIT_LOCK = threading.Lock()
REQ_LOCK = threading.Lock()
REQUESTS_DIR = STATE_DIR / "requests"


def _vault_path(rel, allow_dir=False):
    """Resolve a vault-relative path safely, or abort.

    Rejects absolute paths, backslashes, NUL, empty segments and any segment
    starting with '.' (blocks '..', dotfiles, and the whole .hios tree),
    then verifies the resolved path stays inside the vault.
    """
    rel = str(rel or "")
    if not rel or rel.startswith("/") or "\\" in rel or "\x00" in rel:
        abort(400)
    for seg in rel.split("/"):
        if not seg or seg.startswith("."):
            abort(400)
    target = (VAULT / rel).resolve()
    if not target.is_relative_to(VAULT.resolve()):
        abort(400)
    if target.is_dir():
        if not allow_dir:
            abort(400)
    elif not target.is_file():
        abort(404)
    return target


def _atomic_write_text(path, text):
    tmp = path.parent / (path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)

# ---------------------------------------------------------------- front matter (stdlib)


def _parse_front_matter(text):
    meta, body = {}, text
    if text.startswith("---"):
        lines = text.split("\n")
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                body = "\n".join(lines[i + 1:])
                for raw in lines[1:i]:
                    if ":" not in raw:
                        continue
                    key, _, val = raw.partition(":")
                    key, val = key.strip(), val.strip()
                    if val.startswith("[") and val.endswith("]"):
                        meta[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
                    else:
                        meta[key] = val.strip("'\"")
                break
    return meta, body.strip()

# ---------------------------------------------------------------- routes


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/health")
def health():
    with LOCK:
        limited = _ai_limited_locked()
        resume = AI_HEALTH["limited_until"] if limited else None
    usage_data = _read_json(USAGE_FILE, {})
    usage = (usage_data.get(time.strftime("%Y-%m-%d"), {})
             if isinstance(usage_data, dict) else {})
    if not isinstance(usage, dict):
        usage = {}
    return jsonify(ok=True, vault=VAULT.name, time=time.time(),
                   ai="limited" if limited else "ok", ai_resume=resume,
                   ai_provider=AI_PROVIDER, claude_bin=CLAUDE_BIN,
                   usage_today=usage)


@app.get("/api/tasks")
def api_tasks():
    with LOCK:
        active = set(ACTIVE_GROUPS)
        running_tasks = {
            j["task_id"] for j in JOBS.values()
            if j["status"] in ("queued", "pending", "running")
        }
    out = []
    for tid, task in TASKS.items():
        if task.get("internal"):
            continue
        warn = task.get("warning")
        out.append({
            "id": tid,
            "label_ko": task["label_ko"],
            "category": task["category"],
            "topic": bool(task.get("topic")),
            "running": tid in running_tasks,
            "blocked": bool(active & _task_groups(task, {})),
            "warning": warn() if warn else None,
        })
    return jsonify(out)


def _task_groups(task, params):
    g = task["groups"]
    return set(g(params)) if callable(g) else set(g)


def _ai_active_locked():
    """Caller must hold LOCK. Count live AI workers."""
    return sum(1 for j in JOBS.values()
               if j.get("ai") and j["status"] in ("pending", "running"))


def _dispatch_locked():
    """Caller must hold LOCK. Start queued jobs whose groups are free (FIFO)."""
    started = []
    for jid in JOB_ORDER:
        job = JOBS[jid]
        if job["status"] != "queued":
            continue
        if ACTIVE_GROUPS & job["groups"]:
            continue
        if job.get("ai") and (
            _ai_active_locked() >= MAX_AI_CONCURRENT or _ai_limited_locked()
        ):
            continue
        job["status"] = "pending"
        ACTIVE_GROUPS.update(job["groups"])
        started.append(job)
    for job in started:
        threading.Thread(
            target=_runner, args=(job, TASKS[job["task_id"]], job["params"]),
            daemon=True,
        ).start()


def _dispatch():
    with LOCK:
        _dispatch_locked()


def _start_job(task_id, params, label=None):
    """Enqueue a task job — starts immediately if its groups are free,
    otherwise waits in the queue (no more 409 rejections).
    Returns (job_id, err):
      (id, None)      fresh job enqueued
      (id, "dedup")   identical job already queued/pending/running — reuse it
      (None, "cooldown")  task succeeded < task["cooldown"] seconds ago"""
    task = TASKS[task_id]
    groups = _task_groups(task, params)
    key = _idem_key(task_id, params)
    cooldown = task.get("cooldown")
    if cooldown:
        last = _last_task_success(task_id)
        if last and time.time() - last < cooldown:
            return None, "cooldown"
    with LOCK:
        for jid in JOB_ORDER:
            j = JOBS[jid]
            if (j.get("idem_key") == key
                    and j["status"] in ("queued", "pending", "running")):
                return jid, "dedup"
        job_id = uuid.uuid4().hex[:12]
        job = {
            "id": job_id,
            "task_id": task_id,
            "label": label or task["label_ko"],
            "status": "queued",
            "created": time.time(),
            "groups": groups,
            "idem_key": key,
            "ai": bool(task.get("ai")),
            "provider": AI_PROVIDER if task.get("ai") else None,
            "params": params,
            "refresh": task.get("refresh"),
            "log": deque(maxlen=LOG_CAP),
            "log_total": 0,
        }
        JOBS[job_id] = job
        JOB_ORDER.append(job_id)
        _trim_jobs()
        _dispatch_locked()
        if job["status"] == "queued":
            _append_log(job, "[시스템] 대기열 등록 — 앞 작업이 끝나면 자동 시작")
    return job_id, None


def _job_queued(job_id):
    with LOCK:
        j = JOBS.get(job_id)
        return bool(j and j["status"] == "queued")


@app.post("/api/run/<task_id>")
def api_run(task_id):
    if task_id not in TASKS or TASKS[task_id].get("internal"):
        abort(404)
    params = request.get_json(silent=True) or {}
    job_id, err = _start_job(task_id, params)
    if err == "cooldown":
        cd = TASKS[task_id].get("cooldown") or 0
        last = _last_task_success(task_id) or time.time()
        remaining = cd - (time.time() - last)
        return jsonify(job_id=None, cooldown=True,
                       retry_in=max(0, int(remaining + 0.999))), 200
    return jsonify(job_id=job_id, queued=_job_queued(job_id),
                   dedup=(err == "dedup")), 202


@app.get("/api/jobs")
def api_jobs():
    with LOCK:
        return jsonify([_job_summary(JOBS[jid]) for jid in reversed(JOB_ORDER)])


@app.get("/api/jobs/<job_id>")
def api_job(job_id):
    try:
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        offset = 0
    with LOCK:
        job = JOBS.get(job_id)
        if not job:
            abort(404)
        total = job["log_total"]
        buf = list(job["log"])
        available_start = total - len(buf)
        idx = max(0, offset - available_start)
        summary = _job_summary(job)
    summary["lines"] = buf[idx:]
    summary["next_offset"] = total
    return jsonify(summary)


@app.post("/api/jobs/<job_id>/cancel")
def api_cancel(job_id):
    with LOCK:
        job = JOBS.get(job_id)
        if not job:
            abort(404)
        if job["status"] == "queued":   # not started yet — just drop it
            job["status"] = "cancelled"
            job["finished"] = time.time()
            _append_log(job, "[시스템] 대기열에서 취소됨")
            return jsonify(ok=True), 202
        proc = job.get("proc")
        if job["status"] != "running" or proc is None:
            return jsonify(error="not_running"), 409
        job["cancel_requested"] = True
        _append_log(job, "[시스템] 취소 요청 — SIGTERM 전송")
    threading.Thread(target=_kill_group, args=(proc,), daemon=True).start()
    return jsonify(ok=True), 202


@app.get("/api/files/<view_id>")
def api_files(view_id):
    view = VIEWS.get(view_id)
    if not view:
        abort(404)
    return jsonify(_view_files(view))


@app.get("/api/file/<view_id>/<name>")
def api_file(view_id, name):
    view = VIEWS.get(view_id)
    if not view:
        abort(404)
    return jsonify(name=name, content=_safe_read(view, name))


@app.get("/api/status-cards")
def api_status_cards():
    cards = []
    projects_dir = VAULT / "01-Projects"
    if projects_dir.is_dir():
        for proj in sorted(projects_dir.iterdir()):
            status_file = proj / "_STATUS.md"
            if not (proj.is_dir() and status_file.is_file()):
                continue
            meta, body = _parse_front_matter(
                status_file.read_text(encoding="utf-8", errors="replace")
            )
            cards.append({
                "project": proj.name,
                "client": meta.get("client", ""),
                "updated": meta.get("updated", ""),
                "tags": meta.get("tags", []),
                "body": body,
            })
    return jsonify(cards)


# ---------------------------------------------------------------- projects
# Web workspace per consulting project: todos / resource links / meetings /
# documents. Web edits write straight into the vault markdown files.

PROJECTS_DIR = VAULT / "01-Projects"
PROJ_RE = re.compile(r"^[\w\-]+$")
TODO_RE = re.compile(r"^(\s*- \[)( |x)(\] .*)$")
PROJ_LOCK = threading.Lock()


def _proj_dir(name):
    if not PROJ_RE.match(name):
        abort(400)
    p = PROJECTS_DIR / name
    if not p.is_dir() or not p.resolve().is_relative_to(PROJECTS_DIR.resolve()):
        abort(404)
    return p


def _find_subdir(proj, keyword):
    for d in sorted(proj.iterdir()):
        if d.is_dir() and keyword in d.name.lower():
            return d
    return None


def _list_dir_files(d, md_only=False):
    if d is None or not d.is_dir():
        return []
    out = []
    for f in sorted(d.iterdir()):
        if not f.is_file() or f.name.startswith("."):
            continue
        if md_only and f.suffix != ".md":
            continue
        st = f.stat()
        out.append({"name": f.name, "mtime": st.st_mtime, "size": st.st_size})
    out.sort(key=lambda x: x["mtime"], reverse=True)
    return out


def _parse_todos(proj):
    todo_file = proj / "_TODO.md"
    if not todo_file.is_file():
        return []
    todos = []
    for i, line in enumerate(todo_file.read_text(encoding="utf-8").splitlines()):
        m = TODO_RE.match(line)
        if m:
            todos.append({"line": i, "text": m.group(3)[2:].strip(), "done": m.group(2) == "x"})
    return todos


@app.get("/api/projects")
def api_projects():
    out = []
    if PROJECTS_DIR.is_dir():
        for proj in sorted(PROJECTS_DIR.iterdir()):
            if not proj.is_dir() or proj.name.startswith("."):
                continue
            meta = {}
            status_file = proj / "_STATUS.md"
            if status_file.is_file():
                meta, _ = _parse_front_matter(
                    status_file.read_text(encoding="utf-8", errors="replace"))
            todos = _parse_todos(proj)
            items = _load_items(proj)
            meetings = _list_dir_files(_find_subdir(proj, "meeting"), md_only=True)
            out.append({
                "name": proj.name,
                "client": meta.get("client", proj.name),
                "updated": meta.get("updated", ""),
                "open_todos": sum(1 for t in todos if not t["done"]),
                "open_actions": sum(
                    1 for i in items if isinstance(i, dict) and i.get("status") != "done"),
                "latest_meeting": meetings[0]["name"] if meetings else "",
                "meetings": len(meetings),
                "docs": len(_list_dir_files(_find_subdir(proj, "document"))),
            })
    return jsonify(out)


@app.get("/api/projects/<name>")
def api_project(name):
    proj = _proj_dir(name)
    status_body = ""
    status_file = proj / "_STATUS.md"
    if status_file.is_file():
        _, status_body = _parse_front_matter(
            status_file.read_text(encoding="utf-8", errors="replace"))
    resources = ""
    res_file = proj / "_RESOURCES.md"
    if res_file.is_file():
        _, resources = _parse_front_matter(
            res_file.read_text(encoding="utf-8", errors="replace"))
    return jsonify(
        name=name,
        status=status_body,
        todos=_parse_todos(proj),
        resources=resources,
        meetings=_list_dir_files(_find_subdir(proj, "meeting"), md_only=True),
        docs=_list_dir_files(_find_subdir(proj, "document")),
    )


@app.get("/api/projects/<name>/meeting/<path:fname>")
def api_project_meeting(name, fname):
    proj = _proj_dir(name)
    d = _find_subdir(proj, "meeting")
    if d is None or not FILENAME_RE.match(fname):
        abort(404)
    target = (d / fname).resolve()
    if not target.is_relative_to(d.resolve()) or target.suffix != ".md" or not target.is_file():
        abort(404)
    return jsonify(name=fname, content=target.read_text(encoding="utf-8", errors="replace"))


@app.post("/api/projects/<name>/todos")
def api_project_todo_add(name):
    proj = _proj_dir(name)
    text = _clean_response((request.get_json(silent=True) or {}).get("text", ""))
    text = text.replace("\n", " ")
    if not text:
        return jsonify(error="empty"), 400
    todo_file = proj / "_TODO.md"
    with PROJ_LOCK:
        if todo_file.is_file():
            lines = todo_file.read_text(encoding="utf-8").splitlines()
        else:
            lines = ["# " + name + " — To-Do", "", "## Open", "", "## Done"]
        # insert right after "## Open" if present, else append
        for i, line in enumerate(lines):
            if line.strip() == "## Open":
                lines.insert(i + 1, f"- [ ] {text}")
                break
        else:
            lines.append(f"- [ ] {text}")
        todo_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return jsonify(ok=True)


@app.post("/api/projects/<name>/todos/toggle")
def api_project_todo_toggle(name):
    proj = _proj_dir(name)
    data = request.get_json(silent=True) or {}
    try:
        line_no = int(data.get("line", -1))
    except (TypeError, ValueError):
        return jsonify(error="bad_line"), 400
    todo_file = proj / "_TODO.md"
    if not todo_file.is_file():
        abort(404)
    with PROJ_LOCK:
        lines = todo_file.read_text(encoding="utf-8").splitlines()
        if not 0 <= line_no < len(lines):
            return jsonify(error="bad_line"), 400
        m = TODO_RE.match(lines[line_no])
        if not m:
            return jsonify(error="not_todo"), 400
        mark = "x" if m.group(2) == " " else " "
        lines[line_no] = m.group(1) + mark + m.group(3)
        todo_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return jsonify(ok=True, done=mark == "x")


@app.post("/api/projects/<name>/resources")
def api_project_resource_add(name):
    proj = _proj_dir(name)
    data = request.get_json(silent=True) or {}
    title = _clean_response(data.get("title", "")).replace("[", "(").replace("]", ")")
    url = _clean_response(data.get("url", ""))
    note = _clean_response(data.get("note", "")).replace("\n", " ")
    if not title:
        return jsonify(error="empty", message="제목을 입력하세요"), 400
    if url and not (url.startswith("http://") or url.startswith("https://")):
        return jsonify(error="bad_url", message="http(s):// 링크만 저장됩니다"), 400
    entry = f"- [{title}]({url})" if url else f"- {title}"
    if note:
        entry += f" — {note}"
    entry += f" `{time.strftime('%Y-%m-%d')}`"
    res_file = proj / "_RESOURCES.md"
    with PROJ_LOCK:
        if res_file.is_file():
            content = res_file.read_text(encoding="utf-8").rstrip("\n")
        else:
            content = f"# {name} — Resources & Links"
        res_file.write_text(content + "\n" + entry + "\n", encoding="utf-8")
    return jsonify(ok=True)


@app.post("/api/projects/<name>/open")
def api_project_open(name):
    proj = _proj_dir(name)
    which = (request.get_json(silent=True) or {}).get("which", "root")
    target = proj
    if which == "meetings":
        target = _find_subdir(proj, "meeting") or proj
    elif which == "docs":
        target = _find_subdir(proj, "document") or proj
    subprocess.Popen(["open", str(target)])
    return jsonify(ok=True)


# ---------------------------------------------------------------- vault file routes


def _walk_tree(root, max_entries=TREE_MAX_ENTRIES, max_depth=TREE_MAX_DEPTH):
    """Shared directory walk for tree endpoints. Skips dot-entries/symlinks."""
    stats = {"count": 0, "truncated": False}

    def walk(d, depth):
        children = []
        try:
            entries = sorted(d.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return children
        for p in entries:
            if p.name.startswith(".") or p.is_symlink():
                continue
            if stats["count"] >= max_entries:
                stats["truncated"] = True
                break
            stats["count"] += 1
            rel = p.relative_to(VAULT).as_posix()
            if p.is_dir():
                node = {"name": p.name, "path": rel, "dir": True, "children": []}
                if depth < max_depth:
                    node["children"] = walk(p, depth + 1)
                else:
                    stats["truncated"] = True
                children.append(node)
            else:
                try:
                    st = p.stat()
                except OSError:
                    continue
                ext = p.suffix.lower()
                children.append({
                    "name": p.name, "path": rel, "dir": False,
                    "size": st.st_size, "mtime": st.st_mtime,
                    "ext": ext, "editable": ext == ".md",
                })
        return children

    return walk(root, 1), stats["truncated"]


@app.get("/api/projects/<name>/tree")
def api_project_tree(name):
    proj = _proj_dir(name)
    children, truncated = _walk_tree(proj)
    return jsonify(
        name=name,
        root=proj.relative_to(VAULT).as_posix(),
        children=children,
        truncated=truncated,
    )


VAULT_TREE_MAX = 2000


@app.get("/api/vault-tree")
def api_vault_tree():
    """Whole-vault tree: 00~07 top dirs + Templates + root files.

    _walk_tree already skips dot-entries, so .hios/.claude/.git never appear.
    """
    children, truncated = _walk_tree(VAULT, max_entries=VAULT_TREE_MAX)
    return jsonify(root="", children=children, truncated=truncated)


@app.get("/api/vault-file/<path:rel>")
def api_vault_file_get(rel):
    target = _vault_path(rel)
    st = target.stat()
    ext = target.suffix.lower()
    base = {
        "name": target.name,
        "path": target.relative_to(VAULT).as_posix(),
        "size": st.st_size,
        "mtime": st.st_mtime,
        "ext": ext,
    }
    if ext not in TEXT_EXTS or st.st_size > FILE_MAX:
        return jsonify(binary=True, editable=False, **base)
    return jsonify(
        binary=False,
        editable=ext == ".md",
        content=target.read_text(encoding="utf-8", errors="replace"),
        **base,
    )


@app.post("/api/vault-file/<path:rel>")
def api_vault_file_save(rel):
    target = _vault_path(rel)          # existing files only — no create via web
    if target.suffix.lower() != ".md":
        return jsonify(error="not_editable", message=".md 파일만 저장할 수 있습니다"), 400
    data = request.get_json(silent=True) or {}
    content = data.get("content")
    if not isinstance(content, str) or "\x00" in content:
        return jsonify(error="bad_content", message="잘못된 내용"), 400
    if len(content.encode("utf-8")) > FILE_MAX:
        return jsonify(error="too_large", message="2MB를 초과합니다"), 400
    try:
        client_mtime = float(data.get("mtime"))
    except (TypeError, ValueError):
        return jsonify(error="bad_mtime", message="mtime이 필요합니다"), 400
    with EDIT_LOCK:
        st = target.stat()
        if not data.get("force") and abs(st.st_mtime - client_mtime) > 0.0005:
            return jsonify(
                error="conflict",
                message="다른 곳에서 수정됨 (Obsidian?)",
                mtime=st.st_mtime,
            ), 409
        _atomic_write_text(target, content)
        new_mtime = target.stat().st_mtime
    return jsonify(ok=True, mtime=new_mtime)


@app.post("/api/open-path")
def api_open_path():
    data = request.get_json(silent=True) or {}
    target = _vault_path(str(data.get("path", "")), allow_dir=True)
    which = data.get("app")
    if which == "finder":
        argv = ["open", "-R", str(target)] if target.is_file() else ["open", str(target)]
    elif which == "vscode":
        argv = ["open", "-a", "Visual Studio Code", str(target)]
    elif which == "default":
        argv = ["open", str(target)]        # macOS default app (PDF → Preview 등)
    else:
        return jsonify(error="bad_app", message="finder / vscode / default만 지원합니다"), 400
    subprocess.Popen(argv)
    return jsonify(ok=True)


@app.post("/api/vault-create")
def api_vault_create():
    """Create a new folder or empty .md file inside the vault."""
    data = request.get_json(silent=True) or {}
    rel = str(data.get("path", "") or "")
    want_dir = bool(data.get("dir"))
    # same segment rules as _vault_path, but the target must NOT exist yet
    if not rel or rel.startswith("/") or "\\" in rel or "\x00" in rel:
        return jsonify(error="bad_path", message="잘못된 경로"), 400
    for seg in rel.split("/"):
        if not seg or seg.startswith(".") or seg != seg.strip():
            return jsonify(error="bad_path", message="잘못된 경로"), 400
    target = (VAULT / rel).resolve()
    if not target.is_relative_to(VAULT.resolve()):
        return jsonify(error="bad_path", message="잘못된 경로"), 400
    if not target.parent.is_dir() or not target.parent.is_relative_to(VAULT.resolve()):
        return jsonify(error="no_parent", message="상위 폴더가 없습니다"), 400
    if target.exists():
        return jsonify(error="exists", message="이미 존재합니다"), 409
    if not want_dir and target.suffix.lower() != ".md":
        return jsonify(error="md_only", message="파일은 .md만 만들 수 있습니다"), 400
    with EDIT_LOCK:
        if want_dir:
            target.mkdir()
        else:
            _atomic_write_text(target, "")
    return jsonify(ok=True, path=target.relative_to(VAULT).as_posix(), dir=want_dir), 201


@app.post("/api/quick-memo")
def api_quick_memo():
    """Append a one-line memo to today's daily note (### Notes section)."""
    data = request.get_json(silent=True) or {}
    text = _clean_item_text(data.get("text", ""), 1000)
    if not text:
        return jsonify(error="empty", message="메모 내용을 입력하세요"), 400
    today = time.strftime("%Y-%m-%d")
    note = VAULT / f"{today}.md"
    stamp = time.strftime("%H:%M")
    line = f"- **{stamp}** {text}"
    with EDIT_LOCK:
        if note.is_file():
            body = note.read_text(encoding="utf-8", errors="replace")
            if "### Notes" in body:
                head, _, tail = body.partition("### Notes")
                # insert right after the "### Notes" heading line
                nl = tail.find("\n")
                nl = nl if nl >= 0 else len(tail)
                body = head + "### Notes" + tail[:nl] + "\n" + line + tail[nl:]
            else:
                body = body.rstrip("\n") + f"\n\n### Notes\n{line}\n"
        else:
            body = (
                f"---\ndate: {today}\ntype: daily-note\n---\n\n"
                f"# {today}\n\n### Notes\n{line}\n"
            )
        _atomic_write_text(note, body)
    return jsonify(ok=True, file=note.name), 201


# ---------------------------------------------------------------- AI requests
# Free-text request scoped (by prompt) to one project, executed by the
# existing job runner. History in .hios/state/requests/<name>.json (last 30).


def _request_history_file(name):
    return REQUESTS_DIR / f"{name}.json"      # name already PROJ_RE-validated


@app.post("/api/projects/<name>/request")
def api_project_request(name):
    _proj_dir(name)
    data = request.get_json(silent=True) or {}
    prompt = _clean_item_text(data.get("prompt", ""), PROMPT_MAX)
    if not prompt:
        return jsonify(error="empty", message="요청 내용을 입력하세요"), 400
    job_id, _err = _start_job(
        "project_request", {"project": name, "prompt": prompt},
        label=f"AI 요청 · {name}",
    )
    entry = {
        "id": uuid.uuid4().hex[:8],
        "job_id": job_id,
        "prompt": prompt,
        "created": time.time(),
    }
    with REQ_LOCK:
        REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
        hist = _read_json(_request_history_file(name), [])
        if not isinstance(hist, list):
            hist = []
        hist.append(entry)
        _write_json(_request_history_file(name), hist[-30:])
    return jsonify(job_id=job_id, entry=entry, queued=_job_queued(job_id)), 202


@app.get("/api/projects/<name>/requests")
def api_project_requests(name):
    _proj_dir(name)
    with REQ_LOCK:
        hist = _read_json(_request_history_file(name), [])
    if not isinstance(hist, list):
        hist = []
    return jsonify(list(reversed(hist)))


@app.post("/api/ask")
def api_ask():
    """Vault-wide read-only question, answered by a Claude job."""
    data = request.get_json(silent=True) or {}
    q = _clean_item_text(data.get("q", ""), PROMPT_MAX)
    if not q:
        return jsonify(error="empty", message="질문을 입력하세요"), 400
    job_id, _err = _start_job("vault_ask", {"prompt": q}, label=f"질문 · {q[:40]}")
    return jsonify(job_id=job_id, queued=_job_queued(job_id)), 202


# ---------------------------------------------------------------- accounts
# Per-project account/link registry: 01-Projects/<name>/_ACCOUNTS.json
# SECURITY: never store actual passwords — only a pointer to where the
# password lives (Keychain item name, 1Password entry, etc.).

ACCOUNTS_LOCK = threading.Lock()


def _accounts_file(proj):
    return proj / "_ACCOUNTS.json"


def _load_accounts(proj):
    data = _read_json(_accounts_file(proj), [])
    return data if isinstance(data, list) else []


def _clean_account(raw):
    if not isinstance(raw, dict):
        return None
    url = _clean_item_text(raw.get("url", ""), 500)
    if url and not (url.startswith("http://") or url.startswith("https://")):
        url = ""
    item = {
        "service": _clean_item_text(raw.get("service", ""), 120),
        "account": _clean_item_text(raw.get("account", ""), 200),
        "url": url,
        "pw_hint": _clean_item_text(raw.get("pw_hint", ""), 200),
        "note": _clean_item_text(raw.get("note", ""), 500),
    }
    if not item["service"] and not item["account"]:
        return None
    return item


@app.get("/api/projects/<name>/accounts")
def api_accounts_get(name):
    proj = _proj_dir(name)
    return jsonify(_load_accounts(proj))


@app.post("/api/projects/<name>/accounts")
def api_accounts_post(name):
    proj = _proj_dir(name)
    data = request.get_json(silent=True) or {}
    op = data.get("op")
    with ACCOUNTS_LOCK:
        accounts = _load_accounts(proj)
        if op == "add":
            item = _clean_account(data.get("item"))
            if not item:
                return jsonify(error="bad_item", message="서비스명 또는 계정을 입력하세요"), 400
            item["id"] = uuid.uuid4().hex[:8]
            item["updated"] = time.strftime("%Y-%m-%d")
            accounts.append(item)
        elif op == "update":
            aid = str(data.get("id", ""))
            item = _clean_account(data.get("item"))
            if not item:
                return jsonify(error="bad_item", message="서비스명 또는 계정을 입력하세요"), 400
            for i, a in enumerate(accounts):
                if isinstance(a, dict) and a.get("id") == aid:
                    item["id"] = aid
                    item["updated"] = time.strftime("%Y-%m-%d")
                    accounts[i] = item
                    break
            else:
                return jsonify(error="not_found", message="항목이 없습니다"), 404
        elif op == "delete":
            aid = str(data.get("id", ""))
            before = len(accounts)
            accounts = [a for a in accounts if not (isinstance(a, dict) and a.get("id") == aid)]
            if len(accounts) == before:
                return jsonify(error="not_found", message="항목이 없습니다"), 404
        else:
            return jsonify(error="bad_op", message="op는 add/update/delete"), 400
        _write_json(_accounts_file(proj), accounts)
    return jsonify(accounts)


# ---------------------------------------------------------------- action items
# Per-project action board: 01-Projects/<name>/_ACTIONS.json
# Rich items sourced from email/meetings: status, priority, due date,
# people, source deep-links (Gmail thread / Granola note), free-text notes.

ITEMS_LOCK = threading.Lock()
ITEM_STATUSES = {"open", "in_progress", "blocked", "done"}
ITEM_PRIORITIES = {"high", "med", "low"}
ITEM_TEXT_MAX = 4000
ITEM_ID_RE = re.compile(r"^[\w\-]{1,64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _items_file(proj):
    return proj / "_ACTIONS.json"


def _load_items(proj):
    data = _read_json(_items_file(proj), [])
    return data if isinstance(data, list) else []


def _clean_item_text(raw, maxlen=ITEM_TEXT_MAX):
    clean = "".join(ch for ch in str(raw) if ch == "\n" or ch >= " ")
    return clean.strip()[:maxlen]


def _clean_sources(raw):
    out = []
    for s in (raw or [])[:10]:
        if not isinstance(s, dict):
            continue
        url = _clean_item_text(s.get("url", ""), 500)
        if url and not (url.startswith("http://") or url.startswith("https://")):
            continue
        kind = s.get("kind") if s.get("kind") in ("gmail", "granola", "link") else "link"
        out.append({
            "kind": kind,
            "label": _clean_item_text(s.get("label", ""), 200) or url,
            "url": url,
        })
    return out


def _clean_people(raw):
    if not isinstance(raw, list):
        return []
    return [_clean_item_text(p, 60) for p in raw[:10] if _clean_item_text(p, 60)]


@app.get("/api/action-items")
def api_action_items():
    out = []
    for name in _project_names():
        out.append({"project": name, "items": _load_items(PROJECTS_DIR / name)})
    return jsonify(out)


@app.post("/api/action-items/<name>")
def api_action_item_add(name):
    proj = _proj_dir(name)
    data = request.get_json(silent=True) or {}
    title = _clean_item_text(data.get("title", ""), 300)
    if not title:
        return jsonify(error="empty", message="제목을 입력하세요"), 400
    due = str(data.get("due", "") or "")
    item = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "detail": _clean_item_text(data.get("detail", "")),
        "status": data.get("status") if data.get("status") in ITEM_STATUSES else "open",
        "priority": data.get("priority") if data.get("priority") in ITEM_PRIORITIES else "med",
        "due": due if DATE_RE.match(due) else "",
        "people": _clean_people(data.get("people")),
        "sources": _clean_sources(data.get("sources")),
        "note": _clean_item_text(data.get("note", "")),
        "created": time.strftime("%Y-%m-%d"),
        "updated": time.strftime("%Y-%m-%d"),
    }
    with ITEMS_LOCK:
        items = _load_items(proj)
        items.append(item)
        _write_json(_items_file(proj), items)
    return jsonify(ok=True, item=item)


@app.post("/api/action-items/<name>/<item_id>")
def api_action_item_update(name, item_id):
    proj = _proj_dir(name)
    if not ITEM_ID_RE.match(item_id):
        abort(400)
    data = request.get_json(silent=True) or {}
    with ITEMS_LOCK:
        items = _load_items(proj)
        item = next((i for i in items if i.get("id") == item_id), None)
        if item is None:
            abort(404)
        if data.get("delete"):
            items.remove(item)
        else:
            if data.get("status") in ITEM_STATUSES:
                item["status"] = data["status"]
            if data.get("priority") in ITEM_PRIORITIES:
                item["priority"] = data["priority"]
            if "title" in data:
                t = _clean_item_text(data["title"], 300)
                if t:
                    item["title"] = t
            if "detail" in data:
                item["detail"] = _clean_item_text(data["detail"])
            if "note" in data:
                item["note"] = _clean_item_text(data["note"])
            if "due" in data:
                due = str(data["due"] or "")
                item["due"] = due if DATE_RE.match(due) else ""
            if "people" in data:
                item["people"] = _clean_people(data["people"])
            if "sources" in data:
                item["sources"] = _clean_sources(data["sources"])
            item["updated"] = time.strftime("%Y-%m-%d")
        _write_json(_items_file(proj), items)
    return jsonify(ok=True)


# ---------------------------------------------------------------- work items (calendar)
# Unified item feed for the calendar tab:
#  - "file" items: vault md files with a valid `due:` in front matter
#  - "action" items: per-project _ACTIONS.json entries
# Memo/AI requests on file items append to the file's "## Log" section
# (memo) or start an item_request Claude job (ai) — the "메모→엔진" path.

WORK_SCAN_DIRS = ("01-Projects", "02-Areas")
WORK_CACHE = {"ts": 0.0, "items": []}
WORK_CACHE_TTL = 60
WORK_MAX_ITEMS = 800
WORK_LOCK = threading.Lock()
CHECKBOX_RE = re.compile(r"^\s*- \[( |x)\]", re.MULTILINE)
HEADING_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


def _scan_work_files():
    items = []
    for top in WORK_SCAN_DIRS:
        base = VAULT / top
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            rel = p.relative_to(VAULT).as_posix()
            segs = rel.split("/")
            if any(s.startswith(".") or s == "node_modules" for s in segs):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            meta, _ = _parse_front_matter(text)
            due = str(meta.get("due", "") or "")
            if not DATE_RE.match(due):
                continue
            boxes = CHECKBOX_RE.findall(text)
            heading = HEADING_RE.search(text)
            status = str(meta.get("status", "") or "")
            items.append({
                "kind": "file",
                "path": rel,
                "title": heading.group(1).strip() if heading else p.stem,
                "project": segs[1] if len(segs) > 1 else "",
                "client": str(meta.get("client", "") or ""),
                "due": due,
                "status": "done" if status in ("done", "complete", "completed") else (status or "open"),
                "priority": str(meta.get("priority", "") or "med").lower(),
                "tags": meta.get("tags", []) if isinstance(meta.get("tags"), list) else [],
                "mtime": p.stat().st_mtime,
                "done_boxes": sum(1 for b in boxes if b == "x"),
                "total_boxes": len(boxes),
            })
            if len(items) >= WORK_MAX_ITEMS:
                return items
    return items


def _work_items():
    now = time.time()
    with WORK_LOCK:
        if now - WORK_CACHE["ts"] < WORK_CACHE_TTL:
            return WORK_CACHE["items"]
    items = _scan_work_files()
    for name in _project_names():
        for it in _load_items(PROJECTS_DIR / name):
            if not isinstance(it, dict):
                continue
            items.append({
                "kind": "action",
                "project": name,
                "id": str(it.get("id", "")),
                "title": str(it.get("title", "")),
                "detail": str(it.get("detail", "")),
                "note": str(it.get("note", "")),
                "due": str(it.get("due", "")),
                "status": it.get("status", "open"),
                "priority": it.get("priority", "med"),
            })
    with WORK_LOCK:
        WORK_CACHE.update(ts=now, items=items)
    return items


@app.get("/api/work-items")
def api_work_items():
    if request.args.get("refresh") == "1":
        with WORK_LOCK:
            WORK_CACHE["ts"] = 0.0
    return jsonify(_work_items())


@app.get("/api/work-item-detail")
def api_work_item_detail():
    target = _vault_path(request.args.get("path", ""))
    if target.suffix != ".md":
        abort(400)
    text = target.read_text(encoding="utf-8", errors="replace")
    meta, body = _parse_front_matter(text)
    boxes = CHECKBOX_RE.findall(text)
    siblings = sorted(
        f.name for f in target.parent.iterdir()
        if f.is_file() and f.suffix == ".md" and f.name != target.name
        and not f.name.startswith(".")
    )[:15]
    links = []
    for l in WIKILINK_RE.findall(text):
        l = l.strip()
        if l and l not in links:
            links.append(l)
    return jsonify(
        path=target.relative_to(VAULT).as_posix(),
        meta=meta,
        content=body,
        mtime=target.stat().st_mtime,
        done_boxes=sum(1 for b in boxes if b == "x"),
        total_boxes=len(boxes),
        siblings=siblings,
        links=links[:20],
    )


def _append_item_log(target, line):
    """Append a one-line entry to the file's ## Log section (created if absent)."""
    with EDIT_LOCK:
        body = target.read_text(encoding="utf-8", errors="replace").rstrip("\n")
        if "\n## Log" not in body and not body.startswith("## Log"):
            body += "\n\n## Log"
        body += f"\n{line}\n"
        _atomic_write_text(target, body)


@app.post("/api/work-item-memo")
def api_work_item_memo():
    data = request.get_json(silent=True) or {}
    rel = str(data.get("path", "") or "")
    text = _clean_item_text(data.get("text", ""), PROMPT_MAX)
    mode = data.get("mode", "memo")
    if not text:
        return jsonify(error="empty", message="내용을 입력하세요"), 400
    target = _vault_path(rel)
    if target.suffix != ".md":
        return jsonify(error="md_only", message=".md 파일만 지원합니다"), 400
    stamp = time.strftime("%Y-%m-%d %H:%M")
    one_line = text.replace("\n", " ")
    if mode == "ai":
        job_id, _err = _start_job(
            "item_request",
            {"path": target.relative_to(VAULT).as_posix(), "prompt": text},
            label=f"아이템 AI · {target.stem[:30]}",
        )
        _append_item_log(target, f"- {stamp} [AI요청] {one_line}")
        with WORK_LOCK:
            WORK_CACHE["ts"] = 0.0
        return jsonify(job_id=job_id, queued=_job_queued(job_id)), 202
    _append_item_log(target, f"- {stamp} [메모] {one_line}")
    with WORK_LOCK:
        WORK_CACHE["ts"] = 0.0
    return jsonify(ok=True)


# ---------------------------------------------------------------- queue watcher
# Background daemon: 07-Queue/*.md with `status: pending` front matter are
# handed to a non-interactive Claude job automatically. On success the file is
# marked processed and archived to 04-Archive/queue-processed/ (never
# deleted). On failure it is marked failed so it won't retry-loop.

QUEUE_TICK = 30
QUEUE_ACTIVE = {}                 # filename -> job_id (this process only)
QUEUE_ARCHIVE = VAULT / "04-Archive/queue-processed"
QUEUE_NAME_RE = re.compile(r"^[\w\-. ]+\.md$", re.UNICODE)
QUEUE_CONTENT_MAX = 8000


def _queue_set_status(path, status):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    except OSError:
        return
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                break
            if lines[i].startswith("status:"):
                lines[i] = f"status: {status}"
        try:
            path.write_text("\n".join(lines), encoding="utf-8")
        except OSError:
            pass


def _archive_queue_file(path):
    QUEUE_ARCHIVE.mkdir(parents=True, exist_ok=True)
    dest = QUEUE_ARCHIVE / path.name
    n = 2
    while dest.exists():
        dest = QUEUE_ARCHIVE / f"{path.stem}-{n}{path.suffix}"
        n += 1
    try:
        path.replace(dest)
    except OSError:
        pass


def _queue_tick():
    # 1) bookkeeping for jobs that finished
    for fname, job_id in list(QUEUE_ACTIVE.items()):
        with LOCK:
            job = JOBS.get(job_id)
            status = job["status"] if job else "failed"
        if status in ("queued", "pending", "running"):
            continue
        del QUEUE_ACTIVE[fname]
        path = QUEUE_DIR / fname
        if not path.is_file():
            continue
        if status == "success":
            _queue_set_status(path, "processed")
            _archive_queue_file(path)
        else:
            _queue_set_status(path, "failed")
    # 2) pick up the next pending file (one at a time)
    if QUEUE_ACTIVE or not QUEUE_DIR.is_dir():
        return
    for f in sorted(QUEUE_DIR.glob("*.md")):
        if not QUEUE_NAME_RE.match(f.name):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, _ = _parse_front_matter(text)
        # "processing" without an active job = stale from a restart → resume
        if meta.get("status") not in ("pending", "processing"):
            continue
        job_id, err = _start_job(
            "queue_process",
            {"path": f"07-Queue/{f.name}", "content": text[:QUEUE_CONTENT_MAX]},
            label=f"큐 처리 · {f.stem[:40]}",
        )
        if err == "dedup":   # same file already in flight — reattach watcher
            QUEUE_ACTIVE[f.name] = job_id
            return
        if err:              # retry next tick
            return
        _queue_set_status(f, "processing")
        QUEUE_ACTIVE[f.name] = job_id
        return


def _queue_loop():
    time.sleep(20)         # let the server settle first
    while True:
        try:
            _queue_tick()
        except Exception:
            pass
        time.sleep(QUEUE_TICK)


# ---------------------------------------------------------------- git snapshot
# "절대 지워지지 않게": hourly auto-snapshot of the whole vault.
# Runs in-process (launchd bash jobs hit TCC "Operation not permitted").
# Explicit exception to the no-auto-commit rule, approved 2026-07-16.

GIT_SNAPSHOT_SEC = 3600


def _git_snapshot():
    if not (VAULT / ".git").is_dir():
        return
    try:
        chk = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(VAULT), capture_output=True, text=True, timeout=60,
        )
        if chk.returncode != 0 or not chk.stdout.strip():
            return
        subprocess.run(["git", "add", "-A"], cwd=str(VAULT),
                       capture_output=True, timeout=120)
        subprocess.run(
            ["git", "commit", "-m",
             f"auto-snapshot {time.strftime('%Y-%m-%d %H:%M')}"],
            cwd=str(VAULT), capture_output=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


def _git_snapshot_loop():
    time.sleep(120)
    while True:
        try:
            _git_snapshot()
        except Exception:
            pass
        time.sleep(GIT_SNAPSHOT_SEC)


# ---------------------------------------------------------------- scheduler
# Replaces the broken launchd bash job (TCC "Operation not permitted").
# This python process already has vault access, so scheduling lives here.
# Catch-up semantics: if the Mac was asleep at the scheduled time, the job
# runs on the next tick after wake (once per day per task).

# Three daily passes (morning/midday/late-afternoon). Collection tasks
# (rss/reddit/x/morning_refresh) are AI-free — cheap, so they can run on
# every pass. granola_refresh (MCP-only, no AI-free path exists) and
# daily_brief actually spend AI quota, so their cadence is deliberately
# lighter (granola: morning+evening only; noon pass skips both collectors
# and granola — just an email check + a short midday brief).
DAILY_SLOTS = ["07:00", "12:00", "17:00"]
# task -> minute offset from the slot start. Staggered a few minutes apart
# so collectors/AI jobs don't all burst the provider at the same instant.
SLOT_TASKS = {
    "07:00": [("rss", 0), ("reddit", 1), ("x", 2),
              ("morning_refresh", 5), ("granola_refresh", 10),
              ("daily_brief", 30)],
    "12:00": [("morning_refresh", 0), ("daily_brief", 20)],
    "17:00": [("morning_refresh", 0), ("granola_refresh", 5),
              ("rss", 10), ("reddit", 11), ("x", 12),
              ("daily_brief", 30)],
}

SCHEDULE = []
for _slot, _tasks in SLOT_TASKS.items():
    _h, _m = (int(x) for x in _slot.split(":"))
    for _task, _offset in _tasks:
        _mm = _m + _offset
        SCHEDULE.append({
            "task": _task,
            "at": f"{_h + _mm // 60:02d}:{_mm % 60:02d}",
        })
del _slot, _tasks, _h, _m, _task, _offset, _mm
SCHEDULE.sort(key=lambda e: e["at"])

# morning_refresh is AI-free but still needs a live Gmail token,
# so it stays gated on the same readiness check as before.
# HIOS_ENABLE_GMAIL_AUTOMATION=0 remains an explicit kill switch.
if not (os.environ.get("HIOS_ENABLE_GMAIL_AUTOMATION") != "0"
        and _gmail_auth_ready()):
    SCHEDULE = [e for e in SCHEDULE if e["task"] != "morning_refresh"]


def _schedule_slot_key(task_id, at):
    return f"{task_id}@{at}"


# Soft cap on AI-flagged jobs the *scheduler itself* starts per day
# (daily_brief x3 + granola_refresh x2 leaves headroom to 6). Manual
# triggers — Harim doing actual work — are never counted or blocked here.
AI_SCHEDULE_DAILY_CAP = 6


def _scheduler_ai_budget_used(state, today):
    budget = state.get("_ai_budget")
    if not isinstance(budget, dict) or budget.get("date") != today:
        return 0
    try:
        return int(budget.get("count", 0))
    except (TypeError, ValueError):
        return 0


def _scheduler_loop():
    while True:
        try:
            today = time.strftime("%Y-%m-%d")
            hhmm = time.strftime("%H:%M")
            state = _read_json(SCHED_STATE_FILE, {})
            changed = False
            for entry in SCHEDULE:
                tid = entry["task"]
                slot_key = _schedule_slot_key(tid, entry["at"])
                if state.get(slot_key) == today or hhmm < entry["at"]:
                    continue
                if TASKS[tid].get("ai") and (
                        _scheduler_ai_budget_used(state, today) >= AI_SCHEDULE_DAILY_CAP):
                    print(f"[scheduler] {tid}@{entry['at']} 보류 — 하루 자동 AI 예산 "
                          f"{AI_SCHEDULE_DAILY_CAP}회 소진 (수동 트리거는 영향 없음)",
                          file=sys.stderr, flush=True)
                    continue
                job_id, err = _start_job(tid, {})
                # dedup/cooldown = an equivalent run already exists/just
                # succeeded — count this slot as satisfied.
                if err not in (None, "dedup", "cooldown"):
                    continue
                if err is None and TASKS[tid].get("ai"):
                    state["_ai_budget"] = {
                        "date": today,
                        "count": _scheduler_ai_budget_used(state, today) + 1,
                    }
                state[slot_key] = today
                changed = True
            if changed:
                _write_json(SCHED_STATE_FILE, state)
            # periodic dispatch so queued AI jobs resume within a minute
            # after an AI usage-limit hold expires.
            _dispatch()
        except Exception:
            print(f"[scheduler] tick error:\n{traceback.format_exc()}",
                  file=sys.stderr, flush=True)
        time.sleep(60)


@app.get("/api/schedule")
def api_schedule():
    state = _read_json(SCHED_STATE_FILE, {})
    today = time.strftime("%Y-%m-%d")
    return jsonify([
        {
            "task": e["task"],
            "label": TASKS[e["task"]]["label_ko"],
            "at": e["at"],
            "last_date": state.get(_schedule_slot_key(e["task"], e["at"])),
            "done_today": state.get(_schedule_slot_key(e["task"], e["at"])) == today,
        }
        for e in SCHEDULE
    ])

# ---------------------------------------------------------------- actions
# Human-input-required items surfaced as buttons/forms in the dashboard.
# kinds: "choice" (buttons) | "env" (secret form → .hios/.env) |
#        "text" (free input). choice/text responses land in 07-Queue/ as
# markdown so the next Claude session picks them up.

ACTIONS_LOCK = threading.Lock()
RESPONSE_MAX = 500


def _seed_actions():
    now = time.time()
    return [
        {
            "id": "tableau-0714",
            "title": "Tableau 세션 시간 선택 (7/14 화)",
            "desc": "'Meet the Makers: Composable Data Sources' 옵션이 캘린더에 12:00 / 19:00 두 개 있음. 선택하면 큐에 기록되고 다음 Claude 세션이 캘린더를 정리합니다.",
            "kind": "choice",
            "options": ["12:00 참석", "19:00 참석", "안 감"],
            "status": "pending",
            "created": now,
        },
        {
            "id": "reddit-keys",
            "title": "Reddit API 키 입력",
            "desc": "Reddit 수집기가 403으로 막혀 있음. reddit.com/prefs/apps에서 script 앱 생성 후 키를 입력하면 즉시 적용됩니다.",
            "kind": "env",
            "fields": [
                {"key": "REDDIT_CLIENT_ID", "label": "Client ID", "secret": False},
                {"key": "REDDIT_CLIENT_SECRET", "label": "Client Secret", "secret": True},
            ],
            "status": "pending",
            "created": now,
        },
        {
            "id": "x-token",
            "title": "X Bearer Token 입력",
            "desc": "Nitter 인스턴스 다운으로 X 수집 실패 중. developer.x.com에서 Bearer Token을 발급해 입력하면 API 모드로 자동 전환됩니다.",
            "kind": "env",
            "fields": [{"key": "X_BEARER_TOKEN", "label": "Bearer Token", "secret": True}],
            "status": "pending",
            "created": now,
        },
        {
            "id": "client-us",
            "title": "'유에스' 클라이언트 확인",
            "desc": "07-09에 언급한 신규 클라이언트가 미등록 상태. 정확한 기관명을 입력하면 프로젝트로 등록됩니다 (USAID? UNESCO?).",
            "kind": "text",
            "placeholder": "기관명 (예: USAID)",
            "status": "pending",
            "created": now,
        },
    ]


def _ensure_actions():
    if not ACTIONS_FILE.exists():
        _write_json(ACTIONS_FILE, _seed_actions())


def _clean_response(raw):
    clean = "".join(ch for ch in str(raw) if ch == "\n" or ch >= " ")
    return clean.strip()[:RESPONSE_MAX]


def _queue_action_response(action, response):
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    date = time.strftime("%Y-%m-%d")
    path = QUEUE_DIR / f"{date}-action-{action['id']}.md"
    path.write_text(
        "---\n"
        "type: action-response\n"
        f"action: {action['id']}\n"
        "status: pending\n"
        f"created: {date}\n"
        "tags: [queue, action]\n"
        "---\n\n"
        f"# {action['title']}\n\n"
        f"**응답**: {response}\n\n"
        f"HiOS Control Center에서 {time.strftime('%Y-%m-%d %H:%M')} 제출됨 — "
        "다음 Claude 세션이 처리합니다.\n",
        encoding="utf-8",
    )


# --- granola meeting filing: unclassified notes in 00-Inbox become
# clickable "choice" cards; picking a project moves the file into
# 01-Projects/<project>/02-Meetings/ immediately (no queue round-trip).

GRANOLA_ACTION_PREFIX = "granola-inbox-"
SAFE_INBOX_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\- ]*\.md$")


def _project_names():
    root = VAULT / "01-Projects"
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))


def _granola_inbox_actions():
    inbox = VAULT / "00-Inbox"
    projects = _project_names()
    if not inbox.is_dir() or not projects:
        return []
    cards = []
    for f in sorted(inbox.glob("*.md")):
        if not SAFE_INBOX_NAME.match(f.name):
            continue
        try:
            meta, _ = _parse_front_matter(f.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if meta.get("source") != "granola":
            continue
        cards.append({
            "id": GRANOLA_ACTION_PREFIX + f.name,
            "title": f"미팅 분류: {meta.get('title') or f.stem}",
            "desc": f"{meta.get('date', '날짜 미상')} 미팅 — 자동 분류 실패. 프로젝트를 클릭하면 02-Meetings로 즉시 이동합니다.",
            "kind": "choice",
            "options": projects,
            "status": "pending",
        })
    return cards


def _resolve_granola_filing(action_id, data):
    fname = action_id[len(GRANOLA_ACTION_PREFIX):]
    if not SAFE_INBOX_NAME.match(fname):
        abort(400)
    inbox = (VAULT / "00-Inbox").resolve()
    src = (inbox / fname).resolve()
    if src.parent != inbox or not src.is_file():
        abort(404)
    choice = data.get("choice")
    if choice not in _project_names():
        return jsonify(error="bad_choice"), 400
    text = src.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                break
            if lines[i].startswith("client:"):
                lines[i] = f"client: {choice}"
            elif lines[i].startswith("status:"):
                lines[i] = "status: filed"
        text = "\n".join(lines)
    dest_dir = VAULT / "01-Projects" / choice / "02-Meetings"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / fname
    n = 2
    while dest.exists():
        dest = dest_dir / f"{src.stem}-{n}.md"
        n += 1
    dest.write_text(text, encoding="utf-8")
    src.unlink()
    return jsonify(ok=True, result=f"{choice} ← {dest.name}")


@app.get("/api/actions")
def api_actions():
    with ACTIONS_LOCK:
        _ensure_actions()
        actions = _read_json(ACTIONS_FILE, [])
    actions = actions + _granola_inbox_actions()
    public = []
    for a in actions:
        item = {k: a[k] for k in ("id", "title", "desc", "kind", "status") if k in a}
        if a["kind"] == "choice":
            item["options"] = a.get("options", [])
        if a["kind"] == "env":
            item["fields"] = a.get("fields", [])
        if a["kind"] == "text":
            item["placeholder"] = a.get("placeholder", "")
        if a.get("result"):
            item["result"] = a["result"]
        public.append(item)
    return jsonify(public)


@app.post("/api/actions/<action_id>/resolve")
def api_action_resolve(action_id):
    data = request.get_json(silent=True) or {}
    if action_id.startswith(GRANOLA_ACTION_PREFIX):
        with ACTIONS_LOCK:
            return _resolve_granola_filing(action_id, data)
    with ACTIONS_LOCK:
        _ensure_actions()
        actions = _read_json(ACTIONS_FILE, [])
        action = next((a for a in actions if a["id"] == action_id), None)
        if not action:
            abort(404)
        if action["status"] != "pending":
            return jsonify(error="already_resolved"), 409

        if action["kind"] == "env":
            allowed = {f["key"] for f in action.get("fields", [])} & ENV_KEYS
            values = {}
            for k, v in (data.get("values") or {}).items():
                if k not in allowed:
                    return jsonify(error="bad_key", message=f"허용되지 않은 키: {k}"), 400
                v = re.sub(r"[\r\n\"'#\s]", "", str(v))[:RESPONSE_MAX]
                if v:
                    values[k] = v
            if set(values) != allowed:
                return jsonify(error="missing", message="모든 값을 입력하세요"), 400
            _save_env(values)
            action["result"] = "저장됨 (.hios/.env)"
        elif action["kind"] == "choice":
            choice = data.get("choice")
            if choice not in action.get("options", []):
                return jsonify(error="bad_choice"), 400
            _queue_action_response(action, choice)
            action["result"] = choice
        elif action["kind"] == "text":
            text = _clean_response(data.get("text", ""))
            if not text:
                return jsonify(error="empty"), 400
            _queue_action_response(action, text)
            action["result"] = text
        else:
            action["result"] = "확인됨"

        action["status"] = "resolved"
        action["resolved"] = time.time()
        _write_json(ACTIONS_FILE, actions)
    return jsonify(ok=True, result=action["result"])

# ---------------------------------------------------------------- uploads
# Dropzone uploads → AI auto-filing.
# Architecture: files land in a staging dir INSIDE the vault
# (00-Inbox/uploads/<stamp>-<id>/), a read-only Claude job emits a JSON
# manifest, then the server performs the actual moves (Claude never writes;
# binary moves via Write are impossible and Bash would break the scoped-job
# security model). Manifest failure degrades safely: files stay in staging —
# which already lives in the Inbox — and can be re-filed manually.

UPLOADS_FILE = STATE_DIR / "uploads.json"
UPLOADS_LOCK = threading.Lock()
UPLOAD_STAGING = VAULT / "00-Inbox/uploads"
UPLOAD_FILE_MAX = 50 * 1024 * 1024          # per file
UPLOAD_BATCH_MAX = 200 * 1024 * 1024        # per batch
UPLOAD_COUNT_MAX = 50
UPLOAD_BATCH_KEEP = 20
UPLOAD_DENY_EXTS = {".app", ".exe", ".sh", ".command", ".dmg", ".pkg"}
UPLOAD_DEST_TOPS = {"00-Inbox", "01-Projects", "02-Areas", "03-Resources",
                    "05-AI", "06-Entities"}
UPLOAD_UNSORTED = "00-Inbox/unsorted"

# hard cap on the multipart body itself (batch max + form overhead slack)
app.config["MAX_CONTENT_LENGTH"] = UPLOAD_BATCH_MAX + 16 * 1024 * 1024


class _UploadRejected(Exception):
    pass


def _load_upload_batches():
    data = _read_json(UPLOADS_FILE, {"batches": []})
    batches = data.get("batches") if isinstance(data, dict) else []
    return batches if isinstance(batches, list) else []


def _save_upload_batches(batches):
    _write_json(UPLOADS_FILE, {"batches": batches[-UPLOAD_BATCH_KEEP:]})


def _sanitize_upload_name(raw):
    name = os.path.basename(str(raw or "").replace("\\", "/"))
    name = unicodedata.normalize("NFC", name)      # 한글 자모 결합 (macOS NFD)
    name = "".join(ch for ch in name if ch >= " " and ch != "\x7f")
    name = name.lstrip(".")
    name = re.sub(r"[^\w\-. ()가-힣]", "_", name, flags=re.UNICODE)
    name = name.strip()[:120]
    return name or "file"


def _unique_in_set(existing, name):
    if name not in existing:
        return name
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    n = 2
    while True:
        cand = f"{stem}-{n}.{ext}" if dot else f"{stem}-{n}"
        if cand not in existing:
            return cand
        n += 1


def _upload_dest_valid(dest):
    """Validate a manifest destination directory. Returns clean rel path or None."""
    dest = str(dest or "").strip().strip("/")
    if not dest or "\\" in dest or "\x00" in dest:
        return None
    segs = dest.split("/")
    if len(segs) > 4:
        return None
    for seg in segs:
        if not seg or seg.startswith(".") or seg != seg.strip():
            return None
    if segs[0] not in UPLOAD_DEST_TOPS:
        return None
    if segs[0] == "01-Projects" and (len(segs) < 2 or segs[1] not in _project_names()):
        return None
    if not (VAULT / dest).resolve().is_relative_to(VAULT.resolve()):
        return None
    return dest


def _upload_move(src, dest_dir_rel):
    """Move a staged file into the vault; collision-safe with -2 suffix."""
    dest_dir = VAULT / dest_dir_rel
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    n = 2
    while dest.exists():
        dest = dest_dir / f"{src.stem}-{n}{src.suffix}"
        n += 1
    shutil.move(str(src), str(dest))
    return dest


def _upload_classify_prompt(p):
    listing = "\n".join(f"- {f['name']} ({f.get('size', 0)} bytes)" for f in p["files"])
    projects = _project_names()
    project = p.get("project") or ""
    if project:
        scope = (
            f"이 배치는 프로젝트 '{project}' 전용 업로드입니다. 모든 파일의 dest는 "
            f"반드시 01-Projects/{project}/<서브폴더> 형식이어야 합니다 — 다른 "
            "프로젝트나 다른 상위 폴더로 절대 보내지 마세요. doc_updates도 "
            f"{project}에만 제안하세요.\n"
        )
    else:
        scope = (
            f"프로젝트는 반드시 이 실제 폴더명 중에서만 고르세요: {', '.join(projects)}\n"
            "키워드 힌트: UNFPA/CSE→UNFPA-CSE · 보험/fraud/theft→Equitee · "
            "BCM/Moodle/Articulate→WMO · energy/HCF/SDG7→WHO · AICA→Climate-AICA · "
            "유튜브/콘텐츠/샤오홍슈→Visual-Climate\n"
            f"어느 프로젝트/영역인지 알 수 없으면 dest를 \"{UPLOAD_UNSORTED}\"로 하세요.\n"
        )
    return (
        "업로드된 파일들을 분류하세요. 읽기 전용 작업입니다 — 파일 이동/수정/생성은 "
        "서버가 수행하므로 절대 파일을 만들거나 바꾸려 하지 마세요.\n\n"
        f"스테이징 폴더: {p['staging']}/\n"
        f"파일 목록:\n{listing}\n\n"
        "md/txt/csv 등 텍스트 파일과 pdf는 Read 도구로 내용을 확인하세요. "
        "xlsx/docx/이미지처럼 읽을 수 없는 파일은 파일명과 같은 배치의 다른 파일 "
        "맥락으로 추정하세요.\n\n"
        + scope +
        "서브폴더 규칙: 일반 문서→06-Documents, 회의록→02-Meetings, "
        "참고자료→05-References, 산출물→01-Deliverables, 불확실하면→06-Documents\n\n"
        "추가로: 파일이 특정 프로젝트로 분류되면 그 프로젝트의 _RESOURCES.md, _STATUS.md, "
        "_TODO.md를 Read로 읽어보고, 이번 파일들을 반영해 갱신할 가치가 있는 문서에 "
        "추가할 줄들을 제안하세요 (doc_updates). 판단 기준:\n"
        "- _RESOURCES.md: 새 참고자료/문서 목록 — 보통 항상 추가. 형식: "
        "'- [파일명](vault 상대경로) — 한 줄 설명 (업로드 M/D)'\n"
        "- _STATUS.md: 이번 자료가 프로젝트 진행에 의미 있을 때만 한 줄.\n"
        "- _TODO.md: 자료에서 명확한 할 일이 보일 때만 '- [ ] ...' 형식.\n"
        "기존 문서의 톤/구조에 맞추고, 이미 있는 내용과 중복되면 넣지 마세요. "
        "직접 수정하지 말 것 — 서버가 append만 수행합니다.\n\n"
        "답변 마지막에 코드펜스 없이 JSON 객체 하나만 출력하세요:\n"
        '{"files":[{"name":"파일명","dest":"01-Projects/<프로젝트>/<서브폴더>",'
        '"project":"프로젝트명 (미상이면 빈 문자열)","kind":"document|meeting|reference|deliverable|unknown",'
        '"label":"짧은 라벨","summary":"\'이건 ~할 때 쓰는 것\' 형식의 한 문장"}],'
        '"doc_updates":[{"project":"프로젝트명","file":"_RESOURCES.md|_STATUS.md|_TODO.md",'
        '"section":"## 섹션 제목 (기존 섹션이면 그 제목 그대로)","lines":["추가할 줄"]}]}\n'
    )


DOC_UPDATE_FILES = {"_RESOURCES.md", "_STATUS.md", "_TODO.md"}
DOC_UPDATE_MAX_LINES = 20


def _append_doc_section(path, section, lines):
    """Append lines under a heading (append-only; creates file/section if missing)."""
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    rows = text.splitlines()
    for i, row in enumerate(rows):
        if row.strip() != section:
            continue
        # end of this section = next heading or EOF
        j = i + 1
        while j < len(rows) and not rows[j].lstrip().startswith("#"):
            j += 1
        # insert before the section's trailing blank lines
        k = j
        while k > i + 1 and not rows[k - 1].strip():
            k -= 1
        new_rows = rows[:k] + lines + rows[k:]
        _atomic_write_text(path, "\n".join(new_rows).rstrip("\n") + "\n")
        return
    body = text.rstrip("\n")
    block = ("\n\n" if body else "") + section + "\n\n" + "\n".join(lines) + "\n"
    _atomic_write_text(path, body + block)


def _apply_doc_updates(manifest, filed_projects):
    """Apply AI-proposed appends to project meta docs. Returns audit lines."""
    audit = []
    updates = manifest.get("doc_updates")
    if not isinstance(updates, list):
        return audit
    projects = set(_project_names())
    for u in updates[:10]:
        if not isinstance(u, dict):
            continue
        project = str(u.get("project", "") or "")
        fname = str(u.get("file", "") or "")
        section = _clean_item_text(u.get("section", ""), 80)
        raw_lines = u.get("lines")
        if (project not in projects or project not in filed_projects
                or fname not in DOC_UPDATE_FILES
                or not section.startswith("#")
                or not isinstance(raw_lines, list)):
            continue
        lines = [_clean_item_text(l, 500).replace("\n", " ")
                 for l in raw_lines[:DOC_UPDATE_MAX_LINES]
                 if isinstance(l, str) and l.strip()]
        if not lines:
            continue
        path = VAULT / "01-Projects" / project / fname
        try:
            _append_doc_section(path, section, lines)
            audit.append(f"[시스템] {project}/{fname} 업데이트 ({len(lines)}줄)")
        except OSError as exc:
            audit.append(f"[시스템] {project}/{fname} 업데이트 실패: {exc}")
    return audit


def _upload_classify_finalize(job, params):
    """Post-job hook: parse the JSON manifest and move files server-side."""
    bid = params.get("batch_id")
    with LOCK:
        status = job["status"]
        text = "\n".join(job["log"])
    manifest = None
    if status == "success":
        idx = text.rfind('{"files"')
        if idx >= 0:
            try:
                manifest, _ = json.JSONDecoder().raw_decode(text[idx:])
            except ValueError:
                manifest = None
    audit = []
    filed_projects = set()
    with UPLOADS_LOCK:
        batches = _load_upload_batches()
        batch = next((b for b in batches if b.get("id") == bid), None)
        if batch is None:
            return
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
            batch["status"] = "failed"
            _save_upload_batches(batches)
            audit.append("[시스템] 분류 manifest 파싱 실패 — 파일은 스테이징에 유지됨")
        else:
            by_name = {}
            for entry in manifest["files"]:
                if isinstance(entry, dict) and entry.get("name"):
                    by_name[str(entry["name"])] = entry
            staging = VAULT / batch["staging"]
            b_project = batch.get("project") or ""
            for rec in batch["files"]:
                if rec.get("status") == "filed":
                    continue
                entry = by_name.get(rec["name"], {})
                dest_rel = _upload_dest_valid(entry.get("dest")) or UPLOAD_UNSORTED
                if b_project and not (dest_rel == f"01-Projects/{b_project}"
                                      or dest_rel.startswith(f"01-Projects/{b_project}/")):
                    # project-scoped batch: never allow filing outside the project
                    dest_rel = f"01-Projects/{b_project}/06-Documents"
                rec["project"] = b_project or _clean_item_text(entry.get("project", ""), 80)
                rec["kind"] = _clean_item_text(entry.get("kind", ""), 40)
                rec["label"] = _clean_item_text(entry.get("label", ""), 120)
                rec["summary"] = _clean_item_text(entry.get("summary", ""), 300)
                src = staging / rec["name"]
                try:
                    if not src.is_file():
                        raise OSError("스테이징에 파일 없음")
                    moved = _upload_move(src, dest_rel)
                    rec["status"] = "filed"
                    rec["dest"] = moved.relative_to(VAULT).as_posix()
                    if rec["dest"].startswith("01-Projects/"):
                        filed_projects.add(rec["dest"].split("/")[1])
                    audit.append(f"[시스템] {rec['name']} → {rec['dest']}")
                except OSError as exc:
                    rec["status"] = "failed"
                    audit.append(f"[시스템] {rec['name']} 이동 실패: {exc}")
            batch["status"] = "filed"
            _save_upload_batches(batches)
            try:
                staging.rmdir()          # only removes if empty
            except OSError:
                pass
    if isinstance(manifest, dict) and filed_projects:
        audit.extend(_apply_doc_updates(manifest, filed_projects))
    with LOCK:
        for line in audit:
            _append_log(job, line)


TASKS["upload_classify"] = {
    "label_ko": "업로드 분류",
    "category": "AI",
    "groups": {"ai"},
    "ai": True,
    "timeout": AI_TIMEOUT,
    "heartbeat": True,
    "internal": True,   # started only via /api/upload(s)
    "argv": lambda p: _claude_argv(),
    "stdin": _upload_classify_prompt,
    "finalize": _upload_classify_finalize,
}


def _start_batch_classify(bid):
    """Kick off the classify job for a batch. Returns (job_id, err_message)."""
    with UPLOADS_LOCK:
        batches = _load_upload_batches()
        batch = next((b for b in batches if b.get("id") == bid), None)
        if batch is None:
            return None, "배치를 찾을 수 없습니다"
        if batch["status"] == "classifying":
            return None, "이미 분류 중"
        pending = [r for r in batch["files"] if r.get("status") != "filed"]
        if not pending:
            return None, "모든 파일이 이미 분류되었습니다"
        params = {
            "batch_id": bid,
            "staging": batch["staging"],
            "project": batch.get("project", ""),
            "files": [{"name": r["name"], "size": r.get("size", 0)} for r in pending],
        }
    job_id, err = _start_job(
        "upload_classify", params, label=f"업로드 분류 · {len(pending)}개")
    if err:
        return None, err
    with UPLOADS_LOCK:
        batches = _load_upload_batches()
        batch = next((b for b in batches if b.get("id") == bid), None)
        if batch is not None:
            batch["status"] = "classifying"
            batch["job_id"] = job_id
            _save_upload_batches(batches)
    return job_id, None


def _reset_stale_upload_batches():
    """Boot-time: a batch stuck in 'classifying' means the server died mid-job."""
    with UPLOADS_LOCK:
        batches = _load_upload_batches()
        changed = False
        for b in batches:
            if b.get("status") == "classifying":
                b["status"] = "staged"
                changed = True
        if changed:
            _save_upload_batches(batches)


@app.post("/api/upload")
def api_upload():
    files = request.files.getlist("files")
    if not files:
        return jsonify(error="empty", message="파일이 없습니다"), 400
    if len(files) > UPLOAD_COUNT_MAX:
        return jsonify(error="too_many",
                       message=f"한 번에 최대 {UPLOAD_COUNT_MAX}개까지"), 413
    project = str(request.form.get("project", "") or "").strip()
    if project and project not in _project_names():
        return jsonify(error="bad_project", message="알 수 없는 프로젝트"), 400
    batch_id = uuid.uuid4().hex[:8]
    staging = UPLOAD_STAGING / f"{time.strftime('%Y-%m-%d-%H%M')}-{batch_id[:4]}"
    staging.mkdir(parents=True, exist_ok=True)
    records, names, total = [], set(), 0
    try:
        for f in files:
            name = _sanitize_upload_name(f.filename)
            if Path(name).suffix.lower() in UPLOAD_DENY_EXTS:
                raise _UploadRejected(f"허용되지 않는 파일 형식: {name}")
            name = _unique_in_set(names, name)
            names.add(name)
            dest = staging / name
            f.save(str(dest))
            size = dest.stat().st_size
            total += size
            if size > UPLOAD_FILE_MAX:
                raise _UploadRejected(f"파일당 50MB 초과: {name}")
            if total > UPLOAD_BATCH_MAX:
                raise _UploadRejected("배치 합계 200MB 초과")
            records.append({
                "name": name,
                "orig_name": _clean_item_text(f.filename or "", 200),
                "size": size,
                "path": f"{staging.relative_to(VAULT).as_posix()}/{name}",
                "status": "staged",
                "dest": "", "project": "", "kind": "", "label": "", "summary": "",
            })
    except _UploadRejected as exc:
        shutil.rmtree(staging, ignore_errors=True)
        return jsonify(error="rejected", message=str(exc)), 413
    except OSError as exc:
        shutil.rmtree(staging, ignore_errors=True)
        return jsonify(error="save_failed", message=str(exc)), 500

    batch = {
        "id": batch_id,
        "created": time.time(),
        "staging": staging.relative_to(VAULT).as_posix(),
        "status": "staged",
        "project": project,
        "job_id": None,
        "files": records,
    }
    with UPLOADS_LOCK:
        batches = _load_upload_batches()
        batches.append(batch)
        _save_upload_batches(batches)
    job_id, err = _start_batch_classify(batch_id)
    return jsonify(
        batch_id=batch_id,
        count=len(records),
        job_id=job_id,
        conflict=bool(err),
        message=err,
    ), 202


@app.get("/api/uploads")
def api_uploads():
    with UPLOADS_LOCK:
        batches = _load_upload_batches()
    return jsonify(list(reversed(batches)))


@app.post("/api/uploads/<bid>/classify")
def api_upload_classify(bid):
    job_id, err = _start_batch_classify(bid)
    if err:
        return jsonify(error="conflict", message=err), 409
    return jsonify(job_id=job_id), 202


@app.post("/api/uploads/<bid>/reclassify")
def api_upload_reclassify(bid):
    """Manual re-file of one uploaded file — same validation as auto-filing."""
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "") or "")
    dest_rel = _upload_dest_valid(data.get("dest"))
    if not dest_rel:
        return jsonify(error="bad_dest", message="허용되지 않는 목적지"), 400
    with UPLOADS_LOCK:
        batches = _load_upload_batches()
        batch = next((b for b in batches if b.get("id") == bid), None)
        if batch is None:
            abort(404)
        rec = next((r for r in batch["files"] if r.get("name") == name), None)
        if rec is None:
            abort(404)
        if rec.get("status") == "filed" and rec.get("dest"):
            src = VAULT / rec["dest"]
            if not src.resolve().is_relative_to(VAULT.resolve()):
                abort(400)
        else:
            src = VAULT / batch["staging"] / rec["name"]
        if not src.is_file():
            return jsonify(error="missing", message="원본 파일을 찾을 수 없습니다"), 404
        try:
            moved = _upload_move(src, dest_rel)
        except OSError as exc:
            return jsonify(error="move_failed", message=str(exc)), 500
        rec["status"] = "filed"
        rec["dest"] = moved.relative_to(VAULT).as_posix()
        _save_upload_batches(batches)
        new_dest = rec["dest"]
    return jsonify(ok=True, dest=new_dest)


# ------------------------------------------------------- Granola + Gmail sync
# Granola and Gmail are separate jobs so one connector failure never hides or
# blocks the other. Their manifests are parsed and persisted by the server.

EMAILS_FILE = STATE_DIR / "emails.json"
EMAIL_SEEN_FILE = STATE_DIR / "email_actions_seen.json"
EMAIL_DELTA_FILE = STATE_DIR / "email_delta.json"
GRANOLA_STATE_FILE = STATE_DIR / "granola.json"
GRANOLA_ACTION_SEEN_FILE = STATE_DIR / "granola_actions_seen.json"
EMAILS_LOCK = threading.Lock()
GRANOLA_STATE_LOCK = threading.Lock()

GMAIL_API_ROOT = "https://gmail.googleapis.com/gmail/v1/users/me"
GMAIL_LOOKBACK_DAYS = 10
GMAIL_CANDIDATE_MAX = 200
GMAIL_PROJECT_MAX = 100
GMAIL_OTHER_PROJECT = "기타"


def _gmail_project_queries():
    """Project-first Gmail queries, with the same bounded lookback for all."""
    base = f"in:anywhere newer_than:{GMAIL_LOOKBACK_DAYS}d -in:sent -in:drafts"
    return {
        "Climate-AICA": (
            f'{base} {{"Climate-AICA" AICA "climate data literacy" "AICA Award"}}'
        ),
        "Equitee": (
            f'{base} {{from:(equiteco.ca) Equite Equitee "Équité" '
            '"fraud dashboard" "Power BI" Shift "auto theft"}'
        ),
        "UNFPA-CSE": (
            f'{base} {{from:(unfpa.org) to:(unfpa.org) "Data and Knowledge CSE" '
            '"Wafa Dhaouadi" "Steve Petite" "CSE Global Program"}'
        ),
        "Visual-Climate": (
            f'{base} {{from:(visualclimate.org) to:(visualclimate.org) "Visual Climate" '
            'girleffect EvidenceAction "Invoice.ODC@onx.com"}'
        ),
        "WHO": (
            f'{base} {{from:(who.int) to:(who.int) adairrohanih vincis yew '
            '"Health and Energy" "household energy" "HCF electrification" WIMS}'
        ),
        "WMO": (
            f'{base} {{from:(wmo.int) to:(wmo.int) WMO BCM Moodle Articulate '
            '"training module" "course review" "validation workshop" Xiao '
            '"Zhang Di" Mustafa Lu}'
        ),
    }


def _json_http_request(req, timeout=30):
    """Return decoded JSON while keeping OAuth tokens out of error messages."""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        message = ""
        try:
            payload = json.loads(raw)
            detail = payload.get("error")
            message = detail.get("message", "") if isinstance(detail, dict) else str(detail or "")
        except ValueError:
            pass
        safe = _clean_item_text(message or exc.reason or "요청 실패", 240)
        raise RuntimeError(f"Google API HTTP {exc.code}: {safe}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Google API 연결 실패: {_clean_item_text(exc, 240)}") from None
    try:
        payload = json.loads(raw)
    except ValueError:
        raise RuntimeError("Google API가 올바른 JSON을 반환하지 않음") from None
    if not isinstance(payload, dict):
        raise RuntimeError("Google API 응답 형식 오류")
    return payload


def _gmail_access_token():
    """Exchange the encrypted GWS refresh credential for a short-lived token."""
    try:
        proc = subprocess.run(
            [GWS_BIN, "auth", "export", "--unmasked"],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Gmail 인증정보 읽기 실패: {_clean_item_text(exc, 200)}") from None
    if proc.returncode != 0:
        detail = _clean_item_text(proc.stderr or proc.stdout or "gws auth export 실패", 240)
        raise RuntimeError(f"Gmail 인증정보 읽기 실패: {detail}")
    try:
        creds = json.loads(proc.stdout)
    except ValueError:
        raise RuntimeError("Gmail 인증정보 형식 오류") from None
    required = ("client_id", "client_secret", "refresh_token")
    if not isinstance(creds, dict) or any(not creds.get(key) for key in required):
        raise RuntimeError("Gmail 재로그인 필요")
    form = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token",
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    token = _json_http_request(req)
    access_token = token.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise RuntimeError("Gmail access token 발급 실패")
    return access_token


def _gmail_api_get(access_token, resource, params):
    query = urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(
        f"{GMAIL_API_ROOT}/{resource}?{query}",
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    return _json_http_request(req)


def _gmail_list_stubs(access_token, query, limit):
    stubs = []
    page_token = None
    while len(stubs) < limit:
        params = {
            "maxResults": min(500, limit - len(stubs)),
            "q": query,
        }
        if page_token:
            params["pageToken"] = page_token
        payload = _gmail_api_get(access_token, "messages", params)
        page = payload.get("messages", [])
        if not isinstance(page, list):
            raise RuntimeError("Gmail messages.list 응답 형식 오류")
        stubs.extend(item for item in page if isinstance(item, dict) and item.get("id"))
        page_token = payload.get("nextPageToken")
        if not page_token or not page:
            break
    return stubs[:limit]


def _gmail_message_candidate(access_token, stub):
    message_id = str(stub.get("id", ""))
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", message_id):
        raise RuntimeError("Gmail message id 형식 오류")
    payload = _gmail_api_get(access_token, f"messages/{message_id}", {
        "format": "metadata",
        "metadataHeaders": ["From", "To", "Subject", "Date"],
    })
    raw_headers = payload.get("payload", {}).get("headers", [])
    headers = {}
    if isinstance(raw_headers, list):
        for item in raw_headers:
            if isinstance(item, dict):
                name = str(item.get("name", "")).lower()
                if name and name not in headers:
                    headers[name] = str(item.get("value", ""))
    try:
        stamp = int(payload.get("internalDate", 0)) / 1000
        date = time.strftime("%Y-%m-%d", time.localtime(stamp)) if stamp > 0 else ""
    except (TypeError, ValueError, OverflowError):
        date = ""
    return {
        "message_id": message_id,
        "thread_id": _clean_item_text(payload.get("threadId") or stub.get("threadId"), 120),
        "date": date,
        "from": _clean_item_text(headers.get("from", ""), 240),
        "to": _clean_item_text(headers.get("to", ""), 240),
        "subject": _clean_item_text(headers.get("subject", ""), 300),
        "snippet": _clean_item_text(html.unescape(str(payload.get("snippet", ""))), 700),
    }


def _gmail_collect_snapshot():
    """Fetch each project's mail first, then fill gaps from recent incoming."""
    access_token = _gmail_access_token()
    broad_query = (
        f"in:anywhere newer_than:{GMAIL_LOOKBACK_DAYS}d -in:sent -in:drafts"
    )
    project_queries = _gmail_project_queries()
    combined = []
    seen = set()
    searches = [
        (project, query, GMAIL_PROJECT_MAX)
        for project, query in project_queries.items()
    ] + [("기타-보완", broad_query, GMAIL_CANDIDATE_MAX)]
    for source, query, limit in searches:
        for stub in _gmail_list_stubs(access_token, query, limit):
            message_id = str(stub.get("id", ""))
            if not message_id or message_id in seen:
                continue
            seen.add(message_id)
            row = dict(stub)
            row["source_query"] = source
            combined.append(row)

    def fetch(stub):
        candidate = _gmail_message_candidate(access_token, stub)
        candidate["source_query"] = stub.get("source_query", "recent")
        return candidate

    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            candidates = list(pool.map(fetch, combined))
    except Exception as exc:
        raise RuntimeError(f"Gmail 메시지 상세 조회 실패: {_clean_item_text(exc, 240)}") from None
    candidates.sort(key=lambda row: (row.get("date", ""), row.get("message_id", "")), reverse=True)
    return {
        "connection": {"status": "ok", "error": None},
        "queries": {**project_queries, "기타-보완": broad_query},
        "candidates": candidates,
        "candidate_count": len(candidates),
    }



def _extract_granola_manifest(text):
    decoder = json.JSONDecoder()
    found = None
    for match in re.finditer(r"\{", text or ""):
        try:
            candidate, _ = decoder.raw_decode(text[match.start():])
        except ValueError:
            continue
        if (isinstance(candidate, dict)
                and isinstance(candidate.get("connection"), dict)
                and "meetings_seen" in candidate):
            found = candidate
    return found


def _manifest_count(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


GRANOLA_ACTION_SEEN_MAX = 2000


def _granola_action_key(action):
    raw = "|".join((
        str(action.get("granola_id", "")),
        str(action.get("project", "")),
        str(action.get("title", "")),
    ))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]


def _granola_create_actions(actions):
    """Create project action-board items from Granola, idempotently."""
    if not isinstance(actions, list):
        return 0
    with GRANOLA_STATE_LOCK:
        raw_seen = _read_json(GRANOLA_ACTION_SEEN_FILE, [])
        seen = set(raw_seen) if isinstance(raw_seen, list) else set()
    valid_projects = set(_project_names())
    by_project = {}
    pending_keys = set()
    for action in actions[:500]:
        if not isinstance(action, dict):
            continue
        project = str(action.get("project", "") or "")
        title = _clean_item_text(action.get("title", ""), 300)
        granola_id = _clean_item_text(action.get("granola_id", ""), 160)
        if project not in valid_projects or not title or not granola_id:
            continue
        key = _granola_action_key({
            "granola_id": granola_id, "project": project, "title": title,
        })
        if key in seen or key in pending_keys:
            continue
        due = _clean_item_text(action.get("due", ""), 20)
        if due and not DATE_RE.fullmatch(due):
            due = ""
        by_project.setdefault(project, []).append((key, {
            "title": title,
            "detail": _clean_item_text(action.get("detail", ""), 1000),
            "due": due,
            "people": _clean_people(action.get("people")),
            "granola_id": granola_id,
            "note_path": _clean_item_text(action.get("note_path", ""), 500),
        }))
        pending_keys.add(key)

    created = 0
    today = time.strftime("%Y-%m-%d")
    with ITEMS_LOCK:
        for project, group in by_project.items():
            proj = PROJECTS_DIR / project
            items = _load_items(proj)
            for key, action in group:
                items.append({
                    "id": uuid.uuid4().hex[:8],
                    "title": _clean_item_text("[미팅] " + action["title"], 300),
                    "detail": action["detail"],
                    "status": "open",
                    "priority": "med",
                    "due": action["due"],
                    "people": action["people"],
                    "sources": [{
                        "kind": "granola",
                        "label": action["note_path"] or "Granola 회의록",
                        "url": "",
                    }],
                    "note": f"granola_id: {action['granola_id']}",
                    "created": today,
                    "updated": today,
                })
                seen.add(key)
                created += 1
            _write_json(_items_file(proj), items)
    with GRANOLA_STATE_LOCK:
        _write_json(GRANOLA_ACTION_SEEN_FILE, sorted(seen)[-GRANOLA_ACTION_SEEN_MAX:])
    return created


def _granola_refresh_finalize(job, params):
    with LOCK:
        status = job["status"]
        text = "\n".join(job["log"])
    manifest = _extract_granola_manifest(text) if status == "success" else None
    connection = manifest.get("connection") if isinstance(manifest, dict) else {}
    ok = status == "success" and connection.get("status") == "ok"
    now = time.time()
    error = None if ok else _clean_item_text(
        connection.get("error") or f"작업 실패 (상태: {status})", 300
    )
    actions_created = 0
    actions_error = None
    if ok:
        try:
            actions_created = _granola_create_actions(manifest.get("actions", []))
        except Exception as exc:
            actions_error = _clean_item_text(exc, 240)
    with GRANOLA_STATE_LOCK:
        previous = _read_json(GRANOLA_STATE_FILE, {})
        if not isinstance(previous, dict):
            previous = {}
        state = {
            "last_status": "ok" if ok else "error",
            "last_error": error,
            "last_attempt": now,
            "last_success": now if ok else previous.get("last_success"),
            "meetings_seen": _manifest_count(manifest.get("meetings_seen")) if ok else 0,
            "meetings_created": _manifest_count(manifest.get("meetings_created")) if ok else 0,
            "actions_created": actions_created,
            "actions_error": actions_error,
        }
        _write_json(GRANOLA_STATE_FILE, state)
    with LOCK:
        if ok:
            _append_log(
                job,
                f"[시스템] Granola 동기화 완료 — 조회 {state['meetings_seen']}건, "
                f"신규 {state['meetings_created']}건, 액션 {actions_created}건",
            )
            if actions_error:
                _append_log(job, f"[시스템] Granola 액션 반영 실패 — {actions_error}")
        else:
            _append_log(job, f"[시스템] Granola 동기화 실패 — {error}")


TASKS["granola_refresh"] = {
    "label_ko": "Granola 동기화",
    "category": "동기화",
    # AI-free via the official public-api.granola.ai (Bearer token) —
    # mcp.granola.ai requires interactive browser OAuth per user and simply
    # cannot authenticate from a headless server session, no matter the
    # allowedTools/CLI-version tweak. Same rationale as morning_refresh.
    "groups": {"collectors"},
    "ai": False,
    "cooldown": 900,
    "timeout": 300,
    "heartbeat": False,
    "refresh": "projects",
    "argv": lambda p: [PYTHON_BIN, str(HIOS_SCRIPTS / "granola_api_sync.py")],
    "finalize": _granola_refresh_finalize,
}


def _email_set_hash(emails):
    """Stable fingerprint of a project's collected email set (order-free)."""
    keys = sorted(f"{e.get('thread_id', '')}|{e.get('date', '')}" for e in emails)
    return hashlib.sha1("\n".join(keys).encode("utf-8")).hexdigest()[:16]


EMAILS_MAX = GMAIL_CANDIDATE_MAX + 6 * GMAIL_PROJECT_MAX
EMAILS_PER_PROJECT = 15
EMAIL_SEEN_MAX = 1000
THREAD_ID_RE = re.compile(r"^[\w.:\-]{1,60}$")


def _morning_refresh_snapshot_stdin(p):
    """Feed the raw Gmail snapshot to the AI-free classifier (email_classify.py)
    over stdin — no natural-language prompt needed, no AI involved."""
    try:
        snapshot = _gmail_collect_snapshot()
    except Exception as exc:
        snapshot = {
            "connection": {
                "status": "error",
                "error": _clean_item_text(exc, 300),
            },
            "queries": {},
            "candidates": [],
            "candidate_count": 0,
        }
    return json.dumps(snapshot, ensure_ascii=False)


def _extract_email_manifest(text):
    """Return the last JSON object containing an email manifest, any key order."""
    decoder = json.JSONDecoder()
    found = None
    for match in re.finditer(r"\{", text or ""):
        try:
            candidate, _ = decoder.raw_decode(text[match.start():])
        except ValueError:
            continue
        if (isinstance(candidate, dict)
                and isinstance(candidate.get("emails"), list)):
            found = candidate
    return found


def _emails_record_failure(error):
    """Record a failed collection attempt without touching stored emails."""
    with EMAILS_LOCK:
        data = _read_json(EMAILS_FILE, {"updated": None, "emails": []})
        if not isinstance(data, dict):
            data = {"updated": None, "emails": []}
        data["last_status"] = "error"
        data["last_error"] = _clean_item_text(error, 300)
        data["last_attempt"] = time.time()
        _write_json(EMAILS_FILE, data)


def _emails_create_actions(emails):
    """Auto-create action items from needs_action emails.

    Dedup across runs via a seen-thread_id registry so re-collecting the
    same threads never duplicates board items. Returns count created."""
    with EMAILS_LOCK:
        raw = _read_json(EMAIL_SEEN_FILE, [])
        seen = set(raw) if isinstance(raw, list) else set()
    by_proj = {}
    valid_projects = set(_project_names())
    for e in emails:
        tid = e.get("thread_id", "")
        if (e.get("project") not in valid_projects
                or not e.get("needs_action")
                or not THREAD_ID_RE.match(tid)
                or tid in seen):
            continue
        by_proj.setdefault(e["project"], []).append(e)
    created = 0
    today = time.strftime("%Y-%m-%d")
    with ITEMS_LOCK:
        for proj_name, group in by_proj.items():
            proj = PROJECTS_DIR / proj_name
            items = _load_items(proj)
            for e in group:
                items.append({
                    "id": uuid.uuid4().hex[:8],
                    "title": _clean_item_text("[이메일] " + (e.get("subject") or "제목 없음"), 300),
                    "detail": e.get("suggested_action") or e.get("summary", ""),
                    "status": "open",
                    "priority": "med",
                    "due": "",
                    "people": [e["from"]] if e.get("from") else [],
                    "sources": [{
                        "kind": "gmail",
                        "label": e.get("subject") or "Gmail 스레드",
                        "url": f"https://mail.google.com/mail/u/0/#all/{e['thread_id']}",
                    }],
                    "note": "",
                    "created": today,
                    "updated": today,
                })
                seen.add(e["thread_id"])
                created += 1
            _write_json(_items_file(proj), items)
    with EMAILS_LOCK:
        _write_json(EMAIL_SEEN_FILE, sorted(seen)[-EMAIL_SEEN_MAX:])
    return created


def _morning_refresh_finalize(job, params):
    """Post-job hook: parse the email manifest, store it server-side,
    keep per-project stats (incl. 0 counts), and auto-create action items
    from needs_action emails."""
    with LOCK:
        status = job["status"]
        text = "\n".join(job["log"])
    if status != "success":
        _emails_record_failure(f"작업 실패 (상태: {status})")
        return
    manifest = _extract_email_manifest(text)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("emails"), list):
        _emails_record_failure("이메일 manifest 파싱 실패")
        with LOCK:
            _append_log(job, "[시스템] 이메일 manifest 파싱 실패 — emails.json 갱신 안 됨")
        return
    connections = manifest.get("connections")
    gmail_conn = connections.get("gmail") if isinstance(connections, dict) else None
    gmail_status = gmail_conn.get("status") if isinstance(gmail_conn, dict) else None
    if gmail_status != "ok":
        detail = (gmail_conn.get("error") if isinstance(gmail_conn, dict) else None)
        detail = _clean_item_text(detail or "Gmail 커넥터 상태 확인 실패", 240)
        _emails_record_failure(detail)
        with LOCK:
            _append_log(job, f"[시스템] Gmail 수집 실패 — {detail}; 기존 emails.json 보존")
        return
    projects = set(_project_names())
    allowed_projects = projects | {GMAIL_OTHER_PROJECT}
    emails = []
    for e in manifest["emails"][:EMAILS_MAX]:
        if not isinstance(e, dict):
            continue
        project = str(e.get("project", "") or "")
        if project not in allowed_projects:
            continue
        emails.append({
            "project": project,
            "subject": _clean_item_text(e.get("subject", ""), 200),
            "from": _clean_item_text(e.get("from", ""), 120),
            "date": _clean_item_text(e.get("date", ""), 20),
            "thread_id": _clean_item_text(e.get("thread_id", ""), 60),
            "summary": _clean_item_text(e.get("summary", ""), 300),
            "needs_action": bool(e.get("needs_action")),
            "suggested_action": _clean_item_text(e.get("suggested_action", ""), 200),
        })
    searched_raw = manifest.get("searched")
    searched = [p for p in searched_raw if p in projects] if isinstance(searched_raw, list) else []
    stats = {p: 0 for p in sorted(projects)}
    stats[GMAIL_OTHER_PROJECT] = 0
    for e in emails:
        stats[e["project"]] = stats.get(e["project"], 0) + 1
    missed = sorted(projects - set(searched)) if searched else []
    created = _emails_create_actions(emails)
    now = time.time()
    with EMAILS_LOCK:
        _write_json(EMAILS_FILE, {
            "updated": now,
            "emails": emails,
            "stats": stats,
            "searched": searched or sorted(projects),
            "missed": missed,
            "last_status": "ok",
            "last_error": None,
            "last_attempt": now,
        })
    # distribution stage (delta-gated): one scoped update job per project,
    # but ONLY when that project's email set actually changed since the last
    # SUCCESSFUL update (hash recorded in _project_update_finalize) — a run
    # with nothing new costs zero AI calls.
    per_proj = {}
    for e in emails:
        if e["project"] in projects:
            per_proj.setdefault(e["project"], []).append(e)
    with EMAILS_LOCK:
        delta = _read_json(EMAIL_DELTA_FILE, {})
        if not isinstance(delta, dict):
            delta = {}
    dispatched, unchanged = [], []
    for pname in sorted(per_proj):
        if delta.get(pname) == _email_set_hash(per_proj[pname]):
            unchanged.append(pname)
            continue
        _, err = _start_job("project_update",
                            {"project": pname, "emails": per_proj[pname]},
                            label=f"상태 반영 — {pname}")
        if err is None:
            dispatched.append(pname)
    with LOCK:
        _append_log(job, f"[시스템] 이메일 {len(emails)}건 저장 → state/emails.json")
        if created:
            _append_log(job, f"[시스템] needs_action 이메일 → 액션 아이템 {created}건 자동 생성")
        if dispatched:
            _append_log(job, f"[시스템] 프로젝트 상태 반영 작업 {len(dispatched)}건 대기열 등록 "
                             f"({', '.join(dispatched)})")
        if unchanged:
            _append_log(job, f"[시스템] 변경 없음 — 배분 생략: {', '.join(unchanged)}")
        if missed:
            _append_log(job, f"[시스템] ⚠️ 검색 누락 프로젝트: {', '.join(missed)}")


TASKS["morning_refresh"] = {
    "label_ko": "아침 리프레시",
    "category": "동기화",
    # AI-free (rule-based classifier) — not in the "ai" group, so it never
    # waits on AI concurrency/rate-limit gating and runs immediately on a
    # manual trigger even while the AI breaker is engaged.
    "groups": {"collectors"},
    "ai": False,
    "cooldown": 900,         # succeeded < 15 min ago → don't re-collect
    "timeout": 300,          # Gmail REST fetch (up to ~800 candidates via
                              # thread pool) + local keyword classify only
    "heartbeat": False,
    "refresh": "projects",
    "argv": lambda p: [PYTHON_BIN, str(HIOS_SCRIPTS / "email_classify.py")],
    "stdin": _morning_refresh_snapshot_stdin,
    "finalize": _morning_refresh_finalize,
}


# -------- distribution stage: collected emails/meetings → project files.
# After a successful collection, one scoped job per affected project updates
# _STATUS.md/_TODO.md. Per-project groups → up to 3 run in parallel.

def _project_update_prompt(p):
    name = p.get("project", "")
    lines = "\n".join(
        f"- [{e.get('date', '')}] {e.get('from', '')} — {e.get('subject', '')}: "
        f"{e.get('summary', '')}"
        + (f" (⚡ 액션: {e.get('suggested_action', '') or '회신 필요'})"
           if e.get("needs_action") else "")
        for e in p.get("emails", [])
    )
    return (
        f"프로젝트 자동 상태 반영 작업입니다. 대상: 01-Projects/{name}/\n"
        "Headless mode — 질문하지 말고 바로 실행하세요. "
        "이 프로젝트 폴더 범위에서만 읽고 쓰세요.\n\n"
        f"[오늘 수집된 이메일]\n{lines or '- 없음'}\n\n"
        "수행할 일:\n"
        f"1. 01-Projects/{name}/_STATUS.md 를 읽으세요 (없으면 front-matter 포함해 새로 만드세요). "
        "위 이메일, 미팅 노트 폴더(02-Meetings/ 또는 07-Meetings/ 등 이름이 다를 수 있음)의 "
        "최근 7일 노트, _ACTIONS.json 의 열린 항목을 반영해 "
        "'## 최근 동향' 섹션(없으면 만들기)을 날짜별 bullet 로 갱신하세요. "
        "front-matter 와 기존 섹션은 보존하고, 이미 반영된 내용은 중복 추가하지 마세요. "
        "구식이 된 문장은 고치세요.\n"
        f"2. 01-Projects/{name}/_TODO.md 에 위 이메일에서 나온 새 할 일이 있고 "
        "아직 목록에 없으면 추가하세요 (중복 금지, 완료 표시된 항목 건드리지 말 것).\n"
        "3. 파일 삭제/이동 금지. _ACTIONS.json 은 서버가 관리하므로 수정 금지.\n\n"
        "마지막에 무엇을 바꿨는지 2-3줄로 요약 출력하세요.\n"
    )


def _project_update_finalize(job, params):
    """Record the applied email-set hash ONLY on success, so a failed update
    (e.g. usage limit) is retried automatically on the next collection."""
    with LOCK:
        ok = job["status"] == "success"
    if not ok:
        return
    pname = str(params.get("project", "") or "")
    if not pname:
        return
    with EMAILS_LOCK:
        delta = _read_json(EMAIL_DELTA_FILE, {})
        if not isinstance(delta, dict):
            delta = {}
        delta[pname] = _email_set_hash(params.get("emails", []))
        _write_json(EMAIL_DELTA_FILE, delta)


TASKS["project_update"] = {
    "label_ko": "프로젝트 상태 반영",
    "category": "동기화",
    "groups": _project_groups,
    "ai": True,
    "timeout": AI_TIMEOUT,
    "heartbeat": True,
    "internal": True,   # chained automatically after morning_refresh
    "refresh": "projects",
    "argv": lambda p: _claude_argv(),
    "stdin": _project_update_prompt,
    "finalize": _project_update_finalize,
}


@app.get("/api/emails")
def api_emails():
    """Unified email view: all projects + collection stats/health."""
    with EMAILS_LOCK:
        data = _read_json(EMAILS_FILE, {"updated": None, "emails": []})
    if not isinstance(data, dict):
        data = {"updated": None, "emails": []}
    return jsonify(
        updated=data.get("updated"),
        emails=data.get("emails", []),
        stats=data.get("stats", {}),
        searched=data.get("searched", []),
        missed=data.get("missed", []),
        last_status=data.get("last_status"),
        last_error=data.get("last_error"),
        last_attempt=data.get("last_attempt"),
    )


@app.get("/api/projects/<name>/emails")
def api_project_emails(name):
    if name not in _project_names():
        abort(404)
    with EMAILS_LOCK:
        data = _read_json(EMAILS_FILE, {"updated": None, "emails": []})
    emails = [e for e in data.get("emails", []) if e.get("project") == name]
    return jsonify(
        updated=data.get("updated"),
        emails=emails,
        last_status=data.get("last_status"),
        last_error=data.get("last_error"),
    )


# ---------------------------------------------------------------- calendar
# Reads events via EventKit (JXA ObjC bridge) — the old AppleScript
# `whose` query timed out on large synced calendars (90s+); EventKit's
# predicate query returns in ~0.1s. Window: -7d .. +56d so the month
# calendar grid is populated. Cached 15 min; ?refresh=1 to force.

CAL_TTL = 900
CAL_CACHE = {"ts": 0.0, "events": [], "error": None}
CAL_LOCK = threading.Lock()

CAL_SCRIPT = r'''
ObjC.import("EventKit");
function pad(n){ return (n < 10 ? "0" : "") + n; }
function iso(nsdate){
  var d = new Date(nsdate.timeIntervalSince1970 * 1000);
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate())
    + " " + pad(d.getHours()) + ":" + pad(d.getMinutes());
}
var store = $.EKEventStore.alloc.init;
// NB: JXA bridges the enum back as a *string* ("3"), so coerce before comparing.
var status = Number($.EKEventStore.authorizationStatusForEntityType($.EKEntityTypeEvent));
if (status !== 3) {  // 3 = fullAccess (macOS 14+)
  var done = false;
  store.requestFullAccessToEventsWithCompletion(function(){ done = true; });
  var deadline = $.NSDate.dateWithTimeIntervalSinceNow(10);
  while (!done && $.NSDate.date.compare(deadline) === $.NSOrderedAscending) {
    $.NSRunLoop.currentRunLoop.runModeBeforeDate($.NSDefaultRunLoopMode,
      $.NSDate.dateWithTimeIntervalSinceNow(0.1));
  }
  status = Number($.EKEventStore.authorizationStatusForEntityType($.EKEntityTypeEvent));
  if (status !== 3) throw new Error("NOACCESS status=" + status);
  store = $.EKEventStore.alloc.init;
}
var cal = $.NSCalendar.currentCalendar;
var comps = cal.componentsFromDate(
  $.NSCalendarUnitYear | $.NSCalendarUnitMonth | $.NSCalendarUnitDay, $.NSDate.date);
var midnight = cal.dateFromComponents(comps);
var start = midnight.dateByAddingTimeInterval(-7 * 86400);
var end = midnight.dateByAddingTimeInterval(56 * 86400);
var pred = store.predicateForEventsWithStartDateEndDateCalendars(start, end, $());
var evs = store.eventsMatchingPredicate(pred);
var out = [];
for (var i = 0; i < evs.count; i++) {
  var e = evs.objectAtIndex(i);
  out.push((e.calendar.title.js || "") + "\t" + (e.title.js || "")
    + "\t" + iso(e.startDate) + "\t" + iso(e.endDate));
}
out.join("\n");
'''


def _fetch_calendar():
    try:
        proc = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", CAL_SCRIPT],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], f"캘린더 조회 실패: {exc}"
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        if "NOACCESS" in err:
            err = ("캘린더 읽기 권한 필요 — 시스템 설정 > 개인정보 보호 및 보안 > "
                   "캘린더에서 osascript/터미널의 전체 접근을 허용한 뒤 새로고침하세요")
        return [], err or "osascript 실패"
    events, seen = [], set()
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 4:
            continue
        cal, title, start, end = (p.strip() for p in parts)
        key = (title, start)
        if key in seen:
            continue
        seen.add(key)
        events.append({"calendar": cal, "title": title, "start": start, "end": end})
    events.sort(key=lambda e: e["start"])
    return events, None


# ---------------------------------------------------------------- graph view
# Obsidian-style link graph. Scans md files, resolves [[wikilinks]] by stem,
# adds project hub nodes. Capped + cached so it never hurts the UI thread.

GRAPH_CACHE = {"ts": 0.0, "data": None}
GRAPH_TTL = 300
GRAPH_LOCK = threading.Lock()
GRAPH_MAX_NODES = 400
GRAPH_MAX_EDGES = 1200
GRAPH_MAX_FILE = 512 * 1024
GRAPH_SCAN_DIRS = ["01-Projects", "06-Entities", "02-Areas"]
GRAPH_DAILY_COUNT = 30


def _graph_scan_files():
    """Yield (rel_posix, Path) for graph-eligible md files."""
    files = []
    for top in GRAPH_SCAN_DIRS:
        base = VAULT / top
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if any(seg.startswith(".") for seg in p.relative_to(VAULT).parts):
                continue
            if p.is_symlink():
                continue
            files.append((p.relative_to(VAULT).as_posix(), p))
    dailies = sorted(
        (p for p in VAULT.iterdir() if p.is_file() and DAILY_RE.match(p.name)),
        key=lambda p: p.name, reverse=True)[:GRAPH_DAILY_COUNT]
    files.extend((p.name, p) for p in dailies)
    return files


def _build_graph():
    files = _graph_scan_files()
    # stem -> rel index for wikilink resolution (first wins on stem collision)
    stem_index = {}
    for rel, p in files:
        stem_index.setdefault(p.stem, rel)

    projects = set(_project_names())
    nodes, edges = {}, []
    edge_seen = set()
    degree = {}

    def add_edge(a, b):
        if a == b or len(edges) >= GRAPH_MAX_EDGES:
            return
        key = (a, b) if a < b else (b, a)
        if key in edge_seen:
            return
        edge_seen.add(key)
        edges.append({"source": a, "target": b})
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1

    def node_meta(rel):
        parts = rel.split("/")
        if len(parts) == 1:
            return "daily", "daily"
        if parts[0] == "06-Entities":
            return "entity", parts[0]
        group = parts[1] if parts[0] == "01-Projects" and len(parts) > 1 else parts[0]
        return "file", group

    pending = []  # (rel, links, fm_project, is_status)
    for rel, p in files:
        if len(nodes) >= GRAPH_MAX_NODES:
            break
        try:
            if p.stat().st_size > GRAPH_MAX_FILE:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, _body = _parse_front_matter(text)
        links = []
        for l in WIKILINK_RE.findall(text):
            target = stem_index.get(l.strip())
            if target and target != rel:
                links.append(target)
        fm_project = ""
        for key in ("client", "project"):
            v = meta.get(key)
            if isinstance(v, list):
                v = v[0] if v else ""
            v = str(v or "").strip()
            if v in projects:
                fm_project = v
                break
        kind, group = node_meta(rel)
        nodes[rel] = {"id": rel, "name": p.stem, "type": kind, "group": group}
        pending.append((rel, links, fm_project,
                        p.name in ("_STATUS.md",) or bool(links) or bool(fm_project)))

    # project hub nodes
    for name in sorted(projects):
        hub = f"project:{name}"
        nodes[hub] = {"id": hub, "name": name, "type": "project", "group": name}

    for rel, links, fm_project, connectable in pending:
        for target in links:
            if target in nodes:
                add_edge(rel, target)
        if fm_project:
            add_edge(rel, f"project:{fm_project}")
        # membership edge only for files that carry signal (anti-hairball)
        if connectable and rel.startswith("01-Projects/"):
            proj = rel.split("/")[1]
            if proj in projects:
                add_edge(rel, f"project:{proj}")

    for n in nodes.values():
        n["val"] = 1 + degree.get(n["id"], 0)
        if n["type"] == "project":
            n["val"] = max(n["val"], 6)
    return {"nodes": list(nodes.values()), "links": edges,
            "projects": sorted(projects), "generated": time.time()}


@app.get("/api/graph")
def api_graph():
    force = request.args.get("refresh") == "1"
    with GRAPH_LOCK:
        if not force and GRAPH_CACHE["data"] and time.time() - GRAPH_CACHE["ts"] < GRAPH_TTL:
            return jsonify(cached=True, **GRAPH_CACHE["data"])
        data = _build_graph()
        GRAPH_CACHE.update(ts=time.time(), data=data)
    return jsonify(cached=False, **data)


@app.get("/api/calendar")
def api_calendar():
    force = request.args.get("refresh") == "1"
    with CAL_LOCK:
        if not force and time.time() - CAL_CACHE["ts"] < CAL_TTL:
            return jsonify(events=CAL_CACHE["events"], error=CAL_CACHE["error"], cached=True)
        events, err = _fetch_calendar()
        CAL_CACHE.update(ts=time.time(), events=events, error=err)
    return jsonify(events=events, error=err, cached=False)


# ------------------------------------------------------- connection health
# Honest status for every collector — no more silent skips that look like
# success. "degraded" = no confirmed success within CONN_STALE_SEC.

GRANOLA_SYNC_LOG = Path.home() / ".hios/logs/granola-sync.log"
GRANOLA_SYNCED_FILE = Path.home() / ".hios/granola-synced.json"
CONN_STALE_SEC = 26 * 3600


def _granola_health():
    with GRANOLA_STATE_LOCK:
        state = _read_json(GRANOLA_STATE_FILE, {})
    if isinstance(state, dict) and isinstance(state.get("last_attempt"), (int, float)):
        last_success = state.get("last_success")
        fresh = (isinstance(last_success, (int, float))
                 and time.time() - last_success < CONN_STALE_SEC)
        return {
            "status": "ok" if state.get("last_status") == "ok" and fresh else "degraded",
            "last_success": last_success,
            "last_error": state.get("last_error"),
            "meetings_seen": state.get("meetings_seen", 0),
            "meetings_created": state.get("meetings_created", 0),
        }
    out = {"status": "unknown", "last_success": None, "last_error": None}
    try:
        out["last_success"] = GRANOLA_SYNCED_FILE.stat().st_mtime
    except OSError:
        pass
    try:
        tail = GRANOLA_SYNC_LOG.read_text(encoding="utf-8", errors="replace")[-6000:]
    except OSError:
        tail = ""
    last_run = tail.split("=== granola-sync run:")[-1] if tail else ""
    if AI_LIMIT_RE.search(last_run):
        out["last_error"] = "AI 사용량 한도 — 마지막 동기화 실패"
    elif "GRANOLA_AUTH_REQUIRED" in last_run:
        out["last_error"] = "Granola 앱 로그인 필요"
    if "SYNCED:" in last_run:      # last run completed with a sync summary
        m = re.findall(r"=== granola-sync run: ([0-9: -]+?) ===", tail)
        if m:
            try:
                ts = time.mktime(time.strptime(m[-1].strip(), "%Y-%m-%d %H:%M:%S"))
                out["last_success"] = max(out["last_success"] or 0, ts)
            except ValueError:
                pass
    ls = out["last_success"]
    out["status"] = ("ok" if not out["last_error"] and ls
                     and time.time() - ls < CONN_STALE_SEC
                     else "degraded")
    return out


@app.get("/api/health/connections")
def api_health_connections():
    with EMAILS_LOCK:
        em = _read_json(EMAILS_FILE, {})
        if not isinstance(em, dict):
            em = {}
    updated = em.get("updated")
    updated_ok = isinstance(updated, (int, float))
    gmail = {
        "status": ("ok" if em.get("last_status") == "ok" and updated_ok
                   and time.time() - updated < CONN_STALE_SEC else "degraded"),
        "last_success": updated,
        "last_error": em.get("last_error"),
    }
    with CAL_LOCK:
        cal = {
            "status": ("error" if CAL_CACHE["error"]
                       else "ok" if CAL_CACHE["ts"] else "unknown"),
            "last_success": CAL_CACHE["ts"] or None,
            "last_error": CAL_CACHE["error"],
        }
    with LOCK:
        limited = _ai_limited_locked()
        ai = {"status": "limited" if limited else "ok",
              "provider": AI_PROVIDER,
              "resume": AI_HEALTH["limited_until"] if limited else None}
    return jsonify(gmail=gmail, granola=_granola_health(), calendar=cal,
                   ai=ai, time=time.time())


if __name__ == "__main__":
    # Ensure Claude Code and helper CLIs are findable under a minimal launchd PATH.
    _extra = [p for p in ("/usr/local/bin", "/opt/homebrew/bin")
              if p not in os.environ.get("PATH", "").split(":")]
    if _extra:
        os.environ["PATH"] = ":".join(_extra + [os.environ.get("PATH", "")])
    _load_env()
    _ensure_actions()
    _reset_stale_upload_batches()
    if os.environ.get("HIOS_DISABLE_AUTOMATION") != "1":
        threading.Thread(target=_scheduler_loop, daemon=True).start()
        threading.Thread(target=_queue_loop, daemon=True).start()
        if os.environ.get("HIOS_DISABLE_GIT_SNAPSHOT") != "1":
            threading.Thread(target=_git_snapshot_loop, daemon=True).start()
    port = int(os.environ.get("HIOS_PORT", "8787"))
    app.run(host="127.0.0.1", port=port, threaded=True, debug=False)
