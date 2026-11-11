import pcbnew, sys, re, collections
f = sys.argv[1] if len(sys.argv) > 1 else 'impedance_afe.kicad_pcb'
b = pcbnew.LoadBoard(f)
if '--fill' in sys.argv:
    pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(f, b)
pcbnew.WriteDRCReport(b, 'drc.rpt', pcbnew.EDA_UNITS_MILLIMETRES, True)
txt = open('drc.rpt').read()
kinds = collections.Counter(re.findall(r'^\[(\w+)\]', txt, re.M))
print(kinds)
want = [a for a in sys.argv[2:] if not a.startswith('--')]
for blk in re.split(r'\n(?=\[)', txt):
    k = re.match(r'\[(\w+)\]', blk)
    if k and (not want or k.group(1) in want):
        print(blk.strip()[:400]); print('--')
