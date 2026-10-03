"""Round 4: close the ledger rows this round's folds and sections carry."""
import pathlib
import re

ledger = pathlib.Path('book/concept-ledger.md')
out = []
closed = []

# proposed gap title (lowercased) -> (home, status)
closed_rows = {
    "fuller's why": ('85 What the Campaign Is For', 'IN'),
    'the tooling ask': ('85 What the Campaign Is For', 'IN'),
    'the balance of forces': ('85 What the Campaign Is For', 'IN'),
    'the one share ask': ('85 What the Campaign Is For', 'IN'),
    'the arithmetic stopped working': ('85 What the Campaign Is For', 'IN'),
    'startup equipment': ('85 What the Campaign Is For', 'IN'),
    'the highest-use index': ('55 The Six Values of One Pine', 'IN'),
    'glass the top twenty': ('59 The Roof Is Already a Gutter', 'IN'),
    'the cowboy hat laminate': ('59 The Roof Is Already a Gutter', 'PARTIAL'),
    'four-foot sheet finding': ('57 Less Skin for the Same Floor', 'IN'),
    'the sheet that does not fit': ('57 Less Skin for the Same Floor', 'IN'),
    'pad centre reserved': ('65 A Pad, Not a Plot', 'IN'),
    'the reserved centre': ('65 A Pad, Not a Plot', 'IN'),
    'apex socket': ('86 The Module Catalogue', 'PARTIAL'),
    'triangular solar cells': ('45 Heat, Power and the Small Systems', 'PARTIAL'),
    'six-pad reference park': ('65 A Pad, Not a Plot', 'PARTIAL'),
    'ten-thousand-dollar pad returns': ('65 A Pad, Not a Plot', 'PARTIAL'),
    'what a ten-thousand-dollar pad returns': ('65 A Pad, Not a Plot', 'PARTIAL'),
}

for line in ledger.read_text(encoding='utf-8').splitlines():
    if line.startswith('|'):
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) == 6 and cells[5] == 'GAP':
            g = re.search(r'GAP \[([^\]]+)\]', cells[4])
            title = (g.group(1) if g else '').lower()
            for key, (home, status) in closed_rows.items():
                if key in title or title in key:
                    cells[4], cells[5] = home, status
                    closed.append(cells[0])
                    break
            line = '| ' + ' | '.join(cells) + ' |'
    out.append(line)
ledger.write_text('\n'.join(out) + '\n', encoding='utf-8')

tally = {}
left = []
for line in out:
    if not line.startswith('|'):
        continue
    cells = [c.strip() for c in line.strip('|').split('|')]
    if len(cells) == 6 and cells[5] in ('IN', 'PARTIAL', 'GAP'):
        tally[cells[5]] = tally.get(cells[5], 0) + 1
        if cells[5] == 'GAP':
            left.append(cells[0])
print(f'closed {len(closed)}:')
for name in closed:
    print('   -', name)
print('tally:', tally, 'total', sum(tally.values()))
print('still missing:', left)
