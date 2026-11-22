"""ADC/DAC HAT (adc_hat/): net record of intent, read by check.py and the BOM.

Raspberry Pi Zero pHAT outline (65 x 30 mm). Plugs onto J16/J17 of the AFE main board, stacks on a Pi Zero, or runs
from any MCU through the 2x6 edge header J3. J2 (1x12 analog row) takes a socket on the bottom (AFE) or 2.54 mm screw
terminals on top. All SMD parts on top (JLC assembly); J1/J2/J3 and the optional DIP-8 Y1 are hand-soldered.

ADS131M04: AVDD from its own LDO (U3, from 5 V), DVDD/IO = host 3V3. Clock: JP1 1-2 (default) = host GPIO4
(GPCLK0 on a Pi, Pico GP21 on the main board), 2-3 = on-board 8.192 MHz oscillator Y1 (DNP by default).
DAC80502 (dual): VDD = filtered 5 V (+5VA), internal reference, RSTSEL pulled to VDD by R6 (midscale at power-on); VOUTA, VOUTB and
VREFIO go to J2. SPI2C low = SPI (datasheet SBAS793A), the R2 default; JP2 bridged = I2C.
"""
parts = []


def P(ref, sym, value, fp, nets, mpn='', lcsc='', dnp=False, note=''):
    parts.append(dict(ref=ref, sym=sym, value=value, fp=fp, nets={str(k): v for k, v in nets.items()},
                      mpn=mpn, lcsc=lcsc, dnp=dnp, note=note, board=True))


R06 = 'Resistor_SMD:R_0603_1608Metric'
C06 = 'Capacitor_SMD:C_0603_1608Metric'
C08 = 'Capacitor_SMD:C_0805_2012Metric'


# JLC Basic-library parts (checked on jlcpcb.com parts search, 2026-11-21)
L1U, L100N, L220N, L10U = 'C15849', 'C14663', 'C21120', 'C15850'       # 0603 1u 50V X5R, 0603 100n X7R, 0603 220n X7R, 0805 10u 25V
L33R, L10K, L49R9, LFB = 'C23140', 'C25804', 'C23185', 'C1002'         # 0603 1 % 33R, 10k, 49.9R; 0603 600R@100MHz bead


def R(ref, v, a, b, **k): P(ref, 'Device:R', v, R06, {1: a, 2: b}, **k)
def C(ref, v, a, b, fp=C06, **k): P(ref, 'Device:C', v, fp, {1: a, 2: b}, **k)


# Raspberry Pi 40-pin header (socket on the bottom side). Same pin use as the main board's J16.
PI = {1: '+3V3', 17: '+3V3', 2: '+5V', 4: '+5V', 19: 'MOSI', 21: 'MISO', 23: 'SCLK', 24: 'CS_ADC', 26: 'CS_DAC',
      7: 'CLK_IN', 18: 'SYNC', 22: 'DRDY', **{n: 'GND' for n in (6, 9, 14, 20, 25, 30, 34, 39)}}
P('J1', 'Connector_Generic:Conn_02x20_Odd_Even', 'Pi 40-pin', 'Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical',
  PI, mpn='2x20 female 2.54 mm, 8.5 mm (Pi HAT stacking height)', note='bottom side; ID_SD/ID_SC (27/28) unused')
# single row along the bottom edge, pin 1 at the left (top view): channel pairs P,N, then DAC_OUTB, DAC_OUT (A), DAC_REF, GND
AN = {1: 'IN0P', 2: 'IN0N', 3: 'IN1P', 4: 'IN1N', 5: 'IN2P', 6: 'IN2N', 7: 'IN3P', 8: 'IN3N',
      9: 'DAC_OUTB', 10: 'DAC_OUT', 11: 'DAC_REF', 12: 'GND'}
P('J2', 'Connector_Generic:Conn_01x12', 'Analog', 'Connector_PinSocket_2.54mm:PinSocket_1x12_P2.54mm_Vertical',
  AN, mpn='1x12 female 2.54 mm, 8.5 mm (AFE) or 2.54 mm screw terminals (general use)',
  note='AFE: socket on the bottom, mates main-board J17 (INnN tied to GND there; its pin 9 is unconnected); general use: screw terminals on top')
# MCU / cable header on the right-hand short edge (2x6, IDC-ribbon compatible)
P('J3', 'Connector_Generic:Conn_02x06_Odd_Even', 'SPI', 'Connector_PinHeader_2.54mm:PinHeader_2x06_P2.54mm_Vertical',
  {1: '+5V', 2: 'GND', 3: '+3V3', 4: 'GND', 5: 'SCLK', 6: 'MOSI', 7: 'MISO', 8: 'CS_ADC', 9: 'CS_DAC', 10: 'DRDY',
   11: 'SYNC', 12: 'CLK_IN'}, mpn='2x6 pin header 2.54 mm', note='host supplies 5 V (DAC, AVDD LDO) and 3.3 V logic')

P('U1', 'afe:ADS131M04_PW', 'ADS131M04IPWR', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',
  {1: '+3V3A', 2: 'GND', 3: 'AIN0P', 4: 'AIN0N', 5: 'AIN1N', 6: 'AIN1P', 7: 'AIN2P', 8: 'AIN2N', 9: 'AIN3N', 10: 'AIN3P',
   20: '+3V3', 19: 'GND', 18: 'ADC_CAP', 17: 'ADC_CLK', 16: 'MOSI', 15: 'MISO', 14: 'SCLK', 12: 'CS_ADC', 13: 'DRDY',
   11: 'SYNC'}, mpn='ADS131M04IPWR', lcsc='C2862562')
for ch in range(4):
    R(f'R{10+2*ch}', '49.9', f'IN{ch}P', f'AIN{ch}P', lcsc=L49R9, note='input filter')
    R(f'R{11+2*ch}', '49.9', f'IN{ch}N', f'AIN{ch}N', lcsc=L49R9, note='input filter')
    C(f'C{11+ch}', '1n C0G', f'AIN{ch}P', f'AIN{ch}N', lcsc='C106246', mpn='CC0603JRNPO9BN102',
      note='differential AA cap (~1.6 MHz with 2x49.9); C0G (JLC extended: no basic C0G 1n)')
C('C2', '1u', '+3V3A', 'GND', lcsc=L1U, note='LDO output'); C('C3', '100n', '+3V3A', 'GND', lcsc=L100N, note='AVDD')
C('C4', '100n', '+3V3', 'GND', lcsc=L100N, note='DVDD'); C('C5', '1u', '+3V3', 'GND', lcsc=L1U, note='DVDD')
C('C6', '220n', 'ADC_CAP', 'GND', lcsc=L220N, note='ADC CAP pin')

P('U3', 'Regulator_Linear:LP5907MFX-3.3', 'LP5907MFX-3.3', 'Package_TO_SOT_SMD:SOT-23-5',
  {1: '+5V', 3: '+5V', 2: 'GND', 5: '+3V3A'}, mpn='LP5907MFX-3.3/NOPB', lcsc='C80670', note='AVDD LDO, low noise')
C('C1', '1u', '+5V', 'GND', lcsc=L1U, note='LDO input'); C('C15', '10u', '+5V', 'GND', fp=C08, lcsc=L10U, note='5 V entry bulk')

# clock
P('Y1', 'Oscillator:ASE-xxxMHz', '8.192MHz', 'afe:Oscillator_DIP-8_ASE-3.2x2.5_Combo',
  {1: '+3V3', 2: 'GND', 3: 'XO_OUT', 4: '+3V3'}, dnp=True,
  mpn='8.192 MHz 3.3 V CMOS XO: DIP-8 half-size can, or 3.2 x 2.5 mm SMD (TBD)',
  note='fit ONE package and set JP1 2-3 when the host gives no clock')
C('C10', '100n', '+3V3', 'GND', lcsc=L100N, note='Y1 decoupling')
R('R1', '33', 'XO_OUT', 'XO_CLK', lcsc=L33R, note='Y1 source termination')
P('JP1', 'Jumper:SolderJumper_3_Bridged12', 'CLK SRC', 'Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm',
  {1: 'CLK_IN', 2: 'ADC_CLK', 3: 'XO_CLK'}, note='1-2 (default) = host GPIO4; 2-3 = Y1')

# DAC
P('U2', 'afe:DAC80502_DRX', 'DAC80502DRX', 'Package_SON:Texas_DRX_WSON-10_2.5x2.5mm_P0.5mm',
  {1: '+5VA', 4: 'GND', 5: 'DAC_SPI2C', 3: 'RSTSEL', 2: 'DAC_OUT', 9: 'DAC_OUTB', 10: 'DAC_REF', 6: 'SCLK', 7: 'CS_DAC',
   8: 'MOSI'}, mpn='DAC80502DRXR', lcsc='C1880990', note='RSTSEL (3) high via R6: both outputs at midscale on power-up')
P('FB1', 'Device:FerriteBead', '600R@100MHz', 'Inductor_SMD:L_0603_1608Metric', {1: '+5V', 2: '+5VA'},
  lcsc=LFB, note='DAC supply filter')
C('C7', '100n', '+5VA', 'GND', lcsc=L100N, note='DAC VDD'); C('C8', '10u', '+5VA', 'GND', fp=C08, lcsc=L10U, note='DAC VDD')
C('C9', '220n', 'DAC_REF', 'GND', lcsc=L220N, note='VREFIO (datasheet: 150 nF minimum)')
R('R2', '10k', 'DAC_SPI2C', 'GND', lcsc=L10K, note='SPI2C low = SPI')
P('JP2', 'Jumper:SolderJumper_2_Open', 'SPI2C HI', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
  {1: 'DAC_SPI2C', 2: '+5VA'}, note='bridge for I2C mode (SPI2C high)')
R('R6', '10k', 'RSTSEL', '+5VA', lcsc=L10K, note='RSTSEL high = midscale at power-up; to GND for zero scale')

# host-absent defaults
R('R3', '10k', 'CS_ADC', '+3V3', lcsc=L10K); R('R4', '10k', 'CS_DAC', '+3V3', lcsc=L10K); R('R5', '10k', 'SYNC', '+3V3', lcsc=L10K)

for i in range(4):
    P(f'H{i+1}', 'Mechanical:MountingHole', 'M2.5', 'MountingHole:MountingHole_2.7mm_M2.5', {})
