"""ADC/DAC HAT: prepare adc_hat/adc_hat.kicad_pcb for autorouting, then autoroute it.

    FREEROUTING=/path/freerouting-2.5.0.jar /usr/bin/python3 scripts/hat/route.py [passes]

Run on the board as placed by scripts/hat/place.py (it adds locked fan-out vias; re-running adds them again).
1. Net classes Power (0.4 mm) and Clock (0.3 mm); copper joins between the DIP and SMD pads of the Y1 combo footprint;
   locked clock pre-routes: JP1 pin 2 -> U1 CLKIN (ADC_CLK, up and over C6) and R1 -> JP1 pin 3 (XO_CLK, under JP1);
   locked escapes for the left-hand pins of U2 (WSON).
2. GND fan-out: a locked via beside every SMD GND pad (collision-checked), so each pad reaches the bottom plane
   whatever the top-layer routing does to the top pour.
3. scripts/layout/autoroute.py with PCB=this board (GND to the pours, everything else routed).
"""
import math, os, subprocess, sys
HATDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HATDIR, '..', 'layout'))
import pcbnew  # noqa: E402
from common import mm, P, ROOT, via, track, GLOBAL  # noqa: E402
GLOBAL.add('+5VA')                    # HAT-only rail (power symbol, no sheet prefix)

PCB = os.path.join(ROOT, 'adc_hat', 'adc_hat.kicad_pcb')
POWER = ['+5V', '+5VA', '+3V3', '+3V3A']
CLOCK = ['CLK_IN', 'ADC_CLK', 'XO_CLK', 'XO_OUT']
CW = 0.3                              # clock track width
CL, VR, TW = 0.2, 0.3, 0.25           # clearance, via radius, fan-out track width (0.5 mm pitch on U2)


def prepare():
    b = pcbnew.LoadBoard(PCB)
    assert not any(t.GetClass() == 'PCB_VIA' for t in b.GetTracks()), 'board already has vias: re-place it first'
    ns = b.GetDesignSettings().m_NetSettings
    nc = pcbnew.NETCLASS('Power')
    nc.SetTrackWidth(mm(0.4)); nc.SetClearance(mm(CL)); nc.SetViaDiameter(mm(0.6)); nc.SetViaDrill(mm(0.3))
    ns.SetNetclass('Power', nc)
    nc = pcbnew.NETCLASS('Clock')
    nc.SetTrackWidth(mm(CW)); nc.SetClearance(mm(CL)); nc.SetViaDiameter(mm(0.6)); nc.SetViaDrill(mm(0.3))
    ns.SetNetclass('Clock', nc)
    ns.ClearNetclassPatternAssignments()
    for n in POWER:
        ns.SetNetclassPatternAssignment(n, 'Power')
    for n in CLOCK:
        ns.SetNetclassPatternAssignment('/' + n, 'Clock')       # local labels: /NAME

    def pad(ref, n):
        return P(b.FindFootprintByReference(ref).FindPadByNumber(n).GetPosition())
    # clock pre-routes (locked): ADC_CLK leaves JP1 upwards, runs between the Pi header's inner row and JP1/C6, and
    # drops straight onto U1 pin 17; XO_CLK runs under JP1 from R1 to JP1 pin 3.
    j2, u17, r1, j3 = pad('JP1', '2'), pad('U1', '17'), pad('R1', '2'), pad('JP1', '3')
    yt, yb = 6.1, 8.9
    clk = [('ADC_CLK', [j2, (j2[0], yt), (u17[0], yt), u17]), ('XO_CLK', [r1, (r1[0], yb), (j3[0], yb), j3])]
    for net, pts in clk:
        track(b, net, pts, CW)
    # U2 (WSON-10, 0.5 mm pitch, pins 1-5 down the left side): locked escapes at pad width, nested so nothing is boxed in.
    # pin 1 VDD straight up to C7; pin 2 VOUTA out to the left (the router takes it on to J2); pin 3 RSTSEL left and
    # down to R6; pin 4 GND to its own via; pin 5 SPI2C straight down to R2.
    u = {n: pad('U2', str(n)) for n in range(1, 6)}
    xo = u[1][0] - 0.74                        # outer pad ends
    r6, r2 = pad('R6', '1'), pad('R2', '1')
    esc = [('+5VA', [u[1], (u[1][0], pad('C7', '1')[1])]),
           ('DAC_OUT', [u[2], (r6[0] - 1.1, u[2][1])]),
           ('RSTSEL', [u[3], (r6[0], u[3][1]), r6]),
           ('GND', [u[4], (xo - 0.37, u[4][1]), (xo - 0.37, u[4][1] + 1.0)]),
           ('DAC_SPI2C', [u[5], (u[5][0] - 0.21, u[5][1]), (u[5][0] - 0.21, r2[1]), r2])]
    for net, pts in esc:
        track(b, net, pts, 0.25)
    via(b, 'GND', *esc[3][1][-1])
    via(b, 'DAC_OUT', *esc[1][1][-1])           # the router picks VOUTA up here, on either layer
    csegs = [(a, c) for net, pts in clk + esc for a, c in zip(pts, pts[1:])]
    prefanned = {('U2', '4')}

    # combo footprints (Y1: DIP-8 can + SMD inside): join same-numbered THT and SMD pads with copper
    joins = 0
    for fp in b.GetFootprints():
        tht = {p.GetNumber(): p for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNumber()}
        for p in fp.Pads():
            q = tht.get(p.GetNumber())
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and q is not None and p.GetNetname():
                w = 0.4 if p.GetNetname() in POWER or p.GetNetname() == 'GND' else 0.25
                track(b, p.GetNetname(), [P(q.GetPosition()), P(p.GetPosition())], w)
                joins += 1

    # no tracks between the board edge and the Pi header's edge row: they would cut its GND pins off both pours
    j1 = [P(p.GetPosition()) for p in b.FindFootprintByReference('J1').Pads()]
    ye = min(y for x, y in j1) - 1.05          # stop short of the pads (radius 0.85 + 0.2 clearance)
    ra = pcbnew.ZONE(b)
    ra.SetIsRuleArea(True); ra.SetDoNotAllowTracks(True); ra.SetDoNotAllowVias(True)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); ra.SetLayerSet(ls)
    ol = ra.Outline(); ol.NewOutline()
    for x, y in [(min(x for x, y in j1) - 1.3, 0.0), (max(x for x, y in j1) + 1.3, 0.0),
                 (max(x for x, y in j1) + 1.3, ye), (min(x for x, y in j1) - 1.3, ye)]:
        ol.Append(mm(x + 40), mm(y + 30))
    ra.SetZoneName('no tracks above J1 edge row')
    b.Add(ra)

    bb = b.GetBoardEdgesBoundingBox()
    ex0, ey0 = P(bb.GetOrigin()); ex1, ey1 = P(bb.GetEnd())
    boxes, holes = [], []
    for p in b.GetPads():
        r = p.GetBoundingBox()
        boxes.append(((pcbnew.ToMM(r.GetLeft()) - 40, pcbnew.ToMM(r.GetTop()) - 30,
                       pcbnew.ToMM(r.GetRight()) - 40, pcbnew.ToMM(r.GetBottom()) - 30), p.GetNetname(), p))
        if p.GetDrillSizeX() > 0:
            holes.append((P(p.GetPosition()), pcbnew.ToMM(p.GetDrillSizeX()) / 2))

    def boxd(x, y, bx):
        return math.hypot(max(bx[0] - x, 0, x - bx[2]), max(bx[1] - y, 0, y - bx[3]))

    def segbox(a, c, bx, n=12):
        return min(boxd(a[0] + (c[0] - a[0]) * k / n, a[1] + (c[1] - a[1]) * k / n, bx) for k in range(n + 1))

    def segpt(a, c, q):
        dx, dy = c[0] - a[0], c[1] - a[1]
        t = max(0, min(1, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / (dx * dx + dy * dy or 1)))
        return math.hypot(q[0] - a[0] - t * dx, q[1] - a[1] - t * dy)

    vias = [esc[3][1][-1], esc[1][1][-1]]
    added = 0
    for (bx, net, p) in list(boxes):
        if net != 'GND' or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        if (p.GetParentFootprint().GetReference(), p.GetNumber()) in prefanned:
            continue                     # escape + via drawn above
        if any(q.GetNetname() == 'GND' and q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for q in p.GetParentFootprint().Pads()):
            continue                     # joined to a through-hole GND pad of the same part (Y1 combo)
        c = P(p.GetPosition())
        fc = P(p.GetParentFootprint().GetPosition())
        out = math.atan2(c[1] - fc[1], c[0] - fc[0])                    # prefer pointing away from the part centre
        best = None
        angs = sorted((math.pi / 8 * k for k in range(16)),
                      key=lambda a: abs((a - out + math.pi) % (2 * math.pi) - math.pi))
        for a in angs:
            for dist in (0.15, 0.4, 0.7):
                # start just outside the pad edge along the direction
                hx, hy = (bx[2] - bx[0]) / 2, (bx[3] - bx[1]) / 2
                t = min(hx / abs(math.cos(a)) if abs(math.cos(a)) > 1e-6 else 1e9,
                        hy / abs(math.sin(a)) if abs(math.sin(a)) > 1e-6 else 1e9)
                d = t + VR + dist
                v = (c[0] + d * math.cos(a), c[1] + d * math.sin(a))
                if not (ex0 + 0.4 + VR <= v[0] <= ex1 - 0.4 - VR and ey0 + 0.4 + VR <= v[1] <= ey1 - 0.4 - VR):
                    continue
                ok = all(boxd(*v, ob) >= VR + CL + 0.02 and segbox(c, v, ob) >= TW / 2 + CL + 0.02
                         for ob, n2, q in boxes if n2 != 'GND')
                ok = ok and all(math.hypot(v[0] - h[0], v[1] - h[1]) >= hr + 0.15 + 0.25 for h, hr in holes)
                ok = ok and all(math.hypot(v[0] - w[0], v[1] - w[1]) >= 2 * VR + 0.3 for w in vias)
                ok = ok and all(segpt(a2, c2, v) >= VR + CW / 2 + CL + 0.02 and
                                min(segpt(a2, c2, (c[0] + (v[0] - c[0]) * k / 12, c[1] + (v[1] - c[1]) * k / 12))
                                    for k in range(13)) >= TW / 2 + CW / 2 + CL + 0.02 for a2, c2 in csegs)
                ok = ok and all(boxd(*v, ob) >= VR + 0.1 for ob, n2, q in boxes if n2 == 'GND' and q is not p)
                if ok:
                    best = v
                    break
            if best:
                break
        assert best, ('no fan-out via room', p.GetParentFootprint().GetReference(), p.GetNumber())
        via(b, 'GND', *best); track(b, 'GND', [c, best], TW)
        vias.append(best); added += 1
    pcbnew.SaveBoard(PCB, b)
    print('Power class on', POWER, '| Clock class on', CLOCK, '| combo pad joins', joins, '| GND fan-out vias', added)


if __name__ == '__main__':
    prepare()
    passes = sys.argv[1] if len(sys.argv) > 1 else '100'
    env = dict(os.environ, PCB=PCB)
    subprocess.run([sys.executable, os.path.join(HATDIR, '..', 'layout', 'autoroute.py'), passes, '2.0'],
                   env=env, check=True, cwd=os.path.join(HATDIR, '..', 'layout'))
