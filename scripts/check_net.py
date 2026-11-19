"""ERC-lite: compare KiCad-exported netlist with design intent; flag single-node nets and unconnected IC pins."""
from kilib import parse, name
import design, collections, sys

net = parse(open(sys.argv[1] if len(sys.argv) > 1 else 'afe.net').read())
nets = [e for e in net if isinstance(e, list) and name(e) == 'nets'][0]
got = {}
for n in nets[1:]:
    nm = [e for e in n if isinstance(e, list) and name(e) == 'name'][0][1][1].lstrip('/')
    nodes = set()
    for e in n:
        if isinstance(e, list) and name(e) == 'node':
            d = {x[0][1]: x[1][1] for x in e[1:] if isinstance(x, list)}
            nodes.add((d['ref'], d['pin']))
    got[nm] = nodes

want = collections.defaultdict(set)
for p in design.parts:
    for pin, n in p['nets'].items():
        if not p['ref'].startswith('#') and p.get('board', True): want[n].add((p['ref'], pin))  # off-board parts are not in the PCB netlist

bad = 0
for n in sorted(set(want) | set(got)):
    w = {x for x in want.get(n, set())}
    g = {x for x in got.get(n, set()) if not n.startswith('unconnected')}
    if n.startswith('unconnected') and not any(x in {q for v in want.values() for q in v} for x in got[n]): continue
    if n.startswith('unconnected') or n.startswith('Net-('):
        print('UNNAMED/UNCONNECTED NET', n, got[n]); bad += 1; continue
    if w != g:
        print('MISMATCH', n, 'missing', w - g, 'extra', g - w); bad += 1
    real = {r for r, _ in w if not r.startswith('#')}
    if len(w) < 2:
        print('SINGLE-NODE NET', n, w); bad += 1
print('nets:', len(got), 'problems:', bad)
