"""Add the Auto-Scene Manager controls to the Masterclass tab."""

from pathlib import Path

NL = chr(10)
p = Path(r"C:\Users\Don\Desktop\DomeSim\launcher.py")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found:" + NL + old[:260])
    s = s.replace(old, new, 1)


sub(
    '    section(body, "Rebuild the whole set")',
    '    section(body, "Auto-scene manager")' + NL
    + '    mc_compose = CheckRow(' + NL
    + '        body, "Auto-insert brand segments (outro, call to action)", False)' + NL
    + '    mc_compose.pack(fill="x", pady=3)' + NL
    + '    mc_seg_include = LabeledEntry(' + NL
    + '        body, "Also insert (segment keys, comma-sep)", "")' + NL
    + '    mc_seg_include.pack(fill="x", pady=3)' + NL
    + '    mc_seg_exclude = LabeledEntry(' + NL
    + '        body, "Never insert (segment keys, comma-sep)", "")' + NL
    + '    mc_seg_exclude.pack(fill="x", pady=3)' + NL
    + '    note(body, "Templated pieces that repeat across videos and do not "' + NL
    + '               "change: the contact outro, the call to action, the "' + NL
    + '               "who-am-I stack, and the Frankendome party sting. Ticking "' + NL
    + '               "the box splices in everything marked auto; the two "' + NL
    + '               "fields add or suppress individual ones. Run Action = "' + NL
    + '               "list_segments to see the keys, what each does, and which "' + NL
    + '               "soundboard cues it fires. Deliberately OFF by default: "' + NL
    + '               "the nine videos already rendered were made before "' + NL
    + '               "segments existed, and leaving it off is what lets them "' + NL
    + '               "re-render byte-identical.")' + NL
    + NL
    + '    section(body, "Rebuild the whole set")',
)

sub(
    '         "build_packet", "list_lessons", "list_deliverables",' + NL
    + '         "render_all"], "run")',
    '         "build_packet", "list_lessons", "list_deliverables",' + NL
    + '         "list_segments", "soundboard", "render_all"], "run")',
)

sub(
    '        "list_deliverables": "print every video this repository "',
    '        "list_segments": "print the reusable brand segments: what each "' + NL
    + '                         "one is, where it inserts itself, whether it "' + NL
    + '                         "is automatic, and what it plays.",' + NL
    + '        "soundboard": "print the audio soundboard inventory by "' + NL
    + '                      "category, and create the asset folders if they "' + NL
    + '                      "do not exist yet. This repository ships no audio; "' + NL
    + '                      "drop your own files into assets/audio/<category>/ "' + NL
    + '                      "and they become available to segments as "' + NL
    + '                      "category/name.",' + NL
    + '        "list_deliverables": "print every video this repository "',
)

sub(
    '        if mc_render_only.get():' + NL
    + '            cfg["render_only"] = mc_render_only.get()',
    '        cfg["compose_segments"] = mc_compose.get()' + NL
    + '        if mc_seg_include.get():' + NL
    + '            cfg["segments_include"] = mc_seg_include.get()' + NL
    + '        if mc_seg_exclude.get():' + NL
    + '            cfg["segments_exclude"] = mc_seg_exclude.get()' + NL
    + '        if mc_render_only.get():' + NL
    + '            cfg["render_only"] = mc_render_only.get()',
)

p.write_text(s, encoding="utf-8")
print("Auto-scene manager added to the launcher")
