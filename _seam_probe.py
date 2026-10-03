from wedge_book import graphics, numbers

facts = graphics.seam_section_geometry()
print('seam:', facts['seam_id'], '| edge type:', facts['edge_type'])
print('fold deg:', round(facts['fold_deg'], 3),
      '| gap deg:', round(facts['gap_deg'], 3),
      '| sector deg:', facts['sector_deg'], '| trunk in:', facts['trunk_in'])
print('key base in:', round(facts['key_base_in'], 3),
      '| contact depth in:', round(facts['contact_in'], 3))
print('apex   (x, y):', tuple(round(v, 3) for v in facts['apex']))
print('point A(x, y):', tuple(round(v, 3) for v in facts['point_a']))
print('point B(x, y):', tuple(round(v, 3) for v in facts['point_b']))
print('member loops:', len(facts['members']), '| key loops:', len(facts['key']))
for i, loop in enumerate(facts['members']):
    xs = [p[0] for p in loop]
    ys = [p[1] for p in loop]
    print(f'  member {i}: x {min(xs):.2f}..{max(xs):.2f}  y {min(ys):.2f}..{max(ys):.2f}')
for i, loop in enumerate(facts['key']):
    xs = [p[0] for p in loop]
    ys = [p[1] for p in loop]
    print(f'  key    {i}: x {min(xs):.2f}..{max(xs):.2f}  y {min(ys):.2f}..{max(ys):.2f}')
    print('    corners:', [(round(p[0], 2), round(p[1], 2)) for p in loop])
