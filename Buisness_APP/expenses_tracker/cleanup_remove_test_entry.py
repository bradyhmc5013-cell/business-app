import json
from pathlib import Path
p = Path(__file__).with_name('expenses.json')
if not p.exists():
    print('expenses.json not found')
    raise SystemExit(1)

with p.open('r', encoding='utf-8') as f:
    data = json.load(f)

orig_len = len(data)
new = [e for e in data if not (str(e.get('vendor','')).lower() == 'test' and float(e.get('amount',0)) == 1.0)]
if len(new) == orig_len:
    print('No matching test entry found; nothing changed.')
else:
    with p.open('w', encoding='utf-8') as f:
        json.dump(new, f, indent=2)
    print(f'Removed {orig_len - len(new)} test entry(ies).')
