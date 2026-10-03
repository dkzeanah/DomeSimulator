from wedge_book import graphics

for orientation in ("point_dome_in", "point_panel_in", "point_dome_out",
                    "point_panel_out"):
    facts = graphics.seam_section_geometry(orientation=orientation)
    key = facts["key"][0] if facts["key"] else []
    kx = [p[0] for p in key]
    ky = [p[1] for p in key]
    print(f'== {orientation}')
    print(f'   key: x {min(kx):.2f}..{max(kx):.2f}  y {min(ky):.2f}..{max(ky):.2f}'
          f'  base {facts["key_base_in"]:.2f} in  gap {facts["gap_deg"]:.2f}'
          f'  fold {facts["fold_deg"]:.2f}')
    print(f'   apex y {facts["apex"][1]:.2f} | point A {tuple(round(v,2) for v in facts["point_a"])}'
          f' | point B {tuple(round(v,2) for v in facts["point_b"])}')
    for i, loop in enumerate(facts["members"]):
        xs = [p[0] for p in loop]
        ys = [p[1] for p in loop]
        print(f'   member {i}: x {min(xs):6.2f}..{max(xs):6.2f}  y {min(ys):6.2f}..{max(ys):6.2f}')
