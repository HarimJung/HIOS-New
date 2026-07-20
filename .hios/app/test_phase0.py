"""Deterministic backend tests. No AI, MCP, network, or live server."""

import importlib.util
import json
import time
from collections import deque
from pathlib import Path

import pytest


SERVER_PATH = Path(__file__).with_name("server.py")
SPEC = importlib.util.spec_from_file_location("hios_phase0_server", SERVER_PATH)
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class _NoopThread:
    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        pass


class _FakeStdin:
    def write(self, _text):
        pass

    def close(self):
        pass


class _FakeProcess:
    pid = 4242

    def __init__(self, lines, returncode=0):
        self.stdin = _FakeStdin()
        self.stdout = iter(lines)
        self.returncode = returncode

    def wait(self, timeout=None):
        return self.returncode

    def poll(self):
        return self.returncode


def _job(job_id, task_id, status="queued", groups=None, ai=True):
    return {
        "id": job_id,
        "task_id": task_id,
        "label": task_id,
        "status": status,
        "created": time.time(),
        "groups": set(groups or ()),
        "ai": ai,
        "provider": server.AI_PROVIDER if ai else None,
        "params": {},
        "refresh": None,
        "log": deque(maxlen=server.LOG_CAP),
        "log_total": 0,
    }


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "LOG_DIR", tmp_path / "logs")
    server.LOG_DIR.mkdir()
    for name in (
        "HEALTH_FILE", "USAGE_FILE", "TASK_RUNS_FILE", "EMAILS_FILE",
        "EMAIL_DELTA_FILE", "EMAIL_SEEN_FILE", "GRANOLA_STATE_FILE",
        "GRANOLA_ACTION_SEEN_FILE",
        "SCHED_STATE_FILE",
    ):
        monkeypatch.setattr(server, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(server, "GRANOLA_SYNC_LOG", tmp_path / "granola.log")
    monkeypatch.setattr(server, "GRANOLA_SYNCED_FILE", tmp_path / "granola.json")
    monkeypatch.setattr(server.threading, "Thread", _NoopThread)
    server.JOBS.clear()
    server.JOB_ORDER.clear()
    server.ACTIVE_GROUPS.clear()
    server.QUEUE_ACTIVE.clear()
    server.AI_HEALTH.update(limited_until=0.0, since=None, detected_at=None)
    yield server
    server.JOBS.clear()
    server.JOB_ORDER.clear()
    server.ACTIVE_GROUPS.clear()
    server.QUEUE_ACTIVE.clear()


def test_p0_1_limit_rc_zero_trips_breaker_holds_then_resumes_queue(isolated, monkeypatch):
    limited = _job("limited", "limit_task", status="pending", groups={"active"})
    queued = _job("queued", "next_task", groups={"next"})
    isolated.JOBS.update(limited=limited, queued=queued)
    isolated.JOB_ORDER.extend(["limited", "queued"])
    isolated.ACTIVE_GROUPS.add("active")
    isolated.TASKS["next_task"] = {
        "label_ko": "next", "category": "test", "groups": {"next"},
        "ai": True, "timeout": 1, "argv": lambda _p: ["unused"],
    }
    limit_line = "You're out of extra usage · resets 3pm (America/Toronto)\n"
    fake = _FakeProcess([limit_line], returncode=0)
    monkeypatch.setattr(isolated.subprocess, "Popen", lambda *a, **k: fake)

    isolated._runner(limited, {
        "timeout": 1, "heartbeat": False, "argv": lambda _p: ["fake-claude"],
    }, {})

    assert limited["status"] == "failed"
    assert limited["returncode"] == 0
    assert queued["status"] == "queued"
    assert isolated.AI_HEALTH["limited_until"] > time.time()
    persisted = json.loads(isolated.HEALTH_FILE.read_text(encoding="utf-8"))
    assert persisted["ai"] == "limited"
    usage = json.loads(isolated.USAGE_FILE.read_text(encoding="utf-8"))
    today = usage[time.strftime("%Y-%m-%d")]
    assert (today["ai_jobs"], today["failed"], today["limited_hits"]) == (1, 1, 1)
    assert today["provider"] == "claude"

    isolated.AI_HEALTH["limited_until"] = time.time() - 1
    isolated._dispatch()
    assert queued["status"] == "pending"
    queued.update(status="success", started=time.time())
    isolated._clear_ai_limit(queued)
    assert isolated.AI_HEALTH == {
        "limited_until": 0.0, "since": None, "detected_at": None,
    }
    assert json.loads(isolated.HEALTH_FILE.read_text(encoding="utf-8"))["ai"] == "ok"


def test_p0_1_restart_loader_restores_only_unexpired_state(tmp_path):
    path = tmp_path / "health.json"
    path.write_text(json.dumps({
        "limited_until": 2000, "since": 1000, "detected_at": 1100,
        "provider": "claude",
    }), encoding="utf-8")
    assert server._load_ai_health(path, now=1500) == {
        "limited_until": 2000.0, "since": 1000.0, "detected_at": 1100.0,
    }
    assert server._load_ai_health(path, now=2001) == {
        "limited_until": 0.0, "since": None, "detected_at": None,
    }
    path.write_text(json.dumps({
        "limited_until": 3000, "since": 1000, "detected_at": 1100,
        "provider": "codex",
    }), encoding="utf-8")
    assert server._load_ai_health(path, now=1500) == {
        "limited_until": 0.0, "since": None, "detected_at": None,
    }


def test_p0_2_identical_active_request_is_deduplicated(isolated, monkeypatch):
    isolated.AI_HEALTH["limited_until"] = time.time() + 60
    monkeypatch.setitem(isolated.TASKS, "dedup_task", {
        "label_ko": "dedup", "category": "test", "groups": set(),
        "ai": True, "timeout": 1, "argv": lambda _p: ["unused"],
    })
    first, first_err = isolated._start_job("dedup_task", {"b": 2, "a": 1})
    second, second_err = isolated._start_job("dedup_task", {"a": 1, "b": 2})

    assert first_err is None
    assert (second, second_err) == (first, "dedup")
    assert isolated.JOB_ORDER == [first]


def test_p0_3_cooldown_returns_null_without_creating_a_job(isolated, monkeypatch):
    monkeypatch.setitem(isolated.TASKS, "cooldown_task", {
        "label_ko": "cooldown", "category": "test", "groups": set(),
        "ai": True, "cooldown": 900, "timeout": 1,
        "argv": lambda _p: ["unused"],
    })
    isolated.TASK_RUNS_FILE.write_text(
        json.dumps({"cooldown_task": time.time()}), encoding="utf-8"
    )

    with isolated.app.test_client() as client:
        response = client.post("/api/run/cooldown_task", json={})

    assert response.status_code == 200
    assert response.get_json()["job_id"] is None
    assert response.get_json()["cooldown"] is True
    assert 1 <= response.get_json()["retry_in"] <= 900
    assert isolated.JOB_ORDER == []


def test_p0_4_unchanged_email_set_skips_distribution(isolated, monkeypatch):
    emails = [{
        "project": "Alpha", "subject": "Subject", "from": "Sender",
        "date": "2026-07-18", "thread_id": "thread-1", "summary": "Summary",
        "needs_action": False, "suggested_action": "",
    }]
    isolated.EMAIL_DELTA_FILE.write_text(
        json.dumps({"Alpha": isolated._email_set_hash(emails)}), encoding="utf-8"
    )
    monkeypatch.setattr(isolated, "_project_names", lambda: ["Alpha"])
    monkeypatch.setattr(isolated, "_emails_create_actions", lambda _emails: 0)
    starts = []
    monkeypatch.setattr(
        isolated, "_start_job",
        lambda *args, **kwargs: (starts.append((args, kwargs)) or ("job", None)),
    )
    manifest = json.dumps({
        "emails": emails, "searched": ["Alpha"],
        "connections": {"gmail": {"status": "ok", "error": None}},
    })
    job = _job("refresh", "morning_refresh", status="success")
    job["log"].append(manifest)
    job["log_total"] = 1

    isolated._morning_refresh_finalize(job, {})

    assert starts == []
    assert any("변경 없음" in line for line in job["log"])

    emails[0]["thread_id"] = "thread-2"
    job["log"] = deque([
        json.dumps({
            "connections": {"gmail": {"status": "ok", "error": None}},
            "searched": ["Alpha"], "emails": emails,
        })
    ], maxlen=isolated.LOG_CAP)
    job["log_total"] = 1
    isolated._morning_refresh_finalize(job, {})
    assert len(starts) == 1
    assert starts[0][0][0] == "project_update"


def test_p0_4_delta_is_recorded_only_after_success(isolated):
    params = {"project": "Alpha", "emails": [{"thread_id": "t", "date": "d"}]}
    failed = _job("failed", "project_update", status="failed")
    isolated._project_update_finalize(failed, params)
    assert not isolated.EMAIL_DELTA_FILE.exists()

    succeeded = _job("success", "project_update", status="success")
    isolated._project_update_finalize(succeeded, params)
    saved = json.loads(isolated.EMAIL_DELTA_FILE.read_text(encoding="utf-8"))
    assert saved["Alpha"] == isolated._email_set_hash(params["emails"])


def test_p0_5_connection_health_reports_errors_and_staleness(isolated):
    now = time.time()
    isolated.EMAILS_FILE.write_text(json.dumps({
        "updated": now, "last_status": "ok", "last_error": None,
    }), encoding="utf-8")
    isolated.GRANOLA_SYNCED_FILE.write_text("[]", encoding="utf-8")
    isolated.GRANOLA_SYNC_LOG.write_text(
        "=== granola-sync run: 2026-07-18 21:35:46 ===\nGRANOLA_AUTH_REQUIRED\n",
        encoding="utf-8",
    )
    isolated.CAL_CACHE.update(ts=0.0, events=[], error=None)

    with isolated.app.test_client() as client:
        response = client.get("/api/health/connections")

    assert response.status_code == 200
    body = response.get_json()
    assert body["gmail"]["status"] == "ok"
    assert body["granola"]["status"] == "degraded"
    assert body["granola"]["last_error"] == "Granola 앱 로그인 필요"
    assert body["calendar"]["status"] == "unknown"
    assert body["ai"]["status"] == "ok"
    assert body["ai"]["provider"] == "claude"


def test_refresh_rejects_unconfirmed_gmail_and_preserves_cached_emails(isolated):
    cached = {
        "updated": 123.0, "emails": [{"thread_id": "cached"}],
        "last_status": "ok", "last_error": None,
    }
    isolated.EMAILS_FILE.write_text(json.dumps(cached), encoding="utf-8")
    manifest = {
        "searched": [], "emails": [],
        "connections": {
            "gmail": {"status": "error", "error": "Gmail login required"},
            "granola": {"status": "ok", "error": None},
        },
    }
    job = _job("refresh", "morning_refresh", status="success")
    job["log"].append("prefix\n" + json.dumps(manifest) + "\ntrailing output")

    isolated._morning_refresh_finalize(job, {})

    saved = json.loads(isolated.EMAILS_FILE.read_text(encoding="utf-8"))
    assert saved["updated"] == 123.0
    assert saved["emails"] == [{"thread_id": "cached"}]
    assert saved["last_status"] == "error"
    assert saved["last_error"] == "Gmail login required"
    assert any("기존 emails.json 보존" in line for line in job["log"])


def test_gmail_snapshot_merges_recent_and_wmo_queries_without_duplicates(
        isolated, monkeypatch):
    monkeypatch.setattr(isolated, "_gmail_access_token", lambda: "test-token")
    monkeypatch.setattr(
        isolated, "_gmail_project_queries",
        lambda: {"WMO": "newer_than:10d subject:(WMO)"},
    )
    calls = []

    class _SyncPool:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def map(self, func, values):
            return [func(value) for value in values]

    monkeypatch.setattr(isolated, "ThreadPoolExecutor", _SyncPool)

    def fake_get(token, resource, params):
        assert token == "test-token"
        calls.append((resource, params))
        if resource == "messages":
            if "subject:(WMO)" in params["q"]:
                return {"messages": [
                    {"id": "b", "threadId": "tb"},
                    {"id": "c", "threadId": "tc"},
                ]}
            return {"messages": [
                {"id": "a", "threadId": "ta"},
                {"id": "b", "threadId": "tb"},
            ]}
        message_id = resource.rsplit("/", 1)[-1]
        return {
            "id": message_id,
            "threadId": f"t{message_id}",
            "internalDate": "1784419200000",
            "snippet": f"snippet {message_id}",
            "payload": {"headers": [
                {"name": "From", "value": f"sender-{message_id}@wmo.int"},
                {"name": "To", "value": "data.harim.jung@gmail.com"},
                {"name": "Subject", "value": f"Subject {message_id}"},
            ]},
        }

    monkeypatch.setattr(isolated, "_gmail_api_get", fake_get)
    snapshot = isolated._gmail_collect_snapshot()

    assert snapshot["connection"] == {"status": "ok", "error": None}
    assert "newer_than:10d" in snapshot["queries"]["WMO"]
    assert "newer_than:10d" in snapshot["queries"]["기타-보완"]
    assert snapshot["candidate_count"] == 3
    assert {row["message_id"] for row in snapshot["candidates"]} == {"a", "b", "c"}
    by_id = {row["message_id"]: row for row in snapshot["candidates"]}
    assert by_id["a"]["source_query"] == "기타-보완"
    assert by_id["b"]["source_query"] == "WMO"
    assert by_id["c"]["source_query"] == "WMO"
    assert by_id["c"]["from"] == "sender-c@wmo.int"
    detail_calls = [params for resource, params in calls if resource.startswith("messages/")]
    assert len(detail_calls) == 3
    assert all(params["format"] == "metadata" for params in detail_calls)
    assert all(params["metadataHeaders"] == ["From", "To", "Subject", "Date"]
               for params in detail_calls)


def test_gmail_snapshot_stdin_embeds_safe_failure_manifest_without_connector_call(
        isolated, monkeypatch):
    monkeypatch.setattr(
        isolated, "_gmail_collect_snapshot",
        lambda: (_ for _ in ()).throw(RuntimeError("Gmail token expired")),
    )

    stdin_payload = isolated._morning_refresh_snapshot_stdin({})
    snapshot = json.loads(stdin_payload)

    assert snapshot["connection"]["status"] == "error"
    assert "Gmail token expired" in snapshot["connection"]["error"]
    assert snapshot["candidates"] == []


def test_morning_refresh_is_ai_free_and_runs_the_rule_based_classifier():
    task = server.TASKS["morning_refresh"]
    assert task["ai"] is False
    assert task["groups"] == {"collectors"}
    argv = task["argv"]({})
    assert argv[0] == server.PYTHON_BIN
    assert argv[-1] == str(server.HIOS_SCRIPTS / "email_classify.py")


def test_gmail_other_bucket_is_kept_but_never_distributed_as_project(
        isolated, monkeypatch):
    monkeypatch.setattr(isolated, "_project_names", lambda: ["WMO"])
    monkeypatch.setattr(isolated, "_emails_create_actions", lambda _emails: 0)
    starts = []
    monkeypatch.setattr(
        isolated, "_start_job",
        lambda *args, **kwargs: (starts.append((args, kwargs)) or ("job", None)),
    )
    manifest = {
        "searched": ["WMO"],
        "connections": {"gmail": {"status": "ok", "error": None}},
        "emails": [
            {
                "project": "WMO", "subject": "WMO update", "from": "x@wmo.int",
                "date": "2026-07-19", "thread_id": "thread-wmo",
                "summary": "WMO summary", "needs_action": False,
                "suggested_action": "",
            },
            {
                "project": isolated.GMAIL_OTHER_PROJECT, "subject": "Receipt",
                "from": "shop@example.com", "date": "2026-07-19",
                "thread_id": "thread-other", "summary": "Unmatched receipt",
                "needs_action": False, "suggested_action": "",
            },
        ],
    }
    job = _job("gmail", "morning_refresh", status="success")
    job["log"].append(json.dumps(manifest))

    isolated._morning_refresh_finalize(job, {})

    saved = json.loads(isolated.EMAILS_FILE.read_text(encoding="utf-8"))
    assert len(saved["emails"]) == 2
    assert saved["stats"] == {"WMO": 1, isolated.GMAIL_OTHER_PROJECT: 1}
    assert len(starts) == 1
    assert starts[0][0][0] == "project_update"
    assert starts[0][0][1]["project"] == "WMO"


def test_claude_worker_argv_and_task_registry_have_no_codex_binary_dependency():
    argv = server._claude_argv()

    assert argv[:2] == [server.CLAUDE_BIN, "--print"]
    assert "--permission-mode" in argv
    assert argv[argv.index("--permission-mode") + 1] == "acceptEdits"
    assert "--allowedTools" in argv
    assert argv[argv.index("--allowedTools") + 1] == "Read,Write,Edit,Glob,Grep,Bash"
    assert "--max-turns" in argv
    assert argv[argv.index("--max-turns") + 1] == "50"
    assert all("codex" not in str(task.get("argv", "")).lower()
               for task in server.TASKS.values())
    assert all(not task.get("codex") for task in server.TASKS.values())
    assert all(task.get("ai") for task in server.TASKS.values()
               if task.get("category") in {"AI", "브리핑"})


def test_ai_runner_prefixes_repository_safety_rules(isolated, monkeypatch):
    job = _job("codex", "codex_task", status="pending", groups={"ai"})
    isolated.JOBS[job["id"]] = job
    isolated.JOB_ORDER.append(job["id"])
    isolated.ACTIVE_GROUPS.add("ai")
    fake = _FakeProcess([], returncode=0)
    written = []
    fake.stdin.write = written.append
    monkeypatch.setattr(isolated.subprocess, "Popen", lambda *a, **k: fake)

    isolated._runner(job, {
        "timeout": 1, "heartbeat": False, "argv": lambda _p: ["codex", "exec"],
        "stdin": lambda _p: "do the task",
    }, {})

    assert job["status"] == "success"
    assert len(written) == 1
    assert "phase0-wip.patch" in written[0]
    assert "git commit/push" in written[0]
    assert written[0].endswith("do the task")


def test_granola_sync_is_independent_required_mcp_and_records_health(isolated):
    argv = isolated._claude_argv_granola()
    assert argv[:2] == [isolated.CLAUDE_BIN, "--print"]
    assert "Granola MCP가 반드시 필요합니다" in isolated._granola_refresh_prompt({})
    assert any(e["task"] == "granola_refresh" for e in isolated.SCHEDULE)

    manifest = {
        "connection": {"status": "ok", "error": None},
        "meetings_seen": "4", "meetings_created": 2,
    }
    job = _job("granola", "granola_refresh", status="success")
    job["log"].append("progress\n" + json.dumps(manifest))
    isolated._granola_refresh_finalize(job, {})

    saved = json.loads(isolated.GRANOLA_STATE_FILE.read_text(encoding="utf-8"))
    assert saved["last_status"] == "ok"
    assert (saved["meetings_seen"], saved["meetings_created"]) == (4, 2)
    assert saved["actions_created"] == 0
    health = isolated._granola_health()
    assert health["status"] == "ok"
    assert health["last_error"] is None


def test_granola_actions_are_project_scoped_and_deduplicated(
        isolated, monkeypatch, tmp_path):
    projects_dir = tmp_path / "projects"
    (projects_dir / "WMO").mkdir(parents=True)
    monkeypatch.setattr(isolated, "PROJECTS_DIR", projects_dir)
    monkeypatch.setattr(isolated, "_project_names", lambda: ["WMO"])
    valid = {
        "project": "WMO",
        "title": "Moodle course shell 업데이트",
        "detail": "회의 결정에 따라 테스트 콘텐츠를 반영",
        "due": "2026-07-22",
        "people": ["Xiao"],
        "granola_id": "meeting-123",
        "note_path": "01-Projects/WMO/02-Meetings/2026-07-19-wmo-bcm.md",
    }
    invalid_project = dict(valid, project="Unknown", granola_id="meeting-999")

    assert isolated._granola_create_actions([valid, valid, invalid_project]) == 1
    assert isolated._granola_create_actions([valid]) == 0

    items = json.loads(
        (projects_dir / "WMO" / "_ACTIONS.json").read_text(encoding="utf-8")
    )
    assert len(items) == 1
    assert items[0]["title"] == "[미팅] Moodle course shell 업데이트"
    assert items[0]["due"] == "2026-07-22"
    assert items[0]["people"] == ["Xiao"]
    assert items[0]["sources"][0]["kind"] == "granola"
    seen = json.loads(
        isolated.GRANOLA_ACTION_SEEN_FILE.read_text(encoding="utf-8")
    )
    assert len(seen) == 1
