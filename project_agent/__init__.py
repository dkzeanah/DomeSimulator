"""Project Agent — a hyper-specialized media agent for DomeSim.

A narrow orchestrator that turns plain-text chat input into this
repository's finished media (stills, narrated films, books) by:

1. loading a *generated* knowledge base (:mod:`project_agent.spec`)
   dumped from the repo's own menu/dump functions, so project
   understanding is ground truth, not inference;
2. operating a typed tool layer (:mod:`project_agent.tools`) over the
   repo's real programmatic APIs — launch tickets, stills renderers,
   selftests, exporters;
3. resolving every unknown through an explicit placeholder ledger
   (:mod:`project_agent.ledger`) instead of guessing.

The loop (:mod:`project_agent.loop`) runs with either a configured
OpenAI-compatible LLM (function calling) or a built-in deterministic
command parser, so the vertical slice works with no API key at all.

Design document: ``docs/project-agent-blueprint.md``.
Tooling reference: ``docs/agent-utilization-guide.md``.
"""

__version__ = "0.1.0"
