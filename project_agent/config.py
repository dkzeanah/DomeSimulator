"""Paths, environment, locks and limits for the project agent.

Everything the agent writes lives under ``project_agent/`` (its own package
directory) or the repo's conventional output folders.  Engine source is never
written by the agent's tools.

Two things here are load-bearing for robustness:

* :func:`repo_path` is the one place a caller-supplied path becomes a real
  path.  It refuses anything that resolves outside the repository, which is
  what stops an absolute path or a ``..`` walk from reaching the rest of the
  disk.
* :func:`ticket_lock` serialises launch tickets.  The repo's tools are
  configured by writing ``.launcher_configs/<tool>.json`` and then spawning the
  tool, which consumes and deletes it.  Two of those in flight at once — an
  agent run while a render is going, or two agent runs — race for the same
  file, and the loser silently gets the wrong configuration.
"""

from __future__ import annotations

import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

# The repository root is the parent of this package directory.
PKG_DIR = Path(__file__).resolve().parent
REPO_ROOT = PKG_DIR.parent

RUNS_DIR = PKG_DIR / "runs"
KB_DIR = PKG_DIR / "kb"
KB_PATH = KB_DIR / "project_spec.json"
LEDGER_PATH = PKG_DIR / "ledger.jsonl"
EXAMPLES_DIR = PKG_DIR / "examples"
BACKUPS_DIR = PKG_DIR / "backups"
"""Where file backups go.

Deliberately inside the package: the first version scattered
``*.agent-bak-<timestamp>`` files next to the engine files it edited, which
puts agent litter in the repository root and in ``two_v_demo/``."""

LOCKS_DIR = PKG_DIR / "locks"

# Timeouts, in seconds. Named so a caller can say what it is waiting for
# instead of sprinkling integers through the tool layer.
TIMEOUT_QUICK = 300        # compile, validators, a report
TIMEOUT_SELFTEST = 900     # a lesson's proof suite
TIMEOUT_STILLS = 1800      # a headless still render
TIMEOUT_EXPORT = 6 * 3600  # a narrated film export
TICKET_LOCK_WAIT = 900     # how long to wait for another ticket to clear


# ---------------------------------------------------------------------------
# LLM configuration (all optional; absent => the rule-based planner runs)
# ---------------------------------------------------------------------------


def llm_api_key() -> str:
    return (os.environ.get("PROJECT_AGENT_API_KEY")
            or os.environ.get("OPENAI_API_KEY") or "")


def llm_api_base() -> str:
    return (os.environ.get("PROJECT_AGENT_API_BASE")
            or "https://api.openai.com/v1").rstrip("/")


def llm_model() -> str:
    return os.environ.get("PROJECT_AGENT_MODEL") or "gpt-4o-mini"


def llm_configured() -> bool:
    return bool(llm_api_key())


def llm_timeout() -> int:
    try:
        return max(10, int(os.environ.get("PROJECT_AGENT_TIMEOUT", "300")))
    except ValueError:
        return 300


def agent_python() -> str:
    """Interpreter used to spawn the repo's tools for stills/exports."""
    return os.environ.get("PROJECT_AGENT_PYTHON") or sys.executable


def ensure_dirs() -> None:
    for directory in (RUNS_DIR, KB_DIR, EXAMPLES_DIR, BACKUPS_DIR, LOCKS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Safe path resolution
# ---------------------------------------------------------------------------


class PathOutsideRepo(ValueError):
    """A caller-supplied path resolved outside the repository."""


def repo_path(value: str | Path, *, must_exist: bool = False) -> Path:
    """Resolve ``value`` against the repo root and refuse to leave it.

    An absolute path is allowed only when it is already inside the repository;
    ``Path(REPO_ROOT) / "/etc/passwd"`` is simply ``/etc/passwd``, which is why
    joining alone is not a boundary.
    """
    raw = Path(str(value))
    candidate = (raw if raw.is_absolute() else REPO_ROOT / raw)
    resolved = candidate.resolve()
    root = REPO_ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise PathOutsideRepo(
            f"{value!r} resolves to {resolved}, which is outside {root}")
    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"no such path: {resolved}")
    return resolved


def relative_to_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Launch-ticket lock
# ---------------------------------------------------------------------------


class TicketBusy(RuntimeError):
    """Another process holds the launch ticket for this tool."""


def _lock_path(tool: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in tool)
    return LOCKS_DIR / f"{safe}.lock"


def _stale(path: Path, max_age: float) -> bool:
    try:
        return (time.time() - path.stat().st_mtime) > max_age
    except OSError:
        return True


@contextmanager
def ticket_lock(tool: str, wait: float = TICKET_LOCK_WAIT,
                poll: float = 1.0, max_age: float = 12 * 3600):
    """Hold the exclusive right to write ``tool``'s launch ticket.

    The repo's tools consume their ticket at startup, so the window between
    writing one and the tool reading it is small but real. Waiting here is
    better than either racing or refusing: a long export can legitimately hold
    the tool for hours, and the caller usually wants to queue behind it.

    A lock older than ``max_age`` is treated as abandoned (a killed process
    cannot clean up after itself) and is broken rather than waited on forever.
    """
    ensure_dirs()
    path = _lock_path(tool)
    deadline = time.monotonic() + wait
    handle = None
    while True:
        try:
            handle = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if _stale(path, max_age):
                try:
                    path.unlink()
                except OSError:
                    pass
                continue
            if time.monotonic() >= deadline:
                raise TicketBusy(
                    f"another process is using the {tool!r} launch ticket "
                    f"(lock: {path}). Wait for it to finish, or delete the "
                    "lock file if nothing is actually running.") from None
            time.sleep(poll)
    try:
        os.write(handle, f"{os.getpid()} {time.strftime('%Y-%m-%dT%H:%M:%S')}\n"
                 .encode("utf-8"))
        os.close(handle)
        handle = None
        yield path
    finally:
        if handle is not None:
            os.close(handle)
        try:
            path.unlink()
        except OSError:
            pass
