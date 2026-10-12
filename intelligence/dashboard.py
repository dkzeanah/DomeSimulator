"""The Intelligence Dashboard: one local page over everything the observer learned.

Sections: overview, episodes, playbooks, failures, knowledge -- and two that act:

* **DeepSeek** -- verify the API key works (model list and a round trip), then
  ask anything, with the learned data attached as context: the playbooks, the
  action statistics, the recurring failures, and the project agent's tools.
  Preset probes ask how the agent could take over the work.
* **Agent** -- send a message to the project agent. With DeepSeek as the
  planner, *Preview* shows the tool calls it would make without running any;
  *Run* executes them through the agent's own guarded tool layer, one job at a
  time, and shows the output and the run manifest.

Everything is local: the server binds 127.0.0.1 only, the API key is read from
the environment (``DEEPSEEK_API_KEY``, or the agent's own configuration) and is
never sent to the page.

    py -3.12 -m intelligence.dashboard            # opens http://127.0.0.1:8765
    py -3.12 -m intelligence.dashboard --selftest
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import procedures
from .database import DB_PATH, connect

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PORT = 8765


# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------

def _rows(conn, sql: str, args=()) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, args)]


def api_overview() -> dict:
    conn = connect()
    try:
        counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for t in ("sessions", "prompts", "events", "actions", "episodes", "knowledge")}
        counts["playbooks"] = len(procedures.load())
        top = _rows(conn, "SELECT normalized_action AS action, COUNT(*) AS runs, "
                          "SUM(status='failure') AS failures, CAST(AVG(duration_ms) AS INTEGER) AS avg_ms, "
                          "CAST(SUM(duration_ms) AS INTEGER) AS total_ms "
                          "FROM actions GROUP BY normalized_action ORDER BY runs DESC LIMIT 18")
        outcomes = _rows(conn, "SELECT outcome, COUNT(*) AS n FROM episodes GROUP BY outcome ORDER BY n DESC")
        last = conn.execute("SELECT MAX(received_at) FROM events").fetchone()[0]
    finally:
        conn.close()
    return {"counts": counts, "top_actions": top, "outcomes": outcomes, "last_event": last,
            "deepseek": deepseek_config()["configured"], "db": str(DB_PATH)}


def api_episodes(show_all: bool = False) -> list[dict]:
    conn = connect()
    try:
        rows = _rows(conn, "SELECT episode_id, session_id, substr(goal, 1, 220) AS goal, outcome, "
                           "action_count, failure_count, started_at, ended_at FROM episodes "
                           "ORDER BY episode_id DESC")
    finally:
        conn.close()
    if not show_all:
        rows = [r for r in rows if not procedures.NOTIFICATION.match(r["goal"] or "")]
    return rows


def api_episode(episode_id: int) -> dict:
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM episodes WHERE episode_id = ?", (episode_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"error": f"no episode {episode_id}"}
    out = dict(row)
    for key in ("trajectory", "observations", "context_accessed", "initial_state"):
        try:
            out[key] = json.loads(out[key] or "null")
        except json.JSONDecodeError:
            pass
    return out


def api_failures() -> list[dict]:
    conn = connect()
    try:
        return _rows(conn, "SELECT a.action_id, a.prompt_id, a.normalized_action AS action, "
                           "substr(a.generalized, 1, 200) AS pattern, a.started_at, "
                           "substr(COALESCE(o.error, o.result_text), 1, 400) AS result "
                           "FROM actions a LEFT JOIN observations o ON o.tool_use_id = a.tool_use_id "
                           "WHERE a.status = 'failure' ORDER BY a.action_id DESC LIMIT 60")
    finally:
        conn.close()


def api_knowledge() -> list[dict]:
    conn = connect()
    try:
        return _rows(conn, "SELECT tier, kind, subject, claim, confidence, provenance, verification "
                           "FROM knowledge ORDER BY tier, confidence DESC")
    finally:
        conn.close()


def api_extract() -> dict:
    books = procedures.run()
    synced = False
    with contextlib.suppress(Exception):
        from project_agent import learned
        learned.sync()
        synced = True
    return {"playbooks": len(books), "agent_synced": synced}


# ----------------------------------------------------------------------
# DeepSeek
# ----------------------------------------------------------------------

def deepseek_config() -> dict:
    """Key, base and model -- the key never leaves this process."""
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    base = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1").rstrip("/")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    source = "DEEPSEEK_API_KEY" if key else ""
    if not key:
        with contextlib.suppress(Exception):
            from project_agent import config
            if config.llm_configured() and "deepseek" in config.llm_api_base():
                key, base, model, source = (config.llm_api_key(), config.llm_api_base(),
                                            config.llm_model(), "project agent configuration")
    return {"key": key, "base": base, "model": model, "configured": bool(key), "source": source}


def _post(url: str, key: str, payload: dict, timeout: int = 120) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(url: str, key: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_error(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        return f"HTTP {exc.code}: {detail or exc.reason}"
    if isinstance(exc, urllib.error.URLError):
        return f"cannot reach the endpoint: {exc.reason}"
    return f"{type(exc).__name__}: {exc}"


def deepseek_verify() -> dict:
    cfg = deepseek_config()
    if not cfg["configured"]:
        return {"ok": False, "error": "No key. Set DEEPSEEK_API_KEY in your environment and restart."}
    out = {"base": cfg["base"], "model": cfg["model"], "key_source": cfg["source"]}
    try:
        t = time.time()
        models = _get(f"{cfg['base']}/models", cfg["key"])
        out["models"] = [m.get("id") for m in models.get("data", [])]
        out["models_ms"] = int((time.time() - t) * 1000)
        t = time.time()
        reply = _post(f"{cfg['base']}/chat/completions", cfg["key"], {
            "model": cfg["model"], "max_tokens": 12,
            "messages": [{"role": "user", "content": "Reply with exactly: DOMESIM OK"}]})
        out["round_trip_ms"] = int((time.time() - t) * 1000)
        out["reply"] = reply["choices"][0]["message"]["content"].strip()
        out["usage"] = reply.get("usage", {})
        out["ok"] = True
    except Exception as exc:  # noqa: BLE001
        out.update(ok=False, error=_http_error(exc))
    return out


def context_text(parts: list[str]) -> str:
    """The learned data, as text a model can read."""
    chunks = []
    if "overview" in parts:
        ov = api_overview()
        lines = [f"counts: {json.dumps(ov['counts'])}", "most-used actions (runs, failures, avg ms):"]
        lines += [f"  {a['action']}: {a['runs']}, {a['failures']}, {a['avg_ms']}" for a in ov["top_actions"]]
        chunks.append("OBSERVED ACTIVITY\n" + "\n".join(lines))
    if "playbooks" in parts:
        chunks.append("PLAYBOOKS (repeated workflows mined from the episodes)\n"
                      + procedures.text(procedures.load()))
    if "failures" in parts:
        fails = api_failures()[:15]
        chunks.append("RECENT FAILURES\n" + "\n".join(
            f"  {f['action']}: {f['pattern']} -> {(f['result'] or '')[:160]}" for f in fails))
    if "knowledge" in parts:
        chunks.append("DERIVED KNOWLEDGE (tier >= 2)\n" + "\n".join(
            f"  [{k['tier']} {k['verification']}] {k['claim']}" for k in api_knowledge() if k["tier"] >= 2))
    if "agent" in parts:
        with contextlib.suppress(Exception):
            from project_agent import recipes, tools
            lines = [f"  {name}: {str(spec['description']).splitlines()[0]}" for name, spec in tools.TOOLS.items()]
            chunks.append("PROJECT AGENT TOOLS (it can only act through these)\n" + "\n".join(lines)
                          + "\nRECIPES\n" + recipes.recipes_text())
    return "\n\n".join(chunks)


SYSTEM = ("You advise the owner of DomeSim, a geodesic-dome design and media repository. You are "
          "given what an observer learned from watching a coding assistant work in it: activity, "
          "playbooks (repeated workflows), failures, derived knowledge, and the tools of the "
          "project's own automation agent. Be concrete: name playbook steps, agent tools and "
          "recipes, and say plainly what cannot be automated with the tools that exist. Never "
          "invent figures about the domes; numbers come from the project's own code.")


def deepseek_ask(prompt: str, parts: list[str], temperature: float = 0.3) -> dict:
    cfg = deepseek_config()
    if not cfg["configured"]:
        return {"ok": False, "error": "No key. Set DEEPSEEK_API_KEY and restart."}
    ctx = context_text(parts)
    messages = [{"role": "system", "content": SYSTEM}]
    if ctx:
        messages.append({"role": "user", "content": "CONTEXT\n\n" + ctx})
    messages.append({"role": "user", "content": prompt})
    try:
        t = time.time()
        reply = _post(f"{cfg['base']}/chat/completions", cfg["key"],
                      {"model": cfg["model"], "messages": messages, "temperature": temperature})
        return {"ok": True, "reply": reply["choices"][0]["message"]["content"],
                "ms": int((time.time() - t) * 1000), "usage": reply.get("usage", {}),
                "context_chars": len(ctx), "model": cfg["model"]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": _http_error(exc)}


# ----------------------------------------------------------------------
# The project agent
# ----------------------------------------------------------------------

JOBS: dict[str, dict] = {}
AGENT_LOCK = threading.Lock()


def agent_status() -> dict:
    try:
        from project_agent import config
        return {"ok": True, "planner": "llm" if config.llm_configured() else "rule",
                "base": config.llm_api_base() if config.llm_configured() else "",
                "model": config.llm_model() if config.llm_configured() else "",
                "busy": AGENT_LOCK.locked()}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def agent_plan(prompt: str) -> dict:
    """What the LLM planner would do -- tool calls proposed, nothing executed."""
    from project_agent import config, loop
    if not config.llm_configured():
        calls = loop.RulePlanner().plan([{"role": "user", "content": prompt}])
        return {"ok": True, "planner": "rule", "said": "",
                "calls": [{"name": c.name, "args": c.args} for c in calls]}
    try:
        planner = loop.LlmPlanner()
        calls = planner.plan([loop._system_message(), {"role": "user", "content": prompt}])
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "planner": "llm", "model": planner.model, "said": planner.last_text,
            "calls": [{"name": c.name, "args": c.args} for c in calls]}


def _start_job(kind: str, work) -> dict:
    if not AGENT_LOCK.acquire(blocking=False):
        return {"ok": False, "error": "the agent is already running a job; wait for it to finish"}
    job_id = uuid.uuid4().hex[:10]
    job = {"id": job_id, "kind": kind, "state": "running", "output": "", "result": None,
           "started": time.time()}
    JOBS[job_id] = job

    def run():
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                job["result"] = work()
            job["state"] = "done"
        except Exception as exc:  # noqa: BLE001
            job["state"] = "failed"
            job["result"] = {"error": f"{type(exc).__name__}: {exc}"}
        finally:
            job["output"] = buf.getvalue()
            job["elapsed_s"] = round(time.time() - job["started"], 1)
            AGENT_LOCK.release()

    threading.Thread(target=run, daemon=True).start()
    return {"ok": True, "job": job_id}


def agent_execute(calls: list[dict]) -> dict:
    from project_agent import loop
    planned = [loop.ToolCall(name=str(c.get("name")), args=dict(c.get("args") or {})) for c in calls]

    def work():
        done = loop.execute(planned)
        return {"tool_calls": [{"name": c.name, "args": c.args, "result": c.result} for c in done]}
    return _start_job("execute", work)


def agent_chat(prompt: str) -> dict:
    from project_agent import loop
    run_id = time.strftime("dash-%Y%m%d-%H%M%S")
    return _start_job("chat", lambda: loop.run_chat(prompt, run_id))


def job_view(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if job is None:
        return {"error": f"no job {job_id}"}
    view = dict(job)
    if job["state"] == "running":
        view["elapsed_s"] = round(time.time() - job["started"], 1)
    return json.loads(json.dumps(view, default=str))


# ----------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "DomeSimIntelligence/1"

    def log_message(self, fmt, *args):  # quiet console
        pass

    def _send(self, body, status=200, kind="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{kind}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def do_GET(self):  # noqa: N802
        path, _, query = self.path.partition("?")
        try:
            if path == "/":
                return self._send(PAGE.encode("utf-8"), kind="text/html")
            if path == "/api/overview":
                return self._send(api_overview())
            if path == "/api/episodes":
                return self._send(api_episodes("all=1" in query))
            if path.startswith("/api/episode/"):
                return self._send(api_episode(int(path.rsplit("/", 1)[-1])))
            if path == "/api/playbooks":
                return self._send(procedures.load())
            if path == "/api/failures":
                return self._send(api_failures())
            if path == "/api/knowledge":
                return self._send(api_knowledge())
            if path == "/api/deepseek/verify":
                return self._send(deepseek_verify())
            if path == "/api/agent/status":
                return self._send(agent_status())
            if path.startswith("/api/job/"):
                return self._send(job_view(path.rsplit("/", 1)[-1]))
            return self._send({"error": "not found"}, 404)
        except Exception as exc:  # noqa: BLE001
            return self._send({"error": f"{type(exc).__name__}: {exc}"}, 500)

    def do_POST(self):  # noqa: N802
        body = self._body()
        try:
            if self.path == "/api/extract":
                return self._send(api_extract())
            if self.path == "/api/deepseek/ask":
                return self._send(deepseek_ask(str(body.get("prompt", "")), list(body.get("context") or []),
                                               float(body.get("temperature", 0.3))))
            if self.path == "/api/agent/plan":
                return self._send(agent_plan(str(body.get("prompt", ""))))
            if self.path == "/api/agent/execute":
                return self._send(agent_execute(list(body.get("calls") or [])))
            if self.path == "/api/agent/chat":
                return self._send(agent_chat(str(body.get("prompt", ""))))
            return self._send({"error": "not found"}, 404)
        except Exception as exc:  # noqa: BLE001
            return self._send({"error": f"{type(exc).__name__}: {exc}"}, 500)


PAGE = (Path(__file__).with_name("dashboard.html")).read_text(encoding="utf-8") \
    if (Path(__file__).with_name("dashboard.html")).exists() else "<p>dashboard.html missing</p>"


def selftest() -> None:
    ov = api_overview()
    assert ov["counts"]["actions"] >= 0 and isinstance(ov["top_actions"], list)
    assert isinstance(api_episodes(), list) and isinstance(api_failures(), list)
    assert isinstance(api_knowledge(), list)
    assert "PLAYBOOKS" in context_text(["playbooks"])
    assert "key" not in json.dumps(api_overview()).lower().replace("knowledge", "")
    st = agent_status()
    assert st["ok"], st
    print("dashboard selftest ok")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        selftest()
        return 0
    port = args.port
    for attempt in range(10):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port + attempt), Handler)
            break
        except OSError:
            continue
    else:
        print("no free port")
        return 1
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Intelligence Dashboard on {url}  (Ctrl+C to stop)")
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
