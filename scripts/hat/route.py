"""ADC/DAC HAT: prepare adc_hat/adc_hat.kicad_pcb for autorouting, then autoroute it.

    FREEROUTING=/path/freerouting-2.5.0.jar /usr/bin/python3 scripts/hat/route.py [passes]

Run on the board as placed by scripts/hat/place.py (it adds locked fan-out vias; re-running adds them again).
1. Net class Power (0.4 mm) for the supply rails.
2. GND fan-out: a locked via beside every SMD GND pad (collision-checked), so each pad reaches the bottom plane
   whatever the top-layer routing does to the top pour.
3. scripts/layout/autoroute.py with PCB=this board (GND to the pours, everything else routed).
"""
import math, os, subprocess, sys
HATDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HATDIR, '..', 'layout'))
import pcbnew  # noqa: E402
from common import mm, P, ROOT, via, track  # noqa: E402

PCB = os.path.join(ROOT, 'adc_hat', 'adc_hat.kicad_pcb')
POWER = ['+5V', '+5VA', '+3V3', '+3V3A']
CL, VR, TW = 0.2, 0.3, 0.25           # clearance, via radius, fan-out track width (0.5 mm pitch on U2)


def prepare():
    b = pcbnew.LoadBoard(PCB)
    assert not any(t.GetClass() == 'PCB_VIA' for t in b.GetTracks()), 'board already has vias: re-place it first'
    ns = b.GetDesignSettings().m_NetSettings
    nc = pcbnew.NETCLASS('Power')
    nc.SetTrackWidth(mm(0.4)); nc.SetClearance(mm(CL)); nc.SetViaDiameter(mm(0.6)); nc.SetViaDrill(mm(0.3))
    ns.SetNetclass('Power', nc)
    ns.ClearNetclassPatternAssignments()
    for n in POWER:
        ns.SetNetclassPatternAssignment(n, 'Power')

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

    vias = []
    added = 0
    for (bx, net, p) in list(boxes):
        if net != 'GND' or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
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
    print('Power class on', POWER, '| GND fan-out vias', added)


if __name__ == '__main__':
    prepare()
    passes = sys.argv[1] if len(sys.argv) > 1 else '100'
    env = dict(os.environ, PCB=PCB)
    subprocess.run([sys.executable, os.path.join(HATDIR, '..', 'layout', 'autoroute.py'), passes, '2.0'],
                   env=env, check=True, cwd=os.path.join(HATDIR, '..', 'layout'))
