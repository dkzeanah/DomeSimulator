# DomeSim: initial Atlas-assisted task

Work only in C:\Users\Don\Desktop\DomeSim, not DomeSim-codex. Read AGENTS.md
and CLAUDE.md. Preserve existing local edits and all rendered deliverables.

First produce a refactor proposal, not a repository-wide rewrite. The goal is
lower maintenance cost and lower context cost while preserving observable behavior.

1. Call atlas_project. Report index freshness, supported languages, parse errors,
   and excluded/generated/vendor areas. Do not infer whole-project coverage from
   the indexed Python counts.
2. Use atlas_find for each affected capability, then atlas_get for specific symbols.
   Follow next_start_line; ask for missing dependencies rather than guessing.
   Use small, explicit native reads for missing imports, configuration, tests,
   TypeScript or documentation. Record why each fallback was needed.
3. Establish subsystem boundaries: geometry/materials/costing, world/editor,
   films/lessons/deliverables, books, voice, web, and project-agent/intelligence.
   This is a starting taxonomy from the repository agreements, not a verified
   dependency model. Cite source before asserting a dependency or duplication.
4. Propose three small refactor candidates with exact symbols, caller evidence,
   preserved contracts, risks and runnable validation. Distinguish first-party
   code from F5-TTS and generated output. A duplicate name or similar AST is not
   sufficient reason to merge independently meaningful code.
5. Recommend the first bounded change and its before/after tests. Run existing
   relevant checks before implementation. Establish an isolated baseline that
   preserves the current dirty working tree before any broad refactor.
6. For each later authorized change: edit the smallest coherent unit, run affected
   checks, inspect the diff, refresh the DomeSim index, and verify retrieval of
   changed symbols. Keep old addresses/replacements documented where needed.

Keep the initial source retrieval target around 8,000 estimated tokens, then
request more evidence if needed. This is an orientation target, not a hard cap
that justifies omitting evidence. It does not cap native Claude billing.

Return: subsystem summary; evidence addresses; missing coverage; three candidates;
recommended first change; validation commands; and uncertainty. Do not render a
full film or publish output as part of this audit. Do not invent token savings:
record actual model usage when available and label character estimates separately.
