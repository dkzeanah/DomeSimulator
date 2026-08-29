"""A run-of-the-mill frankendome: static, plain, and honestly ugly.

The party sting is a celebration -- seven looks, rainbow panels, cheering.
This is the opposite and exists for the videos that do not want a
celebration: the same bones, sitting still, lit plainly, with nothing
done to flatter them.
"""

from pathlib import Path

NL = chr(10)
p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\segments.py")
s = p.read_text(encoding="utf-8")

if "FRANKEN_PLAIN" in s:
    raise SystemExit("plain segment already present")

body = '''

def scene_seg_franken_plain(app, opaque, transparent, p: float) -> None:
    """The frankendome as it actually is: static, lumpy, unflattered.

    No cycling looks, no lighting, no celebration. The only motion is the
    renderer's own slow camera drift, which is enough to read the shape
    without turning it into an event.
    """
    rng = np.random.default_rng(7)
    jitter = rng.normal(0.0, 1.0, GEOMETRY.vertices.shape) * 0.055
    points = GEOMETRY.vertices + jitter
    edges = list(GEOMETRY.hemisphere_edges)

    for index, edge in enumerate(edges):
        a, b = (points[i] * SCALE for i in edge)
        draw_timber(opaque, a, b, 0.095, index, CHAINSAW, sides=7)

    # Two patched panels and a scatter of glue, because that is what it
    # looked like. Nothing here is animated.
    faces = list(GEOMETRY.hemisphere_faces)
    for face_index, face in enumerate(faces[::9]):
        corners = points[[int(v) for v in face]] * SCALE
        normal = normalize(corners.mean(axis=0))
        transparent.triangle(corners[0], corners[1], corners[2],
                             (0.60, 0.50, 0.36, 0.42), normal)
        draw_patch(opaque, corners, face_index * 11 + 3, 0.08)

    used = sorted({i for edge in edges for i in edge})
    for slot, vertex in enumerate(used[::5]):
        draw_glue(transparent, points[vertex] * SCALE, 0.15, vertex * 13 + slot)

    app.world_labels.append(WorldLabel(
        np.array([0.0, 0.0, SCALE + 1.7]), "FRANKENDOME", (169, 188, 203)))


FRANKEN_PLAIN = Segment(
    key="franken_plain",
    title="Frankendome, plainly",
    kind="sting",
    placement="manual",
    note="The static, unflattered frankendome. No looks, no lights, no "
         "cheering. Use instead of 'party' when a celebration would be "
         "the wrong note.",
    scenes={"seg_franken_plain": scene_seg_franken_plain},
    chapters=(
        Chapter(
            "franken_plain", "00", "Frankendome",
            "Frankendome.",
            ("Frankendome.",),
            (), 4.0, (34.0, 22.0, 18.0), "seg_franken_plain", "hype",
        ),
    ),
)
'''

anchor = "SEGMENTS: dict[str, Segment] = {"
index = s.index(anchor)
s = s[:index] + body.strip() + NL + NL + NL + s[index:]
s = s.replace(
    "    for item in (OUTRO, WHOAMI, CTA_SHARE, CTA_BUILD, PARTY)",
    "    for item in (OUTRO, WHOAMI, CTA_SHARE, CTA_BUILD, PARTY, FRANKEN_PLAIN)",
    1)
p.write_text(s, encoding="utf-8")
print("FRANKEN_PLAIN segment added")
