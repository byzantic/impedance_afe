import pcbnew, subprocess, math, sys, shutil
F = 'impedance_afe.kicad_pcb'
mm, tomm = pcbnew.FromMM, pcbnew.ToMM
OX, OY = 50, 50

def _segdist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)

def fanout(b):
    gnd = b.FindNet('GND')
    obst = []  # (kind, geom, netname)
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            bb = pad.GetBoundingBox(); obst.append(('box', (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()), pad.GetNetname()))
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_TRACK':
            obst.append(('seg', (t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetWidth() / 2), t.GetNetname()))
    def free(x, y, r):
        for k, g, n in obst:
            if n == 'GND': continue
            if k == 'box':
                dx = max(g[0] - x, 0, x - g[2]); dy = max(g[1] - y, 0, y - g[3])
                d = math.hypot(dx, dy)
            else:
                d = _segdist(x, y, *g[:4]) - g[4]
            if d < r: return False
        return True
    n = skipped = 0
    for fp in b.GetFootprints():
        if fp.GetReference() == 'U8': continue
        c = fp.GetPosition()
        for pad in fp.Pads():
            if pad.GetNetname() != 'GND' or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD: continue
            p = pad.GetPosition(); bb = pad.GetBoundingBox()
            dx, dy = p.x - c.x, p.y - c.y
            dirs = sorted([(1, 0), (-1, 0), (0, 1), (0, -1)], key=lambda u: -(u[0] * dx + u[1] * dy))
            placed = False
            for ux, uy in dirs:
                half = (bb.GetWidth() if ux else bb.GetHeight()) / 2
                for extra in (0.7, 1.1, 1.6):
                    vx, vy = int(p.x + ux * (half + mm(extra))), int(p.y + uy * (half + mm(extra)))
                    # via radius 0.3 + clearance 0.55 (covers HighZ 0.5)
                    if free(vx, vy, mm(0.85)) and all(_segdist(*q, p.x, p.y, vx, vy) > mm(0.75) for q in
                                                     [((g[0]+g[2])/2, (g[1]+g[3])/2) for k, g, nn in obst if k == 'box' and nn not in ('GND',)] if False) :
                        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(vx, vy)); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(gnd); b.Add(v)
                        t = pcbnew.PCB_TRACK(b); t.SetStart(p); t.SetEnd(pcbnew.VECTOR2I(vx, vy)); t.SetWidth(mm(0.4)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); b.Add(t)
                        obst.append(('box', (vx - mm(0.3), vy - mm(0.3), vx + mm(0.3), vy + mm(0.3)), 'GND'))
                        n += 1; placed = True; break
                if placed: break
            if not placed: skipped += 1; print('  no fanout for', fp.GetReference(), pad.GetNumber())
    return n, skipped

def import_ses(b, fn, skip=()):
    from kilib import parse, name
    t = parse(open(fn).read())
    def find(node, key):
        return [e for e in node if isinstance(e, list) and name(e) == key]
    routes = find(t, 'routes')[0]
    res = find(routes, 'resolution')[0]
    unit, div = res[1][1], float(res[2][1])
    scale = {'um': 1e-3, 'mm': 1.0, 'mil': 0.0254}[unit] / div   # -> mm
    lib = find(routes, 'library_out')
    padstacks = {}
    if lib:
        for ps in find(lib[0], 'padstack'):
            nm = ps[1][1]
            sh = find(ps, 'shape')[0][1]
            padstacks[nm] = float(sh[2][1]) * scale
    nw = find(routes, 'network_out')[0]
    nt = nv = 0
    for n in find(nw, 'net'):
        if n[1][1] in skip: continue
        net = b.FindNet(n[1][1])
        for w in find(n, 'wire'):
            path = find(w, 'path')[0]
            layer = pcbnew.F_Cu if path[1][1] == 'F.Cu' else pcbnew.B_Cu
            width = float(path[2][1]) * scale
            co = [float(x[1]) * scale for x in path[3:] if isinstance(x, tuple)]
            pts = [(co[i], -co[i + 1]) for i in range(0, len(co), 2)]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                tr = pcbnew.PCB_TRACK(b); tr.SetLayer(layer); tr.SetWidth(mm(width)); tr.SetNet(net)
                tr.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0))); tr.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1))); b.Add(tr); nt += 1
        for v in find(n, 'via'):
            ps = v[1][1]; x, y = float(v[2][1]) * scale, -float(v[3][1]) * scale
            vi = pcbnew.PCB_VIA(b); vi.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            dia = padstacks.get(ps, 0.6); vi.SetWidth(mm(dia)); vi.SetDrill(mm(0.4 if dia >= 0.8 else 0.3)); vi.SetNet(net); b.Add(vi); nv += 1
    return nt, nv

LOCK = {'SUM_HI', 'FB1', 'FB2', 'FB3', 'FB4', 'FB5', 'IHI_OUT', 'RE_IN'}
if __name__ == '__main__':
    passes = sys.argv[sys.argv.index('--passes') + 1] if '--passes' in sys.argv else '30'
    b = pcbnew.LoadBoard(F)
    for t in b.GetTracks():
        if t.GetNetname() == 'GND': t.SetLocked(True)
    for z in list(b.Zones()): b.Remove(z)
    pcbnew.ExportSpecctraDSN(b, 'afe.dsn')
    r = subprocess.run(['java', '-jar', '/root/tools/fr.jar', '-de', 'afe.dsn', '-do', 'afe.ses', '-mp', passes, '-inc', 'GNDc',
                        '--gui.enabled=false'], capture_output=True, text=True, timeout=3000)
    print('\n'.join(l for l in (r.stdout + r.stderr).splitlines() if 'pass' in l.lower() or 'unrouted' in l.lower() or 'complete' in l.lower())[-1500:])
    sys.stdout.flush(); import os; os._exit(0)
