"""Build the knowledge-graph page from the template and the seed.

The page embeds the seed so it is complete even where its database is not
available (a read-only copy), and loads the live, edited graph from its
database where it is.

    py -3.12 -m research.graph_page     # writes research/knowledge-graph.html
"""

from __future__ import annotations

import json
from pathlib import Path

from . import graph_seed

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "graph_page.template.html"
OUT = HERE / "knowledge-graph.html"


def main() -> int:
    graph = graph_seed.build()
    data = json.dumps(graph, separators=(",", ":")).replace("</", "<\\/")
    OUT.write_text(TEMPLATE.read_text(encoding="utf-8").replace("/*SEED*/", data), encoding="utf-8")
    print(OUT.relative_to(graph_seed.ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
