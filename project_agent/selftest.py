"""The agent's own proof suite.

The repo's rule is that a tool proves itself before it is trusted with a
render.  This is that check for the agent: it exercises the contracts the agent
depends on — the tool registry, the path boundary, the ledger's read/write
cycle, the facts map, the registration anchors in the engine files, and the
knowledge sync — and reports every failure rather than stopping at the first.

    py -3.12 -m project_agent selftest

Nothing here renders, exports, or edits an engine file.  The ledger checks run
against a temporary file, so a selftest never touches the real one.
"""

from __future__ import annotations

import importlib
import json
import tempfile
import traceback
from pathlib import Path

from . import config


class Check:
    """One named assertion with a human-readable outcome."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.ok = True
        self.detail = ""

    def fail(self, detail: str) -> None:
        self.ok = False
        self.detail = detail


def _run(name: str, body) -> Check:
    check = Check(name)
    try:
        detail = body()
        check.detail = str(detail or "")
    except AssertionError as exc:
        check.fail(f"assertion failed: {exc}")
    except Exception as exc:                              # noqa: BLE001
        check.fail(f"{type(exc).__name__}: {exc}\n"
                   + "".join(traceback.format_exc(limit=3)))
    return check


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------


def _check_paths() -> str:
    """The path boundary holds for absolute paths and parent walks."""
    inside = config.repo_path("project_agent/config.py")
    assert inside.is_file(), inside
    for bad in (str(Path.home() / ".gitconfig"), "../outside.txt",
                "project_agent/../../escape.txt"):
        try:
            config.repo_path(bad)
        except config.PathOutsideRepo:
            continue
        raise AssertionError(f"{bad!r} was allowed but resolves outside the repo")
    return "absolute paths and parent walks refused"


def _check_tools() -> str:
    """Every registered tool is callable and describes itself correctly."""
    from . import tools

    assert tools.TOOLS, "no tools registered"
    for name, entry in tools.TOOLS.items():
        assert callable(entry.get("call")), f"{name}: no callable"
        assert str(entry.get("description", "")).strip(), f"{name}: no description"
        schema = entry.get("schema") or {}
        function = schema.get("function") or {}
        assert function.get("name") == name, (
            f"{name}: schema names it {function.get('name')!r}")
        params = function.get("parameters") or {}
        properties = params.get("properties", {})
        for required in params.get("required", []):
            assert required in properties, (
                f"{name}: required {required!r} is not a declared property")
        json.dumps(schema)                                # must be serialisable

    unknown = tools.dispatch("nope", {})
    assert unknown["ok"] is False, "an unknown tool reported success"

    help_result = tools.dispatch("help", {})
    assert help_result.get("ok"), f"help failed: {help_result.get('error')}"
    assert "run_recipe" in help_result.get("text", ""), "help lists no tools"

    denied = tools.dispatch("write_file", {"path": "two_v_demo/app.py",
                                           "content": "x"})
    assert denied["ok"] is False, "the write allowlist let engine source through"
    return f"{len(tools.TOOLS)} tools, schemas valid, allowlist holds"


def _check_facts() -> str:
    """Every facts entry resolves to something of the kind it claims."""
    from .facts import FACT_SPECS

    assert FACT_SPECS, "no facts registered"
    broken: list[str] = []
    for fact_id, spec in FACT_SPECS.items():
        try:
            module = importlib.import_module(spec.module)
            attribute = getattr(module, spec.func)
        except Exception as exc:                          # noqa: BLE001
            broken.append(f"{fact_id}: {type(exc).__name__}: {exc}")
            continue
        kind = getattr(spec, "kind", "call")
        if kind == "call" and not callable(attribute):
            broken.append(f"{fact_id}: {spec.module}.{spec.func} is not "
                          "callable but is declared kind='call'")
        if kind == "value" and callable(attribute):
            broken.append(f"{fact_id}: declared kind='value' but is callable")
    assert not broken, "; ".join(broken)

    from . import tools
    probe = tools.dispatch("query_facts", {"id": "wedge.tree_yield"})
    assert probe.get("ok"), f"wedge.tree_yield failed: {probe.get('error')}"
    return f"{len(FACT_SPECS)} facts entries resolve"


def _check_ledger() -> str:
    """The ledger round-trips, stays atomic, and does not duplicate claims."""
    from . import ledger

    original = ledger.LEDGER_PATH
    with tempfile.TemporaryDirectory() as directory:
        ledger.LEDGER_PATH = Path(directory) / "ledger.jsonl"
        try:
            first = ledger.add_item("constant probe_value", kind="declared")
            assert first.id == "led-0001", first.id
            resolved = ledger.resolve(first.id, "275 USD per cord",
                                      source="probe listing")
            assert resolved and resolved.status == "resolved"
            assert ledger.items(status="resolved"), "resolve did not persist"

            text = ("A cord sells for $275 in town. The frame needs 120 "
                    "members. Roughly 40% of the log is lost.")
            filed = ledger.scan_claims(text, quiet=True)
            assert filed, "claim scan filed nothing"
            assert all(item.ask for item in filed), (
                "a filed claim has no guidance; the classification was lost")
            again = ledger.scan_claims(text, quiet=True)
            assert not again, f"re-scanning duplicated {len(again)} claim(s)"

            out = Path(directory) / "constants.py"
            ledger.constants_module(out)
            body = out.read_text(encoding="utf-8")
            assert "probe_value" in body, body[:200]
            assert "275.0" in body, body[:200]

            dropped = ledger.drop(filed[0].id, note="probe")
            assert dropped and dropped.status == "dropped"
            lines = [l for l in ledger.LEDGER_PATH.read_text(
                encoding="utf-8").splitlines() if l.strip()]
            for line in lines:
                json.loads(line)                          # every line is whole
            return f"{len(lines)} items round-tripped, no duplicates"
        finally:
            ledger.LEDGER_PATH = original


def _check_registration_anchors() -> str:
    """The engine files still have every anchor registration depends on."""
    from . import templates

    ready = templates.preflight()
    broken = [f"{c['name']} ({c['detail']})" for c in ready["checks"]
              if not c["ok"]]
    assert ready["ok"], "; ".join(broken)

    # And the insert is exercised in memory, so a shape change is caught here
    # rather than half-way through a registration.
    text = templates.REGISTRY_PATH.read_text(encoding="utf-8")
    probed = templates._insert_registry_entry(text, "SELFTEST_PROBE")
    assert "SELFTEST_PROBE_LESSON" in probed, "registry insert produced nothing"
    assert probed != text and len(probed) > len(text)
    again = templates._insert_registry_entry(probed, "SELFTEST_PROBE")
    assert again == probed, "registry insert is not idempotent"
    return f"{len(ready['checks'])} anchors present, insert is idempotent"


def _check_recipes() -> str:
    """Recipes are registered with runnable entries, and params parse."""
    from . import loop, recipes

    assert recipes.RECIPES, "no recipes registered"
    for name, entry in recipes.RECIPES.items():
        assert callable(entry.get("run")), f"{name}: not runnable"
        assert str(entry.get("label", "")).strip(), f"{name}: no label"
    unknown = recipes.run_recipe("nope", {})
    assert unknown["ok"] is False

    parsed = loop.parse_produce_args(
        ["key=pvtwo", "title=Two Pines", "times=4,20", "--no_narration",
         "declare=cord=275 USD|listing", "script.txt"])
    assert parsed["key"] == "pvtwo", parsed
    assert parsed["times"] == ["4", "20"], parsed
    assert parsed["no_narration"] == "1", parsed
    assert parsed["source"] == "script.txt", parsed
    assert parsed["declare"] == ["cord=275 USD|listing"], parsed
    return f"{len(recipes.RECIPES)} recipes, parser handles every form"


def _check_knowledge() -> str:
    """The knowledge base builds, and names the sections that failed."""
    from . import spec

    data = spec.sync_knowledge(write=False)
    sections = data["sections"]
    failed = [name for name, section in sections.items() if not section["ok"]]
    assert not failed, ("sections failed: " + ", ".join(
        f"{name} ({sections[name]['error']})" for name in failed))
    assert spec.kb_summary(data).strip(), "empty summary"
    return f"{len(sections)} sections synced"


CHECKS = (
    ("paths stay inside the repo", _check_paths),
    ("tool registry", _check_tools),
    ("facts map", _check_facts),
    ("ledger", _check_ledger),
    ("registration anchors", _check_registration_anchors),
    ("recipes and parsing", _check_recipes),
    ("knowledge sync", _check_knowledge),
)


def run(verbose: bool = True) -> int:
    """Run every check.  Returns a process exit code."""
    config.ensure_dirs()
    results = []
    for name, body in CHECKS:
        check = _run(name, body)
        results.append(check)
        if verbose:
            mark = "ok  " if check.ok else "FAIL"
            first = check.detail.splitlines()[0] if check.detail else ""
            print(f"  [{mark}] {name:<28} {first}")
            if not check.ok and len(check.detail.splitlines()) > 1:
                for line in check.detail.splitlines()[1:6]:
                    print(f"         {line}")
    failed = [c for c in results if not c.ok]
    if verbose:
        print()
        print(f"{len(results) - len(failed)}/{len(results)} checks passed"
              if failed else f"all {len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
