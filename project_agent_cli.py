"""Launcher entry point for the Project Agent.

Every other tool in this repository is configured by a launch ticket: the
launcher writes ``.launcher_configs/<tool>.json`` and spawns the script with no
arguments, and the script consumes the ticket at startup (see
``launcher_common.py``).  This file gives the agent that same shape, so it can
sit in the launcher beside everything else.

Run directly with no ticket and it opens the chat REPL, exactly like
``py -3.12 -m project_agent``.

Actions
-------
``chat``      open the chat REPL (in its own console window when launched
              from the GUI, which has no keyboard to type into)
``selftest``  prove the agent's own contracts and exit
``sync``      rebuild the knowledge base from the repo and exit
``demo``      the scripted end-to-end vertical slice
``facts``     derive one figure (``fact`` names it)
``ledger``    print the resolution ledger
``produce``   run a recipe (``recipe`` plus its parameters)
``ask``       run one chat turn non-interactively (``text``)
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import launcher_common as lc  # noqa: E402


def _open_console_repl() -> int:
    """Start the REPL in its own console window.

    The launcher pipes a tool's output into its log pane, which is fine for a
    render and useless for a prompt: there is nowhere to type. On Windows the
    REPL therefore gets a real console of its own; elsewhere it runs inline.
    """
    command = [sys.executable, "-m", "project_agent"]
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        subprocess.Popen(command, cwd=str(ROOT), creationflags=creationflags)
        print("Project Agent chat opened in a new console window.")
        print("Type 'help' there for the command list, 'quit' to close it.")
        return 0
    return subprocess.call(command, cwd=str(ROOT))


def _params_from(cfg: dict) -> dict:
    """Recipe parameters from the ticket.

    Accepts either a ready-made ``params`` object or the flat fields the
    launcher tab fills in, so the GUI never has to build nested JSON.
    """
    from project_agent import loop

    params = dict(cfg.get("params") or {})
    for key in ("key", "title", "source", "export", "size", "fps", "times",
                "demo", "prompt", "environment", "backend", "lesson",
                "voice", "voice_rate", "voice_pitch", "voice_volume",
                "orientation", "overlay", "script"):
        value = cfg.get(key)
        if value not in (None, "", []):
            params[key] = value
    for flag in ("no_narration", "figures", "pdf", "compose_segments"):
        if cfg.get(flag):
            params[flag] = "1"
    if isinstance(params.get("times"), str):
        params["times"] = [t.strip() for t in params["times"].split(",")
                           if t.strip()]
    extra = str(cfg.get("extra_params") or "").strip()
    if extra:
        tokens = [m[0] or m[1] for m in
                  __import__("re").findall(r'"([^"]*)"|(\S+)', extra)]
        params.update(loop.parse_produce_args(tokens))
    declare = cfg.get("declare")
    if declare:
        rows = declare if isinstance(declare, list) else [declare]
        params.setdefault("declare", []).extend(
            str(row) for row in rows if str(row).strip())
    return params


def main() -> int:
    cfg = lc.consume_config("project_agent")
    action = str(cfg.get("action") or "chat").lower()

    if action == "authoring_prompt":
        # Write the paste-into-a-model prompt and stop. No agent, no LLM, no
        # render: this action exists so the knowledge can leave the project as
        # text and come back as a file you save yourself.
        from project_agent.authoring import build_prompt
        out = Path(str(cfg.get("out")
                       or "project_agent/authoring/PROMPT.md"))
        out.parent.mkdir(parents=True, exist_ok=True)
        text = build_prompt(str(cfg.get("brief") or ""))
        out.write_text(text, encoding="utf-8")
        words = len(text.split())
        print(f"wrote {out}")
        print(f"{words:,} words, about {int(words * 1.33):,} tokens")
        print("open it, paste the whole file into your model, and add one "
              "line saying what you want drawn.")
        return 0

    from project_agent import config as agent_config
    from project_agent import ledger, loop, tools
    from project_agent.__main__ import cmd_demo, cmd_facts, cmd_selftest, cmd_sync

    agent_config.ensure_dirs()

    if action == "chat":
        return _open_console_repl()
    if action == "selftest":
        return cmd_selftest()
    if action == "sync":
        return cmd_sync()
    if action == "demo":
        return cmd_demo()
    if action == "facts":
        fact_id = str(cfg.get("fact") or "").strip()
        if not fact_id:
            print("facts needs a fact id, e.g. wedge.tree_yield")
            print(tools.dispatch("list_items", {"kind": "facts"}).get("text", ""))
            return 2
        return cmd_facts(fact_id)
    if action == "ledger":
        print(ledger.ledger_text())
        return 0
    if action == "ask":
        text = str(cfg.get("text") or "").strip()
        if not text:
            print("ask needs text")
            return 2
        run_id = time.strftime("%Y%m%d-%H%M%S") + "-ask"
        manifest = loop.run_chat(text, run_id)
        print(f"manifest: {manifest.get('manifest_path', '')}")
        return 0
    if action == "produce":
        recipe = str(cfg.get("recipe") or "").strip()
        if not recipe:
            print("produce needs a recipe: claims, stills, book, presenter, film")
            return 2
        params = _params_from(cfg)
        print(f"produce {recipe} {params}")
        result = tools.dispatch("run_recipe", {"recipe": recipe,
                                               "params": params})
        if result.get("error"):
            print(f"produce: {result['error']}")
        if result.get("manifest"):
            print(f"manifest: {result['manifest']}")
        return 0 if result.get("ok") else 1

    print(f"unknown action {action!r}; expected one of: chat, selftest, sync, "
          "demo, facts, ledger, ask, produce")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
