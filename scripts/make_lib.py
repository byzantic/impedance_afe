"""Project library 'afe': custom symbols (Pico 2, ADS131M04, DAC80501) and footprints
(DIP-8/SOIC-8 combo, Pico 2 THT). Pinouts from the TI datasheets / Raspberry Pi Pico 2 datasheet."""
import os

F = '(effects (font (size 1.27 1.27)))'

def box_symbol(name, ref, value, fp, left, right, width=20.32, desc=''):
    rows = max(len(left), len(right))
    if rows % 2 == 0: rows += 1
    top = (rows - 1) * 1.27
    hw = width / 2
    out = [f'(symbol "{name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)',
           f'  (property "Reference" "{ref}" (at {-hw} {top + 3.81} 0) (effects (font (size 1.27 1.27)) (justify left)))',
           f'  (property "Value" "{value}" (at {-hw} {-top - 3.81} 0) (effects (font (size 1.27 1.27)) (justify left)))',
           f'  (property "Footprint" "{fp}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'  (property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'  (symbol "{name}_0_1" (rectangle (start {-hw} {top + 1.27}) (end {hw} {-top - 1.27}) '
           f'(stroke (width 0.254) (type default)) (fill (type background))))',
           f'  (symbol "{name}_1_1"']
    for side, pins, x, ang in (('L', left, round(-hw - 2.54, 3), 0), ('R', right, round(hw + 2.54, 3), 180)):
        for i, p in enumerate(pins):
            if p is None: continue
            num, nm, typ = p
            y = round(top - i * 2.54, 3)
            out.append(f'    (pin {typ} line (at {x} {y} {ang}) (length 2.54) (name "{nm}" {F}) (number "{num}" {F}))')
    out.append('  ))')
    return '\n'.join(out)

# Raspberry Pi Pico 2 (same pinout as Pico): physical order, left 1..20, right 40..21
pico_names = {1: 'GP0', 2: 'GP1', 3: 'GND', 4: 'GP2', 5: 'GP3', 6: 'GP4', 7: 'GP5', 8: 'GND', 9: 'GP6', 10: 'GP7',
              11: 'GP8', 12: 'GP9', 13: 'GND', 14: 'GP10', 15: 'GP11', 16: 'GP12', 17: 'GP13', 18: 'GND', 19: 'GP14',
              20: 'GP15', 21: 'GP16', 22: 'GP17', 23: 'GND', 24: 'GP18', 25: 'GP19', 26: 'GP20', 27: 'GP21', 28: 'GND',
              29: 'GP22', 30: 'RUN', 31: 'GP26_ADC0', 32: 'GP27_ADC1', 33: 'AGND', 34: 'GP28_ADC2', 35: 'ADC_VREF',
              36: '3V3_OUT', 37: '3V3_EN', 38: 'GND', 39: 'VSYS', 40: 'VBUS'}
def ptype(n):
    nm = pico_names[n]
    if nm in ('GND', 'AGND'): return 'passive'
    if nm == 'VSYS': return 'power_in'
    if nm in ('3V3_OUT', 'VBUS'): return 'power_out'
    if nm == 'ADC_VREF': return 'passive'
    return 'bidirectional'
pico = box_symbol('RPi_Pico_2', 'A', 'Pico 2', 'afe:RaspberryPi_Pico_2_THT',
                  [(str(n), pico_names[n], ptype(n)) for n in range(1, 21)],
                  [(str(n), pico_names[n], ptype(n)) for n in range(40, 20, -1)], width=25.4,
                  desc='Raspberry Pi Pico 2 (RP2350), socketed')

adc = box_symbol('ADS131M04_PW', 'U', 'ADS131M04', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm',
                 [('1', 'AVDD', 'power_in'), ('2', 'AGND', 'power_in'), ('3', 'AIN0P', 'input'), ('4', 'AIN0N', 'input'),
                  ('6', 'AIN1P', 'input'), ('5', 'AIN1N', 'input'), ('7', 'AIN2P', 'input'), ('8', 'AIN2N', 'input'),
                  ('10', 'AIN3P', 'input'), ('9', 'AIN3N', 'input')],
                 [('20', 'DVDD', 'power_in'), ('19', 'DGND', 'power_in'), ('18', 'CAP', 'passive'), ('17', 'CLKIN', 'input'),
                  ('16', 'DIN', 'input'), ('15', 'DOUT', 'output'), ('14', 'SCLK', 'input'), ('12', '~{CS}', 'input'),
                  ('13', '~{DRDY}', 'output'), ('11', '~{SYNC}/~{RESET}', 'input')], width=22.86,
                 desc='TI ADS131M04 4-ch simultaneous 24-bit delta-sigma ADC, TSSOP-20')

dac = box_symbol('DAC80501_DGS', 'U', 'DAC80501M', 'Package_SO:VSSOP-10_3x3mm_P0.5mm',
                 [('1', 'VDD', 'power_in'), ('4', 'AGND', 'power_in'), ('5', 'SPI2C', 'input'), ('3', 'NC', 'no_connect'),
                  ('9', 'NC', 'no_connect')],
                 [('2', 'VOUT', 'output'), ('10', 'VREFIO', 'passive'), ('6', 'SCLK/SCL', 'input'),
                  ('7', '~{SYNC}/A0', 'input'), ('8', 'SDIN/SDA', 'bidirectional')], width=20.32,
                 desc='TI DAC80501M 16-bit DAC, 2.5 V internal ref, midscale power-on, VSSOP-10')

open('afe.kicad_sym', 'w').write('(kicad_symbol_lib (version 20220914) (generator afe_make_lib)\n'
                                 + '\n'.join([pico, adc, dac]) + '\n)\n')

# ---------------------------------------------------------------- footprints
os.makedirs('afe.pretty', exist_ok=True)
def fp_text(kind, txt, x, y, layer):
    return f'  (fp_text {kind} "{txt}" (at {x} {y}) (layer "{layer}") (effects (font (size 1 1) (thickness 0.15))))'
def rect(x0, y0, x1, y1, layer, w=0.12):
    return f'  (fp_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width {w}) (type solid)) (fill none) (layer "{layer}"))'

# DIP-8 (300 mil) with SOIC-8 rotated 90 deg inside the DIP rows. Same pad numbers -> same net.
dip = [(-3.81, -3.81 + 2.54 * i) for i in range(4)] + [(3.81, 3.81 - 2.54 * i) for i in range(4)]
soic_std = [(-2.475, -1.905 + 1.27 * i) for i in range(4)] + [(2.475, 1.905 - 1.27 * i) for i in range(4)]
soic = [(round(y, 3), round(-x, 3)) for x, y in soic_std]   # rotate 90 deg: pins 1-4 along the bottom
L = ['(footprint "DIP-8_SOIC-8_Combo" (version 20221018) (generator afe_make_lib) (layer "F.Cu")',
     '  (descr "Overlapping DIP-8 (7.62 mm) and SOIC-8 (rotated 90 deg) for single op-amps; fit ONE package. '
     'Same-numbered pads must be joined with copper in the layout.")',
     '  (attr through_hole)',
     fp_text('reference', 'REF**', 0, -5.6, 'F.SilkS'), fp_text('value', 'DIP8_SOIC8', 0, 5.6, 'F.Fab'),
     rect(-5.1, -5.1, 5.1, 5.1, 'F.CrtYd', 0.05), rect(-2.45, -1.95, 2.45, 1.95, 'F.Fab', 0.1),
     '  (fp_circle (center -4.9 -4.6) (end -4.75 -4.6) (stroke (width 0.3) (type solid)) (fill none) (layer "F.SilkS"))']
for i, (x, y) in enumerate(dip):
    shape = 'rect' if i == 0 else 'oval'
    L.append(f'  (pad "{i+1}" thru_hole {shape} (at {x} {y}) (size 1.6 1.6) (drill 0.8) (layers "*.Cu" "*.Mask"))')
for i, (x, y) in enumerate(soic):
    L.append(f'  (pad "{i+1}" smd roundrect (at {x} {y}) (size 0.6 1.95) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))')
L.append(')')
open('afe.pretty/DIP-8_SOIC-8_Combo.kicad_mod', 'w').write('\n'.join(L) + '\n')

# geometry check: SMD pads vs THT pads clearance
import math
minc = 9
for (sx, sy) in soic:
    for (dx_, dy_) in dip:
        ex = max(abs(dx_ - sx) - 0.3, 0); ey = max(abs(dy_ - sy) - 0.975, 0)
        minc = min(minc, math.hypot(ex, ey) - 0.8)
print('combo footprint min SMD-to-THT copper gap: %.2f mm' % minc)

# Pico 2: 2x20, 2.54 mm pitch, rows 17.78 mm apart, pin 1 top-left, pins 21-40 up the right side
L = ['(footprint "RaspberryPi_Pico_2_THT" (version 20221018) (generator afe_make_lib) (layer "F.Cu")',
     '  (descr "Raspberry Pi Pico / Pico 2 through-hole (socket with 2x 1x20 headers). Rows 17.78 mm apart.")',
     '  (attr through_hole)',
     fp_text('reference', 'REF**', 0, -27, 'F.SilkS'), fp_text('value', 'Pico_2', 0, 27, 'F.Fab'),
     rect(-10.5, -25.5, 10.5, 25.5, 'F.SilkS'), rect(-10.75, -25.75, 10.75, 25.75, 'F.CrtYd', 0.05),
     rect(-4, -26.5, 4, -24.5, 'F.Fab', 0.1)]
for n in range(1, 41):
    if n <= 20: x, y = -8.89, -24.13 + (n - 1) * 2.54
    else: x, y = 8.89, 24.13 - (n - 21) * 2.54
    shape = 'rect' if n == 1 else 'oval'
    L.append(f'  (pad "{n}" thru_hole {shape} (at {x} {round(y, 3)}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask"))')
L.append(')')
open('afe.pretty/RaspberryPi_Pico_2_THT.kicad_mod', 'w').write('\n'.join(L) + '\n')

open('sym-lib-table', 'w').write('(sym_lib_table\n  (lib (name "afe")(type "KiCad")(uri "${KIPRJMOD}/afe.kicad_sym")(options "")(descr "AFE project symbols"))\n)\n')
open('fp-lib-table', 'w').write('(fp_lib_table\n  (lib (name "afe")(type "KiCad")(uri "${KIPRJMOD}/afe.pretty")(options "")(descr "AFE project footprints"))\n)\n')
print('library written')
