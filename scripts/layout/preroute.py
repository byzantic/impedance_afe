"""Rev B: hand-route and lock the critical nets, add zones and the SUM_HI guard.  Run after place.py.

Idempotent: removes all tracks, vias, zones and mask drawings, then rebuilds them.
"""
import math
import pcbnew
from common import *  # noqa
import place

b = pcbnew.LoadBoard(PCB)
YBUS = place.YBUS
for t in list(b.GetTracks()):
    b.Remove(t)
for z in list(b.Zones()):
    b.Remove(z)
for d in list(b.GetDrawings()):
    if d.GetLayer() in (pcbnew.F_Mask, pcbnew.B_Mask):
        b.Remove(d)

FC, BC = pcbnew.F_Cu, pcbnew.B_Cu


def fpos(ref):
    return P(b.FindFootprintByReference(ref).GetPosition())


def xf(ref, lx, ly):
    """footprint-local (rotation 0) mm -> board mm"""
    fp = b.FindFootprintByReference(ref)
    x0, y0 = P(fp.GetPosition())
    th = math.radians(fp.GetOrientationDegrees())
    return (x0 + lx * math.cos(th) + ly * math.sin(th), y0 - lx * math.sin(th) + ly * math.cos(th))


def pnet(ref, num):
    return b.FindFootprintByReference(ref).FindPadByNumber(str(num)).GetNetname()


def close(a, c, tol=0.02):
    return abs(a[0] - c[0]) < tol and abs(a[1] - c[1]) < tol


# ================================================================ combo footprint joins (all op-amps)
# Local coords (rotation 0): DIP pins at x=+-3.81; SOIC pins 1-4 at y=+2.475, 8-5 at y=-2.475.
OPAMPS = [r for r in place.DEC]
for u in OPAMPS:
    for n, lx, ly in [(2, -3.81, -1.27), (3, -3.81, 1.27), (4, -3.81, 3.81), (6, 3.81, 1.27), (7, 3.81, -1.27)]:
        assert close(xf(u, lx, ly), pad_xy(b, u, n, smd=False)), (u, n)
    for n, lx, ly in [(2, -0.635, 2.475), (3, 0.635, 2.475), (4, 1.905, 2.475), (6, 0.635, -2.475), (7, -0.635, -2.475)]:
        assert close(xf(u, lx, ly), pad_xy(b, u, n, smd=True)), (u, n)
    L = lambda pts: [xf(u, *p) for p in pts]  # noqa
    n2, n3, n4, n6, n7 = (pnet(u, k) for k in (2, 3, 4, 6, 7))
    # pin 2 and pin 6: through the package interior on F.Cu
    track(b, n2, L([(-3.81, -1.27), (-2.6, -0.6), (-0.635, -0.6), (-0.635, 2.475)]), 0.25)
    track(b, n6, L([(3.81, 1.27), (2.6, 0.6), (0.635, 0.6), (0.635, -2.475)]), 0.25)
    # pin 3: SOIC pad -> via below it; DIP pad -> via on B.Cu (GND: plane does it)
    track(b, n3, L([(0.635, 2.475), (0.635, 4.4)]), 0.25)
    via(b, n3, *xf(u, 0.635, 4.4))
    if n3 != 'GND':
        track(b, n3, L([(-3.81, 1.27), (0.635, 4.4)]), 0.25, BC)
    # pin 7 (+15V): mirror image of pin 3
    track(b, n7, L([(-0.635, -2.475), (-0.635, -4.4)]), 0.3)
    via(b, n7, *xf(u, -0.635, -4.4))
    track(b, n7, L([(3.81, -1.27), (-0.635, -4.4)]), 0.3, BC)
    # pin 4 (-15V): around the outside of the SOIC row on F.Cu
    track(b, n4, L([(-3.81, 3.81), (-3.2, 5.45), (1.905, 5.45), (1.905, 2.475)]), 0.3)

# ================================================================ SUM_HI: WE spine + bus
we = pad_xy(b, 'J7', 1)
u5in = pad_xy(b, 'U5', 2, smd=False)
assert abs(we[0] - u5in[0]) < 0.01
track(b, 'SUM_HI', [we, (we[0], YBUS), u5in], 0.3)
on_bus = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        x, y = P(p.GetPosition())
        if abs(y - YBUS) < 0.01:
            on_bus.append((x, fp.GetReference(), p.GetNumber(), p.GetNetname()))
on_bus.sort()
xs = [x for x, r, n, nn in on_bus if nn == '/SUM_HI']
bad = [(r, n, nn) for x, r, n, nn in on_bus if min(xs) <= x <= max(xs) and nn != '/SUM_HI']
assert not bad, bad
track(b, 'SUM_HI', [(min(xs), YBUS), (max(xs), YBUS)], 0.3)
track(b, 'SUM_HI', [pad_xy(b, 'Q1', 1), pad_xy(b, 'Q1', 2)], 0.3)
print('SUM_HI bus x %.1f..%.1f, %d pads' % (min(xs), max(xs), len(xs)))

# ================================================================ feedback nodes FB1..FB6 and IHI_OUT bus
for r, c, k, x, long_ in place.cols:
    net = pnet(r, 2)
    rp2, cp2, kp1 = pad_xy(b, r, 2), pad_xy(b, c, 2), pad_xy(b, k, 1)
    track(b, net, [cp2, (cp2[0], rp2[1]), rp2], 0.25)
    track(b, net, [rp2, kp1], 0.25)
riser_x = place.UX + 2.33
u5out = pad_xy(b, 'U5', 6, smd=False)
ylong, yshort = 88.0, 100.0
k_long = [k for r, c, k, x, l in place.cols if l]
k_short = [k for r, c, k, x, l in place.cols if not l]
xstep = (pad_xy(b, k_long[-1], 7)[0] + pad_xy(b, k_short[0], 7)[0]) / 2
r32 = pad_xy(b, 'R32', 1)
track(b, 'IHI_OUT', [u5out, (riser_x, u5out[1] - 1.06), (riser_x, ylong), (xstep, ylong), (xstep, yshort),
                     (r32[0], yshort), r32], 0.4)
for k in k_long:
    p = pad_xy(b, k, 7); track(b, 'IHI_OUT', [p, (p[0], ylong)], 0.4)
for k in k_short:
    p = pad_xy(b, k, 7); track(b, 'IHI_OUT', [p, (p[0], yshort)], 0.4)

# ================================================================ RE input (U2 pin 3) and RE_BNC
r19a, r19b = pad_xy(b, 'R19', 1), pad_xy(b, 'R19', 2)
track(b, 'RE_IN', [r19b, pad_xy(b, 'U2', 3, smd=False)], 0.25)
k9 = pad_xy(b, 'K9', 7)
track(b, 'RE_BNC', [k9, (k9[0] + (r19a[1] - k9[1]), r19a[1]), r19a, pad_xy(b, 'J5', 1)], 0.25)

# ================================================================ SUM_LO and the low-gain TIA feedback
q1c, q2a, q2b = pad_xy(b, 'Q1', 3), pad_xy(b, 'Q2', 1), pad_xy(b, 'Q2', 2)
c27a, c27b = pad_xy(b, 'C27', 1), pad_xy(b, 'C27', 2)
r33a, r33b = pad_xy(b, 'R33', 1), pad_xy(b, 'R33', 2)
u6in = pad_xy(b, 'U6', 2, smd=False)
u6out = pad_xy(b, 'U6', 6, smd=False)
r34a, r34b = pad_xy(b, 'R34', 1), pad_xy(b, 'R34', 2)
# SUM_LO: Q1 C / Q2 B+E -> C27 -> R33 -> U6 -IN (short, vertical, 45-degree legs)
track(b, 'SUM_LO', [q1c, q2a, q2b], 0.25)
d = c27a[1] - r33a[1]
track(b, 'SUM_LO', [q1c, c27a, (c27a[0] - d, r33a[1]), r33a], 0.25)
d = u6in[0] - r33a[0]
track(b, 'SUM_LO', [r33a, (r33a[0], u6in[1] + d), u6in], 0.25)
# ILO_OUT: C27/R33 -> corridor right of U6 -> R34; U6 out over the top into the same corridor
xc = u6out[0] + 5.23
d = c27b[1] - r33b[1]
track(b, 'ILO_OUT', [c27b, (c27b[0] + d, r33b[1]), r33b], 0.3)
track(b, 'ILO_OUT', [r33b, (xc, r33b[1] - (xc - r33b[0])), (xc, r34a[1]), r34a], 0.3)
yt = u6out[1] - 1.7
track(b, 'ILO_OUT', [u6out, (u6out[0], yt), (xc, yt), (xc, r34a[1])], 0.3)
# output lanes straight down to the BNCs
track(b, 'ILO_BNC', [r34b, pad_xy(b, 'J10', 1)], 0.3)
track(b, 'IHI_BNC', [pad_xy(b, 'R32', 2), pad_xy(b, 'J9', 1)], 0.3)

# ================================================================ nuller injection, cal mid-nodes
k17, c18, k15 = pad_xy(b, 'K17', 7), pad_xy(b, 'C18', 2), pad_xy(b, 'K15', 1)
track(b, 'NULLC_INJ', [k17, (k17[0] + (c18[1] - k17[1]), c18[1]), c18, k15], 0.25)
k18, r30, k16 = pad_xy(b, 'K18', 7), pad_xy(b, 'R30', 2), pad_xy(b, 'K16', 1)
track(b, 'NULLG_INJ', [k18, (k18[0] - 1.32, r30[1]), r30, k16], 0.25)
track(b, 'NULLC_R', [pad_xy(b, 'C19', 2), pad_xy(b, 'K17', 1)], 0.25)
r18, k11, k12 = pad_xy(b, 'R18', 2), pad_xy(b, 'K11', 1), pad_xy(b, 'K12', 1)
track(b, 'CALR_MID', [r18, k11], 0.25)
track(b, 'CALR_MID', [k12, (k12[0] - 2.4, k12[1] + 1.84), (k12[0] - 2.4, r18[1] - 0.72), r18], 0.25)
c16, k13, k14 = pad_xy(b, 'C16', 2), pad_xy(b, 'K13', 1), pad_xy(b, 'K14', 1)
track(b, 'CALC_MID', [k14, k13], 0.25)
track(b, 'CALC_MID', [c16, (k13[0], c16[1])], 0.25)


# ================================================================ CTL0..15: Pico -> pull -> driver input (F.Cu, planar)
# Slot n (n-th pull from the left) carries CTLn = GPn and feeds driver channel 15-n.  Pico lanes nest: GP0 (top pin)
# runs highest and goes furthest left.  Lanes 0-3 run above the pull row and drop beside their resistor; lanes 4-15
# run under the resistor bodies.  Fan-in beside the Pico: pins below their lane turn at decreasing x going down.
GP_PIN = {0: 1, 1: 2, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14, 11: 15, 12: 16, 13: 17, 14: 19, 15: 20}
for n in range(16):
    ch = 15 - n
    r = f'R{60+ch}'
    p1 = pad_xy(b, r, 1)
    net = pnet(r, 1)
    assert net == N(f'CTL{n}') == pnet('A1', GP_PIN[n]), (n, net)
    dp = pad_xy(b, 'U22', ch + 1) if ch < 8 else pad_xy(b, 'U23', ch - 7)
    track(b, net, [p1, (p1[0], dp[1] - abs(dp[0] - p1[0])), dp], 0.25)
    gp = pad_xy(b, 'A1', GP_PIN[n])
    h = 5.7 + 0.8 * n if n < 4 else 12.3 + 0.65 * (n - 4)
    t = 136.0 + 0.8 * n if gp[1] < h else 137.6 - 0.55 * (n - 2)
    pts = [gp, (t, gp[1]), (t, h)]
    if n < 4:
        xd = p1[0] + 1.6
        pts += [(xd, h), (xd, 19.6), p1]
    else:
        pts += [(p1[0], h), p1]
    track(b, net, pts, 0.25)

# ================================================================ zones
def zone(net, layer, pts, prio=0, clearance=None, name=''):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer); z.SetNet(b.FindNet(N(net)))
    ol = z.Outline(); ol.NewOutline()
    for x, y in pts:
        ol.Append(mm(x + OX), mm(y + OY))
    z.SetAssignedPriority(prio)
    if clearance:
        z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.45))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if name:
        z.SetZoneName(name)
    b.Add(z)
    return z


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


m = 0.5
for lay in (FC, BC):
    zone('GND', lay, rect(m, m, W - m, H - m), 0, name='GND plane')
    zone('PICO_GND', lay, rect(135.5, m, 159.3, 56.0), 1, name='Pico ground (joins GND via FB5/JP5 only)')
    # driven guard (RE_BUF = U2 output) around RE_IN: R19 pin2 -> U2 pin3 and its combo join
    ux = place.U2X
    zone('RE_BUF', lay, rect(ux - 4.53, 114.3, ux + 6.17, 126.2), 2, name='RE_BUF guard')
    # GUARD (U3-driven, J5 shell) around the RE_BNC run from K9 to R19/J5
    k9x, k9y = pad_xy(b, 'K9', 7); jx = pad_xy(b, 'J5', 1)[0]
    zone('GUARD', lay, [(k9x - 2.5, k9y - 1.7), (k9x + 3.8, k9y - 1.7), (k9x + 3.8, 126.6), (jx + 3.5, 126.6),
                         (jx + 3.5, 138.6), (jx - 3.5, 138.6), (jx - 3.5, 136.6), (k9x - 2.5, 126.6)], 2,
         name='GUARD around RE_BNC')

# ================================================================ SUM_HI guard: stitching vias + mask-free band over the GND pour
obst = []  # (x0, y0, x1, y1, net) pad boxes, and track segments
for p in b.GetPads():
    bb = p.GetBoundingBox()
    obst.append(('box', (pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY,
                         pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY), p.GetNetname()))
for t in b.GetTracks():
    (ax, ay), (bx, by) = P(t.GetStart()), P(t.GetEnd())
    w = t.GetWidth(FC) if t.GetClass() == 'PCB_VIA' else t.GetWidth()
    obst.append(('seg', (ax, ay, bx, by, pcbnew.ToMM(w) / 2), t.GetNetname()))
HIGHZ = {N(n) for n in ['SUM_HI', 'SUM_LO', 'RE_IN', 'RE_BNC', 'NULLC_INJ', 'NULLG_INJ'] + [f'FB{i}' for i in range(1, 7)]}


def segd(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def free(x, y, r=0.3):
    for k, g, n in obst:
        if n == 'GND':
            continue
        cl = 0.5 if n in HIGHZ else 0.3
        if k == 'box':
            d = math.hypot(max(g[0] - x, 0, x - g[2]), max(g[1] - y, 0, y - g[3]))
        else:
            d = segd(x, y, *g[:4]) - g[4]
        if d < r + cl:
            return False
    return True


nst = 0
xs_all = sorted(xs)
for yv in (YBUS - 2.3, YBUS + 2.3):
    x = xs_all[0] - 2.0
    while x <= xs_all[-1] + 2.0:
        if free(x, yv):
            via(b, 'GND', x, yv); obst.append(('box', (x - .3, yv - .3, x + .3, yv + .3), 'GND')); nst += 1
            x += 3.0
        else:
            x += 0.5
print('guard stitching vias', nst)

# mask-free band: (SUM_HI copper + 1.6 mm) - (SUM_HI copper + 0.6 mm) - (other-net copper + 0.25 mm)
err = mm(0.01)
hi, other = pcbnew.SHAPE_POLY_SET(), pcbnew.SHAPE_POLY_SET()
for p in b.GetPads():
    if not p.IsOnLayer(FC):
        continue
    tgt = hi if p.GetNetname() == '/SUM_HI' else (None if p.GetNetname() == 'GND' else other)
    if tgt is not None:
        p.TransformShapeToPolygon(tgt, FC, 0, err, pcbnew.ERROR_INSIDE)
for t in b.GetTracks():
    if not t.IsOnLayer(FC) or t.GetNetname() == 'GND':
        continue
    t.TransformShapeToPolygon(hi if t.GetNetname() == '/SUM_HI' else other, FC, 0, err, pcbnew.ERROR_INSIDE)
hi.Simplify(); other.Simplify()
outer, inner = pcbnew.SHAPE_POLY_SET(hi), pcbnew.SHAPE_POLY_SET(hi)
outer.Inflate(mm(1.6), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, err)
inner.Inflate(mm(0.6), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, err)
other.Inflate(mm(0.25), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, err)
outer.BooleanSubtract(inner); outer.BooleanSubtract(other)
outer.Fracture() if hasattr(outer, 'Fracture') else None
band = pcbnew.PCB_SHAPE(b); band.SetShape(pcbnew.SHAPE_T_POLY); band.SetLayer(pcbnew.F_Mask)
band.SetPolyShape(outer); band.SetFilled(True); band.SetWidth(0)
b.Add(band)
print('guard mask band area %.0f mm2' % (outer.Area() / 1e12))

for t in b.GetTracks():
    t.SetLocked(True)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB, b)
print('prerouted; tracks', sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK'),
      'vias', sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA'))
