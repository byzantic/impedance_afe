"""Shared helpers for the Rev B layout scripts (KiCad 9 SWIG pcbnew; run with /usr/bin/python3).

Board coordinates are mm, origin at the board's top-left corner, y down.
The board sits at (OX, OY) on the page.
"""
import os, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from kilib import parse  # noqa: E402

PCB = os.path.join(ROOT, 'impedance_afe.kicad_pcb')
SCH = os.path.join(ROOT, 'impedance_afe.kicad_sch')
FPDIR = '/usr/share/kicad/footprints'
OX, OY = 40.0, 30.0
W, H = 248.0, 150.0


def mm(v):
    return pcbnew.FromMM(v)


def V(x, y):
    return pcbnew.VECTOR2I(mm(x + OX), mm(y + OY))


def P(v):
    return (pcbnew.ToMM(v.x) - OX, pcbnew.ToMM(v.y) - OY)


# ---------------------------------------------------------------- netlist
def _h(e):
    return e[0][1] if isinstance(e, list) and e and isinstance(e[0], tuple) else None


def _find(e, key):
    return [c for c in e if isinstance(c, list) and _h(c) == key]


def _val(e):
    return e[1][1] if len(e) > 1 and isinstance(e[1], tuple) else ''


def read_netlist(fn):
    """-> comps {ref: dict(value, fp, path, dnp)}, nets {name: [(ref, pin)]}"""
    t = parse(open(fn).read())
    comps = {}
    for c in _find(_find(t, 'components')[0], 'comp'):
        ref = _val(_find(c, 'ref')[0])
        sp = _find(c, 'sheetpath')[0]
        sheet = _val(_find(sp, 'tstamps')[0])
        uuid = _val(_find(c, 'tstamps')[0])
        props = {_val(_find(p, 'name')[0]): (_val(_find(p, 'value')[0]) if _find(p, 'value') else '')
                 for p in _find(c, 'property')}
        comps[ref] = dict(value=_val(_find(c, 'value')[0]), fp=_val(_find(c, 'footprint')[0]),
                          path=sheet + uuid, dnp='dnp' in props, props=props)
    nets = {}
    for n in _find(_find(t, 'nets')[0], 'net'):
        nm = _val(_find(n, 'name')[0])
        nets[nm] = [(_val(_find(nd, 'ref')[0]), _val(_find(nd, 'pin')[0])) for nd in _find(n, 'node')]
    return comps, nets


def load_fp(fpid):
    lib, name = fpid.split(':')
    path = os.path.join(ROOT, 'afe.pretty') if lib == 'afe' else os.path.join(FPDIR, lib + '.pretty')
    fp = pcbnew.FootprintLoad(path, name)
    assert fp, fpid
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ---------------------------------------------------------------- board access
def pad_xy(b, ref, num, smd=None):
    """Board-mm position of pad `num` of `ref`. smd=True/False selects SMD/THT pad on combo footprints."""
    fp = b.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() != str(num):
            continue
        if smd is None or (p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD) == smd:
            return P(p.GetPosition())
    raise KeyError((ref, num, smd))


GLOBAL = {'GND', 'PICO_GND', '+15V', '-15V', '+5V', '+3V3', '+3V3A', '+3V3D'}   # power-symbol nets (no sheet prefix)


def N(name):
    """board net name: power-symbol nets are global ('GND'); every other net is a local label ('/NAME')"""
    if name.startswith('/') or name.startswith('unconnected') or name in GLOBAL:
        return name
    return '/' + name


def track(b, net, pts, w=0.25, layer=pcbnew.F_Cu, lock=True):
    ni = b.FindNet(N(net))
    assert ni, net
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if (x0, y0) == (x1, y1):
            continue
        t = pcbnew.PCB_TRACK(b)
        t.SetLayer(layer); t.SetWidth(mm(w)); t.SetNet(ni)
        t.SetStart(V(x0, y0)); t.SetEnd(V(x1, y1)); t.SetLocked(lock)
        b.Add(t); out.append(t)
    return out


def via(b, net, x, y, d=0.6, drill=0.3, lock=True):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(x, y)); v.SetWidth(mm(d)); v.SetDrill(mm(drill))
    v.SetNet(b.FindNet(N(net))); v.SetLocked(lock)
    b.Add(v)
    return v
