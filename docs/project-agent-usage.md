# Project Agent — how it works and how to use it

This is the assistant that lives inside the project. You tell it what you want
in plain words; it operates the project's own tools to make it. It knows only
this project, and that is the point: it does not need to be clever about the
world, only accurate about DomeSim.

Nothing here requires an account, an API key, or an internet connection.

## 1. What it is, in one picture

```
  you type something
        |
        v
  planner ......... turns your words into a list of tool calls
        |            (a built-in command parser, or an LLM if you configure one)
        v
  tools ........... the only things it can do: derive a number, render stills,
        |            run a proof, export a video, build the book, read/write an
        |            allowlisted file, file or resolve an unknown
        v
  the project's real programs (the same ones the launcher runs)
        |
        v
  run manifest .... what was asked, what ran, what came out, which gates passed
```

Three ideas make it trustworthy rather than merely fluent:

**It reads the project instead of remembering it.** `sync` dumps the real
catalogue — every lesson, preset, deliverable, presenter object, book token,
lexicon term and figure the code can compute — into
`project_agent/kb/project_spec.json`, stamped with the commit it came from. It
never guesses what exists.

**Numbers come from code that proves them.** A curated map (`facts.py`) points
at real functions that each have a validator. The agent may call those, with
their declared parameters, and nothing else.

**Unknowns become questions, not guesses.** Anything it cannot compute is
filed in a ledger with a kind, the claim itself, and one line on how to close
it. You answer once; the answer carries its source with it forever after.

## 2. Two ways to run it

**From the launcher** — open the **Project Agent** tab, choose an action, press
*Run Project Agent*. The chat action opens its own console window (the
launcher's log pane has nowhere to type).

**From a terminal:**

```powershell
py -3.12 -m project_agent              # chat
py -3.12 -m project_agent selftest     # check the agent itself
py -3.12 -m project_agent sync         # refresh its map of the project
py -3.12 -m project_agent facts wedge.tree_yield
py -3.12 -m project_agent demo         # guided end-to-end demonstration
py -3.12 -m project_agent produce film key=pine title="..." source=script.txt
```

Start with `selftest`. It takes a few seconds and proves the agent can still
reach everything it depends on.

## 3. The commands

Type these in the chat window (or as `ask` from the launcher tab).

### Learn what exists

```
list lessons | presets | deliverables | facts | tokens | targets | ledger
help
```

### Derive a number

```
facts wedge.tree_yield
facts wedge.build_plan trees=2 design_diameter_in=12.5
facts costing.radius_for_floor floor_sqft=700
```

Every figure comes back with the module that computed it. If the figure you
want is not in `list facts`, it does not exist yet — that is a gap to fill in
code, not something to type into a caption.

### Prove, render, look

```
selftest masterclass lesson=2v      # the lesson's own proofs
stills masterclass at 30,90 lesson=2v
stills dome_forge at 0              # four named views
stills presenter at 4,20 demo=dome_accessibility
view                                # open the folder and actually look
verify deliverables/masterclass/why-wedges-no-sawmill.mp4
```

The order matters and is the house rule: proofs, then stills, then look at
every one, then spend hours on an export.

### Books

```
book audit | read_html | read_pdf | render_figures | progress | outline
```

### Unknowns

```
claims file=project_agent/examples/pine-script.txt
ledger
resolve led-0004 = 275 USD per cord | Tuscaloosa-area listing
declare cord_pickup_usd = 275 USD per cord | same listing
drop led-0005 unsourceable
constants                           # emit a paste-ready constants module
```

## 4. Recipes — complete jobs with gates

A recipe is a whole production run with stops built in. Every one writes
`project_agent/runs/<run>/manifest.json`.

```
produce claims source=script.txt
produce stills backend=masterclass times=30,90 lesson=2v
produce book figures pdf
produce presenter prompt="three scenes about airflow" times=4,20
produce film key=pine_value title="The Twenty Dollar Pine" source=script.txt
```

### The film recipe, step by step

1. **Claim sweep** — every number in your script is filed as a question.
2. **Scaffold** — creates `two_v_demo/lesson_<key>.py` and `<key>_facts.py`
   (skipped if they exist, so a re-run resumes).
3. **Constants** — resolved declared figures from the ledger replace the
   scaffolder's example block.
4. **Narration** — your sentences fill the placeholder chapters. Anything you
   have already written by hand is never overwritten.
5. **Registration** — the three-file contract (`lesson_registry.py`,
   `deliverables.py`, `render_presets.py`). Checked before it writes, backed
   up, validated by the repo's own validators, rolled back on any failure.
6. **Compile → selftest → one still per chapter → look.**
7. **Export and verify** — only when you pass `export=...`.

Leave `export` blank the first time. Stills are minutes; an export is hours.

## 5. What it will not do

* Invent a number, or round one into a caption.
* Write engine code. Writes are confined to `project_agent/`, `exports/`,
  `presentations/`, `book/manuscript/` and new `two_v_demo/lesson_*.py` /
  `*_facts.py` files — plus the three registration files, under backup and
  rollback.
* Read or write anything outside the repository.
* Overwrite a rendered deliverable. Output is append-only.
* Run shell commands you did not ask for.

## 6. Free-text planning (optional)

Set an endpoint and the planner becomes a language model choosing tools
instead of a command parser. Everything else — the tools, the gates, the
ledger — is identical.

```powershell
$env:PROJECT_AGENT_API_KEY  = "..."           # any non-empty value for local
$env:PROJECT_AGENT_API_BASE = "http://localhost:11434/v1"
$env:PROJECT_AGENT_MODEL    = "qwen2.5"
```

Works with OpenAI, Ollama, LM Studio, vLLM, DeepSeek, Groq — anything speaking
the OpenAI chat-completions shape. If the endpoint is unreachable or answers
with an error, the agent says so in one line and keeps running; it does not
fall over.

## 7. Where things live

```
project_agent/
  kb/project_spec.json     the project's own catalogue, regenerated by `sync`
  ledger.jsonl             every unknown, its status, and its source
  runs/<run>/manifest.json what one run asked for, ran, produced, and gated
  runs/_last/*.log         the raw output of every spawned tool
  backups/                 copies of any engine file registration touched
  examples/                sample input
```

## 8. Troubleshooting

**"another process is using the … launch ticket"** — a render is already
running. Tools are configured by a one-shot ticket file, so the agent waits
rather than racing it. Let the render finish.

**A still render produced nothing** — check the log named in the result. The
usual cause is no OpenGL 3.3 driver in that session.

**`selftest` fails on "registration anchors"** — the engine files changed
shape and the agent's insertion points no longer match. That check exists so
you find out here, in seconds, instead of half-way through registering a film.

**The agent does not understand a sentence** — the built-in parser only knows
the commands above. Either use one, or configure an endpoint (§6) for
free-text planning.

## 9. What changed in the hardening pass

The first version of this agent worked but had defects that only showed up
under load or after the repo moved on. Each of these is now fixed *and*
checked by `selftest`:

| Fault | Now |
|---|---|
| `help` crashed on every call | Fixed; covered by the selftest |
| A facts entry pointed at a table and was called as a function | Entries declare `kind`; tables are read as data |
| An absolute path escaped the repository on read | Every path goes through one boundary check |
| A bare `--flag` swallowed the next `key=value` argument | Switches are declared; parsing is checked against every form |
| The registry anchor assumed one lesson name per line | Registration finds the tuple structurally, and is idempotent |
| Backups were written beside engine files | They go to `project_agent/backups/` with a manifest |
| The whole ledger was rewritten per filed claim | Batched, atomic, locked |
| A claim's classification was computed then discarded | Kept, and shown as the guidance line |
| A subprocess timeout raised through a recipe | Reported as a result with its log path |
| A crashing recipe left no manifest | Always writes one |
| Concurrent runs could clobber each other's launch ticket | Tickets are locked per tool |
