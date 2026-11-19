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


# ================================================================ FRONT edge (bottom): cell + scope outputs (rot 180)
# order: CE, RE, GUARD, WE, I_LO, I_HI, V_OUT.  I_LO/I_HI/V_OUT lanes lie right of the SUM_HI bus end (no crossings).
for ref, x in [('J4', 17.5), ('J5', 35.0), ('J6', 52.5), ('J7', 91.0), ('J10', 179.0), ('J9', 196.0), ('J8', 212.0)]:
    put(ref, x, YB, 180)
# BACK edge (top): generator inputs + sync (rot 0, jack up)
put('J3', 52.0, 12.7, 0)       # AC PROBE
put('J2', 70.0, 12.7, 0)       # BIAS/PULSE
put('J11', 171.0, 12.7, 0)     # SYNC_IN

# ================================================================ high-gain TIA (U5) + SUM_HI comb
# U5 rot 90: pin2 (-IN) bottom row, straight above the WE BNC pin.  SUM_HI bus at YBUS runs
# right (ranges, steering transistors) and left (null-injection and cal relays).
WEX = 91.0
UX, UY = WEX + 1.27, YBUS - 8.0
opamp('U5', UX, UY, None)
put('C124', UX + 3.73, 117.8, 90)      # +15V pin1 bottom, GND top (right of the output riser)
put('C125', UX - 4.07, 116.3, 0)       # GND, -15V (above U5, left of the output riser)
# range columns, left to right: (Rf, Cf, relay, x of Rf, long Rf?)  K5/K6 get extra room (Coto option)
# 100M nearest U5 -IN (leakage / PTFE-standoff option), 1k furthest.  Spacing: >=1.4 mm R-C, ~2.4 mm C-next R,
# and a ~4 mm clear standoff gap between U5 and R46.
cols = [('R46', 'C46', 'K6', WEX + 14.5, True), ('R45', 'C45', 'K5', WEX + 25.5, True), ('R44', 'C44', 'K4', WEX + 36.5, True),
        ('R43', 'C43', 'K3', WEX + 46.5, False), ('R42', 'C42', 'K2', WEX + 56.0, False), ('R41', 'C41', 'K1', WEX + 65.5, False)]
for r, c, k, x, long_ in cols:
    put(r, x, YBUS, 90)                                   # pin1 on bus, pin2 up
    put(c, x + (5.0 if long_ else 4.0), YBUS, 90)
    rp = 20.32 if long_ else 10.16
    relay(k, x, YBUS - rp - 4.0, 90)                      # pin1 = FBn, pin7 = IHI_OUT on top
QX = WEX + 74.5
put('Q1', QX, YBUS, 90)              # pins 1,2 SUM_HI (pin1 on bus), pin3 SUM_LO top
put('Q2', QX + 5.0, YBUS - 2.54, 270)  # pin3 SUM_HI on bus, pins 1,2 SUM_LO
# left branch: null injection relays nearest U5, cal relays further left (pin7 = SUM_HI on bus, pin1 up)
DX = UX - 105.27                     # left branch kept rigid relative to U5
relay('K16', 97.2 + DX, YBUS - 15.24, 270)
relay('K15', 90.8 + DX, YBUS - 15.24, 270)
relay('K13', 76.4 + DX, YBUS - 15.24, 270)
relay('K11', 70.0 + DX, YBUS - 15.24, 270)
put('R18', 70.0 + DX, YBUS - 15.24 - 14.2, 270)           # pin1 CE_INT top, pin2 CALR_MID bottom
put('C16', 73.2 + DX, YBUS - 15.24 - 6.1, 270)            # pin1 CE_INT top, pin2 CALC_MID bottom
relay('K12', 70.0 + DX, YBUS - 15.24 - 18.6, 90)          # NC to GND, pin1 CALR_MID bottom
relay('K14', 76.4 + DX, YBUS - 15.24 - 10.8, 90)          # NC to GND, pin1 CALC_MID bottom
put('C18', 90.8 + DX, YBUS - 15.24 - 6.1, 270)            # NULLC_DRV top -> NULLC_INJ bottom
relay('K17', 83.6 + DX, YBUS - 15.24 - 20.8, 270)         # pin1 NULLC_R top, pin7 NULLC_INJ bottom
put('R30', 97.2 + DX, YBUS - 15.24 - 14.4, 270)           # NULLG_AC top -> NULLG_INJ bottom
relay('K18', 102.6 + DX, YBUS - 15.24 - 20.8, 270)        # pin1 NULLG_R top, pin7 NULLG_INJ bottom
put('C19', 83.6 + DX, 89.4, 270)                          # NULLC_DRV top -> NULLC_R bottom (K17 pin1)
put('R31', 107.0 + DX, 66.0, 90)                          # NULLG_AC -> NULLG_R
put('C20', 101.0 + DX, 69.0, 90)                          # NULLG_DRV -> NULLG_AC (film)
opamp('U13', 90.0 + DX, 80.0, 'T')
opamp('U14', 112.0 + DX, 80.0, 'T')
opamp('U12', 92.0 + DX, 52.0, 'L')
put('R28', 99.0 + DX, 46.0, 0); put('R29', 99.0 + DX, 49.5, 0)
put('J14', 104.0, 55.5, 0)           # RV1 (panel C-null pot) cable, Molex KK 254
put('J15', 104.0, 63.0, 0)           # RV2 (panel G-null pot) cable

# ---------------- low-gain TIA above Q1/Q2 (SUM_LO short and vertical; the I_LO / I_HI lanes stay clear)
U6X, U6Y = QX + 2.5, 112.0
put('U6', U6X, U6Y, 90)
put('C126', U6X - 7.0, U6Y - 1.3, 90); put('C127', U6X - 7.0, U6Y + 1.3, 270)   # left: keeps the ILO_OUT corridor free
put('R33', QX - 3.5, 121.5, 0)            # SUM_LO left -> ILO_OUT right (below U6)
put('C27', QX, 124.6, 0)
put('R34', 179.0, U6Y, 270)               # ILO_OUT top -> ILO_BNC bottom, lane straight down to J10
put('R32', 196.0, 101.0, 270)             # IHI_OUT (bus end) top -> IHI_BNC bottom, lane down to J9

# ================================================================ V monitors -> V_OUT (right, above the I_HI lane end)
opamp('U4', 180.0, 87.0, 'B')             # DC monitor (VDIV -> VDC_DRV)
opamp('U8', 200.0, 87.0, 'B')             # AC monitor (ACM_IN -> VAC_DRV)
put('R21', 159.0, 78.0, 0); put('R22', 159.0, 81.5, 0); put('R26', 159.0, 85.0, 0)
put('C17', 160.0, 89.0, 0); put('R23', 159.0, 92.5, 0)
put('R24', 187.5, 78.0, 0)
put('R25', 206.5, 79.0, 0); put('R27', 206.5, 82.5, 0)
relay('K19', 206.0, 100.0, 270)      # NC: VDC_R -> VOUT (pin7 bottom, toward J8)
relay('K20', 212.4, 100.0, 270)      # VAC_R -> VOUT

# ================================================================ RE electrometer / guard / RE_MON
U2X, U2Y = 35.0 - 1.27, YBUS - 15.5
opamp('U2', U2X, U2Y, 'R')
put('R19', 35.0, YBUS + 1.4, 90)     # pin1 RE_BNC (bottom, by J5), pin2 RE_IN up to U2 pin3
opamp('U3', 44.0, 102.0, 'L')
opamp('U7', 44.0, 86.0, 'L')
put('R20', 47.0, YBUS - 9.0, 270)    # GUARD_DRV top -> GUARD bottom (J6, J5 shell)

# ================================================================ control amp / cell relays (bottom left)
opamp('U1', 18.0, 82.0, 'R')
relay('K10', 8.5, 112.0, 270)        # CE_INT top -> CE_BNC bottom (J4)
relay('K9', 24.0, 108.0, 270)        # CE_INT top -> RE_BNC bottom (to R19/J5)
relay('K7', 4.5, 92.0, 0)            # CTRL_OUT <-> CTRL_INV
relay('K8', 4.5, 98.5, 0)            # PI_IN <-> CTRL_INV
put('R15', 4.5, 70.0, 0)             # PI_Z -> CTRL_OUT
put('C15', 17.0, 70.0, 0)            # CTRL_INV -> PI_Z
put('R16', 25.0, 104.0, 90)          # RE_BUF -> PI_IN
put('R17', 15.0, 103.0, 270)         # CTRL_OUT top -> CE_INT bottom

# ================================================================ drive inputs + summer (under the back-edge BNCs)
put('R5', 44.0, 18.0, 270); put('R4', 48.0, 18.0, 270); put('JP2', 46.0, 31.5, 0)    # AC 100k, 50R term -> JP2
put('C12', 52.5, 18.0, 270); put('R6', 57.0, 18.0, 270)                             # AC coupling 1u film, 1M bleed
put('R7', 60.5, 18.0, 270); put('R8', 64.0, 18.0, 270); put('JP3', 58.0, 33.0, 0)  # x1 / x0.1 select
put('R2', 67.5, 18.0, 270); put('R1', 71.0, 18.0, 270); put('R3', 74.5, 18.0, 270)  # BIAS 100k, 50R, 10k -> SUMIN
put('JP1', 70.5, 31.5, 0)
put('U9', 46.0, 50.0, 90); put('C100', 39.0, 48.7, 90); put('C101', 39.0, 51.3, 270)
put('R11', 40.0, 60.0, 0); put('C13', 53.0, 60.0, 0)
opamp('U10', 64.0, 50.0, 'T')
put('R12', 58.0, 60.0, 0); put('C14', 72.0, 64.0, 0); put('R13', 58.0, 63.5, 0); put('R14', 58.0, 67.0, 0)
relay('K21', 30.0, 66.0, 0)                                  # DAC_BIAS -> DAC_SW
put('R9', 48.0, 71.0, 0); put('R10', 48.0, 74.5, 0)

# ================================================================ bias-DAC level shift (DAC_OUT / DAC_REF arrive on J17)
opamp('U11', 122.0, 50.0, 'T')        # clear of the CTL fan-in channel beside the Pico
put('R37', 119.0, 60.0, 0); put('R38', 119.0, 63.5, 0); put('C22', 132.5, 63.5, 0)
put('R39', 119.0, 67.0, 0); put('R40', 119.0, 70.5, 0); put('C23', 132.5, 70.5, 0)

# ================================================================ power (top left); L7805 tab faces into the board
put('J1', 4.0, 7.0, 0)
put('D1', 3.0, 16.0, 0); put('D2', 3.0, 20.0, 0)
put('C1', 18.0, 26.0, 0); put('C2', 26.0, 26.0, 0)
put('FB1', 3.0, 31.0, 0); put('FB2', 3.0, 34.5, 0)
put('C3', 18.0, 34.0, 0); put('C4', 26.0, 34.0, 0)
put('U25', 36.0, 4.0, 180)           # heatsink area kept clear below (y 6..20, x 24..40)
put('C5', 22.0, 4.0, 0); put('C6', 33.0, 26.0, 0); put('C7', 33.0, 34.0, 0)

# ================================================================ relay drivers, pulls, fallback header
put('U22', 128.0, 30.0, 270)         # inputs (1-9) top row, outputs (10-18) bottom row
put('U23', 102.5, 30.0, 270)
put('C60', 107.0, 42.0, 0); put('C61', 81.5, 42.0, 0)
# pulls: one slot above each driver input, same left-to-right order (R(60+m) belongs to channel m).
# Channel order by input x: 15..8 (U23), 7..0 (U22)  ->  slot index 15-m.
SLOTX = [80.5 + 3.2 * j for j in range(8)] + [106.0 + 3.2 * j for j in range(8)]
for m in range(16):
    put(f'R{60+m}', SLOTX[15 - m], 21.0, 90)
put('J12', 85.0, 4.0, 90)          # pin p = GP(p-1): same left-to-right order as the pull slots

# ================================================================ Pico, 3V3, sync, HAT
put('A1', 148.0, 27.0, 0)
put('FB5', 141.0, 54.0, 270); put('JP5', 146.0, 55.0, 0)   # PICO_GND pins inside the Pico ground island
put('D3', 160.9, 16.0, 90)
put('J13', 182.0, 3.0, 0)                 # external SPI master port, back edge, clear of the Pico and the HAT
put('R83', 163.5, 19.5, 0); put('R84', 163.5, 23.0, 0); put('D4', 164.5, 26.5, 0); put('D5', 164.5, 30.0, 0)
put('U26', 177.0, 22.0, 0); put('C8', 176.5, 26.5, 0); put('C9', 176.5, 30.0, 0)
put('FB4', 176.0, 34.0, 0); put('C11', 179.0, 40.0, 0)
put('R47', 161.0, 46.0, 90)               # GP21 clock series R (pad 2 near A1 pin 27)
for ch in range(4):                       # ADC dividers, rows just below J17 (HAT analog link)
    y = 50.5 + 3.5 * ch                   # source -R(4.02k)- node -C- , -R(1k)- GND (R51.. pin2 under the HAT edge)
    put(f'R{50+2*ch}', 160.0, y, 0); put(f'C{50+ch}', 172.4, y, 0); put(f'R{51+2*ch}', 179.6, y, 0)
# HAT (Pi Zero pHAT, 65 x 30) rotated 90 CW: header along the right edge, analog link J17 facing the dividers.
HAT = (188.0, 8.0)                        # main-board position of the HAT's top-left corner after rotation (x, y)


def hat_xy(X, Y):
    """HAT top-view coords (X along the header edge, Y away from it) -> main board"""
    return HAT[0] + 30.0 - Y, HAT[1] + X


put('J16', *hat_xy(8.37, 4.77), 0)       # PinHeader 2x20 (male): pin1 odd row, even pins outboard
put('J17', *hat_xy(38.85, 25.23), 180)   # PinHeader 2x6 (male): pin1 at the DAC end
for i, (X, Y) in enumerate([(3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)]):
    put(f'H{10+i}', *hat_xy(X, Y))

# ================================================================ mounting holes: H1 = GND star bond; others isolated
put('H1', 4.0, 44.0)
for ref, x, y in [('H2', 4.0, 146.0), ('H3', 71.5, 146.0), ('H4', 135.0, 146.0), ('H5', 216.0, 129.0),
                  ('H6', 216.0, 4.0), ('H7', 4.0, 60.0), ('H8', 146.0, 72.0), ('H9', 125.0, 80.0)]:
    put(ref, x, y)

# keep-clear areas (drawn on User.Comments): name, x0, y0, x1, y1
KEEPCLEAR = [('L7805 heatsink', 24.0, 6.0, 42.0, 20.0),
             ('PTFE standoff option (U5 -IN / R46)', UX + 5.5, YBUS - 3.0, WEX + 11.5, YBUS + 3.0),
             ('ADC/DAC HAT 65x30 (11 mm standoffs): nothing tall', HAT[0], HAT[1], HAT[0] + 30.0, HAT[1] + 65.0)]


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
