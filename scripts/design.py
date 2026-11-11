"""Single source of truth: parts, nets, schematic placement for the impedance AFE."""

FP = dict(
    R='Resistor_SMD:R_0805_2012Metric',
    RH='Resistor_SMD:R_1206_3216Metric',
    C='Capacitor_SMD:C_0805_2012Metric',
    CP='Capacitor_SMD:CP_Elec_6.3x7.7',
    SO8='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
    SO20W='Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm',
    DPAK='Package_TO_SOT_SMD:TO-252-2',
    BNC='Connector_Coaxial:BNC_Amphenol_B6252HB-NPP3G-50_Horizontal',
    TB3='TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal',
    HDR='Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical',
    SJ='Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
    FB='Inductor_SMD:L_0805_2012Metric',
    SMA='Diode_SMD:D_SMA',
    SOD123='Diode_SMD:D_SOD-123',
    SOT23='Package_TO_SOT_SMD:SOT-23',
    REED='Relay_THT:Relay_SPST_StandexMeder_SIL_Form1A',
    MH='MountingHole:MountingHole_3.2mm_M3_Pad_Via',
)

parts = []

def P(ref, sym, value, fp, at, nets, mpn='', lcsc='', dnp=False, note=''):
    parts.append(dict(ref=ref, sym=sym, value=value, fp=FP.get(fp, fp), at=at, nets=nets,
                      mpn=mpn, lcsc=lcsc, dnp=dnp, note=note))

def R(ref, val, a, b, at, fp='R', **k): P(ref, 'Device:R', val, fp, at, {'1': a, '2': b}, **k)
def C(ref, val, a, b, at, fp='C', **k): P(ref, 'Device:C', val, fp, at, {'1': a, '2': b}, **k)

OPA = dict(mpn='OPA828IDR', lcsc='C1850247')
def OPAMP(ref, inp, inn, out, at, note=''):
    P(ref, 'Amplifier_Operational:OPA1641', 'OPA828', 'SO8', at,
      {'3': inp, '2': inn, '6': out, '7': '+15V', '4': '-15V'}, note=note, **OPA)

REED = dict(mpn='SIP-1A05 (Standex/Meder SIL05-1A72-71 compatible)', lcsc='C7316298')
def RELAY(ref, a, b, drv, at):
    # pins 1,7 = contact ; 3,5 = coil (KiCad SILxx-1Axx-71x symbol)
    P(ref, 'Relay:SILxx-1Axx-71x', 'SIP-1A05', 'REED', at, {'1': a, '7': b, '3': drv, '5': 'GND'}, **REED)

def BNC(ref, sig, shell, at, label):
    P(ref, 'Connector:Conn_Coaxial', label, 'BNC', at, {'1': sig, '2': shell}, mpn='BNC R/A PCB 50R (Amphenol B6252HB-NPP3G-50 footprint)')

# ---------------------------------------------------------------- POWER (block origin 20,30)
P('J1', 'Connector:Screw_Terminal_01x03', '+15/GND/-15', 'TB3', (30, 50),
  {'1': '+15V_IN', '2': 'GND', '3': '-15V_IN'})
P('D1', 'Device:D_Schottky', 'SS14', 'SMA', (55, 40), {'2': '+15V_IN', '1': 'P15_RAW'}, mpn='SS14')
P('D2', 'Device:D_Schottky', 'SS14', 'SMA', (55, 65), {'2': 'N15_RAW', '1': '-15V_IN'}, mpn='SS14')
P('C1', 'Device:C_Polarized', '47u/35V', 'CP', (75, 50), {'1': 'P15_RAW', '2': 'GND'})
P('C2', 'Device:C_Polarized', '47u/35V', 'CP', (75, 75), {'1': 'GND', '2': 'N15_RAW'})
P('FB1', 'Device:FerriteBead_Small', '600R@100MHz', 'FB', (95, 45), {'1': 'P15_RAW', '2': '+15V'})
P('FB2', 'Device:FerriteBead_Small', '600R@100MHz', 'FB', (95, 70), {'1': 'N15_RAW', '2': '-15V'})
C('C3', '10u/35V X7R', '+15V', 'GND', (110, 50), fp='Capacitor_SMD:C_1206_3216Metric')
C('C4', '10u/35V X7R', 'GND', '-15V', (110, 75), fp='Capacitor_SMD:C_1206_3216Metric')
P('U8', 'Regulator_Linear:LM78M05_TO252', 'LM78M05', 'DPAK', (140, 50), {'1': 'P15_RAW', '2': 'GND', '3': '+5V'}, mpn='MC78M05CDTRKG')
C('C5', '330n', 'P15_RAW', 'GND', (125, 60))
C('C6', '10u', '+5V', 'GND', (155, 60))
P('#FLG1', 'power:PWR_FLAG', 'PWR_FLAG', '', (60, 95), {'1': '+15V'})
P('#FLG2', 'power:PWR_FLAG', 'PWR_FLAG', '', (75, 95), {'1': '-15V'})
P('#FLG3', 'power:PWR_FLAG', 'PWR_FLAG', '', (90, 95), {'1': 'GND'})
P('#FLG4', 'power:PWR_FLAG', 'PWR_FLAG', '', (105, 95), {'1': 'P15_RAW'})
P('#FLG5', 'power:PWR_FLAG', 'PWR_FLAG', '', (120, 95), {'1': 'N15_RAW'})
for i, x in enumerate((180, 195, 210, 225)):
    P(f'H{i+1}', 'Mechanical:MountingHole_Pad', 'M3', 'MH', (x, 50), {'1': 'GND'})

# ---------------------------------------------------------------- INPUT + CONTROL AMP (20,130)
BNC('J2', 'VIN_BNC', 'GND', (30, 150), 'VIN')
R('R1', '49.9', 'VIN_BNC', 'VIN_TERM', (50, 165))
P('JP1', 'Jumper:SolderJumper_2_Open', '50R_TERM', 'SJ', (50, 185), {'1': 'VIN_TERM', '2': 'GND'})
R('R2', '100k', 'VIN_BNC', 'GND', (65, 165))
R('R3', '1k', 'VIN_BNC', 'VSET', (80, 150))
OPAMP('U1', 'VSET', 'CTRL_INV', 'CTRL_OUT', (110, 160), note='Control amp: follower (device) or PI potentiostat')
C('C9', '100p C0G', 'CTRL_INV', 'PI_Z', (100, 190))
R('R6', '1k', 'PI_Z', 'CTRL_OUT', (120, 190))
R('R5', '10k', 'RE_BUF', 'PI_IN', (80, 210))
RELAY('K7', 'PI_IN', 'CTRL_INV', 'K7_DRV', (100, 225))   # PSTAT loop close
RELAY('K6', 'CTRL_OUT', 'CTRL_INV', 'K6_DRV', (130, 225))  # DEV follower
R('R4', '47', 'CTRL_OUT', 'CE', (140, 150))
BNC('J3', 'CE', 'GND', (160, 165), 'CE')
RELAY('K8', 'CE', 'RE_BNC', 'K8_DRV', (160, 210))  # RE local sense
C('C10', '100n', '+15V', 'GND', (95, 245)); C('C11', '100n', '-15V', 'GND', (110, 245))

# ---------------------------------------------------------------- RE BUFFER / GUARD / VOUT (190,130)
BNC('J4', 'RE_BNC', 'GUARD', (195, 150), 'RE')
R('R7', '100', 'RE_BNC', 'RE_IN', (215, 150))
OPAMP('U2', 'RE_IN', 'RE_BUF', 'RE_BUF', (240, 160), note='RE electrometer buffer')
C('C12', '100n', '+15V', 'GND', (225, 185)); C('C13', '100n', '-15V', 'GND', (240, 185))
OPAMP('U3', 'RE_BUF', 'GUARD_DRV', 'GUARD_DRV', (240, 210), note='Guard driver')
R('R9', '49.9', 'GUARD_DRV', 'GUARD', (265, 210))
BNC('J5', 'GUARD', 'GND', (285, 220), 'GUARD')
C('C14', '100n', '+15V', 'GND', (225, 235)); C('C15', '100n', '-15V', 'GND', (240, 235))
R('R10', '1k 0.1%', 'RE_BUF', 'VOUT_DIV', (275, 150))
R('R11', '1k 0.1%', 'VOUT_DIV', 'GND', (275, 170))
OPAMP('U4', 'VOUT_DIV', 'VOUT_DRV', 'VOUT_DRV', (300, 160), note='V monitor = V_RE/2')
R('R12', '49.9', 'VOUT_DRV', 'VOUT_BNC', (320, 150))
BNC('J6', 'VOUT_BNC', 'GND', (340, 165), 'V_OUT')
C('C16', '100n', '+15V', 'GND', (290, 185)); C('C17', '100n', '-15V', 'GND', (305, 185))

# ---------------------------------------------------------------- HIGH-GAIN TIA (370,30)
BNC('J7', 'SUM_HI', 'GND', (380, 60), 'WE')
OPAMP('U5', 'GND', 'SUM_HI', 'IHI_OUT', (420, 60), note='High-gain TIA')
R('R14', '49.9', 'IHI_OUT', 'IHI_BNC', (460, 50))
BNC('J8', 'IHI_BNC', 'GND', (480, 65), 'I_HI')
C('C18', '100n', '+15V', 'GND', (405, 85)); C('C19', '100n', '-15V', 'GND', (420, 85))
ranges = [('10k', '10p C0G', 'R', False), ('100k', '2.2p C0G', 'R', False), ('1M', '1p C0G', 'RH', False),
          ('10M', '0.47p C0G', 'RH', False), ('100M', '0.1p DNP', 'RH', True)]
for i, (rv, cv, rfp, cdnp) in enumerate(ranges):
    n = i + 1; x = 390 + i * 38
    R(f'R{20+n}', rv, 'SUM_HI', f'FB{n}', (x, 120), fp=rfp, note='feedback; high-value: thick-film 1% or better')
    C(f'C{20+n}', cv, 'SUM_HI', f'FB{n}', (x + 10, 120), dnp=cdnp)
    RELAY(f'K{n}', f'FB{n}', 'IHI_OUT', f'K{n}_DRV', (x + 5, 150))
P('D3', 'Diode:BAV99', 'BAV199', 'SOT23', (420, 190), {'1': 'SUM_HI', '2': 'SUM_HI', '3': 'SUM_LO'},
  mpn='BAV199 (low-leakage, pins1+2 tied -> antiparallel pair)')

# ---------------------------------------------------------------- LOW-GAIN TIA (370,200)
OPAMP('U6', 'GND', 'SUM_LO', 'ILO_OUT', (450, 215), note='Low-gain TIA (10 mA FS)')
R('R15', '499', 'SUM_LO', 'ILO_OUT', (440, 240))
C('C26', '68p C0G', 'SUM_LO', 'ILO_OUT', (455, 240))
R('R16', '49.9', 'ILO_OUT', 'ILO_BNC', (480, 205))
BNC('J9', 'ILO_BNC', 'GND', (500, 220), 'I_LO')
C('C27', '100n', '+15V', 'GND', (470, 260)); C('C28', '100n', '-15V', 'GND', (485, 260))
C('C29', '10u/25V', '+15V', 'GND', (500, 260), fp='Capacitor_SMD:C_1206_3216Metric')
C('C30', '10u/25V', 'GND', '-15V', (515, 260), fp='Capacitor_SMD:C_1206_3216Metric')

# ---------------------------------------------------------------- RELAY DRIVER (20,280)
hdr = {'1': 'CTL1', '2': 'CTL2', '3': 'CTL3', '4': 'CTL4', '5': 'CTL5', '6': 'CTL6', '7': 'CTL7', '8': 'CTL8',
       '9': 'GND', '10': 'GND'}
P('J10', 'Connector_Generic:Conn_02x05_Odd_Even', 'GPIO', 'HDR', (40, 320), hdr)
drv = {'2': 'CTL1', '3': 'CTL2', '4': 'CTL3', '5': 'CTL4', '6': 'CTL5', '7': 'CTL6', '8': 'CTL7', '9': 'CTL8',
       '18': 'K1_DRV', '17': 'K2_DRV', '16': 'K3_DRV', '15': 'K4_DRV', '14': 'K5_DRV', '13': 'K6_DRV',
       '12': 'K7_DRV', '11': 'K8_DRV', '1': 'GND', '19': 'GND', '20': '+5V', '10': 'GND'}
P('U7', '74xx:74HCT541', '74HCT541', 'SO20W', (150, 330), drv, mpn='SN74HCT541DWR')
C('C31', '100n', '+5V', 'GND', (180, 300))
default_on = {3, 6, 8}  # 1M range, DEV follower, RE local sense
for n in range(1, 9):
    x = 70 + (n - 1) * 10.16
    if n in default_on:
        R(f'R{40+n}', '100k', f'CTL{n}', '+5V', (x, 370), note='pull-up: default ON')
    else:
        R(f'R{40+n}', '100k', f'CTL{n}', 'GND', (x, 370), note='pull-down: default OFF')
for n in range(1, 9):
    P(f'D{10+n}', 'Device:D', '1N4148W', 'SOD123', (200 + (n - 1) * 15.24, 330), {'1': f'K{n}_DRV', '2': 'GND'}, mpn='1N4148W')

TEXT = [
    ((20, 22), 'POWER: external +/-15 V (bench). Reverse-protected, ferrite-filtered. +5 V for relays/logic.'),
    ((20, 122), 'DRIVE: VIN -> U1. K6 ON = follower (device mode, CE driven, RE senses).|K7 ON + K6 OFF = PI potentiostat (CE driven so V_RE = VIN). |K8 ON = RE tied to CE on board.'),
    ((190, 122), 'RE electrometer buffer (U2), guard driver (U3 -> GUARD BNC|and RE BNC shell), V_OUT = V_RE/2.'),
    ((370, 22), 'HIGH-GAIN TIA: WE -> SUM_HI virtual ground. Range relays on output side (K1..K5).|Off-relay leakage appears as gain error, not offset.'),
    ((370, 180), 'D3: antiparallel low-leakage steering diodes. Above ~ (Vsat/Rf) the hi-gain TIA saturates, SUM_HI rises ~0.6 V,|current diverts to low-gain TIA U6.'),
    ((20, 280), 'RELAY CONTROL: GPIO header -> 74HCT541 (high-side drive, 3.3 V logic OK). Off coils sit at 0 V to keep coil-contact leakage out of the summing node.|CTL1..5 = 10k/100k/1M/10M/100M range, CTL6 = DEV, CTL7 = PSTAT, CTL8 = RE_LOCAL.'),
]
