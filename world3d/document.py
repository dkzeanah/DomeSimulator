"""The world as a document: the three structures, and everything you did to them.

The structures are rebuilt from their solvers every time; your changes are kept as
a list of operations, in order, and replayed on top. That makes undo exact (drop
the last operation and replay), keeps a saved file small and readable, and means a
change to a solver flows into your edited world the next time it opens.

Operations::

    {"op": "delete", "pid": "D017"}
    {"op": "cut", "pid": "Z03A", "point": [x, y, z], "normal": [x, y, z]}
    {"op": "add", "layer": "mine", "kind": "wedge", "a": [x, y, z], "b": [x, y, z], "log_in": 12}
    {"op": "move", "pid": "F07", "delta": [dx, dy, dz]}          (or "layer": "zome")
    {"op": "copy", "pid": "Z03A", "delta": [dx, dy, dz]}
"""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import numpy as np

from . import pieces as pc
from . import structures as st
from .pieces import Piece

ROOT = Path(__file__).resolve().parents[1]
SAVE = Path(__file__).resolve().parent / "saved" / "world.json"
BF_IN3 = 144.0


class Document:
    def __init__(self) -> None:
        self.base = st.build_all()
        self.ops: list[dict] = []
        self.visible = {k: on for k, _l, _s, on in st.LAYERS}
        self.locked = {k: False for k in st.LAYER_KEYS}
        self.active = "mine"
        self.layers: dict[str, list[Piece]] = {}
        self._serial = 0
        self.replay()

    # -- the model -------------------------------------------------------
    def replay(self) -> None:
        self.layers = {k: [copy.copy(p) for p in v] for k, v in self.base.items()}
        self._serial = 0
        for op in self.ops:
            self._apply(op)

    def find(self, pid: str) -> Piece | None:
        for ps in self.layers.values():
            for p in ps:
                if p.pid == pid:
                    return p
        return None

    def _remove(self, pid: str) -> Piece | None:
        for ps in self.layers.values():
            for i, p in enumerate(ps):
                if p.pid == pid:
                    return ps.pop(i)
        return None

    def _apply(self, op: dict) -> bool:
        kind = op["op"]
        if kind == "delete":
            return self._remove(op["pid"]) is not None
        if kind == "cut":
            p = self.find(op["pid"])
            if p is None:
                return False
            parts = pc.cut(p, op["point"], op["normal"])
            if parts is None:
                return False
            ps = self.layers[p.layer]
            i = ps.index(p)
            ps[i:i + 1] = list(parts)
            return True
        if kind == "add":
            self._serial += 1
            a, b = np.asarray(op["a"], float), np.asarray(op["b"], float)
            sol = pc.strut(a, b, op.get("kind", "wedge"), float(op.get("log_in", 12.0)))
            layer = op.get("layer", "mine")
            name = f"{op.get('kind', 'wedge')} strut {self._serial}"
            self.layers.setdefault(layer, []).append(
                Piece(f"M{self._serial:03d}", layer, name, sol, st.WOOD, "strut",
                      {"a": a.tolist(), "b": b.tolist(), "section": op.get("kind", "wedge")}))
            return True
        if kind in ("move", "copy"):
            delta = np.asarray(op["delta"], float)
            targets = (list(self.layers.get(op["layer"], [])) if "layer" in op
                       else [p for p in [self.find(op.get("pid", ""))] if p])
            if not targets:
                return False
            for p in targets:
                if kind == "copy":
                    self._serial += 1
                    q = copy.copy(p)
                    q.pid, q.name, q.meta = f"{p.pid}+{self._serial}", f"{p.name} (copy)", dict(p.meta)
                    q.solid = pc.moved(p.solid, delta)
                    _shift_meta(q, delta)
                    self.layers[p.layer].append(q)
                else:
                    p.solid = pc.moved(p.solid, delta)
                    _shift_meta(p, delta)
            return True
        raise ValueError(f"unknown operation {kind!r}")

    def do(self, op: dict) -> bool:
        """Apply an operation; it is kept only if it did something."""
        if "pid" in op:
            p = self.find(op["pid"])
            if p is not None and self.locked.get(p.layer):
                return False
        if "layer" in op and self.locked.get(op["layer"]):
            return False
        ok = self._apply(op)
        if ok:
            self.ops.append(op)
        return ok

    def undo(self) -> bool:
        if not self.ops:
            return False
        self.ops.pop()
        self.replay()
        return True

    # -- finding things ----------------------------------------------------
    def nodes(self) -> np.ndarray:
        """Every end a new strut could snap to: struts' ends, and the corners of members."""
        pts = []
        for key, ps in self.layers.items():
            if not self.visible.get(key) or key == "person":
                continue
            for p in ps:
                if p.kind in ("member", "strut"):
                    pts.extend(p.axis())
        return np.array(pts, float).reshape(-1, 3)

    def pick(self, origin, direction) -> Piece | None:
        best, best_t = None, float("inf")
        for key, ps in self.layers.items():
            if not self.visible.get(key):
                continue
            for p in ps:
                t = pc.ray_hit(pc.triangles(p), origin, direction)
                if t is not None and t < best_t:
                    best, best_t = p, t
        self.last_hit = None if best is None else np.asarray(origin, float) + np.asarray(direction, float) * best_t
        return best

    # -- keeping it ----------------------------------------------------------
    def save(self, path: Path = SAVE) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema": 1, "ops": self.ops, "visible": self.visible,
                                    "locked": self.locked, "active": self.active}, indent=1), encoding="utf-8")
        return path

    def load(self, path: Path = SAVE) -> bool:
        if not path.is_file():
            return False
        data = json.loads(path.read_text(encoding="utf-8"))
        self.ops = list(data.get("ops", []))
        self.visible.update(data.get("visible", {}))
        self.locked.update(data.get("locked", {}))
        self.active = data.get("active", self.active)
        self.replay()
        return True

    def cut_list(self) -> list[dict]:
        rows = []
        for key, ps in self.layers.items():
            if key == "person":
                continue
            for p in ps:
                if p.kind not in ("member", "strut"):
                    continue
                L, w1, w2 = p.extents()
                rows.append({"layer": key, "piece": p.pid, "name": p.name, "length_in": round(L, 2),
                             "width_in": round(max(w1, w2), 2), "depth_in": round(min(w1, w2), 2),
                             "board_feet": round(p.volume() / BF_IN3, 2)})
        return rows

    def export_cut_list(self) -> Path:
        import medialib
        out = medialib.new_path("dome-zome-foundation-cut-list.csv")
        rows = self.cut_list()
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        return out


def _shift_meta(p: Piece, delta) -> None:
    for k in ("a", "b"):
        if k in p.meta:
            p.meta[k] = (np.asarray(p.meta[k], float) + delta).tolist()


def validate_document() -> None:
    import tempfile
    doc = Document()
    n_dome = len(doc.layers["dome"])
    assert doc.do({"op": "delete", "pid": "D001"})
    assert len(doc.layers["dome"]) == n_dome - 1
    z = doc.find("Z01A")
    a, b = z.axis()
    mid = (a + b) / 2
    assert doc.do({"op": "cut", "pid": "Z01A", "point": mid.tolist(), "normal": (b - a).tolist()})
    assert doc.find("Z01A.a") and doc.find("Z01A.b") and not doc.find("Z01A")
    assert doc.do({"op": "add", "layer": "mine", "kind": "square", "a": [0, 0, 100], "b": [120, 0, 100]})
    assert abs(doc.find("M001").extents()[0] - 120) < 1e-6
    assert doc.do({"op": "move", "layer": "zome", "delta": [12, 0, 0]})
    assert doc.do({"op": "copy", "pid": "M001", "delta": [0, 24, 0]})
    doc.locked["foundation"] = True
    assert not doc.do({"op": "delete", "pid": "F01"}), "a locked layer cannot be edited"
    n_ops = len(doc.ops)
    assert doc.undo() and len(doc.ops) == n_ops - 1 and len(doc.layers["mine"]) == 1
    with tempfile.TemporaryDirectory() as t:
        path = doc.save(Path(t) / "w.json")
        again = Document()
        again.load(path)
        assert len(again.layers["dome"]) == n_dome - 1 and again.find("Z01A.b") and again.find("M001")
    rows = doc.cut_list()
    assert any(r["piece"] == "M001" for r in rows) and all(r["length_in"] > 0 for r in rows)
    hit = doc.pick(np.array([60.0, -200.0, 100.0]), np.array([0.0, 1.0, 0.0]))
    assert hit is not None
