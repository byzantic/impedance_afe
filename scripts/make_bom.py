"""Rev B BOM with debug / precision build columns (grouped)."""
import csv, collections, re, design

def refkey(r):
    m = re.match(r'([A-Z]+)(\d+)', r); return (m.group(1), int(m.group(2)))

groups = collections.OrderedDict()
for p in sorted((p for p in design.parts if not p['ref'].startswith('#')), key=lambda p: refkey(p['ref'])):
    k = (p['value'], p['dbg'], p['prec'], p['fp'].split(':')[1] if ':' in p['fp'] else '(off-board)', p['mpn'], p['lcsc'], p['dnp'])
    groups.setdefault(k, []).append(p['ref'])
with open('BOM_revB.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Designators', 'Qty', 'Value', 'Debug build', 'Precision build', 'Footprint', 'MPN / notes', 'LCSC', 'DNP'])
    for (val, dbg, prec, fp, mpn, lcsc, dnp), refs in sorted(groups.items(), key=lambda kv: refkey(kv[1][0])):
        w.writerow([','.join(refs), len(refs), val, dbg, prec, fp, mpn, lcsc, 'DNP' if dnp else ''])
cnt = collections.Counter()
for p in design.parts:
    if p['ref'].startswith('#') or p['dnp']: continue
    cnt[re.match(r'[A-Z]+', p['ref']).group(0)] += 1
print(len(groups), 'BOM lines;', dict(cnt))
