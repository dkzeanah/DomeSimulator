"""Read-only: the facts surface the new chapters will need."""
import importlib

import kickstarter
import seed_model

print('=== kickstarter.goal_lines ===')
for line in kickstarter.goal_lines():
    print(' ', line)
print('goal:', kickstarter.goal())
print('=== kickstarter.tiers ===')
for t in kickstarter.tiers():
    print(' ', t)
print('=== cost_stack(stem_cell) ===')
stack = kickstarter.cost_stack()
for attr in dir(stack):
    if attr.startswith('_'):
        continue
    value = getattr(stack, attr)
    if not callable(value):
        print(f'  {attr} = {value}')
print('=== quilt_economics(3) ===')
print(' ', kickstarter.quilt_economics(3))
print()
print('=== seed_model: declared prices/markup-ish ===')
for name in sorted(seed_model._defaults()):
    if any(k in name for k in ('price', 'usd', 'margin', 'profit', 'cost', 'target')):
        print(f'  {name} = {seed_model.declared(name)} {seed_model.units_of(name)}')
print()
for mod in ('two_v_demo.creator_menus', 'two_v_demo.dome_creator_menus',
            'two_v_demo.all_domes', 'two_v_demo.seed_bridge'):
    try:
        m = importlib.import_module(mod)
    except Exception as exc:
        print(f'-- {mod}: {type(exc).__name__}')
        continue
    print(f'-- {mod} public:', [n for n in dir(m) if not n.startswith('_')][:14])
