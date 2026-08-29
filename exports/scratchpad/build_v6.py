"""Version six: themed shells, the product lines, a beat, and a cadence."""

from pathlib import Path

NL = chr(10)
p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_hype.py")
s = p.read_text(encoding="utf-8")

if "HYPE_V6_LESSON" in s:
    raise SystemExit("v6 already present")

body = '''

# ----------------------------------------------------------------------
# Version six: one shell, many skins -- with a beat under it
# ----------------------------------------------------------------------

def scene_hype_themes(app, opaque, transparent, p: float) -> None:
    """The same hemisphere, wearing each skin in turn."""
    from .dome_themes import THEMES, draw_theme

    index = min(len(THEMES) - 1, int(clamp(p * 0.999) * len(THEMES)))
    theme = THEMES[index]
    draw_theme(opaque, transparent, theme, SCALE, p * 1.5)
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 1.7]), theme.label,
                   (240, 247, 252)),
        WorldLabel(np.array([0.0, 0.0, -1.2]), theme.pitch, (169, 188, 203)),
    ])


def scene_hype_billboard(app, opaque, transparent, p: float) -> None:
    """A dome beside a road, earning money off its own surface."""
    from .dome_themes import THEME_BY_KEY, draw_theme

    draw_theme(opaque, transparent, THEME_BY_KEY["video"], SCALE, p * 1.9)
    # The road it faces.
    opaque.box((0.0, -11.0, -0.05), (34.0, 5.0, 0.12), (0.13, 0.14, 0.17, 1.0))
    for index in range(9):
        x = -14.0 + index * 3.5
        opaque.box((x, -11.0, 0.03), (1.6, 0.22, 0.06), (0.86, 0.84, 0.52, 1.0))
    app.world_labels.extend([
        WorldLabel(np.array([0.0, 0.0, SCALE + 1.8]),
                   "IF YOU LIVE ON A ROAD", (61, 211, 255)),
        WorldLabel(np.array([0.0, -11.0, 1.4]),
                   "your wall is already facing the traffic",
                   (169, 188, 203)),
    ])


def scene_hype_lines(app, opaque, transparent, p: float) -> None:
    """The four product lines the creator already defines."""
    from .dome_themes import product_lines

    lines = product_lines()
    reveal = clamp(p * 1.3)
    span = 14.4
    step = span / max(1, len(lines) - 1)
    for index, line in enumerate(lines):
        if index / len(lines) > reveal:
            continue
        x = -span * 0.5 + index * step
        low, high = line.diameter_ft_range
        size = 0.9 + (high / 30.0) * 1.5
        colour = PALETTE[index % len(PALETTE)]
        for edge in list(GEOMETRY.hemisphere_edges)[::2]:
            a, b = (GEOMETRY.vertices[i] * size + np.array([x, 0.0, 0.0])
                    for i in edge)
            opaque.cylinder(a, b, 0.05, colour, 6)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, size + 1.4]),
            f"{line.name}" + chr(10) + f"{low:.0f}-{high:.0f} ft" + chr(10)
            + f"{line.stages} stations", _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, 6.2]),
        "FOUR LINES, ONE SKELETON", (111, 235, 155)))


SCENES_V6 = dict(SCENES_V3)
SCENES_V6["hype_themes"] = scene_hype_themes
SCENES_V6["hype_billboard"] = scene_hype_billboard
SCENES_V6["hype_lines"] = scene_hype_lines


# Short lines on purpose: the cadence comes from where the sentences
# break, because the speech engine will not rap for you.
THEME_RUN: tuple[Chapter, ...] = (
    Chapter(
        "skins", "00", "One shell, any skin",
        "The bones do not care what you paint on them.",
        (
            "Same forty panels. Same hundred and twenty sticks. Different paint.",
            "A baseball. A basketball. A disco ball with a facet on every face.",
            "The structure does not care. It never did.",
        ),
        (), 4.0, (34.0, 22.0, 17.0), "hype_themes",
    ),
    Chapter(
        "adspace", "00", "Forty rentable faces",
        "Forty panels. Forty faces. All of them rentable.",
        (
            "Now look at it like a landlord. Forty panels is forty surfaces.",
            "Every one of them flat, every one of them replaceable, every one of",
            "them facing somewhere. That is not a roof. That is inventory.",
        ),
        (), 4.0, (58.0, 20.0, 17.0), "hype_themes",
    ),
    Chapter(
        "billboard", "00", "If you live on a road",
        "Your wall is already facing the traffic.",
        (
            "And if you live on a road, the wall is already pointed at the traffic.",
            "Span one picture across a dozen triangles and the house pays for itself",
            "while you sleep in it. Try that with a rectangle.",
        ),
        (), 4.0, (26.0, 18.0, 22.0), "hype_billboard",
    ),
    Chapter(
        "lines", "00", "Four lines, one skeleton",
        "Home, shed, greenhouse, shelter. Same bones.",
        (
            "Four product lines already exist in the software. A dome home. A storage",
            "shed. A greenhouse. A storm shelter. Twenty-one feet to thirty, or ten",
            "to fifteen for the shelter. Four buildings, four price points, one",
            "skeleton, and the same forty triangles under every one of them.",
        ),
        (), 4.0, (90.0, 16.0, 20.0), "hype_lines",
    ),
)


def _splice_after(chapters, slug, run):
    """Put a run of beats immediately after the named one."""
    out = []
    for chapter in chapters:
        out.append(chapter)
        if chapter.slug == slug:
            out.extend(run)
    return tuple(out)


# v5's wording (no girlfriend remark), plus the themed run after the
# "what it could become" beat, where it belongs.
CHAPTERS_V6 = _splice_after(CHAPTERS_V5, "becomes", THEME_RUN)
CHAPTERS_V6 = tuple(
    replace(chapter, number=f"{index + 1:02d}")
    for index, chapter in enumerate(CHAPTERS_V6)
)


_HYPE_V6_BASE = Lesson(
    key="hype6",
    brand="FRANKENDOME",
    title="Frankendome, Version Six",
    chapters=CHAPTERS_V6,
    scenes=SCENES_V6,
    snapshot_prefix="hype6",
    style="hype",
    # Faster than the other montages. The speech engine cannot rap, so
    # the cadence has to come from rate plus short sentences that break
    # on the beat rather than from any rhythmic control.
    voice_rate="+18%",
    label_layout="declutter",
    audio_bed="beds/frankenbeat",
    audio_bed_gain=0.17,
)

HYPE_V6_LESSON = compose(
    _HYPE_V6_BASE,
    include=("party",),
    exclude=("cta_share",),
)
'''

p.write_text(s.rstrip() + NL + body, encoding="utf-8")
print("v6 written")

registry = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_registry.py")
r = registry.read_text(encoding="utf-8")
r = r.replace("    HYPE_V5_LESSON," + NL + ")",
              "    HYPE_V5_LESSON," + NL + "    HYPE_V6_LESSON," + NL + ")", 1)
r = r.replace("                   HYPE_V4_LESSON, HYPE_V5_LESSON)",
              "                   HYPE_V4_LESSON, HYPE_V5_LESSON, HYPE_V6_LESSON)", 1)
registry.write_text(r, encoding="utf-8")
print("hype6 registered")

deliv = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\deliverables.py")
d = deliv.read_text(encoding="utf-8")
old = ('                compose=True, segments=("franken_plain",)),' + NL + ")")
new = ('                compose=True, segments=("franken_plain",)),' + NL
       + '    Deliverable("hype6", "frankendome-montage-v6.mp4",' + NL
       + '                "Version six: themed shells, the four product lines, "' + NL
       + '                "a faster cadence and a synthesised beat under it.",' + NL
       + '                compose=True, segments=("party",)),' + NL
       + ")")
if old not in d:
    raise SystemExit("deliverable anchor not found")
deliv.write_text(d.replace(old, new, 1), encoding="utf-8")
print("v6 added to the manifest")
