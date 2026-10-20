"""sketch-claude: a SketchUp-style dome modeller that draws its own plan set.

    py -3.12 -m sketch_claude serve      the Dome Sketch app in the browser (http://127.0.0.1:8767)
    py -3.12 -m sketch_claude plans      a new numbered plan-set PDF in deliverables/
    py -3.12 -m sketch_claude promo      a new numbered folder of showcase renders
    py -3.12 -m sketch_claude selftest   the geometry checks, a still and a one-sheet PDF

The dome is the framed-panel 3V dome that ``two_v_demo.panel_method`` solves (the method
credited to Trillium Domes); this package turns that solution into solid sticks, base
sections, a door, a deck and a furnished room, renders them in a hand-drafted style and lays
the drawings out as construction sheets. Every figure on a sheet is computed from the
model; the few that cannot be (stock sizes, door size, screw counts) sit in
``model.DECLARED`` with a reason, and that table is printed in the plan set.

"sketch-claude" names this version, made by Claude; a parallel version made by DeepSeek
is meant to sit beside it under its own name.
"""

TAG = "sketch-claude"
