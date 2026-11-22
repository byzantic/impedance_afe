"""ADC/DAC HAT: create adc_hat/adc_hat.kicad_pcb (Pi Zero pHAT, 65 x 30 mm) from the schematic netlist and place parts.

    kicad-cli sch export netlist -o X.net adc_hat/adc_hat.kicad_sch
    /usr/bin/python3 scripts/hat/place.py X.net
Overwrites adc_hat/adc_hat.kicad_pcb. Coordinates: mm from the board's top-left corner, header edge at the top.
"""
import os, sys
HATDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HATDIR, '..', 'layout'))
import pcbnew  # noqa: E402
from common import mm, V, P, read_netlist, load_fp, ROOT  # noqa: E402

PCB = os.path.join(ROOT, 'adc_hat', 'adc_hat.kicad_pcb')
W, H, RC = 65.0, 30.0, 3.0
HOLES = [(3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)]
# Pi header (top view): pin 1 at the left end of the inner row; even pins on the board-edge row.
PI1 = (32.5 - 9.5 * 2.54, 3.5 + 1.27)
J2_1 = (32.5 - 5.5 * 2.54, 27.5)               # analog 1x12 along the bottom edge, pin 1 at the left (top view)


PL = {
    'U1': (30.0, 14.0, 90), 'U2': (48.5, 14.5, 0), 'U3': (12.0, 23.5, 0),
    # clock: Y1 (DIP-8 can or SMD inside it, top-left) -> R1 -> JP1 -> U1 CLKIN (pin 17, top row)
    'Y1': (12.0, 14.0, 0), 'C10': (3.0, 12.0, 90), 'R1': (20.6, 7.4, 0), 'JP1': (24.8, 7.4, 0),
    # LDO (below Y1) in/out, AVDD (pin 1, bottom-left), DVDD (pin 20, top-left), CAP (pin 18)
    'C1': (8.0, 23.5, 90), 'C15': (12.0, 27.6, 0), 'C2': (16.0, 23.5, 90), 'C3': (25.3, 16.0, 90),
    'C4': (25.3, 12.0, 90), 'C5': (23.6, 12.0, 90), 'C6': (27.9, 8.4, 90),   # C6 clear of the ADC_CLK riser
    # DAC
    'FB1': (45.2, 9.0, 0), 'C7': (48.4, 11.6, 0), 'C8': (51.8, 10.8, 0), 'C9': (53.2, 13.5, 90),
    'R2': (46.6, 19.9, 180), 'JP2': (43.4, 21.9, 0), 'R6': (45.6, 17.6, 270),
    'R3': (39.0, 8.5, 90), 'R4': (40.6, 8.5, 90), 'R5': (42.2, 8.5, 90),
    # MCU / cable header, right-hand short edge between the corner holes (pin 1 top-left)
    'J3': (60.0, 15.0 - 2.5 * 2.54, 0),
}
for ch in range(4):                       # input filters between U1 inputs and J2
    x = 25.6 + 3.3 * ch
    flip = ch in (1, 3)                   # U1 pin order is N,P on channels 1 and 3: mirror so the pairs don't cross
    PL[f'R{10+2*ch}'] = (x + 1.6 if flip else x, 22.0, 90)
    PL[f'R{11+2*ch}'] = (x if flip else x + 1.6, 22.0, 90)
    PL[f'C{11+ch}'] = (x + 0.8, 19.4, 180 if flip else 0)
for i, (x, y) in enumerate(HOLES):
    PL[f'H{i+1}'] = (x, y, 0)


def outline(b):
    pts = [(RC, 0), (W - RC, 0), (W, RC), (W, H - RC), (W - RC, H), (RC, H), (0, H - RC), (0, RC)]
    for a, c in [(0, 1), (2, 3), (4, 5), (6, 7)]:
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        s.SetStart(V(*pts[a])); s.SetEnd(V(*pts[c])); b.Add(s)
    for cx, cy, sx, sy in [(RC, RC, 0, RC), (W - RC, RC, W - RC, 0), (W - RC, H - RC, W, H - RC), (RC, H - RC, RC, H)]:
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
        s.SetCenter(V(cx, cy)); s.SetStart(V(sx, sy)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T), True)
        b.Add(s)


def fit_connector(fp, targets):
    """Put `fp` on the bottom side with pads at `targets` {num: (x, y)}; search orientation, then translate."""
    fp.SetPosition(V(0, 0))
    fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    for r in (0, 90, 180, 270):
        fp.SetOrientationDegrees(r)
        fp.SetPosition(V(0, 0))
        pads = {p.GetNumber(): P(p.GetPosition()) for p in fp.Pads()}
        dx = targets['1'][0] - pads['1'][0]; dy = targets['1'][1] - pads['1'][1]
        if all(abs(pads[n][0] + dx - x) < 1e-3 and abs(pads[n][1] + dy - y) < 1e-3 for n, (x, y) in targets.items()):
            fp.SetPosition(V(dx, dy))
            return r
    raise RuntimeError('no orientation fits ' + fp.GetReference())


def j1_targets():
    t = {}
    for n in range(1, 41):
        k = (n - 1) // 2
        t[str(n)] = (PI1[0] + 2.54 * k, PI1[1] if n % 2 else PI1[1] - 2.54)
    return t


def j2_targets():
    return {str(n): (J2_1[0] + 2.54 * (n - 1), J2_1[1]) for n in range(1, 13)}


def build(netfile):
    comps, nets = read_netlist(netfile)
    assert set(comps) == set(PL) | {'J1', 'J2'}, (set(comps) ^ (set(PL) | {'J1', 'J2'}))
    pin_net = {(r, p): nm for nm, nodes in nets.items() for r, p in nodes}
    if os.path.exists(PCB):
        os.remove(PCB)
    b = pcbnew.NewBoard(PCB)
    b.SetCopperLayerCount(2)
    ds = b.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    ds.m_TrackMinWidth = mm(0.15); ds.m_MinClearance = mm(0.15)
    ds.m_ViasMinSize = mm(0.6); ds.m_MinThroughDrill = mm(0.3); ds.m_ViasMinAnnularWidth = mm(0.13)
    ds.m_CopperEdgeClearance = mm(0.4); ds.m_HoleToHoleMin = mm(0.25); ds.m_HoleClearance = mm(0.25)
    ds.m_SolderMaskExpansion = mm(0.05); ds.m_SolderMaskMinWidth = mm(0.1)
    dflt = ds.m_NetSettings.GetDefaultNetclass()
    dflt.SetClearance(mm(0.2)); dflt.SetTrackWidth(mm(0.25)); dflt.SetViaDiameter(mm(0.6)); dflt.SetViaDrill(mm(0.3))
    netinfo = {}
    for nm in nets:
        ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni); netinfo[nm] = ni
    for ref, c in sorted(comps.items()):
        fp = load_fp(c['fp'])
        fp.SetReference(ref); fp.SetValue(c['value'])
        fp.SetPath(pcbnew.KIID_PATH(c['path']))
        fp.SetDNP(c['dnp']); fp.SetExcludedFromBOM(False)
        for pad in fp.Pads():
            nm = pin_net.get((ref, pad.GetNumber()))
            if nm:
                pad.SetNet(netinfo[nm])
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); fp.Reference().SetTextThickness(mm(0.12))
        fp.Value().SetVisible(False)
        b.Add(fp)
        if ref == 'J1':
            fit_connector(fp, j1_targets())
        elif ref == 'J2':
            fit_connector(fp, j2_targets())
        else:
            x, y, r = PL[ref]
            fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(r)
    outline(b)
    # GND pours, both layers
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(netinfo['GND'])
        z.SetLocalClearance(mm(0.25)); z.SetMinThickness(mm(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.4))
        ol = z.Outline(); ol.NewOutline()
        for x, y in [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)]:
            ol.Append(mm(x + 40), mm(y + 30))
        b.Add(z)
    t = pcbnew.PCB_TEXT(b); t.SetText('ADC/DAC HAT rev A'); t.SetLayer(pcbnew.B_SilkS); t.SetMirrored(True)
    t.SetPosition(V(32.5, 14.0)); t.SetTextSize(pcbnew.VECTOR2I(mm(1.2), mm(1.2))); t.SetTextThickness(mm(0.18)); b.Add(t)
    b.Save(PCB)
    b = pcbnew.LoadBoard(PCB)                 # fill on a reloaded board (fresh connectivity / hole knockouts)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(PCB, b)
    print('placed', len(comps), 'footprints,', len(nets), 'nets ->', PCB)


if __name__ == '__main__':
    build(sys.argv[1])
