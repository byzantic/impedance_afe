#!/bin/bash
# Verify the schematic after an edit: netlist vs design.py, netlist vs a reference netlist (connectivity only), ERC.
# usage: verify.sh REF_NETLIST
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
T=$(mktemp -d)
kicad-cli sch export netlist -o "$T/new.net" "$ROOT/impedance_afe.kicad_sch" >/dev/null
(cd "$ROOT/scripts" && python3 check_net.py "$T/new.net" | tail -3)
python3 - "$1" "$T/new.net" <<'EOF'
import sys; sys.path.insert(0, sys.argv[0] and __import__('os').path.join(__import__('os').getcwd()))
import re
def nets(fn):
    s = open(fn).read()
    out = {}
    for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)', s, re.S):
        nodes = frozenset(re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)))
        out[nodes] = m.group(1)
    return out
a, b = nets(sys.argv[1]), nets(sys.argv[2])
same = set(a) == set(b)
renamed = sorted((a[k], b[k]) for k in set(a) & set(b) if a[k].lstrip('/') != b[k].lstrip('/'))
print('connectivity identical to reference:', same, '| nets', len(a), '->', len(b))
if not same:
    print('  only in ref:', [sorted(k) for k in set(a) - set(b)][:5]); print('  only in new:', [sorted(k) for k in set(b) - set(a)][:5])
print('net renames (beyond / prefix):', renamed[:20])
EOF
kicad-cli sch erc --format json -o "$T/erc.json" "$ROOT/impedance_afe.kicad_sch" >/dev/null
python3 - "$T/erc.json" <<'EOF'
import json, sys, collections
d = json.load(open(sys.argv[1]))
v = [x for s in d['sheets'] for x in s['violations']]
c = collections.Counter((x['type'], x['severity']) for x in v)
print('ERC:', dict(c))
for x in v:
    if x['type'] != 'lib_symbol_mismatch':
        print('  ', x['severity'], x['type'], x['description'], [i['description'] for i in x['items']][:3])
EOF
