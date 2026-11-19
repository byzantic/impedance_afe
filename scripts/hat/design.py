"""ADC/DAC HAT (adc_hat/): net record of intent, read by check.py and the BOM.

Raspberry Pi Zero pHAT outline (65 x 30 mm). Plugs onto J16/J17 of the AFE main board, or stacks on a Pi Zero
(J2 then takes wires). All SMD parts on top (JLC assembly); the two sockets go on the bottom (hand-soldered THT).

ADS131M04: AVDD from its own LDO (U3, from 5 V), DVDD/IO = host 3V3. Clock: JP1 1-2 (default) = host GPIO4
(GPCLK0 on a Pi, Pico GP21 on the main board), 2-3 = on-board 8.192 MHz oscillator Y1 (DNP by default).
DAC80501: VDD = filtered 5 V (+5VA), internal reference; VREFIO and VOUT go to J2.
"""
parts = []


def P(ref, sym, value, fp, nets, mpn='', lcsc='', dnp=False, note=''):
    parts.append(dict(ref=ref, sym=sym, value=value, fp=fp, nets={str(k): v for k, v in nets.items()},
                      mpn=mpn, lcsc=lcsc, dnp=dnp, note=note, board=True))


R06 = 'Resistor_SMD:R_0603_1608Metric'
C06 = 'Capacitor_SMD:C_0603_1608Metric'
C08 = 'Capacitor_SMD:C_0805_2012Metric'


def R(ref, v, a, b, **k): P(ref, 'Device:R', v, R06, {1: a, 2: b}, **k)
def C(ref, v, a, b, fp=C06, **k): P(ref, 'Device:C', v, fp, {1: a, 2: b}, **k)


# Raspberry Pi 40-pin header (socket on the bottom side). Same pin use as the main board's J16.
PI = {1: '+3V3', 17: '+3V3', 2: '+5V', 4: '+5V', 19: 'MOSI', 21: 'MISO', 23: 'SCLK', 24: 'CS_ADC', 26: 'CS_DAC',
      7: 'CLK_IN', 18: 'SYNC', 22: 'DRDY', **{n: 'GND' for n in (6, 9, 14, 20, 25, 30, 34, 39)}}
P('J1', 'Connector_Generic:Conn_02x20_Odd_Even', 'Pi 40-pin', 'Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical',
  PI, mpn='2x20 female 2.54 mm, 8.5 mm (Pi HAT stacking height)', note='bottom side; ID_SD/ID_SC (27/28) unused')
# pin 1 is at the DAC end (right, top view); channels then run IN3..IN0 towards the left, matching U1's pin order
AN = {1: 'DAC_OUT', 2: 'GND', 3: 'DAC_REF', 4: 'GND', 5: 'IN3P', 6: 'IN3N', 7: 'IN2P', 8: 'IN2N',
      9: 'IN1P', 10: 'IN1N', 11: 'IN0P', 12: 'IN0N'}
P('J2', 'Connector_Generic:Conn_02x06_Odd_Even', 'Analog', 'Connector_PinSocket_2.54mm:PinSocket_2x06_P2.54mm_Vertical',
  AN, mpn='2x6 female 2.54 mm, 8.5 mm', note='bottom side; mates main-board J17 (INnN tied to GND there)')

P('U1', 'afe:ADS131M04_PW', 'ADS131M04IPWR', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',
  {1: '+3V3A', 2: 'GND', 3: 'AIN0P', 4: 'AIN0N', 5: 'AIN1N', 6: 'AIN1P', 7: 'AIN2P', 8: 'AIN2N', 9: 'AIN3N', 10: 'AIN3P',
   20: '+3V3', 19: 'GND', 18: 'ADC_CAP', 17: 'ADC_CLK', 16: 'MOSI', 15: 'MISO', 14: 'SCLK', 12: 'CS_ADC', 13: 'DRDY',
   11: 'SYNC'}, mpn='ADS131M04IPWR', lcsc='C2862562')
for ch in range(4):
    R(f'R{10+2*ch}', '49.9', f'IN{ch}P', f'AIN{ch}P', note='input filter')
    R(f'R{11+2*ch}', '49.9', f'IN{ch}N', f'AIN{ch}N', note='input filter')
    C(f'C{11+ch}', '1n C0G', f'AIN{ch}P', f'AIN{ch}N', note='differential AA cap (~1.6 MHz with 2x49.9)')
C('C2', '1u', '+3V3A', 'GND', note='LDO output'); C('C3', '100n', '+3V3A', 'GND', note='AVDD')
C('C4', '100n', '+3V3', 'GND', note='DVDD'); C('C5', '1u', '+3V3', 'GND', note='DVDD')
C('C6', '220n', 'ADC_CAP', 'GND', note='ADC CAP pin')

P('U3', 'Regulator_Linear:LP5907MFX-3.3', 'LP5907MFX-3.3', 'Package_TO_SOT_SMD:SOT-23-5',
  {1: '+5V', 3: '+5V', 2: 'GND', 5: '+3V3A'}, mpn='LP5907MFX-3.3/NOPB', note='AVDD LDO, low noise')
C('C1', '1u', '+5V', 'GND', note='LDO input'); C('C15', '10u', '+5V', 'GND', fp=C08, note='5 V entry bulk')

# clock
P('Y1', 'Oscillator:ASE-xxxMHz', '8.192MHz', 'Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm',
  {1: '+3V3', 2: 'GND', 3: 'XO_OUT', 4: '+3V3'}, mpn='8.192 MHz 3.3 V CMOS XO, 3.2 x 2.5 mm (TBD)', dnp=True,
  note='fit and set JP1 2-3 when the host gives no clock')
C('C10', '100n', '+3V3', 'GND', note='Y1 decoupling')
R('R1', '33', 'XO_OUT', 'XO_CLK', note='Y1 source termination')
P('JP1', 'Jumper:SolderJumper_3_Bridged12', 'CLK SRC', 'Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm',
  {1: 'CLK_IN', 2: 'ADC_CLK', 3: 'XO_CLK'}, note='1-2 (default) = host GPIO4; 2-3 = Y1')

# DAC
P('U2', 'afe:DAC80501_DGS', 'DAC80501MDGS', 'Package_SO:VSSOP-10_3x3mm_P0.5mm',
  {1: '+5VA', 4: 'GND', 5: 'DAC_SPI2C', 2: 'DAC_OUT', 10: 'DAC_REF', 6: 'SCLK', 7: 'CS_DAC', 8: 'MOSI'},
  mpn='DAC80501MDGSR', lcsc='C1852032')
P('FB1', 'Device:FerriteBead', '600R@100MHz', 'Inductor_SMD:L_0603_1608Metric', {1: '+5V', 2: '+5VA'},
  note='DAC supply filter')
C('C7', '100n', '+5VA', 'GND', note='DAC VDD'); C('C8', '10u', '+5VA', 'GND', fp=C08, note='DAC VDD')
C('C9', '150n', 'DAC_REF', 'GND', note='VREFIO')
R('R2', '10k', 'DAC_SPI2C', 'GND', note='SPI2C default low')
P('JP2', 'Jumper:SolderJumper_2_Open', 'SPI2C HI', 'Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm',
  {1: 'DAC_SPI2C', 2: '+5VA'}, note='bridge to tie SPI2C high (open item: level for SPI mode)')

# host-absent defaults
R('R3', '10k', 'CS_ADC', '+3V3'); R('R4', '10k', 'CS_DAC', '+3V3'); R('R5', '10k', 'SYNC', '+3V3')

for i in range(4):
    P(f'H{i+1}', 'Mechanical:MountingHole', 'M2.5', 'MountingHole:MountingHole_2.7mm_M2.5', {})
