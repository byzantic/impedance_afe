"""Rev B single source of truth: parts, nets, schematic placement, build variants.

Impedance / C-V / DLTS / electrochemistry analog front end, Rev B.
Changes from Rev A: bias + AC-probe summing inputs, on-board bias DAC, vector (C + G) nuller,
cal loads (T-switched), cell-disconnect, 1 k range, AC V monitor + V_OUT mode relay,
Pico 2 controller with 24-bit ADC, through-hole parts, DIP-8/SOIC-8 combo op-amp footprints.
"""

FP = dict(
    R='Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal',
    RHV='Resistor_THT:R_Axial_DIN0414_L11.9mm_D4.5mm_P20.32mm_Horizontal',
    C='Capacitor_THT:C_Disc_D3.0mm_W1.6mm_P2.50mm',
    CD='Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm',
    CF='Capacitor_THT:C_Rect_L7.2mm_W2.5mm_P5.00mm_FKS2_FKP2_MKS2_MKP2',
    CP='Capacitor_THT:CP_Radial_D6.3mm_P2.50mm',
    FB='Inductor_THT:L_Axial_L5.3mm_D2.2mm_P10.16mm_Horizontal_Vishay_IM-1',
    OPA='afe:DIP-8_SOIC-8_Combo',
    REED='Relay_THT:Relay_SPST_StandexMeder_SIL_Form1A',
    REEDB='Relay_THT:Relay_SPST_StandexMeder_SIL_Form1B',
    BNC='Connector_Coaxial:BNC_Amphenol_B6252HB-NPP3G-50_Horizontal',
    TB3='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal',
    H2x10='Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical',
    H2x6='Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical',
    J2='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',
    J3='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
    DO35='Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal',
    DO41='Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal',
    TO92='Package_TO_SOT_THT:TO-92_Inline',
    TO220='Package_TO_SOT_THT:TO-220-3_Vertical',
    DIP18='Package_DIP:DIP-18_W7.62mm_Socket',
    OSC='Oscillator:Oscillator_DIP-14',
    POT='Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical',
    MH='MountingHole:MountingHole_3.2mm_M3_Pad_Via',
)

parts = []
def P(ref, sym, value, fp, at, nets, mpn='', lcsc='', dnp=False, note='', dbg=None, prec=None):
    parts.append(dict(ref=ref, sym=sym, value=value, fp=FP.get(fp, fp), at=at, nets=nets, mpn=mpn, lcsc=lcsc,
                      dnp=dnp, note=note, dbg=dbg if dbg is not None else value,
                      prec=prec if prec is not None else (dbg if dbg is not None else value)))

class Grid:
    def __init__(s, x0, y0, cols, dx=17.78, dy=17.78):
        s.x0, s.y0, s.cols, s.dx, s.dy, s.i = x0, y0, cols, dx, dy, 0
    def __call__(s):
        c, r = s.i % s.cols, s.i // s.cols; s.i += 1
        return (s.x0 + c * s.dx, s.y0 + r * s.dy)

def R(ref, val, a, b, g, fp='R', **k): P(ref, 'Device:R', val, fp, g() if callable(g) else g, {'1': a, '2': b}, **k)
def C(ref, val, a, b, g, fp='C', **k): P(ref, 'Device:C', val, fp, g() if callable(g) else g, {'1': a, '2': b}, **k)
def CP(ref, val, pos, neg, g, **k): P(ref, 'Device:C_Polarized', val, 'CP', g() if callable(g) else g, {'1': pos, '2': neg}, **k)
def FBD(ref, a, b, g): P(ref, 'Device:FerriteBead', '600R@100MHz', 'FB', g() if callable(g) else g, {'1': a, '2': b})
def BNC(ref, sig, shell, at, label): P(ref, 'Connector:Conn_Coaxial', label, 'BNC', at, {'1': sig, '2': shell},
                                       mpn='BNC R/A PCB 50R (Amphenol B6252HB-NPP3G-50 pattern)')

OPA_FAST = dict(dbg='OPA134PA', prec='OPA828ID (SOIC) or OPA627AP (DIP)')
OPA_SLOW = dict(dbg='OPA134PA', prec='OPA134PA')
DECOUPLE = []
def OPAMP(ref, inp, inn, out, at, fast, note=''):
    P(ref, 'Amplifier_Operational:OPA1641', 'OPA828/OPA134', 'OPA', at,
      {'3': inp, '2': inn, '6': out, '7': '+15V', '4': '-15V'}, note=note, **(OPA_FAST if fast else OPA_SLOW))
    DECOUPLE.append(ref)

RELAY_GEN = dict(mpn='Standex/Meder SIL05-1A72-71 or generic SIP-1A05', lcsc='C7316298')
def RELAY(ref, a, b, drv, at, nc=False, prec=None):
    """pins 1,7 = contact ; 3 = coil+ (driver output) ; 5 = coil- (GND). nc=True -> form B (normally closed)."""
    if nc:
        P(ref, 'Relay:SILxx-1Bxx-71x', 'SIP-1B05 (NC)', 'REEDB', at, {'1': a, '7': b, '3': drv, '5': 'GND'},
          mpn='Standex/Meder SIL05-1B72-71', dbg='SIP-1B05', prec=prec)
    else:
        P(ref, 'Relay:SILxx-1Axx-71x', 'SIP-1A05', 'REED', at, {'1': a, '7': b, '3': drv, '5': 'GND'},
          dbg='SIP-1A05', prec=prec, **RELAY_GEN)

TEXT = []
def T(x, y, s): TEXT.append(((x, y), s))

# ================================================================ POWER  (x 20..230, y 25..120)
T(20, 22, 'POWER: external +/-15 V bench supply (Schottky reverse protection, ferrite filtering). L7805 -> +5 V (relays, DAC, Pico VSYS).|MCP1700 -> +3V3, split by ferrites into +3V3A (ADC analog) and +3V3D (ADC digital, oscillator, logic pull-ups).')
g = Grid(30, 40, 11, 17.78, 20.32)
P('J1', 'Connector:Screw_Terminal_01x03', '+15/GND/-15', 'TB3', g(), {'1': '+15V_IN', '2': 'GND', '3': '-15V_IN'})
P('D1', 'Diode:1N5819', '1N5819', 'DO41', g(), {'2': '+15V_IN', '1': 'P15_RAW'})
P('D2', 'Diode:1N5819', '1N5819', 'DO41', g(), {'2': 'N15_RAW', '1': '-15V_IN'})
CP('C1', '47u/35V', 'P15_RAW', 'GND', g); CP('C2', '47u/35V', 'GND', 'N15_RAW', g)
FBD('FB1', 'P15_RAW', '+15V', g); FBD('FB2', 'N15_RAW', '-15V', g)
CP('C3', '10u/35V', '+15V', 'GND', g); CP('C4', '10u/35V', 'GND', '-15V', g)
P('U25', 'Regulator_Linear:L7805', 'L7805CV', 'TO220', g(), {'1': 'P15_RAW', '2': 'GND', '3': '+5V'}, note='~1.5 W: add clip-on heatsink')
C('C5', '330n', 'P15_RAW', 'GND', g, fp='CD')
CP('C6', '10u/25V', '+5V', 'GND', g); C('C7', '100n', '+5V', 'GND', g, fp='CD')
P('U26', 'Regulator_Linear:MCP1700x-330xxTO', 'MCP1700-3302E/TO', 'TO92', g(), {'2': '+5V', '1': 'GND', '3': '+3V3'})
C('C8', '1u', '+5V', 'GND', g, fp='CD'); C('C9', '1u', '+3V3', 'GND', g, fp='CD')
FBD('FB3', '+3V3', '+3V3A', g); FBD('FB4', '+3V3', '+3V3D', g)
CP('C10', '10u/16V', '+3V3A', 'GND', g); CP('C11', '10u/16V', '+3V3D', 'GND', g)
P('D3', 'Diode:1N5819', '1N5819', 'DO41', g(), {'2': '+5V', '1': 'VSYS'}, note='Pico VSYS feed; USB may be plugged in at the same time')
FBD('FB5', 'PICO_GND', 'GND', g)
P('JP5', 'Connector_Generic:Conn_01x02', 'PICO_GND_TIE', 'J2', g(), {'1': 'PICO_GND', '2': 'GND'}, note='fit jumper to hard-tie Pico ground')
for i, n in enumerate(['+15V', '-15V', 'GND', 'P15_RAW', 'N15_RAW', '+3V3A', '+3V3D', 'VSYS', 'PICO_GND']):
    P(f'#FLG{i+1}', 'power:PWR_FLAG', 'PWR_FLAG', '', g(), {'1': n})
for i in range(4):
    P(f'H{i+1}', 'Mechanical:MountingHole_Pad', 'M3', 'MH', g(), {'1': 'GND'})

# ================================================================ INPUTS / SUMMER / DAC  (x 20..270, y 130..330)
T(20, 128, 'DRIVE INPUTS: BIAS/PULSE (DC) + AC PROBE (AC-coupled, JP3 = x1 or x0.1) + on-board bias DAC (via K21),|summed by U9 and re-inverted by U10:  VSET = V_bias + V_dac + k*V_ac.')
g = Grid(30, 145, 8, 25.4, 38.1)
BNC('J2', 'BIAS_BNC', 'GND', g(), 'BIAS/PULSE')
R('R1', '49.9', 'BIAS_BNC', 'BIAS_TERM', g); P('JP1', 'Connector_Generic:Conn_01x02', '50R_TERM', 'J2', g(), {'1': 'BIAS_TERM', '2': 'GND'})
R('R2', '100k', 'BIAS_BNC', 'GND', g); R('R3', '10k 0.1%', 'BIAS_BNC', 'SUMIN', g)
BNC('J3', 'AC_BNC', 'GND', g(), 'AC_PROBE')
R('R4', '49.9', 'AC_BNC', 'AC_TERM', g); P('JP2', 'Connector_Generic:Conn_01x02', '50R_TERM', 'J2', g(), {'1': 'AC_TERM', '2': 'GND'})
R('R5', '100k', 'AC_BNC', 'GND', g); C('C12', '1u film', 'AC_BNC', 'AC_C', g, fp='CF'); R('R6', '1M', 'AC_C', 'GND', g)
R('R7', '10k 0.1%', 'AC_C', 'AC_X1', g); R('R8', '100k 0.1%', 'AC_C', 'AC_X01', g)
P('JP3', 'Connector_Generic:Conn_01x03', 'AC_GAIN x1/x0.1', 'J3', g(), {'1': 'AC_X1', '2': 'SUMIN', '3': 'AC_X01'})
RELAY('K21', 'DAC_BIAS', 'DAC_SW', 'KD15', g())
R('R9', '10k 0.1%', 'DAC_SW', 'SUMIN', g); R('R10', '100k', 'DAC_SW', 'GND', g)
OPAMP('U9', 'GND', 'SUMIN', 'SUM_OUT', (90, 265), False, 'Input summer (inverting)')
R('R11', '10k 0.1%', 'SUMIN', 'SUM_OUT', (70, 292)); C('C13', '10p C0G', 'SUMIN', 'SUM_OUT', (85, 292))
OPAMP('U10', 'GND', 'INV_IN', 'VSET_RAW', (150, 265), False, 'Re-inverter')
R('R12', '10k 0.1%', 'SUM_OUT', 'INV_IN', (120, 292)); R('R13', '10k 0.1%', 'INV_IN', 'VSET_RAW', (135, 292))
C('C14', '10p C0G', 'INV_IN', 'VSET_RAW', (150, 292)); R('R14', '1k', 'VSET_RAW', 'VSET', (180, 265))

T(20, 312, 'BIAS DAC: DAC80501M (midscale at power-up) 0..5 V -> U11:  V_DAC_BIAS = 10.05 V - 4.02*V_DAC  (+10..-10 V, 0 V at midscale).|Connected to the summer only when K21 closes (firmware sets range first).')
g = Grid(30, 315, 7, 20.32, 20.32)
P('U20', 'afe:DAC80501_DGS', 'DAC80501MDGS', 'Package_SO:VSSOP-10_3x3mm_P0.5mm', (40, 345),
  {'1': '+5V', '4': 'GND', '5': 'DAC_SPI2C', '2': 'DAC_OUT', '10': 'DAC_REF', '6': 'SCK', '7': 'CS_DAC', '8': 'MOSI'},
  mpn='DAC80501MDGSR', lcsc='C1852032', note='SMD (JLC place)')
g = Grid(80, 330, 6, 25.4, 30.48)
P('JP4', 'Connector_Generic:Conn_01x03', 'SPI2C select', 'J3', g(), {'1': 'GND', '2': 'DAC_SPI2C', '3': '+5V'}, note='SPI2C level for SPI mode: confirm in datasheet')
R('R36', '10k', 'DAC_SPI2C', 'GND', g)
C('C24', '100n', '+5V', 'GND', g, fp='CD'); CP('C25', '10u/16V', '+5V', 'GND', g); C('C26', '150n', 'DAC_REF', 'GND', g, fp='CD')
R('R37', '10k 0.1%', 'DAC_OUT', 'LS_INV', g); R('R38', '40.2k 0.1%', 'LS_INV', 'DAC_BIAS', g); C('C22', '22p C0G', 'LS_INV', 'DAC_BIAS', g)
R('R39', '10k 0.1%', 'DAC_REF', 'LS_Y', g); R('R40', '40.2k 0.1%', 'LS_Y', 'GND', g); C('C23', '100n film', 'LS_Y', 'GND', g, fp='CF')
OPAMP('U11', 'LS_Y', 'LS_INV', 'DAC_BIAS', (250, 345), False, 'DAC level shift')

# ================================================================ CONTROL AMP / CELL / CAL  (x 290..540, y 130..330)
T(290, 128, 'CONTROL AMP U1: K7 DEV = follower (CE = VSET). K8 PSTAT (K7 off) = PI loop, V_RE = VSET. K9 RE_LOCAL ties RE sense to CE_INT.|K10 CELL connects CE_INT to the CE BNC (open = cell disconnected). Cal loads (K11/K13) are T-switched: off -> mid node grounded by K12/K14 (NC).')
OPAMP('U1', 'VSET', 'CTRL_INV', 'CTRL_OUT', (320, 160), True, 'Control amplifier')
g = Grid(355, 150, 7, 27.94, 38.1)
C('C15', '100p C0G', 'CTRL_INV', 'PI_Z', g); R('R15', '1k', 'PI_Z', 'CTRL_OUT', g); R('R16', '10k', 'RE_BUF', 'PI_IN', g)
RELAY('K7', 'CTRL_OUT', 'CTRL_INV', 'KD6', g()); RELAY('K8', 'PI_IN', 'CTRL_INV', 'KD7', g())
R('R17', '47', 'CTRL_OUT', 'CE_INT', g)
RELAY('K10', 'CE_INT', 'CE_BNC', 'KD9', g())
BNC('J4', 'CE_BNC', 'GND', g(), 'CE')
RELAY('K9', 'CE_INT', 'RE_BNC', 'KD8', g())
R('R18', '10k 0.1%', 'CE_INT', 'CALR_MID', g, note='cal reference R')
RELAY('K11', 'CALR_MID', 'SUM_HI', 'KD10', g()); RELAY('K12', 'CALR_MID', 'GND', 'KD10', g(), nc=True)
C('C16', '100p 1% C0G', 'CE_INT', 'CALC_MID', g, note='cal reference C')
RELAY('K13', 'CALC_MID', 'SUM_HI', 'KD11', g()); RELAY('K14', 'CALC_MID', 'GND', 'KD11', g(), nc=True)

# ================================================================ RE / GUARD / V MONITORS  (x 290..540, y 215..330)
T(290, 245, 'RE: U2 electrometer follower, U3 guard driver (RE BNC shell + GUARD BNC), U7 RE_MON buffer (keeps monitor and nuller load off U2).|V_OUT BNC: K19 (NC) = DC monitor V_RE/2 (U4); VMODE on -> K20 = AC monitor x10.1, AC-coupled ~100 Hz (U8).')
BNC('J5', 'RE_BNC', 'GUARD', (300, 265), 'RE')
R('R19', '100', 'RE_BNC', 'RE_IN', (318, 265))
OPAMP('U2', 'RE_IN', 'RE_BUF', 'RE_BUF', (345, 270), True, 'RE electrometer buffer')
OPAMP('U3', 'RE_BUF', 'GUARD_DRV', 'GUARD_DRV', (385, 270), True, 'Guard driver')
R('R20', '49.9', 'GUARD_DRV', 'GUARD', (410, 265)); BNC('J6', 'GUARD', 'GND', (430, 265), 'GUARD')
OPAMP('U7', 'RE_BUF', 'RE_MON', 'RE_MON', (465, 270), True, 'RE_MON buffer')
g = Grid(300, 305, 9, 27.94, 38.1)
R('R21', '10k 0.1%', 'RE_MON', 'VDIV', g); R('R22', '10k 0.1%', 'VDIV', 'GND', g)
OPAMP('U4', 'VDIV', 'VDC_DRV', 'VDC_DRV', g(), False, 'DC V monitor (/2)')
C('C17', '15n film', 'RE_MON', 'ACM_IN', g, fp='CF'); R('R23', '100k', 'ACM_IN', 'GND', g)
OPAMP('U8', 'ACM_IN', 'ACM_FB', 'VAC_DRV', g(), True, 'AC V monitor x10.1')
R('R24', '9.09k 0.1%', 'VAC_DRV', 'ACM_FB', g); R('R25', '1k 0.1%', 'ACM_FB', 'GND', g)
R('R26', '49.9', 'VDC_DRV', 'VDC_R', g); R('R27', '49.9', 'VAC_DRV', 'VAC_R', g)
RELAY('K19', 'VDC_R', 'VOUT_BNC', 'KD14', g(), nc=True); RELAY('K20', 'VAC_R', 'VOUT_BNC', 'KD14', g())
BNC('J8', 'VOUT_BNC', 'GND', g(), 'V_OUT')

# ================================================================ NULLER  (x 560..830, y 210..330)
T(560, 213, 'NULLER (vector): U12 makes -V_RE. RV1 (0..-1) -> U13 -> 100p (+910p via K17) injects -jwC.V  (C null).|RV2 (+1..-1) -> U14 -> 220n -> 20k (2k via K18) injects G null, AC-coupled (no DC into WE). K15/K16 (NULL_EN) connect to SUM_HI.')
g = Grid(570, 240, 7, 33.02, 38.1)
OPAMP('U12', 'GND', 'NINV_IN', 'NULL_NEG', g(), False, 'Null inverter')
R('R28', '10k 0.1%', 'RE_MON', 'NINV_IN', g); R('R29', '10k 0.1%', 'NINV_IN', 'NULL_NEG', g)
P('RV1', 'Device:R_Potentiometer', '10k 10-turn (C null)', 'POT', g(), {'1': 'GND', '3': 'NULL_NEG', '2': 'NC_WIP'},
  dbg='Bourns 3296W-1-103', prec='Bourns 3590S-2-103 panel + dial (off-board)')
OPAMP('U13', 'NC_WIP', 'NULLC_DRV', 'NULLC_DRV', g(), True, 'C-null buffer')
C('C18', '100p 1% C0G', 'NULLC_DRV', 'NULLC_INJ', g); C('C19', '910p 1% C0G', 'NULLC_DRV', 'NULLC_R', g)
RELAY('K17', 'NULLC_R', 'NULLC_INJ', 'KD13', g()); RELAY('K15', 'NULLC_INJ', 'SUM_HI', 'KD12', g())
P('RV2', 'Device:R_Potentiometer', '10k 10-turn (G null)', 'POT', g(), {'1': 'RE_MON', '3': 'NULL_NEG', '2': 'NG_WIP'},
  dbg='Bourns 3296W-1-103', prec='Bourns 3590S-2-103 panel + dial (off-board)')
OPAMP('U14', 'NG_WIP', 'NULLG_DRV', 'NULLG_DRV', g(), False, 'G-null buffer')
C('C20', '220n film', 'NULLG_DRV', 'NULLG_AC', g, fp='CF'); R('R30', '20k', 'NULLG_AC', 'NULLG_INJ', g)
R('R31', '2.2k', 'NULLG_AC', 'NULLG_R', g)
RELAY('K18', 'NULLG_R', 'NULLG_INJ', 'KD13', g()); RELAY('K16', 'NULLG_INJ', 'SUM_HI', 'KD12', g())

# ================================================================ TIAs  (x 560..830, y 25..200)
T(560, 22, 'HIGH-GAIN TIA U5: WE = SUM_HI virtual ground. Ranges K1..K6 = 1k, 10k, 100k, 1M, 10M, 100M (relays on the output side).|1 MHz C-V: use 1k and 10k only (100k and up roll off below 1 MHz). Q1/Q2 C-B junctions: low-leakage steering to the low-gain TIA U6.')
BNC('J7', 'SUM_HI', 'GND', (575, 45), 'WE')
OPAMP('U5', 'GND', 'SUM_HI', 'IHI_OUT', (610, 50), True, 'High-gain TIA')
R('R32', '49.9', 'IHI_OUT', 'IHI_BNC', (640, 45)); BNC('J9', 'IHI_BNC', 'GND', (660, 45), 'I_HI')
ranges = [  # Rf, Cf precision (OPA828), Cf debug (OPA134), fp, cap dnp
    ('1k 0.1%', '22p C0G', '47p C0G', 'R', False),
    ('10k 0.1%', '10p C0G', '15p C0G', 'R', False),
    ('100k 0.1%', '2.2p C0G', '4.7p C0G', 'R', False),
    ('1M 0.5%', '1p C0G', '1.5p C0G', 'RHV', False),
    ('10M 1%', '0.47p / gimmick', '0.47p / gimmick', 'RHV', True),
    ('100M 1%', 'stray only', 'stray only', 'RHV', True)]
for i, (rv, cp, cd, rfp, cdnp) in enumerate(ranges):
    n = i + 1; x = 580 + i * 40
    R(f'R{40+n}', rv, 'SUM_HI', f'FB{n}', (x, 85), fp=rfp,
      dbg=rv.split()[0] + ' 1% metal film', prec=rv + (' metal foil' if i < 3 else ' glass high-megohm'))
    C(f'C{40+n}', cp, 'SUM_HI', f'FB{n}', (x + 15, 85), dnp=cdnp, dbg=cd, prec=cp)
    RELAY(f'K{n}', f'FB{n}', 'IHI_OUT', f'KD{i}', (x + 7, 115),
          prec='Coto 9007-05-00 class (>=1e12 ohm; check footprint)' if n >= 5 else None)
P('Q1', 'Transistor_BJT:2N3904', '2N3904 (C-B diode)', 'TO92', (600, 150), {'2': 'SUM_HI', '1': 'SUM_HI', '3': 'SUM_LO'},
  note='collector-base junction as low-leakage diode, anode SUM_HI')
P('Q2', 'Transistor_BJT:2N3904', '2N3904 (C-B diode)', 'TO92', (625, 150), {'2': 'SUM_LO', '1': 'SUM_LO', '3': 'SUM_HI'},
  note='collector-base junction as low-leakage diode, anode SUM_LO')
OPAMP('U6', 'GND', 'SUM_LO', 'ILO_OUT', (680, 160), True, 'Low-gain TIA, 10 mA FS')
R('R33', '499 0.1%', 'SUM_LO', 'ILO_OUT', (660, 185)); C('C27', '68p C0G', 'SUM_LO', 'ILO_OUT', (675, 185))
R('R34', '49.9', 'ILO_OUT', 'ILO_BNC', (705, 155)); BNC('J10', 'ILO_BNC', 'GND', (725, 160), 'I_LO')

# ================================================================ ADC  (x 20..270, y 370..580)
T(20, 400, 'ADC: ADS131M04, 4 simultaneous channels, +/-1.2 V FS. Each input = 4.02k/1k divider (/5.02, +/-5 V -> +/-1.0 V) + 10 nF (~20 kHz).|CH0 = V DC monitor, CH1 = I_HI, CH2 = I_LO, CH3 = AC V monitor. 8.192 MHz clock from X1.')
P('U21', 'afe:ADS131M04_PW', 'ADS131M04IPWR', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', (60, 450),
  {'1': '+3V3A', '2': 'GND', '3': 'ADC0P', '4': 'GND', '6': 'ADC1P', '5': 'GND', '7': 'ADC2P', '8': 'GND', '10': 'ADC3P', '9': 'GND',
   '20': '+3V3D', '19': 'GND', '18': 'ADC_CAP', '17': 'ADC_CLK', '16': 'MOSI', '15': 'MISO', '14': 'SCK', '12': 'CS_ADC',
   '13': 'ADC_DRDY', '11': 'ADC_SYNC'}, mpn='ADS131M04IPWR', lcsc='C2862562', note='SMD (JLC place)')
g = Grid(110, 420, 7, 22.86, 30.48)
for ch, src in enumerate(['VDC_DRV', 'IHI_OUT', 'ILO_OUT', 'VAC_DRV']):
    R(f'R{50+2*ch}', '4.02k 0.1%', src, f'ADC{ch}P', g); R(f'R{51+2*ch}', '1k 0.1%', f'ADC{ch}P', 'GND', g)
    C(f'C{50+ch}', '10n C0G', f'ADC{ch}P', 'GND', g, fp='CD')
C('C54', '220n', 'ADC_CAP', 'GND', g, fp='CD')
C('C55', '100n', '+3V3A', 'GND', g, fp='CD'); C('C56', '1u', '+3V3A', 'GND', g, fp='CD')
C('C57', '100n', '+3V3D', 'GND', g, fp='CD'); C('C58', '1u', '+3V3D', 'GND', g, fp='CD')
P('X1', 'Oscillator:ACO-xxxMHz-A', '8.192MHz 3.3V CMOS', 'OSC', g(), {'1': '+3V3D', '7': 'GND', '8': 'XO_OUT', '14': '+3V3D'})
R('R35', '33', 'XO_OUT', 'ADC_CLK', g); C('C59', '100n', '+3V3D', 'GND', g, fp='CD')

# ================================================================ CONTROLLER / DRIVERS  (x 290..830, y 370..580)
T(290, 382, 'CONTROL: Pico 2 (socketed) drives CTL0..15 -> 2x TBD62783A high-side source drivers -> relay coils (off coils sit at 0 V).|J12 = CTL fallback header (Pico removed). 4.7k pulls set power-up state: ON = CTL3 (1M), CTL6 (DEV), CTL8 (RE_LOCAL).')
ctl_names = ['RNG_1k', 'RNG_10k', 'RNG_100k', 'RNG_1M', 'RNG_10M', 'RNG_100M', 'DEV', 'PSTAT', 'RE_LOCAL', 'CELL',
             'CAL_R', 'CAL_C', 'NULL_EN', 'NULL_RNG', 'VMODE_AC', 'DAC_EN']
pico = {'3': 'PICO_GND', '8': 'PICO_GND', '13': 'PICO_GND', '18': 'PICO_GND', '23': 'PICO_GND', '28': 'PICO_GND',
        '33': 'PICO_GND', '38': 'PICO_GND', '39': 'VSYS', '30': 'PICO_RUN',
        '21': 'MISO', '22': 'CS_ADC', '24': 'SCK', '25': 'MOSI', '26': 'CS_DAC', '27': 'ADC_DRDY', '29': 'ADC_SYNC',
        '31': 'SYNC_IN', '32': 'AUX27', '34': 'AUX28'}
gp_pin = {0: 1, 1: 2, 2: 4, 3: 5, 4: 6, 5: 7, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14, 11: 15, 12: 16, 13: 17, 14: 19, 15: 20}
for gp, pin in gp_pin.items(): pico[str(pin)] = f'CTL{gp}'
P('A1', 'afe:RPi_Pico_2', 'Raspberry Pi Pico 2', 'afe:RaspberryPi_Pico_2_THT', (330, 450), pico,
  mpn='SC1631 (Pico 2) on 2x 1x20 sockets')
P('U22', 'Transistor_Array:TBD62783A', 'TBD62783APG', 'DIP18', (430, 430),
  {**{str(i + 1): f'CTL{i}' for i in range(8)}, **{str(18 - i): f'KD{i}' for i in range(8)}, '9': '+5V', '10': 'GND'},
  note='internal output clamp diodes; VIN(on) 2.0 V min')
P('U23', 'Transistor_Array:TBD62783A', 'TBD62783APG', 'DIP18', (430, 495),
  {**{str(i + 1): f'CTL{i+8}' for i in range(8)}, **{str(18 - i): f'KD{i+8}' for i in range(8)}, '9': '+5V', '10': 'GND'})
C('C60', '100n', '+5V', 'GND', (455, 415), fp='CD'); C('C61', '100n', '+5V', 'GND', (455, 480), fp='CD')
g = Grid(480, 395, 8, 15.24, 20.32)
for n in range(16):
    if n in (3, 6, 8): R(f'R{60+n}', '4.7k', f'CTL{n}', '+3V3D', g, note='pull-up: ON at power-up')
    else: R(f'R{60+n}', '4.7k', f'CTL{n}', 'GND', g, note='pull-down: OFF at power-up (<=8.2k for RP2350 GPIO erratum)')
hdr = {str(n + 1): f'CTL{n}' for n in range(16)}; hdr.update({'17': 'GND', '18': 'GND', '19': 'GND', '20': 'GND'})
P('J12', 'Connector_Generic:Conn_02x10_Odd_Even', 'CTL0..15 fallback', 'H2x10', (500, 470), hdr)
P('J13', 'Connector_Generic:Conn_02x06_Odd_Even', 'SPI/AUX', 'H2x6', (540, 470),
  {'1': 'SCK', '2': 'MOSI', '3': 'MISO', '4': 'CS_ADC', '5': 'CS_DAC', '6': 'ADC_DRDY', '7': 'ADC_SYNC', '8': 'SYNC_IN',
   '9': 'AUX27', '10': 'AUX28', '11': 'PICO_RUN', '12': 'GND'})
g = Grid(580, 450, 6, 20.32, 20.32)
R('R80', '10k', 'CS_ADC', '+3V3D', g); R('R81', '10k', 'CS_DAC', '+3V3D', g); R('R82', '10k', 'ADC_SYNC', '+3V3D', g)
BNC('J11', 'SYNC_BNC', 'GND', g(), 'SYNC_IN')
R('R83', '100k', 'SYNC_BNC', 'GND', g); R('R84', '10k', 'SYNC_BNC', 'SYNC_IN', g)
P('D4', 'Diode:1N4148', '1N4148', 'DO35', g(), {'2': 'SYNC_IN', '1': '+3V3D'})
P('D5', 'Diode:1N4148', '1N4148', 'DO35', g(), {'2': 'GND', '1': 'SYNC_IN'})

# ---------------------------------------------------------------- op-amp decoupling (placed in a strip)
g = Grid(580, 520, 14, 17.78, 20.32)
for i, u in enumerate(DECOUPLE):
    C(f'C{100+2*i}', '100n', '+15V', 'GND', g, fp='CD', note=f'decouple {u}')
    C(f'C{101+2*i}', '100n', 'GND', '-15V', g, fp='CD', note=f'decouple {u}')
T(580, 512, 'Op-amp decoupling: one pair per op-amp, place at each op-amp supply pin.')

RELAY_MAP = {  # driver line -> relays (for docs)
    0: 'K1', 1: 'K2', 2: 'K3', 3: 'K4', 4: 'K5', 5: 'K6', 6: 'K7', 7: 'K8', 8: 'K9', 9: 'K10',
    10: 'K11+K12', 11: 'K13+K14', 12: 'K15+K16', 13: 'K17+K18', 14: 'K19+K20', 15: 'K21'}
