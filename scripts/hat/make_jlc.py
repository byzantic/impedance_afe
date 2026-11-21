"""ADC/DAC HAT: JLCPCB fab + assembly files (Gerber zip, BOM, CPL) into OUTDIR (keep fab outputs out of the repo).

    python3 scripts/hat/make_jlc.py OUTDIR

BOM: JLC columns (Comment, Designator, Footprint, LCSC Part #), grouped by part, LCSC codes from scripts/hat/design.py.
No-fit parts (J1/J2 hand-soldered sockets on the bottom, Y1 DNP) are listed with Comment "DNP: ..." and no LCSC code:
choose "do not place" for them in the JLC BOM step.  Solder jumpers and mounting holes aren't parts and are left out.
CPL: Designator, Mid X, Mid Y, Layer, Rotation from KiCad's placement export (all parts, including the no-fit ones).
"""
import collections, csv, importlib.util, os, re, subprocess, sys, tempfile, zipfile

HATDIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HATDIR, '..', '..'))
PCB = os.path.join(ROOT, 'adc_hat', 'adc_hat.kicad_pcb')
out = os.path.abspath(sys.argv[1])
assert not out.startswith(ROOT + os.sep), 'write fab outputs outside the repo'
os.makedirs(out, exist_ok=True)

spec = importlib.util.spec_from_file_location('hd', os.path.join(HATDIR, 'design.py'))
hd = importlib.util.module_from_spec(spec); spec.loader.exec_module(hd)
parts = [p for p in hd.parts if not p['ref'].startswith(('H', 'JP'))]
nofit = {p['ref'] for p in parts if p['dnp'] or p['ref'].startswith('J')}


def key(r):
    return re.match(r'[A-Z]+', r).group(0), int(re.search(r'\d+', r).group(0))


# Gerbers + drill
g = tempfile.mkdtemp()
subprocess.run(['kicad-cli', 'pcb', 'export', 'gerbers', '-o', g + '/', '--layers',
                'F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts', PCB], check=True, capture_output=True)
subprocess.run(['kicad-cli', 'pcb', 'export', 'drill', '-o', g + '/', '--format', 'excellon', '--excellon-separate-th',
                '--drill-origin', 'absolute', PCB], check=True, capture_output=True)
with zipfile.ZipFile(os.path.join(out, 'HAT_gerbers.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(g)):
        z.write(os.path.join(g, f), f)

# BOM
groups = collections.OrderedDict()
for p in sorted(parts, key=lambda p: key(p['ref'])):
    fp = p['fp'].split(':')[1]
    if p['ref'] in nofit:
        comment = 'DNP: ' + (p['mpn'] or p['value'])
        lcsc = ''
    else:
        comment = p['mpn'] if p['ref'].startswith('U') and p['mpn'] else p['value']
        lcsc = p['lcsc']
    groups.setdefault((comment, fp, lcsc), []).append(p['ref'])
with open(os.path.join(out, 'HAT_BOM_JLC.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    for (comment, fp, lcsc), refs in groups.items():
        w.writerow([comment, ','.join(refs), fp, lcsc])
missing = [r for (c, fp, l), refs in groups.items() for r in refs if not l and r not in nofit]
assert not missing, ('fitted parts without an LCSC code', missing)

# CPL
pos = os.path.join(g, 'pos.csv')
subprocess.run(['kicad-cli', 'pcb', 'export', 'pos', '-o', pos, '--format', 'csv', '--units', 'mm', '--side', 'both', PCB],
               check=True, capture_output=True)
refs = {p['ref'] for p in parts}
n = 0
with open(pos) as fi, open(os.path.join(out, 'HAT_CPL_JLC.csv'), 'w', newline='') as fo:
    w = csv.writer(fo)
    w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for r in csv.DictReader(fi):
        if r['Ref'] in refs:
            w.writerow([r['Ref'], r['PosX'] + 'mm', r['PosY'] + 'mm', r['Side'].capitalize(), f"{float(r['Rot']):g}"])
            n += 1
assert n == len(refs), (n, len(refs))
print(f'{out}: HAT_gerbers.zip, HAT_BOM_JLC.csv ({len(groups)} lines, no-fit {sorted(nofit, key=key)}), '
      f'HAT_CPL_JLC.csv ({n} parts)')
