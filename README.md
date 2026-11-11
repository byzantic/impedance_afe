# Impedance / C-V / DLTS / Electrochem AFE — Rev A (generated)

Fabrication outputs (Gerbers, JLCPCB BOM/CPL, schematic PDF, renders) are attached to each [GitHub Release](../../releases), not stored in the repo.

KiCad 7 format (opens in KiCad 8/9, which will offer to upgrade the files). 2-layer, 150 × 110 mm, 1.6 mm FR4, JLCPCB rules (0.25 mm default track/clearance, 0.6/0.3 mm vias).

## Architecture
| Block | Parts | Function |
|---|---|---|
| Power | J1, D1/D2, FB1/FB2, U8 | External ±15 V (bench supply), Schottky reverse protection, ferrite + bulk filtering, 78M05 → +5 V for relays and logic |
| Drive | J2 → R3 → U1 (OPA828), R4 → J3 (CE) | **Device mode** (K6 on): U1 is a follower, CE = VIN, RE senses the DUT. **Potentiostat** (K7 on, K6 off): PI loop, R5 = 10k, C9 = 100p, R6 = 1k zero, drives CE so that V_RE = VIN |
| RE / guard | J4 → R7 → U2 (electrometer follower), U3 → R9 → J5 and the J4 shell | Driven guard on the RE cable shield and the GUARD BNC; RE_BUF copper guard around U2's input |
| V monitor | R10/R11 (0.1 %) → U4 → J6 | V_OUT = V_RE / 2, back-terminated in 49.9 Ω |
| Hi-gain TIA | J7 (WE) → U5, R21–R25 ∥ C21–C25, K1–K5 | Virtual ground on WE. Ranges 10k / 100k / 1M / 10M / 100M (±5 V full scale = 500 µA … 50 nA). Relays sit on the output side, so off-relay leakage shows up as a gain error, not an offset |
| Lo-gain TIA | D3 (BAV199 antiparallel) → U6, R15 = 499 Ω ∥ 68 p | Above about V_sat/R_f, U5 saturates, WE rises about 0.6 V and the current diverts to U6 (10 mA full scale). Needs no sync and adds no charge injection |
| Control | J10 → U7 (74HCT541) → coils, D11–D18 | High-side coil drive, so off coils sit at 0 V (keeps coil-to-contact leakage out of the summing node) |

Output polarity: I_HI = −I_WE·R_f and I_LO = −I_WE·499 Ω, where I_WE is current flowing *into* the WE terminal.

## GPIO header J10 (3.3 V logic OK; 100k pulls to +5 V or GND)
| Pin | Signal | Relay | Default |
|---|---|---|---|
| 1 | CTL1 | K1 10k range | off |
| 2 | CTL2 | K2 100k | off |
| 3 | CTL3 | K3 1M | **on** |
| 4 | CTL4 | K4 10M | off |
| 5 | CTL5 | K5 100M | off |
| 6 | CTL6 | K6 DEV (follower) | **on** |
| 7 | CTL7 | K7 PSTAT (PI loop) | off |
| 8 | CTL8 | K8 RE_LOCAL (RE tied to CE on the board) | **on** |
| 9, 10 | GND | | |
Exactly one range should be on at a time; use break-before-make, ~2 ms. Keep ≤ 4 coils on at once (74HCT541 Icc limit). For potentiostat mode: CTL6 = 0, CTL7 = 1, CTL8 = 0.

## Verification status
- Netlist: the KiCad-exported netlist was checked against the design intent by script (69 nets, 0 mismatches). **KiCad's own ERC was not run** (KiCad 7 has no headless ERC). Run ERC in KiCad before ordering.
- PCB DRC (KiCad 7): 0 clearance errors, 0 unconnected. The remaining items are cosmetic silkscreen overlaps/edge clips and "footprint not in library table" notices.
- Not simulated. Loop stability (especially the PI potentiostat with a real cell) and the TIA compensation values are first-pass hand calculations.

## Things to check / known limitations
1. **Reed relay pinout** assumes Standex/Meder SIL: pins 1 and 7 are the contact, pins 3 and 5 are the coil. Confirm against the datasheet of the part you buy.
2. Generic SIP-1A05 insulation is specified at only ≥1e10 Ω. That is up to ~1 % gain error on the 100M range (calibrate it out), or fit Coto 9007 / Pickering parts (≥1e12) on K4/K5.
3. During a DLTS fill pulse the WE node sits about 0.6 V off ground (diode drop), so the DUT voltage is lower by that amount while I_LO is active.
4. At 1 MHz C-V, expect a few degrees of phase shift in the V and I chains. Calibrate with reference R/C loads (open/short/load) for C-V.
5. PI compensation (C9/R6) and C26 may need tuning for your cells and cables.
6. Most passives have no LCSC numbers. Use JLC's BOM matcher. Verified: OPA828IDR = C1850247, reed relay = C7316298. The 100 MΩ (R25) and 0.47 pF (C24) values may need sourcing.
7. The BNC footprint is the Amphenol B6252HB right-angle. Check that your BNCs match its pin pattern. JLC CPL rotations for SOT-23/SOIC may need fixing in the JLC preview.
8. The pull-ups go to +5 V. With a 3.3 V MCU high, about 17 µA flows into the GPIO clamp (harmless for most MCUs). Fit 3.3 V-referenced pull-ups if you prefer.
9. The pulse-sync input is not needed with diode steering, so none was fitted.

## Regenerating
Everything comes from `scripts/design.py`. Run the scripts from the repo root with KiCad 7's Python (`pcbnew`) and Freerouting. `route.py` expects the jar at `/root/tools/fr.jar`, so edit that path first.
```
python3 scripts/gen_sch.py          # schematic + sym_uuid.json
kicad-cli sch export netlist -o afe.net impedance_afe.kicad_sch && python3 scripts/check_net.py
PASSES=80 bash scripts/build_pcb.sh # place, pre-route critical nets, autoroute, clean up
```
Note: the autoroute pass is not deterministic. The board in this repo is the checked result; regenerating will change the routing.
