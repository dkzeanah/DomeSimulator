"""Claude's starter library of illustration elements for the Book Studio, drawn as SVG in the house
style (library.HOUSE_STYLE), each filed in assets/images/illustrations with origin "claude".

    py -3.12 -m books.studio.elements          # draw them all and file any that changed

The domes are not sketches: they are the solver's 2V dome (generated/dome-mesh.json, from the
raw-wedge simulator's build_2v_hemisphere), turned and projected, its triangles painted back to
front and shaded by how each one faces the light. Everything else is drawn by hand, in code, so a
change of palette is a change in one place.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from books.studio import library as lib  # noqa: E402

MESH = ROOT / "website" / "src" / "generated" / "dome-mesh.json"
INK, PAPER, RUST = "#2c1e14", "#faf4e6", "#964818"
WOOD, WOOD_LT, BARK = "#c8914e", "#d9b07a", "#5a3a22"
PINE, PINE_LT, GOLD = "#2c5a2a", "#3f7a34", "#e8b45a"


def svg(w: int, h: int, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" stroke-linejoin="round" stroke-linecap="round">'
            f"{body}</svg>")


def pts(ps) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in ps)


def _mix(a: str, b: str, t: float) -> str:
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


# ----------------------------------------------------------------------
# The solver's dome
# ----------------------------------------------------------------------

def _dome(turn_deg: float = 18, tilt_deg: float = 16, panels: bool = True, size: int = 1000) -> str:
    m = json.loads(MESH.read_text(encoding="utf-8"))
    R = m["radiusFt"]
    a, t = math.radians(turn_deg), math.radians(tilt_deg)
    light = (-0.45, 0.55, 0.70)

    def proj(v):
        x, y, z = v
        X = x * math.cos(a) - y * math.sin(a)
        D = x * math.sin(a) + y * math.cos(a)            # depth: larger is nearer the viewer
        Y = z * math.cos(t) - D * math.sin(t)
        return X, Y, D

    P = [proj(v) for v in m["vertices"]]
    sx = lambda X: size / 2 + X / R * size * 0.44
    sy = lambda Y: size * 0.80 - Y / R * size * 0.44 * 1.0
    body = [f'<ellipse cx="{size / 2}" cy="{size * 0.82}" rx="{size * 0.47}" ry="{size * 0.07}" fill="{INK}" opacity="0.18"/>']
    if panels:
        faces = []
        for f in m["faces"]:
            v = [m["vertices"][i] for i in f[:3]]
            ux, uy, uz = (v[1][k] - v[0][k] for k in range(3))
            wx, wy, wz = (v[2][k] - v[0][k] for k in range(3))
            n = (uy * wz - uz * wy, uz * wx - ux * wz, ux * wy - uy * wx)
            c = [sum(p[k] for p in v) / 3 for k in range(3)]
            if n[0] * c[0] + n[1] * c[1] + n[2] * c[2] < 0:
                n = tuple(-q for q in n)
            ln = math.sqrt(sum(q * q for q in n)) or 1
            n = tuple(q / ln for q in n)
            lit = max(0.0, n[0] * light[0] + n[1] * light[1] + n[2] * light[2])
            depth = sum(P[i][2] for i in f[:3]) / 3
            facing = n[0] * math.sin(a) + n[1] * math.cos(a)   # toward the viewer
            faces.append((depth, f, lit, facing))
        for depth, f, lit, facing in sorted(faces, key=lambda q: q[0]):
            if facing < -0.05:
                continue                                       # the far side is hidden by the near
            col = _mix(_mix(BARK, WOOD_LT, 0.25 + 0.75 * lit), PAPER, 0.08)
            body.append(f'<polygon points="{pts((sx(P[i][0]), sy(P[i][1])) for i in f[:3])}" fill="{col}" stroke="{INK}" stroke-width="5"/>')
    else:
        edges = sorted(m["edges"], key=lambda e: (P[e[0]][2] + P[e[1]][2]) / 2)
        for e in edges:
            p, q = P[e[0]], P[e[1]]
            near = (p[2] + q[2]) / 2 > -R * 0.2
            body.append(f'<line x1="{sx(p[0]):.1f}" y1="{sy(p[1]):.1f}" x2="{sx(q[0]):.1f}" y2="{sy(q[1]):.1f}" '
                        f'stroke="{WOOD if near else _mix(WOOD, PAPER, 0.45)}" stroke-width="{14 if near else 9}"/>')
        for p in sorted(P, key=lambda p: p[2]):
            body.append(f'<circle cx="{sx(p[0]):.1f}" cy="{sy(p[1]):.1f}" r="11" fill="{BARK}"/>')
    return svg(size, size, "".join(body))


# ----------------------------------------------------------------------
# Hand-drawn pieces
# ----------------------------------------------------------------------

def pine() -> str:
    tiers = []
    for i, (w, y, h) in enumerate(((330, 560, 300), (270, 420, 270), (210, 290, 240), (140, 170, 210))):
        col = PINE if i % 2 == 0 else PINE_LT
        tiers.append(f'<polygon points="{pts([(500 - w, y + h), (500, y), (500 + w, y + h)])}" fill="{col}" stroke="{INK}" stroke-width="6"/>')
    return svg(1000, 1000, f'<rect x="470" y="780" width="60" height="170" rx="10" fill="{BARK}" stroke="{INK}" stroke-width="6"/>' + "".join(tiers))


def fallen_log() -> str:
    rings = "".join(f'<circle cx="820" cy="500" r="{r}" fill="none" stroke="{_mix(BARK, WOOD_LT, 0.5)}" stroke-width="4"/>' for r in (40, 80, 120))
    return svg(1000, 1000,
               f'<rect x="120" y="340" width="700" height="320" rx="40" fill="{BARK}" stroke="{INK}" stroke-width="7"/>'
               + "".join(f'<path d="M{x},360 q30,140 0,280" fill="none" stroke="{_mix(BARK, INK, 0.4)}" stroke-width="5"/>' for x in (220, 330, 450, 560, 680))
               + f'<ellipse cx="820" cy="500" rx="150" ry="160" fill="{WOOD_LT}" stroke="{INK}" stroke-width="7"/>{rings}'
               + f'<circle cx="820" cy="500" r="10" fill="{BARK}"/>')


def log_end_split(ways: int = 8) -> str:
    out = []
    for k in range(ways):
        a0, a1 = 2 * math.pi * k / ways, 2 * math.pi * (k + 1) / ways
        mid = (a0 + a1) / 2
        dx, dy = 40 * math.cos(mid), 40 * math.sin(mid)
        c = (500 + dx, 500 + dy)
        p0 = (c[0] + 330 * math.cos(a0), c[1] + 330 * math.sin(a0))
        p1 = (c[0] + 330 * math.cos(a1), c[1] + 330 * math.sin(a1))
        out.append(f'<path d="M{c[0]:.1f},{c[1]:.1f} L{p0[0]:.1f},{p0[1]:.1f} A330,330 0 0,1 {p1[0]:.1f},{p1[1]:.1f} Z" '
                   f'fill="{WOOD_LT}" stroke="{INK}" stroke-width="6"/>')
        b0 = (c[0] + 345 * math.cos(a0 + 0.02), c[1] + 345 * math.sin(a0 + 0.02))
        b1 = (c[0] + 345 * math.cos(a1 - 0.02), c[1] + 345 * math.sin(a1 - 0.02))
        out.append(f'<path d="M{b0[0]:.1f},{b0[1]:.1f} A345,345 0 0,1 {b1[0]:.1f},{b1[1]:.1f}" fill="none" stroke="{BARK}" stroke-width="22"/>')
    return svg(1000, 1000, "".join(out))


def wedge() -> str:
    tip, back_l, back_r = (180, 640), (820, 420), (820, 780)
    return svg(1000, 1000,
               f'<polygon points="{pts([tip, (760, 300), (900, 300), back_l])}" fill="{WOOD}" stroke="{INK}" stroke-width="6"/>'
               f'<path d="M{tip[0]},{tip[1]} L{back_l[0]},{back_l[1]} Q900,600 {back_r[0]},{back_r[1]} Z" fill="{WOOD_LT}" stroke="{INK}" stroke-width="6"/>'
               f'<path d="M{back_l[0]},{back_l[1]} L900,300 Q980,480 900,660 L{back_r[0]},{back_r[1]} Q900,600 {back_l[0]},{back_l[1]}" fill="{BARK}" stroke="{INK}" stroke-width="6"/>')


def triangle_panel() -> str:
    A, B, C = (500, 140), (140, 800), (860, 800)
    def bar(p, q):
        return f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="{WOOD}" stroke-width="64"/>'
    return svg(1000, 1000, f'<polygon points="{pts([A, B, C])}" fill="{_mix(WOOD_LT, PAPER, 0.55)}" stroke="none"/>'
               + bar((A[0] - 20, A[1] + 30), (B[0] + 40, B[1] - 10)) + bar((B[0] - 10, B[1]), (C[0] - 40, C[1])) + bar((C[0], C[1] + 10), (A[0] + 20, A[1] - 20))
               + f'<polygon points="{pts([A, B, C])}" fill="none" stroke="{INK}" stroke-width="6"/>')


def sun() -> str:
    rays = "".join(f'<line x1="{500 + 250 * math.cos(a):.1f}" y1="{500 + 250 * math.sin(a):.1f}" x2="{500 + 380 * math.cos(a):.1f}" '
                   f'y2="{500 + 380 * math.sin(a):.1f}" stroke="{GOLD}" stroke-width="30"/>' for a in (k * math.pi / 6 for k in range(12)))
    return svg(1000, 1000, rays + f'<circle cx="500" cy="500" r="210" fill="{GOLD}" stroke="{RUST}" stroke-width="8"/>')


def cloud() -> str:
    puffs = [(330, 560, 150), (480, 470, 190), (650, 520, 160), (780, 590, 110), (240, 620, 100)]
    return svg(1000, 1000, "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ffffff" stroke="{INK}" stroke-width="5"/>' for x, y, r in puffs)
               + f'<rect x="150" y="600" width="720" height="120" rx="60" fill="#ffffff"/>')


def hills() -> str:
    return svg(2000, 700,
               f'<rect width="2000" height="700" fill="#f0c890"/>'
               f'<path d="M0,420 C300,260 600,300 900,380 C1200,460 1500,240 2000,330 L2000,700 L0,700 Z" fill="{PINE_LT}" stroke="{INK}" stroke-width="5"/>'
               f'<path d="M0,540 C400,430 800,470 1200,520 C1500,560 1800,470 2000,500 L2000,700 L0,700 Z" fill="{PINE}" stroke="{INK}" stroke-width="5"/>')


def pip() -> str:
    """Pip: a girl with long brown hair, a green hard hat, a hi-vis vest and red trousers."""
    skin, hair = "#dba37a", "#4c2010"
    return svg(600, 1000,
               f'<path d="M190,250 C150,420 170,560 210,600 L390,600 C430,560 450,420 410,250 Z" fill="{hair}" stroke="{INK}" stroke-width="5"/>'
               f'<rect x="250" y="560" width="45" height="300" rx="18" fill="#b2382b" stroke="{INK}" stroke-width="5"/>'
               f'<rect x="305" y="560" width="45" height="300" rx="18" fill="#b2382b" stroke="{INK}" stroke-width="5"/>'
               f'<ellipse cx="270" cy="870" rx="45" ry="22" fill="{BARK}"/><ellipse cx="330" cy="870" rx="45" ry="22" fill="{BARK}"/>'
               f'<path d="M210,380 L390,380 L410,600 L190,600 Z" fill="#f4bc38" stroke="{INK}" stroke-width="5"/>'
               f'<line x1="300" y1="385" x2="300" y2="600" stroke="{INK}" stroke-width="4"/>'
               f'<rect x="200" y="470" width="200" height="16" fill="#e8e8e0"/>'
               f'<path d="M210,400 Q150,470 175,560" fill="none" stroke="{skin}" stroke-width="36"/>'
               f'<path d="M390,400 Q450,470 425,560" fill="none" stroke="{skin}" stroke-width="36"/>'
               f'<circle cx="300" cy="270" r="105" fill="{skin}" stroke="{INK}" stroke-width="5"/>'
               f'<circle cx="262" cy="270" r="11" fill="{INK}"/><circle cx="338" cy="270" r="11" fill="{INK}"/>'
               f'<path d="M260,318 Q300,345 340,318" fill="none" stroke="{INK}" stroke-width="6"/>'
               f'<circle cx="240" cy="305" r="16" fill="#e88a7a" opacity="0.6"/><circle cx="360" cy="305" r="16" fill="#e88a7a" opacity="0.6"/>'
               f'<path d="M190,215 Q300,90 410,215 Z" fill="#336e48" stroke="{INK}" stroke-width="6"/>'
               f'<rect x="170" y="205" width="260" height="24" rx="12" fill="#336e48" stroke="{INK}" stroke-width="6"/>'
               f'<path d="M205,240 C195,330 200,420 225,470" fill="none" stroke="{hair}" stroke-width="30"/>'
               f'<path d="M395,240 C405,330 400,420 375,470" fill="none" stroke="{hair}" stroke-width="30"/>')


def chainsaw() -> str:
    teeth = "".join(f'<rect x="{x}" y="414" width="18" height="12" fill="{INK}"/>' for x in range(470, 930, 34))
    return svg(1000, 600,
               f'<rect x="440" y="250" width="500" height="150" rx="75" fill="#c8ccd2" stroke="{INK}" stroke-width="6"/>{teeth}'
               f'<rect x="120" y="190" width="360" height="270" rx="40" fill="#e07a3c" stroke="{INK}" stroke-width="6"/>'
               f'<path d="M150,190 Q170,90 290,90 L380,90" fill="none" stroke="{INK}" stroke-width="26"/>'
               f'<rect x="180" y="250" width="140" height="70" rx="12" fill="{INK}" opacity="0.8"/>')


def maul() -> str:
    return svg(1000, 1000,
               f'<rect x="470" y="300" width="60" height="620" rx="24" fill="{WOOD}" stroke="{INK}" stroke-width="6" transform="rotate(-30 500 600)"/>'
               f'<path d="M300,190 L620,120 L700,320 L330,330 Z" fill="#6f767e" stroke="{INK}" stroke-width="7" transform="rotate(-30 500 600)"/>'
               f'<path d="M300,190 L210,260 L330,330 Z" fill="#c8ccd2" stroke="{INK}" stroke-width="7" transform="rotate(-30 500 600)"/>')


def boxes_town() -> str:
    out = []
    for i, (x, w, h, c) in enumerate(((60, 220, 420, "#b8b0a0"), (300, 180, 560, "#a8a090"), (500, 240, 360, "#c0b8a8"),
                                      (760, 200, 480, "#a09888"), (980, 260, 380, "#b8b0a0"))):
        y = 900 - h
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}" stroke="{INK}" stroke-width="6"/>')
        for wy in range(y + 40, 880, 90):
            for wx in range(x + 30, x + w - 40, 70):
                out.append(f'<rect x="{wx}" y="{wy}" width="36" height="44" fill="#f0e2a8" stroke="{INK}" stroke-width="3"/>')
    return svg(1300, 920, "".join(out) + f'<rect x="0" y="900" width="1300" height="20" fill="{INK}"/>')


def night_stars() -> str:
    import random
    rnd = random.Random(7)
    stars = "".join(f'<circle cx="{rnd.randint(0, 2000)}" cy="{rnd.randint(0, 800)}" r="{rnd.choice((2, 3, 4, 6))}" fill="#fff4d0"/>' for _ in range(160))
    return svg(2000, 800, f'<rect width="2000" height="800" fill="#141c3a"/>{stars}'
               f'<circle cx="1640" cy="170" r="80" fill="#fff4d0"/><circle cx="1675" cy="150" r="80" fill="#141c3a"/>')


ELEMENTS = {
    "solver-2v-dome-panelled": ("The solver's 2V wedge dome closed in, seen from a little above, its triangles shaded by the light.", lambda: _dome(panels=True)),
    "solver-2v-dome-frame": ("The solver's 2V dome as a bare frame: 65 struts meeting at 26 nodes.", lambda: _dome(panels=False)),
    "pine-tree": ("A tall pine in four tiers on a short brown trunk.", pine),
    "fallen-pine-log": ("A fallen pine log from the side, its cut end showing growth rings.", fallen_log),
    "log-end-split-eight-ways": ("The end of a log split into eight wedges, opened apart, bark on each back.", log_end_split),
    "one-wedge": ("One wedge split from a log: the sharp point, two sawn faces, the curved bark back.", wedge),
    "triangle-of-three-wedges": ("One triangle panel framed by three wedge struts in a pinwheel.", triangle_panel),
    "golden-sun": ("A golden sun with twelve rays.", sun),
    "white-cloud": ("A soft white cloud.", cloud),
    "rolling-green-hills": ("Two bands of rolling green hills under a sunset sky: a wide background strip.", hills),
    "pip-standing": ("Pip, a girl with long brown hair, a green hard hat, a hi-vis vest and red trousers, smiling.", pip),
    "chainsaw": ("An orange chainsaw with a silver bar and chain.", chainsaw),
    "splitting-maul": ("A splitting maul: a steel head on a wooden handle.", maul),
    "town-of-boxes": ("A row of tall boxy buildings with lit windows: the town of boxes.", boxes_town),
    "night-sky-with-stars": ("A navy night sky full of stars and a crescent moon: a wide background strip.", night_stars),
}


def main() -> int:
    for name, (prompt, draw) in ELEMENTS.items():
        got = lib.add_svg(name, draw(), "claude", prompt, "Drawn by books.studio.elements (Claude's starter library).")
        print(f"{'filed' if got['new'] else 'unchanged'}  {got['file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
