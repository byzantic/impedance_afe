import pcbnew, sys
f = sys.argv[1]
b = pcbnew.LoadBoard(f)
def key(p): return (round(p.x / 1000), round(p.y / 1000))
removed = 0
for it in range(10):
    tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']
    vias = {key(v.GetPosition()): v.GetNetname() for v in b.GetTracks() if v.GetClass() == 'PCB_VIA'}
    pads = [(p, p.GetNetname()) for p in b.GetPads()]
    ends = {}
    seen = set(); dup = []
    for t in tracks:
        k = (t.GetLayer(), t.GetNetname(), tuple(sorted([key(t.GetStart()), key(t.GetEnd())])))
        if k in seen: dup.append(t); continue
        seen.add(k)
        for p in (t.GetStart(), t.GetEnd()):
            ends.setdefault((t.GetLayer(), key(p)), []).append(t)
    bad = list(dup)
    for t in tracks:
        if t in dup: continue
        for p in (t.GetStart(), t.GetEnd()):
            kp = key(p)
            ok = len(ends.get((t.GetLayer(), kp), [])) > 1 or vias.get(kp) == t.GetNetname()
            if not ok:
                ok = any(n == t.GetNetname() and pad.IsOnLayer(t.GetLayer()) and pad.HitTest(p) for pad, n in pads)
            if not ok:
                # T-junction onto another track's interior
                ok = any(o is not t and o.GetLayer() == t.GetLayer() and o.GetNetname() == t.GetNetname() and o.HitTest(p, 1000) for o in tracks)
            if not ok: bad.append(t); break
    if not bad: break
    for t in bad: b.Delete(t); removed += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(f, b)
print('removed', removed)
