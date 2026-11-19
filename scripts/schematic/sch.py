"""Minimal KiCad 9 schematic editor on the kilib S-expression tree (parse -> edit -> dump).

Coordinates are schematic mm, y down.  Library pin coordinates are y up; instance transform:
    p = at + R(rot) . (x, -y)     (rot in degrees, counter-clockwise on screen)
"""
import math, os, sys, uuid as _uuid
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from kilib import parse, dump  # noqa: E402

SCH = os.path.join(ROOT, 'impedance_afe.kicad_sch')
G = 1.27  # grid


def S(s):
    return ('S', s)


def A(s):
    return ('A', str(s))


def head(e):
    return e[0][1] if isinstance(e, list) and e and isinstance(e[0], tuple) else None


def find(e, key):
    return [c for c in e if isinstance(c, list) and head(c) == key]


def find1(e, key):
    r = find(e, key)
    return r[0] if r else None


def val(e, i=1):
    return e[i][1]


def num(v):
    return float(v[1]) if isinstance(v, tuple) else float(v)


def fmt(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def snap(v):
    return round(round(v / G) * G, 4)


def uid():
    return S(str(_uuid.uuid4()))


def rot(x, y, deg):
    a = math.radians(deg)
    c, s = round(math.cos(a)), round(math.sin(a))
    return (x * c + y * s, -x * s + y * c)


class Sch:
    def __init__(self, path=SCH):
        self.path = path
        self.t = parse(open(path).read())
        self.root_uuid = val(find1(self.t, 'uuid'))
        self.libs = {val(s): s for s in find(find1(self.t, 'lib_symbols'), 'symbol')}
        self._pwr = max([int(self.ref(x)[4:]) for x in self.symbols() if self.ref(x).startswith('#PWR')] + [0])

    # ------------------------------------------------------------ symbols
    def symbols(self):
        return find(self.t, 'symbol')

    def ref(self, sym):
        for p in find(sym, 'property'):
            if val(p) == 'Reference':
                return val(p, 2)

    def sym(self, ref):
        for s in self.symbols():
            if self.ref(s) == ref:
                return s
        raise KeyError(ref)

    def at(self, sym):
        a = find1(sym, 'at')
        return num(a[1]), num(a[2]), num(a[3]) if len(a) > 3 else 0.0

    def lib_pins(self, lib_id, unit=1):
        """{number: (x, y)} in library coords (y up), units 0 and `unit`"""
        out = {}
        top = self.libs[lib_id]
        base = lib_id.split(':')[1]
        subs = find(top, 'symbol')
        for s in subs:
            nm = val(s)
            parts = nm[len(base) + 1:].split('_') if nm.startswith(base + '_') else None
            if not parts or int(parts[0]) not in (0, unit):
                continue
            for p in find(s, 'pin'):
                a = find1(p, 'at')
                out[val(find1(p, 'number'))] = (num(a[1]), num(a[2]))
        return out

    def mirrored(self, sym):
        m = find1(sym, 'mirror')
        return m[1][1] if m else None

    def _xf(self, sym, px, py):
        """library vector (y up) -> screen offset"""
        x0, y0, r = self.at(sym)
        sx, sy = px, -py
        m = self.mirrored(sym)
        if m:
            assert r == 0, 'mirror only with rotation 0'
            if m == 'x':
                sy = -sy
            else:
                sx = -sx
        return rot(sx, sy, r)

    def pins(self, ref):
        s = self.sym(ref)
        x0, y0, r = self.at(s)
        unit = int(num(find1(s, 'unit')[1]))
        out = {}
        for n, (px, py) in self.lib_pins(val(find1(s, 'lib_id')), unit).items():
            dx, dy = self._xf(s, px, py)
            out[n] = (round(x0 + dx, 4), round(y0 + dy, 4))
        return out

    def pin_dir(self, ref, n):
        """unit vector pointing away from the symbol body at pin n (screen coords)"""
        s = self.sym(ref)
        unit = int(num(find1(s, 'unit')[1]))
        lid = val(find1(s, 'lib_id'))
        base = lid.split(':')[1]
        for sub in find(self.libs[lid], 'symbol'):
            nm = val(sub)
            parts = nm[len(base) + 1:].split('_') if nm.startswith(base + '_') else None
            if not parts or int(parts[0]) not in (0, unit):
                continue
            for p in find(sub, 'pin'):
                if val(find1(p, 'number')) == str(n):
                    a = math.radians(num(find1(p, 'at')[3]))
                    dx, dy = self._xf(s, -round(math.cos(a)), -round(math.sin(a)))
                    return (round(dx), round(dy))
        raise KeyError((ref, n))

    def pin(self, ref, n):
        return self.pins(ref)[str(n)]

    def move(self, ref, x, y, r=None, mirror=None):
        """move symbol (and its fields) so its origin is at (x, y); optional new rotation / mirror ('x' or None)"""
        s = self.sym(ref)
        x0, y0, r0 = self.at(s)
        a = find1(s, 'at')
        a[1:] = [A(fmt(x)), A(fmt(y)), A(fmt(r if r is not None else r0))]
        for m in find(s, 'mirror'):
            s.remove(m)
        if mirror:
            s.insert(s.index(a) + 1, [A('mirror'), A(mirror)])
        for p in find(s, 'property'):
            pa = find1(p, 'at')
            px, py = num(pa[1]) - x0, num(pa[2]) - y0
            pr = num(pa[3]) if len(pa) > 3 else 0
            if r is not None and r != r0:
                px, py = rot(px, py, r - r0)
            pa[1:] = [A(fmt(x + px)), A(fmt(y + py)), A(fmt(pr))]

    def field_at(self, ref, field, x, y, angle=0, justify=None):
        s = self.sym(ref)
        for p in find(s, 'property'):
            if val(p) == field:
                find1(p, 'at')[1:] = [A(fmt(x)), A(fmt(y)), A(fmt(angle))]
                eff = find1(p, 'effects')
                for j in find(eff, 'justify'):
                    eff.remove(j)
                if justify:
                    eff.append([A('justify')] + [A(j) for j in justify.split()])

    # ------------------------------------------------------------ items
    def items(self, key):
        return find(self.t, key)

    def remove(self, item):
        self.t.remove(item)

    def _insert(self, item):
        i = self.t.index(find1(self.t, 'sheet_instances'))
        self.t.insert(i, item)

    def wire(self, pts):
        pts = [(snap(x), snap(y)) for x, y in pts]
        for a, b in zip(pts, pts[1:]):
            if a == b:
                continue
            assert a[0] == b[0] or a[1] == b[1], ('non-orthogonal wire', a, b)
            self._insert([A('wire'), [A('pts'), [A('xy'), A(fmt(a[0])), A(fmt(a[1]))], [A('xy'), A(fmt(b[0])), A(fmt(b[1]))]],
                          [A('stroke'), [A('width'), A('0')], [A('type'), A('default')]], [A('uuid'), uid()]])

    def label(self, text, x, y, angle=0):
        """local label; angle 0: text to the right of the point, 180: left, 90: up, 270: down"""
        just = {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}[angle]
        self._insert([A('label'), S(text), [A('at'), A(fmt(snap(x))), A(fmt(snap(y))), A(fmt(angle))],
                      [A('fields_autoplaced'), A('yes')],
                      [A('effects'), [A('font'), [A('size'), A('1.27'), A('1.27')]], [A('justify')] + [A(j) for j in just.split()]],
                      [A('uuid'), uid()]])

    def junction(self, x, y):
        self._insert([A('junction'), [A('at'), A(fmt(snap(x))), A(fmt(snap(y)))], [A('diameter'), A('0')],
                      [A('color'), A('0'), A('0'), A('0'), A('0')], [A('uuid'), uid()]])

    def no_connect(self, x, y):
        self._insert([A('no_connect'), [A('at'), A(fmt(snap(x))), A(fmt(snap(y)))], [A('uuid'), uid()]])

    def text(self, s, x, y, size=1.27):
        self._insert([A('text'), S(s), [A('exclude_from_sim'), A('no')], [A('at'), A(fmt(x)), A(fmt(y)), A('0')],
                      [A('effects'), [A('font'), [A('size'), A(fmt(size)), A(fmt(size))]], [A('justify'), A('left'), A('bottom')]],
                      [A('uuid'), uid()]])

    def add_lib_symbol(self, lib_id, node):
        if lib_id not in self.libs:
            ls = find1(self.t, 'lib_symbols')
            ls.append(node); self.libs[lib_id] = node

    def power(self, lib_id, value, x, y, angle=0):
        """power symbol instance; pin at (x, y)"""
        self._pwr += 1
        ref = '#PWR%04d' % self._pwr
        x, y = snap(x), snap(y)

        def prop(k, v, dx, dy, hide):
            e = [A('effects'), [A('font'), [A('size'), A('1.27'), A('1.27')]]]
            if hide:
                e.append([A('hide'), A('yes')])
            return [A('property'), S(k), S(v), [A('at'), A(fmt(x + dx)), A(fmt(y + dy)), A('0')], e]
        down = lib_id == 'power:GND'
        vdx, vdy = rot(0, 5.08 if down else -3.81, angle)
        node = [A('symbol'), [A('lib_id'), S(lib_id)], [A('at'), A(fmt(x)), A(fmt(y)), A(fmt(angle))], [A('unit'), A('1')],
                [A('exclude_from_sim'), A('no')], [A('in_bom'), A('yes')], [A('on_board'), A('yes')], [A('dnp'), A('no')],
                [A('fields_autoplaced'), A('yes')], [A('uuid'), uid()],
                prop('Reference', ref, 0, 0, True), prop('Value', value, vdx, vdy, False),
                prop('Footprint', '', 0, 0, True), prop('Datasheet', '', 0, 0, True), prop('Description', '', 0, 0, True),
                [A('pin'), S('1'), [A('uuid'), uid()]],
                [A('instances'), [A('project'), S('impedance_afe'), [A('path'), S('/' + self.root_uuid),
                                                                     [A('reference'), S(ref)], [A('unit'), A('1')]]]]]
        self._insert(node)
        return node

    def add_symbol(self, lib_id, ref, value, footprint, x, y, r=0, props=None, on_board=True):
        lib, name = lib_id.split(':')
        if lib_id not in self.libs:
            t = parse(open('/usr/share/kicad/symbols/%s.kicad_sym' % lib).read())
            node = [e for e in find(t, 'symbol') if val(e) == name][0]
            node[1] = S(lib_id)
            self.add_lib_symbol(lib_id, node)

        def prop(k, v, dx, dy, hide):
            e = [A('effects'), [A('font'), [A('size'), A('1.27'), A('1.27')]]]
            if hide:
                e.append([A('hide'), A('yes')])
            return [A('property'), S(k), S(v), [A('at'), A(fmt(x + dx)), A(fmt(y + dy)), A('0')], e]
        pins = sorted({n for n in self.lib_pins(lib_id)}, key=lambda n: (len(n), n))
        node = [A('symbol'), [A('lib_id'), S(lib_id)], [A('at'), A(fmt(x)), A(fmt(y)), A(fmt(r))], [A('unit'), A('1')],
                [A('exclude_from_sim'), A('no')], [A('in_bom'), A('yes')], [A('on_board'), A('yes' if on_board else 'no')],
                [A('dnp'), A('no')], [A('uuid'), uid()],
                prop('Reference', ref, 2.54, -2.54, False), prop('Value', value, 2.54, 0, False),
                prop('Footprint', footprint, 0, 0, True), prop('Datasheet', '', 0, 0, True), prop('Description', '', 0, 0, True)]
        for k, v in (props or {}).items():
            node.append(prop(k, v, 0, 0, True))
        for n in pins:
            node.append([A('pin'), S(n), [A('uuid'), uid()]])
        node.append([A('instances'), [A('project'), S('impedance_afe'), [A('path'), S('/' + self.root_uuid),
                                                                          [A('reference'), S(ref)], [A('unit'), A('1')]]]])
        self._insert(node)
        return node

    def set_prop(self, ref, key, value):
        s = self.sym(ref)
        for p in find(s, 'property'):
            if val(p) == key:
                p[2] = S(value)
                return
        x, y, _ = self.at(s)
        s.insert(s.index(find(s, 'property')[-1]) + 1,
                 [A('property'), S(key), S(value), [A('at'), A(fmt(x)), A(fmt(y)), A('0')],
                  [A('effects'), [A('font'), [A('size'), A('1.27'), A('1.27')]], [A('hide'), A('yes')]]])

    def set_flag(self, ref, key, yes):
        s = self.sym(ref)
        find1(s, key)[1] = A('yes' if yes else 'no')

    def rect(self, x0, y0, x1, y1, dashed=True):
        self._insert([A('polyline'), [A('pts')] + [[A('xy'), A(fmt(x)), A(fmt(y))] for x, y in
                                                    [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]],
                      [A('stroke'), [A('width'), A('0')], [A('type'), A('dash' if dashed else 'default')]],
                      [A('uuid'), uid()]])

    def save(self, path=None):
        open(path or self.path, 'w').write(dump(self.t) + '\n')
