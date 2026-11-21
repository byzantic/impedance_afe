"""Rev B: autoroute the pre-routed board with Freerouting.  Run after place.py + preroute.py; running it again
continues from the existing (unlocked) routing.

    FREEROUTING=/path/freerouting-2.5.0.jar [PCB=other.kicad_pcb] /usr/bin/python3 autoroute.py [passes] [B.Cu cost]

1. Export Specctra DSN from a zone-less copy (locked pre-routes go out as fixed wiring).
2. Empty the pin list of GND: its pads stay as obstacles, the pours connect them (PICO_GND is routed too).
3. Bias the router to F.Cu (B.Cu trace cost x `B.Cu cost`), so the bottom plane stays as whole as possible.
4. Run Freerouting headless, import the SES into the real board, refill the zones, save.
Work files go to $AUTOROUTE_DIR (default: a temp dir).
"""
import os, re, subprocess, sys, tempfile
import pcbnew
from common import PCB
PCB = os.path.abspath(os.environ.get('PCB', PCB))      # e.g. PCB=adc_hat/adc_hat.kicad_pcb

def fill():
    """refill all zones in a fresh process (filling right after an SES import crashes the KiCad 9 bindings)"""
    subprocess.run([sys.executable, '-c', 'import pcbnew; b = pcbnew.LoadBoard(%r); '
                    'pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(%r, b)' % (PCB, PCB)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


JAR = os.environ.get('FREEROUTING')
assert JAR and os.path.exists(JAR), 'set FREEROUTING to the freerouting jar'
passes = int(sys.argv[1]) if len(sys.argv) > 1 else 100
bcost = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
wd = os.environ.get('AUTOROUTE_DIR') or tempfile.mkdtemp(prefix='afe_route_')
os.makedirs(wd, exist_ok=True)
dsn0, dsn, ses = (os.path.join(wd, n) for n in ('afe0.dsn', 'afe.dsn', 'afe.ses'))

# 1. zone-less copy -> DSN
b = pcbnew.LoadBoard(PCB)
bb = b.GetBoardEdgesBoundingBox()        # (one LoadBoard per process: a second one misbehaves in KiCad 9)
for z in list(b.Zones()):
    if not z.GetIsRuleArea():               # rule areas (keep-outs) go to the router; copper pours don't
        b.Remove(z)
tmp = os.path.join(wd, 'nozone.kicad_pcb')
pcbnew.SaveBoard(tmp, b)
assert pcbnew.ExportSpecctraDSN(pcbnew.LoadBoard(tmp), dsn0)

# 2./3. plane nets out, layer costs in
s = open(dsn0).read()
for net in ('GND',):                     # PICO_GND (10 pins) is routed as well: the island alone can get cut off
    s, n = re.subn(r'(\(net %s\n\s*)\(pins[^)]*\)' % re.escape(net), r'\1(pins)', s)
    assert n == 1, net
# locked GND items (stitching / fan-out vias, joins) become net-less fixed obstacles; otherwise the router joins them
# to each other with GND wiring.  KiCad keeps the locked originals on SES import.
w = s.index('  (wiring')
s = s[:w] + re.sub(r'\(net GND\)', '', s[w:])
ar = f"""    (autoroute_settings
      (fanout off) (autoroute on) (postroute on) (vias on)
      (via_costs 60) (plane_via_costs 5) (start_ripup_costs 100) (start_pass_no 1)
      (layer_rule F.Cu (active on) (preferred_direction horizontal)
        (preferred_direction_trace_costs 1.0) (against_preferred_direction_trace_costs 1.6))
      (layer_rule B.Cu (active on) (preferred_direction vertical)
        (preferred_direction_trace_costs {bcost}) (against_preferred_direction_trace_costs {2 * bcost}))
    )
"""
i = s.index('    (boundary', s.index('  (structure'))
s = s[:i] + ar + s[i:]
# keep-out frame inside the board edge: Freerouting would otherwise route closer than KiCad's copper-edge clearance
x0, x1 = pcbnew.ToMM(bb.GetLeft()) * 1000, pcbnew.ToMM(bb.GetRight()) * 1000          # DSN: um, y up
y0, y1 = -pcbnew.ToMM(bb.GetBottom()) * 1000, -pcbnew.ToMM(bb.GetTop()) * 1000
e, k = 650, 1600
ko = ''.join(f'    (keepout "" (rect {lay} {a} {b} {c} {d}))\n' for lay in ('F.Cu', 'B.Cu') for a, b, c, d in
             [(x0, y0, x0 + e, y1), (x1 - e, y0, x1, y1), (x0, y0, x1, y0 + e), (x0, y1 - e, x1, y1)] +
             # rounded corners (radius <= 3 mm): square keep-outs so tracks can't cut across the arcs
             [(x0, y0, x0 + k, y0 + k), (x1 - k, y0, x1, y0 + k), (x0, y1 - k, x0 + k, y1), (x1 - k, y1 - k, x1, y1)])
i = s.index('    (via ', s.index('  (structure'))
open(dsn, 'w').write(s[:i] + ko + s[i:])

# 4. route
env = {k: v for k, v in os.environ.items() if k not in ('LD_LIBRARY_PATH', 'LD_PRELOAD')}
log = open(os.path.join(wd, 'freerouting.log'), 'w')
subprocess.run(['java', '-Xmx2g', '-Djava.awt.headless=true', '-jar', JAR, '-mt', '4', '-de', dsn, '-do', ses,
                f'--router.autorouter.max_passes={passes}', '--gui.enabled=false'],
               cwd=wd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
for line in open(os.path.join(wd, 'freerouting.log')):
    if 'Auto-routing stage completed' in line or 'Optimization' in line and 'completed' in line:
        print(line.strip()[24:])
POST = """import pcbnew
b = pcbnew.LoadBoard(%r)
assert pcbnew.ImportSpecctraSES(b, %r), 'SES import failed'
stray = [t for t in b.GetTracks() if t.GetNetname().startswith('unconnected-')]   # router debris on NC pads
for t in stray:
    b.Remove(t)
thin = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetWidth() < pcbnew.FromMM(0.15)]
for t in thin:                                   # Freerouting neck-downs (0.125 mm) at pads -> JLC minimum
    t.SetWidth(pcbnew.FromMM(0.15))
pcbnew.SaveBoard(%r, b)
print('removed', len(stray), 'stray tracks on no-connect nets; widened', len(thin), 'neck-downs to 0.15 mm')
""" % (PCB, ses, PCB)
# a second LoadBoard in one process hands back an unwrapped SWIG pointer (KiCad 9), so import in a fresh process
r = subprocess.run([sys.executable, '-c', POST], capture_output=True, text=True, check=True)
print(r.stdout.strip())
fill()
print('routed ->', PCB, '| work files in', wd)
