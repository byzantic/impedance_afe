import pcbnew, json
import design

FPDIR = '/usr/share/kicad/footprints'
OX, OY = 50, 50          # board origin offset (mm)
W, H = 150, 110
def mm(v): return pcbnew.FromMM(v)
def V(x, y): return pcbnew.VECTOR2I(mm(x + OX), mm(y + OY))

# ref: (x, y, rot)  board coords, y down
PL = {
    # power (top-left)
    'J1': (5, 8, 0), 'D1': (24, 20, 0), 'D2': (24, 27, 180),
    'C1': (6, 22, 90), 'C2': (6, 32, 270), 'FB1': (31, 20, 0), 'FB2': (31, 27, 0),
    'C3': (37, 20, 90), 'C4': (37, 27, 90), 'U8': (15, 41, 0), 'C5': (6, 41, 90), 'C6': (24, 41, 90),
    'C29': (40, 33, 90), 'C30': (44, 33, 90),
    # input / control amp (left)
    'J2': (30, 12.7, 0), 'R1': (40, 13, 90), 'JP1': (44, 13, 90), 'R2': (48, 18, 90), 'R3': (30, 36, 90),
    'U1': (22, 68, 90), 'C10': (25, 62, 0), 'C11': (25, 74, 0),
    'C9': (14, 60, 0), 'R6': (14, 63, 0), 'R5': (28, 52, 0),
    'K6': (7, 88, 90), 'K7': (13, 88, 90), 'R4': (22, 82, 90),
    'J3': (22, 97.3, 180), 'K8': (36, 72, 270),
    # RE buffer / guard / vout (middle)
    'J4': (46, 97.3, 180), 'R7': (46, 88, 90), 'U2': (46, 78, 90), 'C12': (42, 72, 0), 'C13': (51, 84, 0),
    'U3': (60, 76, 90), 'C14': (57, 70, 0), 'C15': (64, 82, 0), 'R9': (66, 88, 90), 'J5': (68, 97.3, 180),
    'R10': (52, 46, 90), 'R11': (56, 46, 90), 'U4': (56, 34, 90), 'C16': (60, 28, 0), 'C17': (60, 40, 0),
    'R12': (50, 24, 90), 'J6': (55, 12.7, 0),
    # relay driver (top middle)
    'J10': (74, 3.5, 0), 'U7': (86, 30, 0), 'C31': (86, 20, 0),
    # high-gain TIA (right)
    'J7': (112, 97.3, 180), 'U5': (112, 76, 90), 'C18': (109.2, 69.6, 0), 'C19': (116.5, 76, 90),
    'R21': (106, 81.5, 180), 'C21': (106, 83.7, 180), 'R22': (106, 85.9, 180), 'C22': (106, 88.1, 180),
    'R23': (119, 81.5, 0), 'C23': (119, 83.9, 0), 'R24': (119, 86.3, 0), 'C24': (119, 88.7, 0),
    'R25': (119, 91.1, 0), 'C25': (119, 93.3, 0),
    'K1': (105, 66, 90), 'K2': (98, 66, 90), 'K3': (119, 66, 90), 'K4': (126, 66, 90), 'K5': (133, 66, 90),
    'R14': (139, 50, 270), 'J8': (134, 97.3, 180),
    'D3': (108.5, 91.5, 180),
    # low-gain TIA
    'U6': (93, 80, 90), 'R15': (93, 86, 0), 'C26': (93, 88.2, 0), 'C27': (89, 74, 0), 'C28': (98, 85, 90),
    'R16': (86, 86, 90), 'J9': (90, 97.3, 180),
    'H1': (4, 105, 0), 'H2': (146, 105, 0), 'H3': (146, 4, 0), 'H4': (42, 4, 0),
}
for n in range(1, 9):
    PL[f'R{40+n}'] = (66 + (n - 1) * 2.0 if False else 70, 20 + (n - 1) * 2.2, 0)
for n in range(1, 9):
    PL[f'D{10+n}'] = (100, 20 + (n - 1) * 2.6, 0)

board = pcbnew.BOARD()
ds = board.GetDesignSettings()
board.SetCopperLayerCount(2)
ds.SetBoardThickness(mm(1.6))

nets = {}
def net(n):
    if n not in nets:
        ni = pcbnew.NETINFO_ITEM(board, n); board.Add(ni); nets[n] = ni
    return nets[n]

sym_uuid = json.load(open('sym_uuid.json'))
for p in design.parts:
    if p['ref'].startswith('#'): continue
    lib, name = p['fp'].split(':')
    fp = pcbnew.FootprintLoad(f'{FPDIR}/{lib}.pretty', name)
    assert fp, p['fp']
    fp.SetReference(p['ref']); fp.SetValue(p['value'])
    fp.SetFPIDAsString(p['fp']) if hasattr(fp, 'SetFPIDAsString') else None
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetPath(pcbnew.KIID_PATH('/' + sym_uuid[p['ref']]))
    x, y, r = PL[p['ref']]
    fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(r)
    for pad in fp.Pads():
        if (p['ref'], pad.GetNumber()) in {('K6', '5'), ('J10', '9'), ('J10', '10'), ('K7', '5'), ('K8', '5'), ('U2', '2')} or p['ref'].startswith('K') and pad.GetNumber() == '5':
            pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    if p['dnp']: fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)
    padnums = set()
    for pad in fp.Pads():
        num = pad.GetNumber(); padnums.add(num)
        if num in p['nets']: pad.SetNet(net(p['nets'][num]))
    assert set(p['nets']) <= padnums, (p['ref'], set(p['nets']) - padnums)
    fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); fp.Reference().SetTextThickness(mm(0.12))
    fp.Value().SetVisible(False)
    board.Add(fp)

# outline
corners = [(0, 0), (W, 0), (W, H), (0, H)]
for i in range(4):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(*corners[i])); s.SetEnd(V(*corners[(i + 1) % 4])); s.SetWidth(mm(0.1)); board.Add(s)

def zone(netname, layer, pts, prio=0, clearance=0.3):
    z = pcbnew.ZONE(board); z.SetLayerSet(pcbnew.LSET(layer)); z.SetNet(net(netname))
    ol = z.Outline(); ol.NewOutline()
    for x, y in pts: ol.Append(mm(x + OX), mm(y + OY))
    z.SetAssignedPriority(prio) if hasattr(z, 'SetAssignedPriority') else z.SetPriority(prio)
    z.SetLocalClearance(mm(clearance)); z.SetMinThickness(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z); return z

m = 0.4
full = [(m, m), (W - m, m), (W - m, H - m), (m, H - m)]
zone('GND', pcbnew.F_Cu, full, 0)
zone('GND', pcbnew.B_Cu, full, 0)
# driven guard (RE_BUF) under/around RE input path, both layers
gx0, gy0, gx1, gy1 = 43.6, 79.2, 49.2, 90.2
zone('RE_BUF', pcbnew.F_Cu, [(gx0, gy0), (gx1, gy0), (gx1, gy1), (gx0, gy1)], 2, 0.4)

ds.m_TrackMinWidth = mm(0.15); ds.m_ViasMinSize = mm(0.6); ds.m_MinThroughDrill = mm(0.3)
pcbnew.SaveBoard('impedance_afe.kicad_pcb', board)
print('footprints', len(board.GetFootprints()), 'nets', len(nets))
