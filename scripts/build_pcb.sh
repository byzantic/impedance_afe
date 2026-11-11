set -e -o pipefail
python3 gen_pcb.py 2>/dev/null
python3 write_pro.py
python3 preroute.py 2>/dev/null
python3 -c "
import pcbnew, route
b=pcbnew.LoadBoard(route.F); print('fanout', route.fanout(b)); pcbnew.SaveBoard(route.F,b)" 2>/dev/null
python3 route.py --passes ${PASSES:-80} 2>&1 | grep -v swig | tail -4
python3 - 2>&1 <<'P' | grep -v swig
import pcbnew, route
b = pcbnew.LoadBoard('impedance_afe.kicad_pcb')
print('import', route.import_ses(b, 'afe.ses', skip={'GND', ''} | route.LOCK))
for t in b.GetTracks():
    if t.GetNetname() in route.LOCK: t.SetLocked(True)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard('impedance_afe_routed.kicad_pcb', b)
P
python3 cleanup.py impedance_afe_routed.kicad_pcb 2>&1 | grep -v swig
