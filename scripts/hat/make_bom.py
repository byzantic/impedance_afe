"""ADC/DAC HAT BOM -> docs/BOM_adc_hat.csv (grouped). Run from anywhere."""
import collections, csv, importlib.util, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('hat_design', os.path.join(HERE, 'design.py'))
hd = importlib.util.module_from_spec(spec); spec.loader.exec_module(hd)


def refkey(r):
    m = re.match(r'([A-Z]+)(\d+)', r); return (m.group(1), int(m.group(2)))


groups = collections.OrderedDict()
for p in sorted(hd.parts, key=lambda p: refkey(p['ref'])):
    k = (p['value'], p['fp'].split(':')[1], p['mpn'], p['lcsc'], p['dnp'])
    groups.setdefault(k, []).append(p['ref'])
out = os.path.join(HERE, '..', '..', 'docs', 'BOM_adc_hat.csv')
with open(out, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Designators', 'Qty', 'Value', 'Footprint', 'MPN / notes', 'LCSC', 'DNP'])
    for (val, fp, mpn, lcsc, dnp), refs in sorted(groups.items(), key=lambda kv: refkey(kv[1][0])):
        w.writerow([','.join(refs), len(refs), val, fp, mpn, lcsc, 'DNP' if dnp else ''])
print(len(groups), 'BOM lines ->', os.path.normpath(out))
