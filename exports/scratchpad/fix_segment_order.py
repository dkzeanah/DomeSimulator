"""An outro is last by definition, not by declaration order."""

from pathlib import Path

NL = chr(10)
Q = chr(34) * 3
p = Path(r"C:\Users\Don\Desktop\DomeSim\two_v_demo\segments.py")
s = p.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global s
    if old not in s:
        raise SystemExit("pattern not found:" + NL + old[:300])
    s = s.replace(old, new, 1)


sub(
    "    default_on: bool = False" + NL
    + "    " + Q + "Whether composition includes it unless a lesson opts out." + Q + NL
    + "    note: str = " + chr(34) + chr(34),
    "    default_on: bool = False" + NL
    + "    " + Q + "Whether composition includes it unless a lesson opts out." + Q + NL
    + "    order: int = 0" + NL
    + "    " + Q + "Tie-break among segments sharing a placement; higher goes" + NL
    + "    later. An outro is forced last regardless, because that is what an" + NL
    + "    outro is." + Q + NL
    + "    note: str = " + chr(34) + chr(34),
)

sub(
    "    # Manual insertions land before the closing segments." + NL
    + "    for segment in manual + ends:",
    "    # Closing segments run in order, and an outro is always genuinely" + NL
    + "    # last -- otherwise whichever happened to be declared first wins," + NL
    + "    # which is how the contact card landed mid-film the first time." + NL
    + '    ends.sort(key=lambda item: (item.kind == "outro", item.order))' + NL
    + "    manual.sort(key=lambda item: item.order)" + NL
    + "    for segment in manual + ends:",
)

p.write_text(s, encoding="utf-8")
print("outro forced last; order field added")
