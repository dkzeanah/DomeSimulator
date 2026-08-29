"""Final build-lesson polish: readable failure cards, better layout camera."""

from pathlib import Path

p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\lesson_build.py")
s = p.read_text(encoding="utf-8")

start = s.index("    for index, (title, note, colour) in enumerate(entries):")
end = s.index("def scene_build_recap(")
block = s[start:end]

replacement = '''    for index, (title, note, colour) in enumerate(entries):
        if reveal < (index + 0.1) / len(entries):
            continue
        x = 5.2 - index * 4.7
        opaque.box((x, 0.0, 1.75), (2.9, 0.35, 2.3),
                   (colour[0], colour[1], colour[2], 1.0))
        # A red cross in front of each board, not buried inside it.
        for first, second in (((-1.15, 0.75), (1.15, 2.75)),
                              ((-1.15, 2.75), (1.15, 0.75))):
            opaque.cylinder(np.array([x + first[0], -0.45, first[1]]),
                            np.array([x + second[0], -0.45, second[1]]),
                            0.10, RED, 8)
        app.world_labels.append(WorldLabel(
            np.array([x, 0.0, 3.7]), title + chr(10) + note, _rgb(colour)))
    app.world_labels.append(WorldLabel(
        np.array([-2.0, 0.0, 6.3]),
        "NONE OF THESE ARE GEOMETRY PROBLEMS", (111, 235, 155),
    ))


'''

s = s[:start] + replacement + s[end:]
s = s.replace('20.0, (32.0, 42.0, 15.0), "build_layout",',
              '20.0, (32.0, 52.0, 17.5), "build_layout",')
s = s.replace('19.0, (90.0, 18.0, 17.5), "build_failures",',
              '19.0, (90.0, 16.0, 19.0), "build_failures",')
p.write_text(s, encoding="utf-8")
print("build polish applied")
