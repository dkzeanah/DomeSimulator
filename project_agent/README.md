# Project Agent — a hyper-specialized media agent for DomeSim

A small, self-contained orchestrator that turns plain-text instructions into
this repository's media (stills, narrated films, books) by operating the
existing programmatic tooling.

It is **not** a general assistant. It knows one project, it can only call the
tools listed below, and it never invents a number: anything it cannot compute
becomes a written question in a ledger.

* Usage, in plain language: `../docs/project-agent-usage.md`
* Design rationale: `../docs/project-agent-blueprint.md`
* What the underlying tools can do: `../docs/agent-utilization-guide.md`

Engine code is never written by the agent. Its writes are confined to
`project_agent/`, `exports/`, `presentations/`, `book/manuscript/`, and new
`two_v_demo/lesson_*.py` / `*_facts.py` files. The one exception is lesson
registration, which edits three known files under backup, validation and
rollback (see below).

## Run

```powershell
py -3.12 -m project_agent              # chat REPL
py -3.12 -m project_agent selftest     # prove the agent's own machinery
py -3.12 -m project_agent sync         # rebuild the knowledge base, exit
py -3.12 -m project_agent facts wedge.tree_yield
py -3.12 -m project_agent demo         # end-to-end vertical slice
```

Or use the launcher's **Project Agent** tab, which drives the same actions
through the repo's usual launch ticket (`project_agent_cli.py`). The chat
action opens its own console window, because a REPL needs somewhere to type.

Everything above works with **no API key**, using the built-in rule planner.
To enable free-text planning against any OpenAI-compatible endpoint:

```powershell
$env:PROJECT_AGENT_API_KEY = "..."
$env:PROJECT_AGENT_API_BASE = "http://localhost:11434/v1"   # e.g. Ollama
$env:PROJECT_AGENT_MODEL = "gpt-4o-mini"                    # or qwen2.5 etc.
py -3.12 -m project_agent
```

## What it is

Five cooperating pieces:

1. **Knowledge base** (`spec.py`) — `sync_knowledge()` dumps the project spec
   from the repo's own menu functions (lessons, presets, deliverables,
   presenter object catalogue and focus targets, live book tokens, the
   lexicon, the facts map, the house rules) into `kb/project_spec.json`, with
   the commit it was taken from. "Understanding DomeSim" is this file,
   refreshed on demand — ground truth, never inference.
2. **Facts map** (`facts.py`) — a curated index of real, validated functions
   (and tables) that compute figures. `query_facts` may call only these, with
   only their declared parameters.
3. **Tool layer** (`tools.py`) — 18 typed tools with JSON schemas over the
   real APIs: `sync_knowledge`, `list_items`, `query_facts`, `selftest`,
   `render_stills`, `export_video`, `export_book`, `verify_render`,
   `read_file`, `write_file`, `declare_constant`, `resolve`, `drop_claim`,
   `scan_claims`, `constants_module`, `view`, `run_recipe`, `help`.
4. **Resolution ledger** (`ledger.py`) — every unknown is a first-class item
   (`computed | declared | estimated | placeholder | dropped | review`) with a
   question, guidance on how to close it, and a status.
5. **Recipes** (`recipes.py`) — ordered, gated production plans. Every run
   writes `runs/<run>/manifest.json`, so a produce run is an auditable file.

## Chat commands (rule planner)

```
list facts | lessons | presets | deliverables | tokens | targets | ledger
facts wedge.tree_yield                # derive a number (proved by selftests)
facts wedge.build_plan trees=2 design_diameter_in=12.5
selftest masterclass lesson=2v        # proofs before frames
stills masterclass at 30,90 lesson=2v # headless PNGs
stills dome_forge at 0                # four named views
declare cord_pickup_usd = 275 USD per cord | Tuscaloosa-area listing
resolve led-0004 = 300 USD delivered | same listing
drop led-0005 unsourceable
claims file=project_agent/examples/pine-script.txt
constants                             # emit resolved constants module
book read_html | read_pdf | audit | render_figures
verify deliverables/masterclass/why-wedges-no-sawmill.mp4
view                                  # open the run folder and LOOK
selftest                              # the agent's own checks
```

## Recipes

`produce <recipe> ...` in the REPL, `python -m project_agent produce ...` on
the command line, or the launcher tab.

| Recipe | What it does |
|---|---|
| `claims` | pasted text → classified claims → resolution ledger |
| `stills` | render + open stills from any world |
| `book` | full book selftest → HTML (optional PDF/figures) |
| `presenter` | stage/validate a Presentation → stills → export |
| `film` | the teaching-film loop (below) |

The **film** recipe, end to end: claim sweep on the source text → scaffold (skipped
on resume) → constants injection from the ledger → narration fill from the source
sentences (never clobbers authored copy) → registration in the three-file contract
→ compile → selftest → one still per chapter, opened for review → optional export →
verify.

Everything is resumable: re-running skips work whose output already exists.

## Robustness notes

The behaviours below are deliberate, and `py -3.12 -m project_agent selftest`
checks each of them:

* **Paths cannot leave the repo.** Every caller-supplied path goes through
  `config.repo_path`, which refuses absolute paths and `..` walks. (An
  absolute path used to escape entirely, because `REPO_ROOT / "/elsewhere"`
  *is* `/elsewhere`.)
* **Launch tickets are locked.** Tools are configured by writing
  `.launcher_configs/<tool>.json` and spawning the tool, which consumes it.
  Two of those in flight race, and the loser runs with the wrong config, so
  the agent takes a lock for the tool while it spawns.
* **The ledger is written atomically**, under a lock, in batches. A claim scan
  files one write, not one per sentence.
* **Registration fails before it writes.** `templates.preflight()` checks
  every anchor in `lesson_registry.py`, `deliverables.py` and
  `render_presets.py` first; all three edits are computed before any is
  written; each file is backed up; the repo's own validators run; any failure
  rolls all three back.
* **Backups live in `project_agent/backups/`** with a manifest, not beside the
  engine files they copy.
* **Subprocess timeouts are reported, not raised**, with the log path.
* **A recipe that crashes still writes its manifest.**

## Notes

* Pixel stills need a working OpenGL 3.3 driver (hidden window or standalone
  context). CSV/SVG/OBJ/text exports need none.
* Spawned repo tools log to files inside `runs/_last/`, never pipes, so runs
  survive constrained shells.
* The facts map is curated on purpose: `query_facts` can only call the named,
  validated functions with the declared parameters.
