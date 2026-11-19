"""Run kicad-cli DRC (with schematic parity) and summarise.  Usage: check.py [types-to-list ...] [--all]"""
import json, subprocess, sys, collections, os, tempfile
from common import PCB, ROOT

out = os.path.join(tempfile.gettempdir(), 'afe_drc.json')
subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--schematic-parity', '--severity-all',
                '--units', 'mm', '-o', out, PCB], cwd=ROOT, capture_output=True)
d = json.load(open(out))
want = [a for a in sys.argv[1:] if not a.startswith('--')]
cnt = collections.Counter(v['type'] for v in d['violations'])
print('violations:', dict(cnt))
print('unconnected:', len(d.get('unconnected_items', [])))
par = d.get('schematic_parity', [])
print('parity:', len(par), dict(collections.Counter(p['type'] for p in par)))
for p in par[:20]:
    print('  P', p['type'], p['description'], [i['description'] for i in p['items']])
for v in d['violations']:
    if v['type'] in want or '--all' in sys.argv:
        print(' ', v['type'], '|', ' <-> '.join(i['description'][:60] + ' @(%.1f,%.1f)' % (i['pos']['x'] - 40, i['pos']['y'] - 30)
                                         for i in v['items']))
