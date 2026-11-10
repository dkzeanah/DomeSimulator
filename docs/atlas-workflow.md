# Atlas-assisted DomeSim development

## Available now

The project `.mcp.json` starts a four-tool, project-scoped Atlas MCP server. Its
host script currently lives in MacroAutomate's bridge, but it directly reuses the
maintained Atlas engine/database in avideditor/projects/harness. It needs neither
the Fan HTTP gateway nor Cutline, DeepSeek, a model API key, or port 3080. No
retrieval call invokes an LLM. A client model will still bill for tool schemas,
requests, responses and its own reasoning/output.

From PowerShell:

```powershell
Set-Location 'C:\Users\Don\Desktop\DomeSim'
claude
```

Use Claude's `/mcp` to check the `atlas` connection. Claude Code may require its
normal project-server trust approval. Ask it:

> Follow docs/atlas-claude-task.md. Begin with atlas_project, then retrieve only
> the source needed for the initial refactor proposal.

The server provides:

| Tool | Purpose |
|---|---|
| atlas_project | Counts, indexing time, Python coverage, top directory counts |
| atlas_find | Task-intent search within DomeSim; at most 12 metadata matches |
| atlas_get | Exact symbol page, at most 120 lines/8,000 source characters; continuation cursor |
| atlas_impact | Bounded recorded edges and resolvable callers, with incompleteness warning |

Detected stale bodies are withheld. The engine's current freshness comparison
uses its existing short body hash; this is not a cryptographic consistency
guarantee. Returned SHA-256 values identify retrieved content for a future context
ledger; they are not currently an automatic cache or persistent snapshot service.
Each request uses a read-only SQLite connection. The tools cannot edit or reindex
the project. The client retains its own native read/edit/shell capabilities.

Refresh only DomeSim using the existing CLI (no source rewrite):

```powershell
Set-Location 'C:\Users\Don\Desktop\avideditor\projects\harness'
py -3.12 -m atlas.cli index 'C:\Users\Don\Desktop\DomeSim' --name DomeSim --bucket sim3d --priority 90
py -3.12 -m atlas.cli export
```

Indexing currently scans Python with existing exclusion/size/count limits. It
does not establish complete TypeScript/React, SQL, config, Markdown or runtime
dependency coverage. Native reads remain an explicit, measured fallback. Call
edges are heuristics, including name resolution ambiguity. Empty caller results
do not imply safe isolation. No broad refactor has been executed by setup.

Use Python 3.12 for DomeSim indexing: the shared avideditor venv currently runs
3.11 and reports two valid 3.12 f-string constructs as parse errors. `dflat.py` is
a pre-existing flattened Markdown document with a Python extension; its parse
failure is expected and does not indicate an executable source regression.

## Connect other clients

Any stdio MCP client can launch the same interpreter, script and two environment
variables from `.mcp.json`; the four-tool interface is not Claude-specific.
For Codex, the following is a configuration fragment to merge into the desired
trusted configuration, not a replacement for existing settings:

```toml
[mcp_servers.atlas]
command = 'C:\Users\Don\Desktop\aAutomateMacro\fan\DeepSeekBridge\.venv\Scripts\python.exe'
args = ['C:\Users\Don\Desktop\aAutomateMacro\fan\DeepSeekBridge\bridge\atlas_mcp.py']

[mcp_servers.atlas.env]
ATLAS_WORKSPACE = 'C:\Users\Don\Desktop\avideditor\projects\harness'
ATLAS_PROJECT = 'DomeSim'
```

DeepSeek Harness can use the same stdio command in a separate optional MCP client
entry (serverName atlas). Its existing `fan` entry continues to offer desktop,
DeepSeek-agent and media execution; adding Atlas does not replace that entry.
Neither client configuration has been changed automatically by this setup.

## Shared harness and custom control interface: next implementation

Keep a deterministic context service and a task controller as separate layers:

```
Control interface -> task controller -> Claude / Codex / DeepSeek adapter
                         |                         |
                         +------ Atlas MCP --------+
                                                   |
                                     edits, tests, Fan/media tools
                                                   |
                               events, usage, diff, artifacts -> interface
```

MCP supplies context/tools; it does not itself launch a Claude conversation or
consume the agent's streaming response. Use Claude Agent SDK for programmatic
sessions and permission callbacks, or `claude -p` JSON streaming for a simpler
adapter. Use Codex app-server for bidirectional turns, approvals and events.
DeepSeek needs its own existing Harness/agent task adapter; web port 3080 alone
is not an interchangeable protocol. Capability-detect each installed version.

Reuse the existing SideLearner CLI adapter, Fan task/event storage and Atlas token
ledger where they fit. The current SideLearner CLI adapter waits for process
completion; streaming, resume and normalized approvals need additional adapters.
The four-tool server is a foundation, not this completed orchestration layer.

The controller should keep task/run IDs, client/provider session IDs, allowed
workspace, source revision + dirty diff fingerprint, index snapshot/coverage,
bounded retrieved-content IDs, model/settings, events, tests, diff and artifacts.
Record changes and evidence references rather than replaying complete directories
and histories. Avoid loading Fan's entire automation tool catalog for read-only
code questions. Reference-only content IDs do not give a model unseen content;
resend required evidence after compaction or when switching agents.

The interface should expose project/subsystem and coverage views, task input,
provider/model selection, live tool/command events, context inspector, usage,
diff/tests, approvals, cancellation, and reindex status. Show agent-reported
explanations and observable actions; private model reasoning is not a dashboard
requirement. Cancellation must stop owned child work, not just hide a UI row.
One writer per workspace; parallel edits require isolated workspaces and explicit
integration. Automatic reindexing must follow completed edits and expose failures.

## Measure before refactoring

Compare normal Claude exploration against Atlas-assisted Claude on the same fixed
DomeSim revision and tasks, with fresh sessions, same model/settings and identical
success criteria. Normal exploration is a fair baseline; forcing a full-directory
dump only measures a separate worst case. Include representative subsystem,
cross-subsystem, change-impact and repair tasks, including unsupported languages.

Record provider input/output/cached usage, tool schema overhead, retrievals,
fallback reads, retries, validation, latency and outcomes across multiple runs.
Distinguish estimated retrieval size from actual billed/cached tokens and any
subscription limits. Where billing is not exposed, report it as unknown.
Price totals only with provider-specific current rates. Score factual claims
against source, dependency accuracy, uncertainty, patch behavior and tests.

The earlier exploratory DeepSeek/Atlas-engine benchmark saved about 82.5% of
cumulative tokens after a follow-up. That was not DomeSim, Claude, a whole agent
session, or a guaranteed production saving. Compare real DomeSim tasks before
claiming a winner. A small prompt that misses the right source is a failed run.

Refactor only DomeSim: establish coverage/baseline tests, rank bounded candidates,
preserve public imports/CLI/data/output contracts, make one coherent change at a
time, test, refresh, and compare again. Exclude vendor/generated assets from source
refactor scope. Avoid wholesale Atlas condense/coagulate/materialize operations.

## Protocol references

- [Claude MCP](https://code.claude.com/docs/en/mcp)
- [Claude programmatic execution](https://code.claude.com/docs/en/headless)
- [Codex app-server](https://learn.chatgpt.com/docs/app-server)
