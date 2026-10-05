"""Project Intelligence Observer v1.

A passive recorder of how Claude Code understands, navigates, changes and
verifies this repository, kept as a local SQLite dataset for teaching a
smaller project-specific reasoning system later.

    observer        records one hook event (called by .claude/hooks/intelligence_observer.py)
    database        paths, connection, schema
    normalize       redaction, path symbols, command -> action-vocabulary name
    seed_actions    import the vocabulary from .claude/settings.local.json
    build_episode   reconstruct one user request as an episode
    analyze_actions vocabulary counts, procedures, knowledge tiers
    inspect         command-line viewer

Nothing here ever decides anything for Claude Code: hooks always exit 0 and
print nothing, so they cannot block, approve or add context.
"""

__version__ = "1.0"
