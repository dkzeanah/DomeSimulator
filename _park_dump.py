"""Read-only: the park model's numbers for the pad chapter."""
import dataclasses
import pathlib
import re

import park_model as pm

out = []
out.append('Pad fields: ' + (str([f.name for f in dataclasses.fields(pm.Pad)])
                             if dataclasses.is_dataclass(pm.Pad) else 'n/a'))
out.append('=== dome catalogue ===')
for dome in pm.dome_catalogue():
    out.append(f'  {dome}')
out.append(f'=== pad sizes === {pm.pad_sizes()}')
src = pathlib.Path('park_model.py').read_text(encoding='utf-8')
names = sorted(set(re.findall(r'Declared\(\s*"([a-z_0-9]+)"', src)))
out.append('=== declared keys ===')
for name in names:
    try:
        out.append(f'  {name} = {pm.declared(name)}')
    except Exception as exc:
        out.append(f'  {name} = ? ({type(exc).__name__})')
for fn in ('metering_options', 'heavy_tenant_exposure'):
    f = getattr(pm, fn, None)
    if f:
        r = f()
        out.append(f'{fn} = {r if not isinstance(r, tuple) else [str(x) for x in r]}')
pathlib.Path('_park.txt').write_text('\n'.join(out), encoding='utf-8')
print('written', len(out), 'lines')
