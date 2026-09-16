"""CLI entry for the Project Agent.

    python -m project_agent            # chat REPL
    python -m project_agent sync       # rebuild the knowledge base and exit
    python -m project_agent facts <id> # one facts-module query
    python -m project_agent demo       # scripted end-to-end vertical slice

The demo proves the whole chain with no API key: knowledge sync ->
facts derivation -> headless stills -> claim scan / gap finding ->
ledger resolution -> constants module -> manifest -> open the outputs
for visual review.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from . import config, ledger, loop, tools
from .config import ensure_dirs


def _banner() -> None:
    planner = "LLM function-calling" if config.llm_configured() else "rule parser"
    print("=" * 72)
    print(" DomeSim Project Agent  -  hyper-specialized media agent")
    print(f" repo: {config.REPO_ROOT}")
    print(f" planner: {planner}"
          + (f"  ({config.llm_model()} @ {config.llm_api_base()})"
             if config.llm_configured() else "  (set PROJECT_AGENT_API_KEY for "
             "free-text planning)"))
    print(" commands: list facts | facts <id> | stills <backend> at t1,t2 "
          "| selftest | declare | resolve | claims | book | verify | view | "
          "help")
    print(" recipes:  produce film key=<key> title=\"<title>\" source=<text.txt> "
          "[declare=name=value unit|source] [export=out.mp4]")
    print("           produce presenter demo=<demo>|prompt=\"<brief>\" "
          "[export=out.mp4] | produce book [figures] [pdf]")
    print("           produce stills backend=<world> at t1,t2 | produce claims "
          "source=<text.txt>")
    print("=" * 72)


def cmd_sync() -> int:
    from . import spec
    print("syncing project knowledge from the repo...")
    data = spec.sync_knowledge(write=True)
    print(spec.kb_summary(data))
    failures = [name for name, sec in data["sections"].items() if not sec["ok"]]
    if failures:
        print(f"note: {len(failures)} section(s) failed and were recorded: "
              f"{', '.join(failures)}")
        print("  (expected where optional dependencies are missing; the spec "
              "stays usable)")
    print(f"saved: {config.KB_PATH}")
    return 0


def cmd_selftest() -> int:
    """Prove the agent's own contracts before trusting it with a render."""
    from . import selftest
    print("project agent selftest")
    return selftest.run()


def cmd_facts(fact_id: str) -> int:
    result = tools.dispatch("query_facts", {"id": fact_id})
    print(json.dumps(result, indent=2, default=str)[:6000])
    return 0 if result.get("ok") else 1


def cmd_demo() -> int:
    ensure_dirs()
    run_id = time.strftime("%Y%m%d-%H%M%S") + "-demo"
    run_dir = config.RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    def step(label: str, name: str, args: dict) -> dict:
        print(f"\n--- {label} ---")
        result = tools.dispatch(name, args)
        records.append({"label": label, "tool": name, "args": args,
                        "ok": result.get("ok"), "result": result})
        if result.get("error"):
            print(f"  ERROR: {result['error']}")
        for path in result.get("paths", []):
            print(f"  + {path}")
        for path in result.get("missing", []):
            print(f"  - MISSING {path}")
        for key in ("written", "item", "filed", "opened"):
            if key in result and result[key] not in (None, "", []):
                print(f"  {key}: {result[key]}")
        return result

    # 1. Knowledge sync — the whole "understanding a limited project set".
    from . import spec
    data = spec.sync_knowledge(write=True)
    print("--- 1. knowledge sync ---")
    print(spec.kb_summary(data))

    # 2. Facts derivation — the derive-and-simulate step.
    yield_result = step("2a. facts: what one tree yields (computed + proved)",
                        "query_facts", {"id": "wedge.tree_yield"})
    if yield_result.get("ok"):
        ty = yield_result["result"]
        print(f"    solid bf: {ty['solid_bf']}  wedge bf: {ty['wedge_bf']}  "
              f"2x4 bf: {ty['two_by_four_bf']}  struts: {ty['strut_count']}  "
              f"wedge recovery: {ty.get('wedge_recovery')}")
    pine_result = step("2b. facts: the pine value-ladder model",
                       "query_facts", {"id": "pine.model"})
    if pine_result.get("ok"):
        pine = pine_result["result"]
        print(f"    framing value/tree: {pine['framing_value']}  "
              f"financed: {pine['financed_value']}  wage: {pine['wage']}")

    # 3. Headless stills — the vertical slice's proof.
    stills_result = step("3a. stills: 2V lesson at 30s and 90s",
                         "render_stills",
                         {"backend": "masterclass", "lesson": "2v",
                          "times": ["30", "90"], "size": "1600x900"})
    forge_result = step("3b. stills: dome forge, four named views",
                        "render_stills",
                        {"backend": "dome_forge", "times": ["0"], "size": "1600x900"})

    # 4. Gap finding on the pine script.
    sample = config.EXAMPLES_DIR / "pine-script.txt"
    claims_result = step(f"4. claim scan: {sample.name}", "scan_claims",
                         {"path": str(sample.relative_to(config.REPO_ROOT))})
    if claims_result.get("ok"):
        print(f"    {claims_result['filed']} numeric claims filed:")
        for item in claims_result["items"]:
            print(f"      {item['id']}  [{item['kind']}] {item['question'][:100]}")

    # 5. The easy resolving system: declare one gap shut, emit constants.
    declare_result = step("5a. resolve a gap: the Tuscaloosa cord listing",
                          "declare_constant",
                          {"name": "cord_pickup_usd", "value": "275",
                           "unit": "USD per cord",
                           "source": "Tuscaloosa-area firewood seller listing"})
    constants_result = step("5b. emit paste-ready constants module",
                            "constants_module",
                            {"out": f"project_agent/runs/{run_id}/resolved_constants.py"})

    # 6. Manifest + visual review gate.
    outputs = []
    for result in (stills_result, forge_result):
        outputs.extend(result.get("paths", []) if isinstance(result, dict) else [])
    manifest = {
        "run_id": run_id, "kind": "vertical-slice demo",
        "brief": ("prove the chain: chat input -> knowledge -> facts -> "
                  "stills -> claim scan -> ledger resolution -> constants"),
        "records": records,
        "outputs": outputs,
        "gates": {
            "stills_produced": bool(outputs),
            "gaps_filed": claims_result.get("filed", 0) if claims_result.get("ok") else 0,
            "gaps_resolved": 1 if declare_result.get("ok") else 0,
            "constants_emitted": bool(constants_result.get("ok")),
        },
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print(f"\n--- 6. manifest ---")
    print(f"    run: {run_id}")
    print(f"    stills: {len(outputs)}  manifest: {run_dir / 'manifest.json'}")
    print(f"    ledger: {config.LEDGER_PATH}")

    view_result = tools.dispatch("view", {"path": str(run_dir)})
    print("\nopening the run folder so every still can be looked at "
          "(the stills-before-video gate).")
    print(f"demo complete: {run_dir}")
    return 0


def repl() -> int:
    _banner()
    run_counter = 0
    print("\ntype a command (help for the list, quit to exit).\n")
    while True:
        try:
            user_text = input("agent> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return 0
        if not user_text:
            continue
        if user_text.lower() in ("quit", "exit", "q"):
            print("bye")
            return 0
        if user_text.lower() == "sync":
            cmd_sync()
            continue
        if user_text.lower() in ("selftest", "check"):
            cmd_selftest()
            continue
        run_counter += 1
        run_id = time.strftime("%Y%m%d-%H%M%S") + f"-chat{run_counter}"
        try:
            loop.run_chat(user_text, run_id)
        except KeyboardInterrupt:
            print("\n(interrupted; the run manifest may be incomplete)")
            continue
        except Exception as exc:                          # noqa: BLE001
            # One bad turn must not end the session: report and keep the REPL.
            print(f"!!! {type(exc).__name__}: {exc}")
            continue
        pending = ledger.items(status="pending")
        if pending:
            print(f"\n{len(pending)} ledger item(s) pending - "
                  f"say 'ledger' to review, 'resolve led-XXXX = value | "
                  f"source' to close one.")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    mode = args[0] if args else "chat"
    if mode == "sync":
        return cmd_sync()
    if mode == "facts":
        return cmd_facts(args[1] if len(args) > 1 else "")
    if mode == "demo":
        return cmd_demo()
    if mode in ("selftest", "check"):
        return cmd_selftest()
    if mode == "produce":
        recipe = args[1] if len(args) > 1 else ""
        params = loop.parse_produce_args(args[2:])
        result = tools.dispatch("run_recipe", {"recipe": recipe, "params": params})
        if result.get("error"):
            print(f"produce: {result['error']}")
        if result.get("manifest"):
            print(f"manifest: {result['manifest']}")
        return 0 if result.get("ok") else 1
    if mode in ("chat", "repl"):
        return repl()
    print("usage: python -m project_agent [chat|sync|selftest|demo|"
          "facts <id>|produce <recipe> key=... title=... source=...]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
