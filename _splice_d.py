"""Splice group D's table into the ledger at its placeholder."""
import pathlib
import re

ledger = pathlib.Path('book/concept-ledger.md')
table = pathlib.Path('_ledger_group_d.md').read_text(encoding='utf-8').strip()
text = ledger.read_text(encoding='utf-8')
if '<!-- GROUP D TABLE -->' not in text:
    raise SystemExit('placeholder missing — already spliced?')
text = text.replace('<!-- GROUP D TABLE -->', table)

# the ledger's other tables keep the same six columns, so nothing else changes
ledger.write_text(text, encoding='utf-8')

rows = [ln for ln in text.splitlines() if ln.startswith('|')]
data = [ln for ln in rows if re.match(r'^\|', ln) and not ln.startswith('|---')]
tally = {}
gaps = {}
for ln in data:
    cells = [c.strip() for c in ln.strip('|').split('|')]
    if len(cells) != 6:
        continue
    status = cells[5]
    if status in {'IN', 'PARTIAL', 'GAP'}:
        tally[status] = tally.get(status, 0) + 1
        if status == 'GAP':
            m = re.search(r'GAP \[([^\]]+)\]', cells[4])
            gaps.setdefault(m.group(1) if m else '(none)', []).append(cells[0])

print('ledger rows now:', len(data), '| tally:', tally)
print('gap groups:', len(gaps))
out = ['concept rows by status: ' + str(tally), '', 'GAP groups (all four sections):']
for title in sorted(gaps):
    out.append(f'* {title} ({len(gaps[title])}): ' + '; '.join(gaps[title]))
pathlib.Path('_gap_final.txt').write_text('\n'.join(out), encoding='utf-8')
print('written _gap_final.txt')
