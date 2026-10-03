"""Read-only: dump every fact the new chapters and sections need."""
import pathlib

from two_v_demo import scratch_facts as sf
import seed_model

out = []

out.append('== scratch_facts.render_settings()')
s = sf.render_settings()
for a in dir(s):
    if not a.startswith('_') and not callable(getattr(s, a)):
        out.append(f'  {a} = {getattr(s, a)}')
out.append('== scratch_facts.shader_constants()')
c = sf.shader_constants()
for a in dir(c):
    if not a.startswith('_') and not callable(getattr(c, a)):
        out.append(f'  {a} = {getattr(c, a)}')
out.append(f'  FRAME {sf.FRAME_WIDTH}x{sf.FRAME_HEIGHT} @ {sf.FRAME_FPS} fps'
           f' | SCALE {sf.SCALE} | STRUT_SIDES {sf.STRUT_SIDES}'
           f' | HUB_RINGS {sf.HUB_RINGS} x {sf.HUB_SEGMENTS}'
           f' | STRUT_RADIUS {sf.STRUT_RADIUS} | HUB_RADIUS {sf.HUB_RADIUS}')

batch = sf.dome_batch()
out.append('== dome_batch()')
for a in dir(batch):
    if not a.startswith('_') and not callable(getattr(batch, a)):
        out.append(f'  {a} = {getattr(batch, a)}')

for name in ('steps_tube', 'steps_buffer', 'steps_frame', 'steps_counts'):
    out.append(f'== scratch_facts.{name}()')
    out += ['  ' + ln for ln in getattr(sf, name)()]

out.append('')
out.append(f'== seed_model.MODULES ({len(seed_model.MODULES)})')
for m in seed_model.MODULES:
    out.append(f'  {m.key} | {m.label} | mount {m.mount} | ${m.cost}'
               f' | watts {m.watts} | water {m.water} | drain {m.drain}')

out.append('')
out.append('== seed_model.fitouts()')
for key in seed_model.FITOUT_ORDER:
    fit = seed_model.fitout(key)
    out.append(f'  {key}: {fit}')

pathlib.Path('_facts_dump.txt').write_text('\n'.join(out), encoding='utf-8')
print('written', len(out), 'lines')
