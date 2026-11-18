import json
def cls(name, w, clr, via=0.6, drill=0.3):
    return {"name": name, "clearance": clr, "track_width": w, "via_diameter": via, "via_drill": drill,
            "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.2, "line_style": 0, "wire_width": 6, "bus_width": 12,
            "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}
power = ["+15V", "-15V", "+5V", "P15_RAW", "N15_RAW", "+15V_IN", "-15V_IN"]
highz = ["SUM_HI", "SUM_LO", "RE_IN", "RE_BNC", "FB1", "FB2", "FB3", "FB4", "FB5"]
p = json.load(open("impedance_afe.kicad_pro"))
p.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {}).update({
    "min_clearance": 0.15, "min_track_width": 0.15, "min_via_diameter": 0.6, "min_through_hole_diameter": 0.3,
    "min_hole_clearance": 0.25, "min_hole_to_hole": 0.5, "min_copper_edge_clearance": 0.3})
p["net_settings"] = {"classes": [cls("Default", 0.25, 0.25), cls("Power", 0.6, 0.25, 0.8, 0.4),
                                 cls("GNDc", 0.6, 0.25, 0.6, 0.3), cls("HighZ", 0.3, 0.5)],
   "meta": {"version": 3}, "net_colors": None, "netclass_assignments": None,
   "netclass_patterns": [{"netclass": "Power", "pattern": n} for n in power] + [{"netclass": "HighZ", "pattern": n} for n in highz]
                        + [{"netclass": "GNDc", "pattern": "GND"}]}
json.dump(p, open("impedance_afe.kicad_pro", "w"), indent=2)
