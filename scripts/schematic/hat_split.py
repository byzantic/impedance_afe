"""One-off: move the ADC/DAC to the pHAT sub-board (adc_hat/).

Deletes U20, U21 and their local support parts, prunes the wiring left dangling, and adds
J16 (2x20 socket, Raspberry Pi pinout) and J17 (2x6 analog socket) in their place.
"""
from redraw import *  # noqa
from redraw import _pt, _on

GONE = ['U20', 'JP4', 'R36', 'C24', 'C25', 'C26', 'U21', 'C54', 'C55', 'C56', 'C57', 'C58', 'C59',
        'X1', 'R35', 'JP6', 'R80', 'R81', 'R82', 'FB3', 'C10', '#FLG6']   # +3V3A has no loads left

# Raspberry Pi 40-pin header (J16) and analog link (J17); None = no connect
PI = {1: '+3V3D', 17: '+3V3D', 2: '+5V', 4: '+5V', 19: 'MOSI', 21: 'MISO', 23: 'SCK', 24: 'CS_ADC', 26: 'CS_DAC',
      7: 'HAT_CLK', 18: 'ADC_SYNC', 22: 'ADC_DRDY', **{n: 'GND' for n in (6, 9, 14, 20, 25, 30, 34, 39)}}
AN = {1: 'ADC0P', 3: 'ADC1P', 5: 'ADC2P', 7: 'ADC3P', 9: 'DAC_OUT', 11: 'DAC_REF',
      **{n: 'GND' for n in (2, 4, 6, 8, 10, 12)}}


def _pts(w):
    return [_pt(num(x[1]), num(x[2])) for x in find(find1(w, 'pts'), 'xy')]


def prune(s):
    """Remove dangling wire segments, then orphaned labels / power symbols / junctions / no-connects."""
    while True:
        pins = {_pt(*p) for sym in s.symbols() if not s.ref(sym).startswith('#PWR') for p in s.pins(s.ref(sym)).values()}
        named = {_pt(num(find1(l, 'at')[1]), num(find1(l, 'at')[2])) for l in s.items('label')}
        named |= {_pt(*s.at(sym)[:2]) for sym in s.symbols() if s.ref(sym).startswith('#PWR')}
        wires = [(w, _pts(w)) for w in s.items('wire')]
        ends = {}
        for _, (a, b) in wires:
            ends[a] = ends.get(a, 0) + 1; ends[b] = ends.get(b, 0) + 1

        def held(p, me):
            if p in pins or p in named or ends[p] > 1:
                return True
            return any(_on(p, a, b) for w, (a, b) in wires if w is not me)
        dead = [w for w, (a, b) in wires if not (held(a, w) and held(b, w))]
        if not dead:
            break
        for w in dead:
            s.remove(w)
    wires = [_pts(w) for w in s.items('wire')]
    touch = {p for sg in wires for p in sg} | pins

    def on_wire(p):
        return p in touch or any(_on(p, a, b) for a, b in wires)
    for l in s.items('label'):
        a = find1(l, 'at')
        if not on_wire(_pt(num(a[1]), num(a[2]))):
            s.remove(l)
    for sym in s.symbols():
        if s.ref(sym).startswith('#PWR') and not on_wire(_pt(*s.at(sym)[:2])):
            s.remove(sym)
    for nc in s.items('no_connect'):
        a = find1(nc, 'at')
        if _pt(num(a[1]), num(a[2])) not in pins:
            s.remove(nc)
    for j in s.items('junction'):
        a = find1(j, 'at'); p = _pt(num(a[1]), num(a[2]))
        n = sum(1 for sg in wires for q in sg if q == p) + sum(2 for a_, b_ in wires if _on(p, a_, b_)) + (p in pins)
        if n < 3:
            s.remove(j)


def relabel(s, old, new, near=None):
    for l in s.items('label'):
        if val(l) == old:
            a = find1(l, 'at')
            if near is None or (abs(num(a[1]) - near[0]) < 0.1 and abs(num(a[2]) - near[1]) < 0.1):
                l[1] = S(new)


def main():
    s = Sch()
    for r in GONE:
        s.remove(s.sym(r))
    prune(s)
    relabel(s, 'PICO_CLK', 'HAT_CLK')
    relabel(s, 'ADC_CLK', 'HAT_CLK')              # J13 pin 9
    for t in s.items('text'):
        v = val(t)
        if v.startswith(('ADC clock: JP6', 'X1 decoupling', 'U20 decoupling', 'U21 decoupling', 'R80-R82')):
            s.remove(t)

    FPI = 'Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical'
    FAN = 'Connector_PinSocket_2.54mm:PinSocket_2x06_P2.54mm_Vertical'
    s.add_symbol('Connector_Generic:Conn_02x20_Odd_Even', 'J16', 'ADC/DAC HAT (Pi 40-pin)', FPI, 210.82, 469.9, 0,
                 {'Note': 'Raspberry Pi header pinout; adc_hat sub-board plugs in here (or stacks on a Pi Zero)'})
    s.add_symbol('Connector_Generic:Conn_02x06_Odd_Even', 'J17', 'ADC/DAC HAT analog', FAN, 151.13, 482.6, 0,
                 {'Note': 'ADCn P/N pairs (N = GND here), DAC_OUT, DAC_REF'})
    b = Block(s, ['J16', 'J17'])
    b.F('J16', (212.09, 441.96), (212.09, 444.5), None)
    b.F('J17', (152.4, 472.44), (152.4, 474.98), None)
    for n in range(1, 41):
        net = PI.get(n)
        if net is None:
            b.nc('J16', n)
        else:
            b.term('J16', n, 2.54, net=net)
    for n, net in AN.items():
        b.term('J17', n, 2.54, net=net)
    b.finish(auto=False)
    s.text('J16: ADC/DAC sub-board (adc_hat/, Pi Zero pHAT outline). SPI0 = 19/21/23, CE0 24 = CS_ADC, CE1 26 = CS_DAC,\\n'
           'GPIO4 (7, GPCLK0) = HAT_CLK from Pico GP21 via R47, GPIO24 (18) = ADC_SYNC, GPIO25 (22) = ADC_DRDY.\\n'
           'J17: analog link to the sub-board (ADCn N tied to GND here).'.replace('\\n', '\n'), 129.54, 525.78)
    s.save()


if __name__ == '__main__':
    main()
