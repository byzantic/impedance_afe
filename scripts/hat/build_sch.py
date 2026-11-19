"""One-shot: create adc_hat/adc_hat.kicad_sch (A4) from scripts/hat/design.py, drawn wired.

Like the main-board block scripts, this starts from scratch: re-running it overwrites hand edits in KiCad.
"""
import copy, json, os, sys, uuid
HATDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HATDIR, '..', 'schematic'))
import redraw  # noqa: E402
from redraw import *  # noqa: E402,F401
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location('hat_design', os.path.join(HATDIR, 'design.py'))
hd = importlib.util.module_from_spec(spec); spec.loader.exec_module(hd)

OUT = os.path.join(ROOT, 'adc_hat')
SCHF = os.path.join(OUT, 'adc_hat.kicad_sch')
PIN = {(p['ref'], pin): n for p in hd.parts for pin, n in p['nets'].items()}
redraw.RAILS = dict(redraw.RAILS, **{'+5VA': 'power:+5V'})
RAILS = redraw.RAILS
UP, DN, LT, RT = (0, -1), (0, 1), (-1, 0), (1, 0)


class HB(Block):
    def net(self, ref, n):
        return PIN.get((ref, str(n)))


def template():
    os.makedirs(OUT, exist_ok=True)
    u = str(uuid.uuid4())
    open(SCHF, 'w').write(f'''(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (generator_version "9.0")
  (uuid "{u}")
  (paper "A4")
  (title_block
    (title "ADC/DAC HAT: ADS131M04 + DAC80501 (Pi Zero pHAT)")
    (date "2026-11-19")
    (rev "A")
    (comment 1 "Plugs onto the impedance AFE (J16/J17) or stacks on a Raspberry Pi Zero")
    (comment 2 "Drawn by scripts/hat/build_sch.py; edit in KiCad. scripts/hat/design.py = net record"))
  (lib_symbols)
  (sheet_instances
    (path "/"
      (page "1")))
  (embedded_fonts no))
''')
    open(os.path.join(OUT, 'sym-lib-table'), 'w').write(
        '(sym_lib_table\n  (lib (name "afe")(type "KiCad")(uri "${KIPRJMOD}/../afe.kicad_sym")(options "")(descr "AFE project symbols"))\n)\n')
    main = json.load(open(os.path.join(ROOT, 'impedance_afe.kicad_pro')))
    pro = {'meta': {'filename': 'adc_hat.kicad_pro', 'version': 3},
           'board': {'design_settings': main['board']['design_settings']},
           'net_settings': {'classes': [c for c in main['net_settings']['classes'] if c['name'] == 'Default'],
                            'meta': {'version': 4}},
           'schematic': {'meta': {'version': 1}}, 'sheets': [[u, 'Root']]}
    pro['board']['design_settings'].pop('drc_exclusions', None)
    json.dump(pro, open(os.path.join(OUT, 'adc_hat.kicad_pro'), 'w'), indent=2)


def libs(s):
    main = Sch()
    for lid in ['afe:ADS131M04_PW', 'afe:DAC80501_DGS', 'power:GND', 'power:+5V', 'power:+3V3']:
        s.add_lib_symbol(lid, copy.deepcopy(main.libs[lid]))
    t = parse(open('/usr/share/kicad/symbols/Regulator_Linear.kicad_sym').read())
    node = copy.deepcopy([e for e in find(t, 'symbol') if val(e) == 'LP5907MFX-1.2'][0])

    def ren(e):
        if isinstance(e, list):
            if e and e[0] == A('symbol') and len(e) > 1 and isinstance(e[1], tuple) and 'LP5907MFX-1.2' in e[1][1]:
                e[1] = S(e[1][1].replace('LP5907MFX-1.2', 'LP5907MFX-3.3'))
            for x in e:
                ren(x)
    ren(node)
    node[1] = S('Regulator_Linear:LP5907MFX-3.3')
    for p in find(node, 'property'):
        if val(p) == 'Value':
            p[2] = S('LP5907MFX-3.3')
    s.add_lib_symbol('Regulator_Linear:LP5907MFX-3.3', node)
    t = parse(open('/usr/share/kicad/symbols/power.kicad_sym').read())
    n = copy.deepcopy([e for e in find(t, 'symbol') if val(e) == 'PWR_FLAG'][0]); n[1] = S('power:PWR_FLAG')
    s.add_lib_symbol('power:PWR_FLAG', n)


def add_parts(s):
    for p in hd.parts:
        props = {k: v for k, v in (('MPN', p['mpn']), ('LCSC', p['lcsc']), ('Note', p['note'])) if v}
        s.add_symbol(p['sym'], p['ref'], p['value'], p['fp'], 0, 0, 0, props)
        if p['dnp']:
            s.set_flag(p['ref'], 'dnp', True)


def flag(s, b, net, x, y):
    """rail symbol at (x, y) pointing up, PWR_FLAG hanging below it on a 5.08 mm wire"""
    b.rail(net, (x, y), UP)
    b.w((x, y), (x, y + 5.08))
    s.power('power:PWR_FLAG', 'PWR_FLAG', x, y + 5.08, 180)


def horizontal_rail_text(s, refs):
    ends = {}
    for ref in refs:
        for n, p in s.pins(ref).items():
            d = s.pin_dir(ref, n)
            ends[(round(p[0] + 2.54 * d[0], 2), round(p[1] + 2.54 * d[1], 2))] = d
    for sym in s.symbols():
        r = s.ref(sym)
        if not r.startswith('#PWR'):
            continue
        x, y, rot = s.at(sym)
        d = ends.get((round(x, 2), round(y, 2)))
        if d and d[0]:
            a = (-int(rot)) % 360
            s.field_at(r, 'Value', x + 5.08 * d[0], y, angle=a, justify='left' if d[0] > 0 else 'right')


def draw(s):
    refs = [p['ref'] for p in hd.parts]
    b = HB(s, refs)
    # ---- connectors
    b.pl('J1', 40.64, 76.2); b.F('J1', (41.91, 48.26), (41.91, 50.8), None)
    b.pl('J2', 40.64, 144.78); b.F('J2', (41.91, 134.62), (41.91, 137.16), None)
    for j, n_pins in (('J1', 40), ('J2', 12)):
        for n in range(1, n_pins + 1):
            b.term(j, n)
    s.text('J1 = Raspberry Pi 40-pin (socket, bottom side).\\nSPI0 19/21/23, CE0 24 = ADC, CE1 26 = DAC,\\n'
           'GPIO4 (7, GPCLK0) = CLK_IN, GPIO24 (18) = SYNC,\\nGPIO25 (22) = DRDY. ID_SD/ID_SC (27/28) unused.'
           .replace('\\n', '\n'), 22.86, 113.03)
    s.text('J2 = analog (socket, bottom side): IN0..3 P/N,\\nDAC_OUT, DAC_REF. Main board ties INnN to GND.'
           .replace('\\n', '\n'), 22.86, 163.83)
    # ---- input filters: INnP -R- AINnP, INnN -R- AINnN, 1n differential between
    for k in range(4):
        x0, y0 = 81.28, 43.18 + 17.78 * k
        rp, rn, c = f'R{10+2*k}', f'R{11+2*k}', f'C{11+k}'
        b.pl(rp, x0, y0, 90); b.pl(rn, x0, y0 + 7.62, 90); b.pl(c, x0 + 10.16, y0 + 3.81)
        b.term(rp, 1); b.term(rn, 1)
        b.w(b.p(rp, 2), (x0 + 17.78, y0)); b.lab(f'AIN{k}P', (x0 + 17.78, y0), RT)
        b.w(b.p(rn, 2), (x0 + 17.78, y0 + 7.62)); b.lab(f'AIN{k}N', (x0 + 17.78, y0 + 7.62), RT)
        b.F(rp, (x0 - 0.635, y0 - 2.54), (x0 + 0.635, y0 - 2.54), 'right')
        s.field_at(rp, 'Value', x0 + 0.635, y0 - 2.54, angle=270, justify='left')
        b.F(rn, (x0 - 0.635, y0 + 11.43), (x0 + 0.635, y0 + 11.43), 'right')
        s.field_at(rn, 'Value', x0 + 0.635, y0 + 11.43, angle=270, justify='left')
        b.F(c, (x0 + 12.7, y0 + 2.54), (x0 + 12.7, y0 + 5.08), 'left')
    s.text('Input filter: 2 x 49.9R + 1 nF diff (~1.6 MHz).\\nAdjust for the source; 0R + DNP to bypass.'.replace('\\n', '\n'),
           99.06, 125.73)
    # ---- ADC
    b.pl('U1', 152.4, 76.2); b.F('U1', (152.4, 57.15), (152.4, 59.69), None)
    for n in range(1, 21):
        b.term('U1', n)
    # ---- DAC + SPI2C strap
    b.pl('U2', 152.4, 137.16); b.F('U2', (152.4, 127.0), (152.4, 129.54), None)
    sp = b.p('U2', 5)
    b.pl('R2', 127.0, sp[1] + 3.81); b.at_pin('R2', 2, DN)
    b.pl('JP2', 111.76, sp[1], 180); b.F('JP2', (111.76, sp[1] + 3.81), (111.76, sp[1] + 6.35), None)
    b.w(sp, b.p('JP2', 1)); b.at_pin('JP2', 2, UP)
    for n in (1, 2, 3, 4, 6, 7, 8, 9, 10):
        b.term('U2', n)
    # ---- AVDD LDO
    b.pl('U3', 215.9, 45.72); b.F('U3', (215.9, 36.83), (215.9, 39.37), None)
    pi, pe, po = b.p('U3', 1), b.p('U3', 3), b.p('U3', 5)
    b.w(pe, (pi[0] - 2.54, pe[1]), (pi[0] - 2.54, pi[1])); b.w(pi, (pi[0] - 5.08, pi[1])); b.rail('+5V', (pi[0] - 5.08, pi[1]), UP)
    b.w(po, (po[0] + 5.08, po[1])); b.rail('+3V3A', (po[0] + 5.08, po[1]), UP)
    b.at_pin('U3', 2, DN); b.nc('U3', 4)
    # ---- DAC supply filter
    b.pl('FB1', 251.46, 43.18, 90 if s.lib_pins('Device:FerriteBead')['1'][1] > 0 else 270)
    b.F('FB1', (251.46, 38.1), (251.46, 49.53), None)
    for n in (1, 2):
        q = b.p('FB1', n); dx = -5.08 if q[0] < 251.46 else 5.08
        b.w(q, (q[0] + dx, q[1])); b.rail(PIN[('FB1', str(n))], (q[0] + dx, q[1]), UP)
    # ---- clock: Y1 -> R1 -> JP1 pin 3; JP1 pin 1 = CLK_IN (host); pin 2 = ADC_CLK
    b.pl('Y1', 215.9, 81.28); b.F('Y1', (222.25, 72.39), (222.25, 74.93), 'left')
    en, vdd, out = b.p('Y1', 1), b.p('Y1', 4), b.p('Y1', 3)
    b.w(vdd, (vdd[0], vdd[1] - 2.54)); b.w(en, (en[0] - 2.54, en[1]), (en[0] - 2.54, vdd[1] - 2.54), (vdd[0], vdd[1] - 2.54))
    b.rail('+3V3', (vdd[0], vdd[1] - 2.54), UP)
    b.at_pin('Y1', 2, DN)
    b.pl('R1', out[0] + 7.62, out[1], 90); b.w(out, b.p('R1', 1))
    b.F('R1', (out[0] + 7.62, out[1] - 2.54), (out[0] + 7.62, out[1] + 3.81), None)
    b.pl('JP1', out[0] + 22.86, out[1], 180); b.F('JP1', (out[0] + 27.94, out[1] - 7.62), (out[0] + 27.94, out[1] - 5.08), 'left')
    b.w(b.p('R1', 2), b.p('JP1', 3))
    b.term('JP1', 1); b.term('JP1', 2)
    s.text('JP1: 1-2 (default) = host clock on J1-7 (Pico GP21 8.000 MHz on the AFE,\\n'
           'GPCLK0 on a Pi); cut, bridge 2-3 and fit Y1 for 8.192 MHz on board.'.replace('\\n', '\n'), 195.58, 100.33)
    # ---- host-absent pull-ups
    for i, r in enumerate(['R3', 'R4', 'R5']):
        b.pl(r, 210.82 + 10.16 * i, 127.0, 180); b.at_pin(r, 2, UP); b.term(r, 1)
    s.text('CS / SYNC pull-ups (host absent)', 205.74, 116.84)
    # ---- decoupling strip
    strip_ = ['C15', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10']
    for i, c in enumerate(strip_):
        x = 22.86 + 10.16 * i
        b.pl(c, x, 187.96); b.at_pin(c, 2, DN)
        if PIN[(c, '1')] in RAILS:
            b.at_pin(c, 1, UP)
        else:
            b.term(c, 1, 2.54, UP)
    s.text('Decoupling: C15/C1 LDO in (+5V), C2/C3 AVDD, C4/C5 DVDD, C6 CAP, C7/C8 DAC VDD, C9 VREFIO, C10 Y1',
           20.32, 170.18)
    # ---- power flags
    for i, net in enumerate(['+5V', '+3V3', '+5VA', 'GND']):
        x, y = 66.04 + 10.16 * i, 144.78
        if net == 'GND':
            b.w((x, y), (x, y + 5.08)); b.rail('GND', (x, y + 5.08), DN); s.power('power:PWR_FLAG', 'PWR_FLAG', x, y, 0)
        else:
            flag(s, b, net, x, y)
    for i, h in enumerate(['H1', 'H2', 'H3', 'H4']):
        b.pl(h, 210.82 + 10.16 * i, 157.48); b.F(h, (210.82 + 10.16 * i, 162.56), (210.82 + 10.16 * i, 165.1), None)
    s.text('M2.5 mounting holes (pHAT pattern 58 x 23 mm)', 205.74, 149.86)
    n = b.finish(auto=False)
    horizontal_rail_text(s, ['J1', 'J2', 'U1', 'U2'])
    return n


if __name__ == '__main__':
    template()
    s = Sch(SCHF)
    libs(s)
    add_parts(s)
    print('wires', draw(s))
    s.save()
