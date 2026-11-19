"""Replace rail net labels with power symbols (sheet-wide, one-off).  Run once; idempotent (no rail labels left)."""
from sch import *  # noqa

RAILS = {'GND': 'power:GND', '+15V': 'power:+15V', '-15V': 'power:-15V', '+5V': 'power:+5V',
         '+3V3': 'power:+3V3', '+3V3A': 'power:+3V3', '+3V3D': 'power:+3V3'}


def lib_power(name):
    t = parse(open('/usr/share/kicad/symbols/power.kicad_sym').read())
    for s in find(t, 'symbol'):
        if val(s) == name:
            s[1] = S('power:' + name)
            return s
    raise KeyError(name)


def orient(lib_id, dx, dy):
    """rotation that points the symbol body along (dx, dy) (away from the pin)"""
    body = (0, 1) if lib_id == 'power:GND' else (0, -1)
    for a in (0, 90, 180, 270):
        if rot(*body, a) == (dx, dy):
            return a
    raise ValueError((dx, dy))


def convert(s):
    for lid in set(RAILS.values()):
        s.add_lib_symbol(lid, lib_power(lid.split(':')[1]))
    wires = s.items('wire')
    ends = {}
    for w in wires:
        a, b = [(num(xy[1]), num(xy[2])) for xy in find(find1(w, 'pts'), 'xy')]
        ends.setdefault((round(a[0], 3), round(a[1], 3)), []).append(b)
        ends.setdefault((round(b[0], 3), round(b[1], 3)), []).append(a)
    n = 0
    for lab in s.items('label'):
        name = val(lab)
        if name not in RAILS:
            continue
        a = find1(lab, 'at')
        p = (round(num(a[1]), 3), round(num(a[2]), 3))
        other = ends.get(p)
        assert other and len(other) == 1, (name, p, other)
        ox, oy = other[0]
        dx, dy = p[0] - ox, p[1] - oy
        L = max(abs(dx), abs(dy))
        s.power(RAILS[name], name, p[0], p[1], orient(RAILS[name], round(dx / L), round(dy / L)))
        s.remove(lab); n += 1
    return n


if __name__ == '__main__':
    s = Sch()
    print('converted', convert(s))
    s.save()
