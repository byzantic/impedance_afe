"""One-off: DAC80501 (single) -> DAC80502 (dual, WSON-10 DRX) on the HAT; J2 pin 9 GND -> DAC_OUTB.

Adds symbol afe:DAC80502_DRX to afe.kicad_sym (same pin positions as DAC80501_DGS: pin 3 RSTSEL replaces NC, pin 9
VOUTB replaces NC), swaps U2 in adc_hat.kicad_sch, pulls RSTSEL up to +5VA through R6 (midscale power-on, as the DAC80501M; its
own net so the WSON pins 1-3 can escape) and labels pin 9 / J2 pin 9 DAC_OUTB.  Edits the schematic in place; run once.
"""
import os, re, sys
HATDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HATDIR, '..', 'schematic'))
from sch import *  # noqa
from redraw import _pt, orient  # noqa

LIB = os.path.join(ROOT, 'afe.kicad_sym')
SCHF = os.path.join(ROOT, 'adc_hat', 'adc_hat.kicad_sch')
FP = 'Package_SON:Texas_DRX_WSON-10_2.5x2.5mm_P0.5mm'

# 1. library symbol
lib = open(LIB).read()
assert 'DAC80502_DRX' not in lib
i = lib.index('(symbol "DAC80501_DGS"'); j = lib.index('\n  ))\n', i) + len('\n  ))\n')
new = lib[i:j].replace('DAC80501_DGS', 'DAC80502_DRX').replace('"DAC80501M"', '"DAC80502"')
new = new.replace('Package_SO:VSSOP-10_3x3mm_P0.5mm', FP)
new = new.replace('TI DAC80501M 16-bit DAC, 2.5 V internal ref, midscale power-on, VSSOP-10',
                  'TI DAC80502 dual 16-bit DAC, 2.5 V internal ref, RSTSEL power-on scale, WSON-10 2.5x2.5 (DRX)')
new = new.replace('(pin no_connect line (at -12.7 -2.54 0) (length 2.54) (name "NC"',
                  '(pin input line (at -12.7 -2.54 0) (length 2.54) (name "RSTSEL"')
new = new.replace('(pin no_connect line (at -12.7 -5.08 0) (length 2.54) (name "NC"',
                  '(pin output line (at -12.7 -5.08 0) (length 2.54) (name "VOUTB"')
new = new.replace('(name "VOUT"', '(name "VOUTA"')
assert new.count('RSTSEL') == 2 and 'VOUTB' in new and '"NC"' not in new
open(LIB, 'w').write(lib[:j] + new + lib[j:])

# 2. schematic
s = Sch(SCHF)
node = [e for e in find(parse(open(LIB).read()), 'symbol') if val(e) == 'DAC80502_DRX'][0]
node[1] = S('afe:DAC80502_DRX')
find1(s.t, 'lib_symbols').remove(s.libs.pop('afe:DAC80501_DGS'))
s.add_lib_symbol('afe:DAC80502_DRX', node)
u2 = s.sym('U2')
find1(u2, 'lib_id')[1] = S('afe:DAC80502_DRX')
s.set_prop('U2', 'Value', 'DAC80502DRX'); s.set_prop('U2', 'Footprint', FP)
s.set_prop('U2', 'MPN', 'DAC80502DRXR'); s.set_prop('U2', 'LCSC', 'C1880990')
s.set_prop('U2', 'Description', 'Dual 16-bit DAC, internal 2.5 V reference')


def drop_nc(p):
    for nc in s.items('no_connect'):
        a = find1(nc, 'at')
        if _pt(num(a[1]), num(a[2])) == _pt(*p):
            s.remove(nc); return
    raise KeyError(p)


p3, p9 = _pt(*s.pin('U2', '3')), _pt(*s.pin('U2', '9'))
drop_nc(p3); drop_nc(p9)
q3 = (p3[0] - 2.54, p3[1]); s.wire([p3, q3]); s.label('RSTSEL', *q3, 180)
x2, y2, _ = s.at(s.sym('R2'))                         # R2 fields to its left, clear of the RSTSEL label
s.field_at('R2', 'Reference', x2 - 2.54, y2 - 1.27, justify='right'); s.field_at('R2', 'Value', x2 - 2.54, y2 + 1.27, justify='right')
s.add_symbol('Device:R', 'R6', '10k', 'Resistor_SMD:R_0603_1608Metric', 185.42, 152.4, 90,
             {'LCSC': 'C25804', 'Note': 'RSTSEL high = midscale at power-up; to GND for zero scale'})
a, c = sorted([_pt(*s.pin('R6', '1')), _pt(*s.pin('R6', '2'))])
s.wire([a, (a[0] - 2.54, a[1])]); s.label('RSTSEL', a[0] - 2.54, a[1], 180)
s.wire([c, (c[0] + 2.54, c[1])]); s.power('power:+5V', '+5VA', c[0] + 2.54, c[1], 0)
s.field_at('R6', 'Reference', 185.42, 149.86, angle=270, justify=None)
s.field_at('R6', 'Value', 185.42, 154.94, angle=270, justify=None)   # (field angles as redraw.Block.F sets them)
q9 = (p9[0] - 2.54, p9[1]); r9 = (q9[0], q9[1] + 5.08)
s.wire([p9, q9]); s.wire([q9, r9]); s.label('DAC_OUTB', *r9, 270)

# J2 pin 9: GND stub -> DAC_OUTB
pj = _pt(*s.pin('J2', '9'))
far = None
for w in s.items('wire'):
    a, b = [_pt(num(xy[1]), num(xy[2])) for xy in find(find1(w, 'pts'), 'xy')]
    if pj in (a, b):
        far = b if a == pj else a
        break
assert far
for sym in s.symbols():
    if s.ref(sym).startswith('#PWR') and _pt(*s.at(sym)[:2]) == far:
        assert val(find1(sym, 'lib_id')) == 'power:GND'
        s.remove(sym); break
else:
    raise KeyError('J2-9 GND symbol')
s.label('DAC_OUTB', *far, 0)

for t in s.items('text'):
    v = val(t)
    if v.startswith('J2 = analog, 1x12'):
        t[1] = S(v.replace('GND, DAC_OUT, DAC_REF, GND', 'DAC_OUTB, DAC_OUT (A), DAC_REF, GND'))
    elif v.startswith('Decoupling:'):
        t[1] = S(v.replace('C7/C8 DAC VDD', 'C7/C8 DAC VDD; R6 RSTSEL pull-up (midscale at power-on)'))
tb = find1(find1(s.t, 'title_block'), 'title')
tb[1] = S(val(tb).replace('DAC80501', 'DAC80502'))
s.save()
print('U2 -> DAC80502_DRX; R6 RSTSEL pull-up; U2-9 and J2-9 = DAC_OUTB')
