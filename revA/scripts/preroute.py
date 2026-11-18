"""Hand-route the precision nets (summing node, feedback, IHI bus, RE input) and lock them."""
import pcbnew
F = 'impedance_afe.kicad_pcb'
mm = pcbnew.FromMM; OX, OY = 50, 50
b = pcbnew.LoadBoard(F)
def pad(ref, n):
    p = b.FindFootprintByReference(ref).FindPadByNumber(str(n)).GetPosition()
    return (pcbnew.ToMM(p.x) - OX, pcbnew.ToMM(p.y) - OY)
def T(net, pts, w=0.3, layer=pcbnew.F_Cu):
    ni = b.FindNet(net)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetLayer(layer); t.SetWidth(mm(w)); t.SetNet(ni)
        t.SetStart(pcbnew.VECTOR2I(mm(x0 + OX), mm(y0 + OY))); t.SetEnd(pcbnew.VECTOR2I(mm(x1 + OX), mm(y1 + OY)))
        t.SetLocked(True); b.Add(t)

# ---- SUM_HI: vertical bus from U5 pin2 to WE BNC, stubs to every feedback element + D3
p2 = pad('U5', 2); bx = p2[0]; we = pad('J7', 1)
T('SUM_HI', [p2, (bx, we[1] - 1.6), (we[0], we[1] - 0.6), we])
for ref in ['R21', 'C21', 'R22', 'C22', 'R23', 'C23', 'R24', 'C24', 'R25', 'C25']:
    q = pad(ref, 1); T('SUM_HI', [q, (bx, q[1])])
d1, d2 = pad('D3', 1), pad('D3', 2)
T('SUM_HI', [d1, d2]); T('SUM_HI', [((d1[0]), (d1[1] + d2[1]) / 2), (bx, (d1[1] + d2[1]) / 2)])

# ---- feedback nets to range relays (pin1 of each relay)
def fb(net, r, c, path):
    pr, pc = pad(r, 2), pad(c, 2)
    T(net, [pc, (pr[0], pc[1]), pr])
    T(net, [pr] + path)
T('FB1', [pad('C21', 2), pad('R21', 2)]); T('FB1', [pad('R21', 2), (pad('R21', 2)[0], 68.0), (pad('K1', 1)[0], 67.4), pad('K1', 1)])
r22, c22 = pad('R22', 2), pad('C22', 2)
T('FB2', [c22, r22, (102.5, r22[1]), (102.5, 68.0), (pad('K2', 1)[0] + 0.6, 67.4), pad('K2', 1)])
fb('FB3', 'R23', 'C23', [(pad('R23', 2)[0], 68.0), (pad('K3', 1)[0] + 0.6, 67.4), pad('K3', 1)])
fb('FB4', 'R24', 'C24', [(122.6, pad('R24', 2)[1]), (122.6, 69.6), (pad('K4', 1)[0], 69.6), pad('K4', 1)])
fb('FB5', 'R25', 'C25', [(124.6, pad('R25', 2)[1]), (124.6, 72.6), (pad('K5', 1)[0], 72.6), pad('K5', 1)])

# ---- IHI_OUT bus: U5 out -> top bus -> relay pin7s -> R14
p6 = pad('U5', 6); ybus = 47.6
T('IHI_OUT', [p6, (p6[0], ybus)], 0.4)
xs = sorted(pad(k, 7)[0] for k in ['K1', 'K2', 'K3', 'K4', 'K5'])
T('IHI_OUT', [(xs[0], ybus), (pad('R14', 1)[0], ybus), pad('R14', 1)], 0.4)
for k in ['K1', 'K2', 'K3', 'K4', 'K5']:
    q = pad(k, 7); T('IHI_OUT', [(q[0], ybus), q], 0.4)

# ---- RE input: R7 -> U2 +in
r7, u3 = pad('R7', 2), pad('U2', 3)
T('RE_IN', [r7, (u3[0], r7[1] - 1.2), u3])
pcbnew.SaveBoard(F, b)
print('prerouted')
