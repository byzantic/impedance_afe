"""Rev B: create impedance_afe.kicad_pcb from the schematic netlist and place every part.

Run from anywhere with /usr/bin/python3 (needs KiCad 9 SWIG pcbnew):
    kicad-cli sch export netlist -o /tmp/afe.net impedance_afe.kicad_sch
    /usr/bin/python3 scripts/layout/place.py /tmp/afe.net
Overwrites impedance_afe.kicad_pcb.  Board coords: mm, origin top-left, y down.
Digital/power along the top (back) edge, analog BNC row along the bottom (front) edge.
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


def opamp(ref, x, y, side='E'):
    """Combo footprint rotated 90: inputs (1-4) on the bottom row, outputs (8-5) on top.
    Decoupling pair, 5 mm discs: 'E' (default) book-ends the socket, C+ (+15V top, GND bottom) at the left end by
    pin 7, C- (GND top, -15V bottom) at the right end by pin 4.  'R'/'L'/'T'/'B' stack both on one side."""
    put(ref, x, y, 90)
    cp, cn = DEC[ref]
    if side == 'E':
        put(cp, x - 7.0, y - 2.5, 270); put(cn, x + 7.0, y - 2.5, 270)
    elif side == 'R':
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
# Pitch: 26.5 mm either side of RE (insulated, GUARD-shell socket), 24 mm on the output group.  GUARD (J6) stays left of
# K11 (the left end of the SUM_HI bus) so the R20 -> J6 guard run never crosses the bus.
RE_X = 40.5
for ref, x in [('J4', 14.0), ('J5', RE_X), ('J6', 67.0), ('J7', 104.0), ('J10', 192.0), ('J9', 216.0), ('J8', 240.0)]:
    put(ref, x, YB, 180)
# BACK edge (top): generator inputs + sync (rot 0, jack up)
put('J3', 46.0, 12.7, 0)       # AC PROBE   (24 mm pitch to BIAS: room for plugs)
put('J2', 70.0, 12.7, 0)       # BIAS/PULSE
put('J11', 190.0, 12.7, 0)     # SYNC_IN, ~23 mm clear of the controller's RJ45

# ================================================================ high-gain TIA (U5) + SUM_HI comb
# U5 rot 90: pin2 (-IN) bottom row, straight above the WE BNC pin.  SUM_HI bus at YBUS runs
# right (ranges, steering transistors) and left (null-injection and cal relays).
WEX = 104.0
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
put('R31', 95.0 + DX, 91.3, 0)                            # NULLG_AC -> NULLG_R (K18 pin1)
put('C20', 97.5 + DX, 87.8, 0)                            # NULLG_DRV -> NULLG_AC (film)
opamp('U13', 90.0 + DX, 80.0)
opamp('U14', 112.0 + DX, 80.0)
# U12 (null inverter) sits between the two null buffers, below the channel the relay-coil lines use under the drivers
opamp('U12', 100.0 + DX, 63.0)
put('R28', 88.5 + DX, 70.5, 0); put('R29', 101.0 + DX, 70.5, 0)
# pot cables (Molex KK 254; a Bourns 3296W also fits pads 1-3) either side of U12, open space round them
put('J14', 80.0 + DX, 64.0, 0)       # RV1 (C null): NULL_NEG, NC_WIP -> U13
put('J15', 111.0 + DX, 64.0, 0)      # RV2 (G null): NULL_NEG, NG_WIP -> U14

# ---------------- low-gain TIA above Q1/Q2 (SUM_LO short and vertical; the I_LO / I_HI lanes stay clear)
U6X, U6Y = QX + 2.5, 112.0
put('U6', U6X, U6Y, 90)
put('C126', U6X - 7.0, U6Y - 1.3, 90); put('C127', U6X - 7.0, U6Y + 1.3, 270)   # left: keeps the ILO_OUT corridor free
put('R33', QX - 3.5, 121.5, 0)            # SUM_LO left -> ILO_OUT right (below U6)
put('C27', QX, 124.6, 0)
put('R34', U6X + 11.0, U6Y, 270)          # ILO_OUT top -> ILO_BNC bottom, lane straight down to J10
put('R32', 216.0, 101.0, 270)             # IHI_OUT (bus end) top -> IHI_BNC bottom, lane down to J9

# ================================================================ V monitors -> V_OUT (right, above the I_HI lane end)
VM = 20.0                                 # monitor cluster x offset (Rev B first pass had it 20 mm further left)
opamp('U4', 180.0 + VM, 89.0)        # DC monitor (VDIV -> VDC_DRV)
opamp('U8', 200.0 + VM, 89.0)        # AC monitor (ACM_IN -> VAC_DRV)
put('R21', 159.0 + VM, 78.0, 0); put('R22', 159.0 + VM, 81.5, 0); put('R26', 159.0 + VM, 85.0, 0)
put('C17', 160.0 + VM, 89.0, 0); put('R23', 159.0 + VM, 92.5, 0)
put('R24', 185.0 + VM, 80.0, 0)
put('R25', 210.0 + VM, 86.0, 0); put('R27', 210.0 + VM, 89.5, 0)
relay('K19', 234.0, 100.0, 270)      # NC: VDC_R -> VOUT (pin7 bottom, toward J8)
relay('K20', 240.4, 100.0, 270)      # VAC_R -> VOUT

# ================================================================ RE electrometer / guard / RE_MON
U2X, U2Y = RE_X - 1.27, YBUS - 15.5
opamp('U2', U2X, U2Y, 'R')
put('R19', RE_X, YBUS + 1.4, 90)     # pin1 RE_BNC (bottom, by J5), pin2 RE_IN up to U2 pin3
opamp('U3', RE_X + 9.0, 102.0)
opamp('U7', RE_X + 9.0, 86.0)
put('R20', RE_X + 12.0, YBUS - 9.0, 270)    # GUARD_DRV top -> GUARD bottom (J6, J5 shell)

# ================================================================ control amp / cell relays (bottom left)
opamp('U1', 18.0, 82.0)
relay('K10', 8.5, 112.0, 270)        # CE_INT top -> CE_BNC bottom (J4)
relay('K9', RE_X - 11.0, 108.0, 270)  # CE_INT top -> RE_BNC bottom (to R19/J5)
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
opamp('U9', 46.0, 50.0)
put('R11', 40.0, 60.0, 0); put('C13', 53.0, 60.0, 0)
opamp('U10', 64.0, 50.0)
put('R12', 58.0, 60.0, 0); put('C14', 72.0, 64.0, 0); put('R13', 58.0, 63.5, 0); put('R14', 58.0, 67.0, 0)
relay('K21', 30.0, 66.0, 0)                                  # DAC_BIAS -> DAC_SW
put('R9', 48.0, 71.0, 0); put('R10', 48.0, 74.5, 0)

# ================================================================ bias-DAC level shift (DAC_OUT / DAC_REF arrive on J17)
opamp('U11', 171.0, 50.0)             # right of the controller module, near J17 (DAC_OUT / DAC_REF)
put('R37', 162.0, 60.0, 0); put('R38', 162.0, 63.5, 0); put('C22', 175.5, 63.5, 0)
put('R39', 162.0, 67.0, 0); put('R40', 162.0, 70.5, 0); put('C23', 175.5, 70.5, 0)

# ================================================================ power (top left); L7805 tab faces into the board
put('J1', 4.0, 7.0, 0)
put('D1', 3.0, 16.0, 0); put('D2', 3.0, 20.0, 0)
put('C1', 18.0, 26.0, 0); put('C2', 26.0, 26.0, 0)
put('FB1', 3.0, 31.0, 0); put('FB2', 3.0, 34.5, 0)
put('C3', 18.0, 34.0, 0); put('C4', 26.0, 34.0, 0)
put('U25', 30.0, 4.0, 180)           # heatsink area kept clear below (y 6..20, x 21..34)
put('C5', 35.2, 1.8, 270);                 # input cap upright beside pin 1 (P15_RAW)
put('C6', 33.0, 26.0, 0); put('C7', 33.0, 34.0, 0)

# ================================================================ shift registers, pulls, relay drivers (back edge)
# Column order, back edge down: 74HC595 (outputs on its lower row) -> 4.7k pull (CTL pad lower, rail pad upper) ->
# TBD62783 input (upper row).  Slot j carries CTLj, left to right; 595 pins 1-7 (QB..QH) sit over slots 1-7 of their
# group and QA (pin 15, upper row) wraps round the left end of the package to slot 0.
SB = 3.0                             # bank offset from the back edge: room for two tracks above the 595 upper row
put('U22', 128.0, 33.0 + SB, 270)    # inputs (1-9) top row, outputs (10-18) bottom row
put('U23', 102.5, 33.0 + SB, 270)
put('C61', 78.8, 41.3 + SB, 270)     # U23 left end (pins 9 +5V / 10 GND)
put('C60', 131.5, 41.3 + SB, 270)    # U22 right end (no room between the drivers)
SLOTX = [80.5 + 3.2 * j for j in range(8)] + [106.0 + 3.2 * j for j in range(8)]
for m in range(16):                  # R(60+m) belongs to channel m, whose input is CTL(15-m) -> slot 15-m
    put(f'R{60+m}', SLOTX[15 - m], 24.0 + SB, 90)
put('U27', SLOTX[1] + 1.98, 9.62 + SB, 90)    # CTL0..7; pin 1 (QB) over slot 1
put('U28', SLOTX[9] + 1.98, 9.62 + SB, 90)    # CTL8..15
put('C62', 107.3, 9.6 + SB, 90); put('C63', 132.0, 9.6 + SB, 90)
put('R76', 134.8, 13.0 + SB, 90)     # RLY_OE pull-up

# ================================================================ Pico, 3V3, sync, HAT
# Controller: Pico 2 or ESP32-S3-ETH.  The ESP32's RJ45/USB-C end is 19.87 mm beyond pins 1/40, so the footprint sits
# 18.5 mm further in than a bare Pico would; a Pico 2's USB is then recessed ~18 mm from the back edge.
A1Y = 27.0 + 18.5
put('A1', 148.0, A1Y, 0)
ESP_END = A1Y + 28.8                       # ESP32-S3-ETH far end (microSD inserted from here)
# ground link: FB5 / JP5 straddle the bottom-left corner of the controller ground island (pin1 PICO_GND inside)
ISLAND_Y = ESP_END + 1.2
put('FB5', 134.2, ISLAND_Y - 9.5, 270)
put('JP5', 131.0, ISLAND_Y - 2.0, 270)
put('D3', 160.9, 16.0, 90)
put('J13', W - 1.5 - 23.43, 14.3, 90)     # 2x8 right-angle box header, back-right corner, opening at the back edge
put('R83', 183.5, 19.5, 0); put('R84', 183.5, 23.0, 0); put('D4', 184.5, 26.5, 0); put('D5', 184.5, 30.0, 0)  # under J11
put('U26', 165.5, 22.0, 0); put('C8', 164.5, 26.5, 0); put('C9', 164.5, 30.0, 0)     # +3V3D regulator by the controller
put('FB4', 164.0, 34.0, 0); put('C11', 171.0, 39.5, 0)
put('R47', 160.8, 57.0, 90)               # GP21 clock series R (pad 2 near A1 pin 27)
HAT = (W - 31.5, 17.0)                    # main-board position of the HAT's top-left corner after rotation (x, y)
J2X0 = 32.5 - 5.5 * 2.54                  # HAT J2 (1x12) pin 1, HAT coords (X along the long edge); row at Y = 27.5
for ch in range(4):                       # ADC dividers, one row per channel, level with J17 pin 2ch+1 (ADCchP)
    y = HAT[1] + J2X0 + 5.08 * ch         # source -R(4.02k)- node -C- , -R(1k)- GND
    put(f'R{50+2*ch}', HAT[0] - 35.5, y, 0); put(f'C{50+ch}', HAT[0] - 22.5, y, 0); put(f'R{51+2*ch}', HAT[0] - 15.0, y, 0)
# HAT (Pi Zero pHAT, 65 x 30) rotated 90 CW: header along the right edge, analog link J17 facing the dividers.


def hat_xy(X, Y):
    """HAT top-view coords (X along the header edge, Y away from it) -> main board"""
    return HAT[0] + 30.0 - Y, HAT[1] + X


put('J16', *hat_xy(8.37, 4.77), 0)       # PinHeader 2x20 (male): pin1 odd row, even pins outboard
put('J17', *hat_xy(J2X0, 27.5), 0)       # PinHeader 1x12 (male), one column; pin 1 = ADC0P (top)
for i, (X, Y) in enumerate([(3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)]):
    put(f'H{10+i}', *hat_xy(X, Y))

# ================================================================ mounting holes: H1 = GND star bond; others isolated
put('H1', 4.0, 44.0)
for ref, x, y in [('H2', 27.25, 146.0), ('H3', 85.5, 146.0), ('H4', 148.0, 146.0), ('H5', 244.0, 128.0),
                  ('H6', 211.0, 5.0), ('H7', 53.75, 146.0), ('H8', 166.0, 80.0), ('H9', 125.0, 80.0)]:
    put(ref, x, y)

# keep-clear areas (drawn on User.Comments): name, x0, y0, x1, y1
KEEPCLEAR = [('L7805 heatsink', 21.0, 6.0, 34.0, 20.0),
             ('PTFE standoff option (U5 -IN / R46)', UX + 5.5, YBUS - 3.0, WEX + 11.5, YBUS + 3.0),
             ('ADC/DAC HAT 65x30 (11 mm standoffs): nothing tall', HAT[0], HAT[1], HAT[0] + 30.0, HAT[1] + 65.0),
             ('microSD access (ESP32-S3-ETH): nothing tall', 137.25, ESP_END, 158.75, ESP_END + 15.0)]


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
