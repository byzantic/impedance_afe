"""Block redraw helpers: strip a block's pin stubs/labels/rail symbols, then draw wired nets.

A Drawing collects orthogonal wire polylines, splits segments at T-points, adds junctions where
three or more ends meet (pins count as ends), and emits everything into the Sch.
"""
from sch import *  # noqa
import os, sys


def _pt(x, y):
    return (snap(x), snap(y))


def strip(s, refs):
    """Remove the stub wire on every pin of `refs`, and the label / power symbol / no-connect at its ends."""
    pins = {}
    for r in refs:
        for n, p in s.pins(r).items():
            pins[_pt(*p)] = (r, n)
    wires = s.items('wire')
    gone = set()
    far = set()
    for w in wires:
        a, b = [_pt(num(xy[1]), num(xy[2])) for xy in find(find1(w, 'pts'), 'xy')]
        if a in pins or b in pins:
            far.add(b if a in pins else a)
            s.remove(w); gone.add('wire')
    for lab in s.items('label'):
        a = find1(lab, 'at')
        if _pt(num(a[1]), num(a[2])) in far:
            s.remove(lab)
    for sym in s.symbols():
        if s.ref(sym).startswith('#PWR'):
            x, y, _ = s.at(sym)
            if _pt(x, y) in far:
                s.remove(sym)
    for nc in s.items('no_connect'):
        a = find1(nc, 'at')
        if _pt(num(a[1]), num(a[2])) in pins:
            s.remove(nc)


class Drawing:
    def __init__(self, s):
        self.s = s
        self.segs = []
        self.pinpts = set()

    def w(self, *pts):
        pts = [_pt(*p) for p in pts]
        for a, b in zip(pts, pts[1:]):
            if a != b:
                assert a[0] == b[0] or a[1] == b[1], ('diagonal', a, b)
                self.segs.append((a, b))

    def pins_of(self, refs):
        for r in refs:
            for p in self.s.pins(r).values():
                self.pinpts.add(_pt(*p))

    def emit(self):
        # split segments at any other segment end lying on their interior
        ends = {p for sg in self.segs for p in sg}
        out = []
        for a, b in self.segs:
            cuts = [p for p in ends | self.pinpts if p not in (a, b) and _on(p, a, b)]
            pts = sorted([a, b] + cuts, key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2)
            out += list(zip(pts, pts[1:]))
        cnt = {}
        for a, b in out:
            cnt[a] = cnt.get(a, 0) + 1; cnt[b] = cnt.get(b, 0) + 1
        for p in self.pinpts:
            if p in cnt:
                cnt[p] += 1
        for a, b in out:
            self.s.wire([a, b])
        for p, c in cnt.items():
            if c >= 3:
                self.s.junction(*p)
        return len(out)


def _on(p, a, b):
    if a[0] == b[0] == p[0]:
        return min(a[1], b[1]) < p[1] < max(a[1], b[1])
    if a[1] == b[1] == p[1]:
        return min(a[0], b[0]) < p[0] < max(a[0], b[0])
    return False


# ====================================================================== block builder
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import design  # noqa: E402

RAILS = {'GND': 'power:GND', '+15V': 'power:+15V', '-15V': 'power:-15V', '+5V': 'power:+5V',
         '+3V3': 'power:+3V3', '+3V3A': 'power:+3V3', '+3V3D': 'power:+3V3', 'PICO_GND': 'power:GND'}
PINNET = {(p['ref'], pin): n for p in design.parts for pin, n in p['nets'].items()}
ANG = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}


def orient(lib_id, dv):
    body = (0, 1) if lib_id == 'power:GND' else (0, -1)
    for a in (0, 90, 180, 270):
        if rot(*body, a) == tuple(dv):
            return a
    raise ValueError(dv)


class Block:
    def __init__(self, s, refs):
        self.s, self.refs = s, list(refs)
        strip(s, self.refs)
        self.d = Drawing(s)
        self.named = set()      # points carrying a label / power symbol
        self.ncs = set()
        self.fset = set()       # refs whose fields were placed explicitly

    def pl(self, ref, x, y, r=0, mirror=None):
        assert abs(snap(x) - x) < 1e-6 and abs(snap(y) - y) < 1e-6, ('off-grid placement', ref, x, y)
        self.s.move(ref, x, y, r, mirror)

    def p(self, ref, n):
        return _pt(*self.s.pin(ref, n))

    def w(self, *pts):
        self.d.w(*pts)

    def net(self, ref, n):
        return PINNET.get((ref, str(n)))

    def rail(self, net, pt, dv=(0, 1)):
        lid = RAILS[net]
        self.s.power(lid, net, *pt, orient(lid, dv))
        self.named.add(_pt(*pt))

    def lab(self, net, pt, dv=(1, 0)):
        self.s.label(net, *pt, ANG[tuple(dv)])
        self.named.add(_pt(*pt))

    def nc(self, ref, n):
        p = self.p(ref, n); self.s.no_connect(*p); self.ncs.add(p)

    def term(self, ref, n, L=2.54, dv=None, net=None):
        """stub from the pin, then power symbol (rails) or label; no-connect if the pin is unused"""
        net = net or self.net(ref, n)
        p = self.p(ref, n)
        if net is None:
            self.nc(ref, n); return
        dv = tuple(dv or self.s.pin_dir(ref, n))
        q = _pt(p[0] + dv[0] * L, p[1] + dv[1] * L)
        if L:
            self.w(p, q)
        (self.rail if net in RAILS else self.lab)(net, q, dv)

    def at_pin(self, ref, n, dv=None):
        """power symbol / label directly on the pin (no stub)"""
        net = self.net(ref, n)
        self.term(ref, n, 0, dv, net)

    def F(self, ref, ref_xy, val_xy, just='left'):
        s = self.s
        sym = s.sym(ref)
        r = s.at(sym)[2] % 360
        a = (-r) % 360 if r in (90, 270) else 0
        if (r == 180) != (s.mirrored(sym) == 'y'):   # KiCad mirrors justification for these
            just = {'left': 'right', 'right': 'left'}.get(just, just)
        s.field_at(ref, 'Reference', *ref_xy, angle=a, justify=just)
        s.field_at(ref, 'Value', *val_xy, angle=a, justify=just)
        self.fset.add(ref)

    def autofields(self):
        """rotation-aware default Reference/Value placement for simple parts"""
        s = self.s
        for ref in self.refs:
            if ref in self.fset:
                continue
            sym = s.sym(ref)
            lid = val(find1(sym, 'lib_id'))
            x, y, r = s.at(sym)
            r = int(r) % 360
            vert = r in (0, 180)
            if ref.startswith('#FLG'):
                for p in find(sym, 'property'):
                    if val(p) == 'Value':
                        eff = find1(p, 'effects')
                        if not find(eff, 'hide'):
                            eff.append([A('hide'), A('yes')])
                continue
            if lid in ('Device:R', 'Device:C', 'Device:C_Polarized', 'Device:FerriteBead', 'Device:R_Potentiometer'):
                dx = 3.81 if lid in ('Device:C_Polarized', 'Device:FerriteBead', 'Device:R_Potentiometer') else 2.54
                if vert:
                    self.F(ref, (x + dx, y - 1.27), (x + dx, y + 1.27), 'left')
                else:
                    if lid == 'Device:FerriteBead':
                        self.F(ref, (x, y - 6.35), (x, y - 3.81), None)
                    else:
                        self.F(ref, (x, y - 2.54), (x, y + 3.175), None)
            elif lid.startswith('Diode:'):
                if vert:
                    self.F(ref, (x, y - 3.175), (x, y + 3.81), None)
                else:
                    self.F(ref, (x + 2.54, y - 1.27), (x + 2.54, y + 1.27), 'left')
            elif lid.startswith('Relay:'):
                if r in (0, 180):
                    self.F(ref, (x - 8.89, y - 1.27), (x - 8.89, y + 1.27), 'right')
                elif r == 90:
                    self.F(ref, (x + 10.16, y - 1.27), (x + 10.16, y + 1.27), 'left')
                else:
                    self.F(ref, (x, y + 8.89), (x, y + 11.43), None)
            elif lid == 'Connector:Conn_Coaxial' and r != 0:
                self.F(ref, (x + 3.81, y - 1.27), (x + 3.81, y + 1.27), 'left')
            elif lid.startswith('Connector_Generic:Conn_01') or lid.startswith('Connector:Screw'):
                if r == 0:
                    self.F(ref, (x + 3.81, y - 1.27), (x + 3.81, y + 1.27), 'left')
                elif r == 180:
                    self.F(ref, (x - 3.81, y - 1.27), (x - 3.81, y + 1.27), 'right')
                else:
                    self.F(ref, (x + 5.08, y + 1.27), (x + 5.08, y + 3.81), 'left')

    def finish(self, auto=True):
        s, d = self.s, self.d
        self.autofields()
        touched = {p for sg in d.segs for p in sg} | self.named | self.ncs
        if auto:
            for r in self.refs:
                for n, p in s.pins(r).items():
                    p = _pt(*p)
                    if p not in touched and not any(_on(p, a, b) for a, b in d.segs):
                        self.term(r, n)
        pinmap = {}
        for r in self.refs:
            for n, p in s.pins(r).items():
                pinmap.setdefault(_pt(*p), []).append((r, n))
        d.pinpts |= set(pinmap)
        # auto-name wired nets that carry no label / power symbol
        pts = {p for sg in d.segs for p in sg} | set(pinmap) | self.named
        par = {p: p for p in pts}

        def f(x):
            while par[x] != x:
                par[x] = par[par[x]]; x = par[x]
            return x
        for a, b in d.segs:
            par[f(a)] = f(b)
            for p in pts:
                if p not in (a, b) and _on(p, a, b):
                    par[f(p)] = f(a)
        groups = {}
        for p in pts:
            groups.setdefault(f(p), set()).add(p)
        for g in groups.values():
            nets = {self.net(r, n) for p in g for r, n in pinmap.get(p, [])} - {None}
            assert len(nets) <= 1, ('short in drawing', nets, sorted(g)[:4])
            if not nets or g & self.named:
                continue
            net = nets.pop()
            assert net not in RAILS, ('rail wired without a power symbol', net, sorted(g)[:3])
            segs = [(a, b) for a, b in d.segs if a in g and b in g]
            if not segs:
                continue
            L = lambda sg: abs(sg[0][0] - sg[1][0]) + abs(sg[0][1] - sg[1][1])  # noqa
            hor = [sg for sg in segs if sg[0][1] == sg[1][1] and L(sg) >= 5.08]
            a, b = max(hor or segs, key=L)
            if a[1] == b[1]:
                x0, x1 = sorted((a[0], b[0]))
                q = _pt(x0 + min(1.27, (x1 - x0) / 2), a[1]); s.label(net, *q, 0)
            else:
                y0, y1 = sorted((a[1], b[1]))
                q = _pt(a[0], y1 - min(1.27, (y1 - y0) / 2)); s.label(net, *q, 90)
            self.named.add(q)
        d.pinpts |= self.named
        return d.emit()
