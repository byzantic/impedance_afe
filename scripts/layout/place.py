"""Rev B: create impedance_afe.kicad_pcb from the schematic netlist and place every part.

Run from anywhere with /usr/bin/python3 (needs KiCad 9 SWIG pcbnew):
    kicad-cli sch export netlist -o /tmp/afe.net impedance_afe.kicad_sch
    /usr/bin/python3 scripts/layout/place.py /tmp/afe.net
Overwrites impedance_afe.kicad_pcb.  Board coords: mm, origin top-left, y down.
Digital/power along the top edge, analog BNC row along the bottom edge (WE/U5 centre-bottom).
"""
import os, sys
import pcbnew
from common import *  # noqa

YB = H - 12.7          # BNC pin-1 row (bottom edge, connector rotated 180 -> jack points down)
YBUS = YB - 5.3        # SUM_HI bus
PL = {}                # ref -> (x, y, rot)


def put(ref, x, y, r=0):
    assert ref not in PL, ref
    PL[ref] = (round(x, 3), round(y, 3), r)


DEC = {'U9': ('C100', 'C101'), 'U10': ('C102', 'C103'), 'U11': ('C104', 'C105'), 'U1': ('C106', 'C107'),
       'U2': ('C108', 'C109'), 'U3': ('C110', 'C111'), 'U7': ('C112', 'C113'), 'U4': ('C114', 'C115'),
       'U8': ('C116', 'C117'), 'U12': ('C118', 'C119'), 'U13': ('C120', 'C121'), 'U14': ('C122', 'C123'),
       'U5': ('C124', 'C125'), 'U6': ('C126', 'C127')}


def opamp(ref, x, y, side='R'):
    """Combo footprint rotated 90: inputs (1-4) on the bottom row, outputs (8-5) on top.
    Decoupling pair on `side`: C+ (pin1 +15V) and C- (pin2 -15V), 5 mm discs."""
    put(ref, x, y, 90)
    cp, cn = DEC[ref]
    if side == 'R':
        put(cp, x + 7.0, y - 1.3, 90); put(cn, x + 7.0, y + 1.3, 270)
    elif side == 'L':
        put(cp, x - 7.0, y - 1.3, 90); put(cn, x - 7.0, y + 1.3, 270)
    elif side == 'T':
        put(cp, x - 6.3, y - 7.0, 0); put(cn, x + 6.3, y - 7.0, 180)
    elif side == 'B':
        put(cp, x - 6.3, y + 7.0, 0); put(cn, x + 6.3, y + 7.0, 180)
    # side None: caller places the pair


def relay(ref, x, y, r):
    """SIL reed: pin1 at (x, y). r=90 -> pins go UP (pin7 15.24 above), 270 -> DOWN, 0 -> right, 180 -> left."""
    put(ref, x, y, r)


# ================================================================ bottom BNC row (rot 180) + left-edge inputs
for ref, x in [('J4', 20), ('J5', 44), ('J6', 64), ('J7', 104), ('J9', 172), ('J10', 192), ('J8', 211)]:
    put(ref, x, YB, 180)
put('J2', 12.7, 62, 90)        # BIAS/PULSE
put('J3', 12.7, 86, 90)        # AC PROBE
put('J11', 207, 12.7, 0)       # SYNC_IN (top edge)

# ================================================================ high-gain TIA (U5) + SUM_HI comb
# U5 rot 90: pin2 (-IN) bottom row, straight above the WE BNC pin.  SUM_HI bus at YBUS runs
# right (ranges, steering transistors) and left (null-injection and cal relays).
UX, UY = 105.27, YBUS - 8.0
opamp('U5', UX, UY, None)
put('C124', 109.0, 117.8, 90)      # +15V pin1 bottom, GND top (right of the output riser)
put('C125', 101.2, 116.3, 0)       # GND, -15V (above U5, left of the output riser)
# range columns, left to right: (Rf, Cf, relay, x of Rf, long Rf?)  K5/K6 get extra room (Coto option)
# 100M nearest U5 -IN (leakage / PTFE-standoff option), 1k furthest.
cols = [('R46', 'C46', 'K6', 113.2, True), ('R45', 'C45', 'K5', 122.6, True), ('R44', 'C44', 'K4', 132.0, True),
        ('R43', 'C43', 'K3', 138.4, False), ('R42', 'C42', 'K2', 145.0, False), ('R41', 'C41', 'K1', 151.6, False)]
for r, c, k, x, long_ in cols:
    put(r, x, YBUS, 90)                                   # pin1 on bus, pin2 up
    put(c, x + (3.6 if long_ else 2.9), YBUS, 90)
    rp = 20.32 if long_ else 10.16
    relay(k, x, YBUS - rp - 4.0, 90)                      # pin1 = FBn, pin7 = IHI_OUT on top
put('Q1', 159.5, YBUS, 90)          # pins 1,2 SUM_HI (pin1 on bus), pin3 SUM_LO top
put('Q2', 164.5, YBUS - 2.54, 270)  # pin3 SUM_HI on bus, pins 1,2 SUM_LO
# left branch: null injection relays nearest U5, cal relays further left (pin7 = SUM_HI on bus, pin1 up)
relay('K16', 97.2, YBUS - 15.24, 270)
relay('K15', 90.8, YBUS - 15.24, 270)
relay('K13', 76.4, YBUS - 15.24, 270)
relay('K11', 70.0, YBUS - 15.24, 270)
# cal parts
put('R18', 70.0, YBUS - 15.24 - 14.2, 270)                # pin1 CE_INT top, pin2 CALR_MID bottom
put('C16', 73.2, YBUS - 15.24 - 6.1, 270)                 # pin1 CE_INT top, pin2 CALC_MID bottom
relay('K12', 70.0, YBUS - 15.24 - 18.6, 90)               # NC to GND, pin1 CALR_MID bottom
relay('K14', 76.4, YBUS - 15.24 - 10.8, 90)               # NC to GND, pin1 CALC_MID bottom
# null injection parts (short HighZ stubs into K15/K16 pin1)
put('C18', 90.8, YBUS - 15.24 - 6.1, 270)                 # NULLC_DRV top -> NULLC_INJ bottom
relay('K17', 83.6, YBUS - 15.24 - 20.8, 270)              # pin1 NULLC_R top, pin7 NULLC_INJ bottom
put('R30', 97.2, YBUS - 15.24 - 14.4, 270)                # NULLG_AC top -> NULLG_INJ bottom
relay('K18', 102.6, YBUS - 15.24 - 20.8, 270)             # pin1 NULLG_R top, pin7 NULLG_INJ bottom
put('C19', 83.6, 89.4, 270)                               # NULLC_DRV top -> NULLC_R bottom (K17 pin1)
put('R31', 107.0, 66.0, 90)                               # NULLG_AC -> NULLG_R
put('C20', 101.0, 69.0, 90)                               # NULLG_DRV -> NULLG_AC (film)
opamp('U13', 90.0, 80.0, 'T')
opamp('U14', 112.0, 80.0, 'T')
opamp('U12', 92.0, 52.0, 'L')
put('R28', 99.0, 46.0, 0); put('R29', 99.0, 49.5, 0)
put('J14', 128.0, 61.0, 0)                # RV1 (panel C-null pot) cable, Molex KK 254
put('J15', 128.0, 69.0, 0)                # RV2 (panel G-null pot) cable
# low-gain TIA (between I_HI and I_LO BNCs)
opamp('U6', 182.0, YBUS - 11.0, 'R')
put('R33', 174.5, YBUS - 4.5, 90)         # SUM_LO bottom -> ILO_OUT top
put('C27', 171.5, YBUS - 4.5, 90)
put('R34', 196.0, YBUS - 8.76, 270)       # ILO_OUT top -> ILO_BNC bottom (J10)
put('R32', 166.0, 101.0, 270)             # IHI_OUT top -> IHI_BNC bottom

# ================================================================ V monitors -> V_OUT (bottom right)
opamp('U8', 198.0, 82.0, 'L')
opamp('U4', 198.0, 102.0, 'L')
put('R21', 204.5, 92.5, 0); put('R22', 204.5, 96.0, 0)
put('C17', 174.0, 77.5, 0); put('R23', 174.0, 81.5, 0)
put('R24', 205.5, 79.0, 0); put('R25', 205.5, 82.5, 0)
put('R26', 204.5, 106.0, 0); put('R27', 217.5, 106.0, 90)
relay('K19', 210.4, 111.0, 270)      # NC: VDC_R -> VOUT (pin7 bottom, toward J8)
relay('K20', 216.8, 111.0, 270)      # VAC_R -> VOUT

# ================================================================ RE electrometer / guard / RE_MON
U2X, U2Y = 42.73, YBUS - 15.5
opamp('U2', U2X, U2Y, 'R')
put('R19', 44.0, YBUS + 1.4, 90)     # pin1 RE_BNC (bottom, by J5), pin2 RE_IN up to U2 pin3
opamp('U3', 44.0, 101.0, 'R')
opamp('U7', 58.0, 101.0, 'R')
put('R20', 58.0, YBUS - 9.0, 270)    # GUARD_DRV top -> GUARD bottom (J6, J5 shell)

# ================================================================ control amp / cell relays (bottom left)
opamp('U1', 24.0, 119.0, 'R')
relay('K9', 18.0, YBUS - 1.0, 0)     # CE_INT -> RE_BNC (pin7 right, toward R19/J5)
relay('K10', 8.5, 112.0, 270)        # CE_INT top -> CE_BNC bottom
relay('K7', 14.3, 107.5, 0)          # CTRL_OUT <-> CTRL_INV
relay('K8', 14.3, 101.0, 0)          # PI_IN <-> CTRL_INV
put('R15', 17.0, 95.6, 0)            # PI_Z -> CTRL_OUT
put('C15', 30.5, 95.6, 0)            # CTRL_INV -> PI_Z
put('R16', 34.5, 108.0, 90)          # RE_BUF -> PI_IN
put('R17', 14.0, 115.0, 270)         # CTRL_OUT top -> CE_INT bottom

# ================================================================ inputs / summer (left edge)
put('R1', 17.0, 54.0, 0); put('JP1', 31.0, 53.0, 0)
put('R2', 17.0, 66.5, 0); put('R3', 17.0, 70.0, 0)
put('R4', 17.0, 79.0, 0); put('JP2', 31.0, 78.0, 0)
put('R5', 17.0, 82.5, 0); put('C12', 17.0, 89.0, 0)
put('R6', 25.0, 89.0, 0)
put('R7', 36.0, 85.0, 0); put('R8', 36.0, 81.5, 0)
put('JP3', 49.0, 81.5, 0)
opamp('U9', 44.0, 68.0, 'T')
put('R11', 36.0, 77.0, 0); put('C13', 52.0, 77.0, 0)
opamp('U10', 64.0, 68.0, 'T')
put('R12', 54.0, 81.5, 0); put('R13', 54.0, 85.0, 0); put('C14', 70.0, 77.0, 0)
put('R14', 54.0, 88.5, 0)
relay('K21', 30.0, 46.0, 0)
put('R9', 46.0, 54.5, 0); put('R10', 46.0, 51.0, 0)

# ================================================================ bias DAC + level shift (top, left of drivers)
put('U20', 56.0, 8.0, 0)
put('JP4', 48.0, 4.0, 90); put('R36', 46.0, 14.0, 0)
put('C24', 62.0, 4.0, 0); put('C25', 71.0, 6.0, 0); put('C26', 62.0, 14.0, 0)
put('R37', 46.0, 20.0, 0); put('R38', 46.0, 23.5, 0); put('C22', 60.0, 23.5, 0)
put('R39', 46.0, 27.0, 0); put('R40', 46.0, 30.5, 0); put('C23', 60.0, 30.5, 0)
opamp('U11', 64.0, 40.0, 'L')

# ================================================================ power (top left); L7805 tab faces into the board
put('J1', 4.0, 7.0, 0)
put('D1', 3.0, 16.0, 0); put('D2', 3.0, 20.0, 0)
put('C1', 18.0, 26.0, 0); put('C2', 26.0, 26.0, 0)
put('FB1', 3.0, 31.0, 0); put('FB2', 3.0, 34.5, 0)
put('C3', 18.0, 34.0, 0); put('C4', 26.0, 34.0, 0)
put('U25', 36.0, 4.0, 180)           # heatsink area kept clear below (y 6..20, x 24..40)
put('C5', 22.0, 4.0, 0); put('C6', 33.0, 26.0, 0); put('C7', 33.0, 34.0, 0)

# ================================================================ relay drivers, pulls, fallback header
put('U22', 127.0, 30.0, 270)         # inputs (1-9) top row, outputs (10-18) bottom row
put('U23', 101.5, 30.0, 270)
put('C60', 106.0, 42.0, 0); put('C61', 80.5, 42.0, 0)
for i in range(16):
    bank, k = divmod(i, 8)
    x0 = 105.0 if bank == 0 else 79.5
    put(f'R{60+i}', x0 + 3.2 * k, 21.0, 90)
put('J12', 84.0, 4.0, 90)

# ================================================================ Pico, ADC, clock, 3V3, sync
put('A1', 148.0, 27.0, 0)
put('FB5', 141.0, 54.0, 270); put('JP5', 146.0, 55.0, 0)   # PICO_GND pins inside the Pico ground island
put('D3', 161.5, 16.0, 90)
put('J13', 163.5, 24.0, 0)
put('R80', 170.5, 32.0, 90); put('R81', 173.7, 32.0, 90); put('R82', 176.9, 32.0, 90)
put('U26', 168.0, 6.0, 0); put('C8', 174.0, 10.0, 90); put('C9', 177.5, 10.0, 90)
put('FB3', 181.0, 14.0, 90); put('FB4', 184.5, 14.0, 90)
put('C10', 189.0, 5.0, 0); put('C11', 189.0, 12.5, 0)
put('R83', 203.0, 19.0, 0); put('R84', 203.0, 22.5, 0); put('D4', 204.0, 26.0, 0); put('D5', 204.0, 29.5, 0)
put('X1', 171.0, 46.0, 0); put('C59', 182.0, 27.0, 90)
put('U21', 194.0, 40.0, 0)
put('R35', 186.0, 51.0, 0)
put('C54', 200.0, 33.0, 0); put('C55', 186.0, 32.0, 90); put('C56', 189.0, 32.0, 90)
put('C57', 200.0, 44.0, 0); put('C58', 200.0, 47.5, 0)
for ch in range(4):
    y = 55.0 + 3.5 * ch
    put(f'R{50+2*ch}', 168.0, y, 0); put(f'R{51+2*ch}', 182.0, y, 0); put(f'C{50+ch}', 196.0, y, 0)

# ================================================================ mounting holes
put('H1', 4.0, 44.0); put('H2', 216.0, 40.0); put('H3', 4.0, 146.0); put('H4', 216.0, 60.0)

# keep-clear areas (drawn on User.Comments): name, x0, y0, x1, y1
KEEPCLEAR = [('L7805 heatsink', 24.0, 6.0, 42.0, 20.0), ('PTFE standoff option (U5 -IN / R46)', 106.0, 129.6, 112.0, 134.4)]


# ---------------------------------------------------------------- build
def build(netfile):
    comps, nets = read_netlist(netfile)
    missing = set(comps) - set(PL)
    extra = set(PL) - set(comps)
    assert not missing and not extra, (sorted(missing), sorted(extra))
    pin_net = {}
    for nm, nodes in nets.items():
        for ref, pin in nodes:
            pin_net[(ref, pin)] = nm

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
    ns = ds.m_NetSettings
    dflt = ns.GetDefaultNetclass()
    dflt.SetClearance(mm(0.25)); dflt.SetTrackWidth(mm(0.25)); dflt.SetViaDiameter(mm(0.6)); dflt.SetViaDrill(mm(0.3))

    def ncls(name, track, clear):
        nc = pcbnew.NETCLASS(name)
        nc.SetTrackWidth(mm(track)); nc.SetClearance(mm(clear)); nc.SetViaDiameter(mm(0.6)); nc.SetViaDrill(mm(0.3))
        ns.SetNetclass(name, nc)
    ncls('Power', 0.6, 0.25)
    ncls('HighZ', 0.25, 0.5)
    ncls('GND', 0.4, 0.25)
    ns.ClearNetclassPatternAssignments()
    for pat, cls in ([(n, 'Power') for n in ['+15V', '-15V', '+5V', '+15V_IN', '-15V_IN', 'P15_RAW', 'N15_RAW']] +
                     [(n, 'HighZ') for n in ['SUM_HI', 'SUM_LO', 'RE_IN', 'RE_BNC', 'NULLC_INJ', 'NULLG_INJ']] +
                     [(f'FB{i}', 'HighZ') for i in range(1, 7)] + [('GND', 'GND'), ('PICO_GND', 'GND')]):
        ns.SetNetclassPatternAssignment(N(pat), cls)

    netinfo = {}
    for nm in nets:
        ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni); netinfo[nm] = ni

    for ref, c in sorted(comps.items()):
        fp = load_fp(c['fp'])
        fp.SetReference(ref); fp.SetValue(c['value'])
        fp.SetPath(pcbnew.KIID_PATH(c['path']))
        fp.SetSheetname(c['props'].get('Sheetname', '')); fp.SetSheetfile(c['props'].get('Sheetfile', ''))
        fp.SetDNP(c['dnp'])
        fp.SetExcludedFromBOM(False)          # symbols carry no exclude-from-BOM flag (MountingHole fp default differs)
        x, y, r = PL[ref]
        fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(r)
        for pad in fp.Pads():
            nm = pin_net.get((ref, pad.GetNumber()))
            if nm:
                pad.SetNet(netinfo[nm])
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.9), mm(0.9))); fp.Reference().SetTextThickness(mm(0.13))
        fp.Value().SetVisible(False)
        b.Add(fp)
        # reference centred in the part outline, along its long axis (BNCs keep the library position)
        if not (c['fp'].startswith('Connector_Coaxial') or ref.startswith('H')):
            fp.BuildCourtyardCaches()
            bb = fp.GetCourtyard(pcbnew.F_Cu if False else pcbnew.F_CrtYd).BBox()
            fp.Reference().SetPosition(bb.Centre())
            fp.Reference().SetTextAngle(pcbnew.EDA_ANGLE(90 if bb.GetHeight() > 1.4 * bb.GetWidth() else 0,
                                                         pcbnew.DEGREES_T))
            if min(bb.GetWidth(), bb.GetHeight()) < mm(2.6):
                fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); fp.Reference().SetTextThickness(mm(0.12))

    # outline, 2 mm corner radius
    R = 2.0
    segs = [((R, 0), (W - R, 0)), ((W, R), (W, H - R)), ((W - R, H), (R, H)), ((0, H - R), (0, R))]
    for a, z in segs:
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(V(*a)); s.SetEnd(V(*z)); s.SetWidth(mm(0.1)); b.Add(s)
    for cx, cy, sx, sy in [(R, R, 0, R), (W - R, R, W - R, 0), (W - R, H - R, W, H - R), (R, H - R, R, H)]:
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetCenter(V(cx, cy)); s.SetStart(V(sx, sy)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
        s.SetWidth(mm(0.1)); b.Add(s)

    # BNC labels on silk
    for ref, lab in [('J4', 'CE'), ('J5', 'RE (shell=GUARD)'), ('J6', 'GUARD'), ('J7', 'WE'), ('J9', 'I_HI'),
                     ('J10', 'I_LO'), ('J8', 'V_OUT'), ('J2', 'BIAS/PULSE'), ('J3', 'AC PROBE'), ('J11', 'SYNC_IN')]:
        x, y, r = PL[ref]
        t = pcbnew.PCB_TEXT(b); t.SetText(lab); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(1.2), mm(1.2))); t.SetTextThickness(mm(0.18))
        if r == 180:
            t.SetPosition(V(x, y - 4.0))
        elif r == 90:
            t.SetPosition(V(x + 6.0, y - 6.0))
        else:
            t.SetPosition(V(x - 12, y + 4.0))
        b.Add(t)

    for name, x0, y0, x1, y1 in KEEPCLEAR:
        r_ = pcbnew.PCB_SHAPE(b); r_.SetShape(pcbnew.SHAPE_T_RECT); r_.SetLayer(pcbnew.Cmts_User)
        r_.SetStart(V(x0, y0)); r_.SetEnd(V(x1, y1)); r_.SetWidth(mm(0.15)); b.Add(r_)
        t = pcbnew.PCB_TEXT(b); t.SetText(name); t.SetLayer(pcbnew.Cmts_User); t.SetPosition(V((x0 + x1) / 2, (y0 + y1) / 2))
        t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0))); b.Add(t)
    pcbnew.SaveBoard(PCB, b)
    print('placed', len(comps), 'footprints,', len(nets), 'nets ->', PCB)


if __name__ == '__main__':
    build(sys.argv[1])
