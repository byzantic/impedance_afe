# CLAUDE.md: working brief for this repo

Analog front end for impedance / C-V (1 MHz), DLTS and electrochemistry. The outputs (V, I_HI, I_LO) go to a PicoScope. Read `README.md` first. It has the specs, block list, Pico control map and open items.

## Current state
- **Rev B schematic is done and checked.** It passes KiCad 10 ERC with 0 errors and 0 warnings after "Update Symbols from Library". The exported netlist matches the design intent (176 nets, 0 mismatches).
- **Rev B PCB: first pass placed + critical nets pre-routed and locked** (`scripts/layout/place.py` then `preroute.py`). Not autorouted yet. DRC: silkscreen only, parity 0.
- **ADC/DAC moved to a sub-board:** `adc_hat/` (own KiCad project, Pi Zero pHAT 65 × 30 mm, all SMD, JLC-assembled). It plugs onto main-board J16 (Pi 40-pin pinout, male) and J17 (2×6 analog), or stacks on a Pi Zero. Record: `scripts/hat/design.py`; schematic builder `scripts/hat/build_sch.py` (one-shot, overwrites hand edits); placement `scripts/hat/place.py`; BOM `scripts/hat/make_bom.py` → `docs/BOM_adc_hat.csv`.
- `revA/` holds the superseded Rev A (schematic plus routed board, converted to KiCad 9/10). Use it for reference only.

## Source of truth
- **The KiCad files at the repo root are the source.** Edit them with KiCad or the KiCad 10 tooling.
- **Do not run `scripts/gen_sch.py`, `scripts/make_lib.py` or anything in `revA/scripts/`.** They write KiCad 7 files and would overwrite the KiCad 10 schematic and project library. `scripts/design.py` is still a readable record of intent (nets, values, debug/precision parts).
- `scripts/check_net.py` is still useful. After any schematic change, run:
  `kicad-cli sch export netlist -o afe.net impedance_afe.kicad_sch && python3 scripts/check_net.py afe.net`
  It compares against `design.py`. If the schematic is changed on purpose, update `design.py` to match, or note that the check is retired.
- `scripts/schematic/` edits the existing KiCad schematic in place (wired drawing, power symbols, J14/J15). Its block scripts restart from a stripped state, so **re-running them overwrites hand edits in KiCad**; treat the KiCad file as the source from now on. `verify.sh REF.net` checks a schematic edit (net check, connectivity vs a reference netlist, ERC).
- Rails are power symbols (global nets `GND`, `+15V`, `-15V`, `+5V`, `+3V3`, `+3V3A`, `+3V3D`, `PICO_GND`); every other net is a local label (`/NAME`). RV1/RV2 are off-board panel pots (excluded from the board) on J14/J15.
- Project library `afe` (`afe.kicad_sym`, `afe.pretty/`): Pico 2 symbol and footprint, ADS131M04 and DAC80501 symbols, and the `DIP-8_SOIC-8_Combo` op-amp footprint. `adc_hat/sym-lib-table` points at `../afe.kicad_sym`.
- HAT check: `kicad-cli sch export netlist -o hat.net adc_hat/adc_hat.kicad_sch`, then run `scripts/check_net.py` with `scripts/hat` first on `sys.path` (so it imports the HAT `design.py`).

## Owner's preferences
- Short responses with full technical detail. The owner is an experienced EE. Don't fabricate; ask when unsure.
- **2-layer, JLCPCB** rules: 0.15 mm minimum track/space, 0.3 mm drill / 0.6 mm via. Use 0.25 mm default track and clearance.
- **Through-hole** on the main board everywhere except the SOIC half of the op-amp combo footprints. The ADC/DAC HAT is all SMD and JLC-assembled (its two sockets are THT on the bottom).
- Keep fab outputs (Gerbers, CPL, JLC BOM, PDFs) **out of the repo**; they go in GitHub Releases. `docs/BOM_revB.csv` is a design document and stays.
- Commit on `main` only when asked. The owner converts and edits in KiCad 10.

## Layout brief (Rev B)
**Board:** larger than Rev A's 150 × 110 mm. Expect roughly 180–220 × 130–150 mm: 10 BNCs, 21 reed relays, DIP parts, a socketed Pico. Two layers, with the bottom layer a mostly unbroken ground plane.

**Edge placement (connectors on two opposite edges only, for an enclosure with end panels)**
- **Front (bottom):** CE, RE, GUARD, WE, I_LO, I_HI, V_OUT. I_LO/I_HI/V_OUT lanes must stay right of the SUM_HI bus end (no crossings).
- **Back (top):** J1 power, BIAS/PULSE + AC PROBE (summer U9/U10 below them), Pico USB, SYNC_IN, J13, the ADC/DAC HAT (back-right corner).
- **Power:** J1 terminal block. The L7805 (≈1.5 W) gets room for a clip-on heatsink.
- **Mounting holes:** H1 (GND, by J1) is the only chassis bond; H2–H9 isolated M3 NPTH; H10–H13 M2.5 HAT standoffs.

**Critical nodes. Hand-route these first, then lock them.**
1. **SUM_HI (WE / U5 pin 2):**
   - shortest possible route from the WE BNC to U5 −IN, with the Rf/Cf networks (R41–R46, C41–C46), the steering transistors Q1/Q2, the null injection relays K15/K16 and the cal relays K11/K13 clustered around it
   - surround it with a guard ring at ground (it's a virtual ground) and remove solder mask over the ring
   - no other nets inside the ring
   - leave room for an optional PTFE standoff for the 100M range
2. **RE_IN (U2 pin 3):** R19 → U2 +IN, short, with a **driven guard on RE_BUF** (the U2 output) around it, on both layers if practical. The J5 RE BNC shell is GUARD (driven by U3), not ground.
3. **Range relays K1–K6:** on the **output side**. FBn nodes run to the relay contacts and IHI_OUT runs as a bus to every relay. Keep the FBn traces short and away from the coil drive lines.
4. **Combo footprints (all op-amps):** same-numbered DIP and SOIC pads are separate pads in the footprint and **must be joined with copper**. On U2 and U5 keep the pin 2/3 joins as short as possible, because they add capacitance and leakage to the sensitive inputs.
5. **Nuller:** NULLC_INJ and NULLG_INJ run from K15/K16 into SUM_HI. Keep C18/C19 close to the relays. The 1 MHz null path should be short and away from I_HI.

**Grounding**
- Star point near J1, with separate returns from the analog area and the digital corner.
- PICO_GND joins GND only through FB5 (JP5 can hard-tie it). Don't let the Pico ground pour merge into the analog plane except at that point.
- No SPI, clock (GP21 / X1 → JP6 → ADC_CLK) or relay-coil traces through the input area.

**Relays**
- Coils are driven high-side by U22/U23 (KD0–KD15). Coil pin 5 goes to GND.
- Route the coil lines along the digital side, away from SUM_HI and RE_IN.
- Reed relay pinout (Standex/Meder SIL): contact on 1–7, coil on 3–5. Not yet confirmed against the specific part.

**Net classes to set up:** Power (±15 V, +5 V, raw rails: 0.6 mm), HighZ (SUM_HI, SUM_LO, RE_IN, RE_BNC, FB1–FB6, NULLC_INJ, NULLG_INJ: 0.5 mm clearance), Default (0.25/0.25).

## How Rev A was laid out (a method that worked)
1. Place everything by script from a coordinate table. Check courtyard overlaps with DRC and iterate.
2. Hand-route the precision nets (sum node, feedback, IHI bus, RE input) and **lock** them.
3. Add GND fanout vias from SMD ground pads next to the pads, collision-checked.
4. Export Specctra DSN with the zones removed and the **GND net class ignored** (`-inc GNDc`), so the planes carry ground. Autoroute with Freerouting (`java -jar freerouting.jar -de x.dsn -do x.ses -mp 80 -inc GNDc`). Import the SES and refill the zones.
5. Clean up dangling and duplicate segments, then rerun DRC. Loop until there are 0 clearance errors and 0 unconnected.

Rev A used KiCad 7's SWIG `pcbnew` Python module. **KiCad 10 may not ship it** (KiCad is moving to the IPC API: `kicad-python`/`kipy`, with KiCad running and the API server enabled). Check what's available first. Alternatives: the IPC API, or editing `.kicad_pcb` S-expressions directly and verifying with `kicad-cli pcb drc`. Always verify with `kicad-cli pcb drc` and render with `kicad-cli pcb export svg` to look at the result.

## Verification before calling layout done
- `kicad-cli pcb drc --schematic-parity` clean: 0 errors, 0 unconnected, no parity mismatches.
- Visual check of renders: input area, guard rings, star ground, digital corner.
- Pad-to-pad joins present on every combo footprint.
- Report anything not done or not verified. Don't claim DRC is clean without running it.

## Open items (from the README; don't silently resolve them)
DAC80501 SPI2C level for SPI mode (JP4) · reed relay pinouts · Coto relay footprint for the precision 10M/100M ranges · 2N3904 C-B leakage · RP2350 GPIO pull-down erratum (4.7 k pulls fitted) · PI loop tuning · firmware not yet written.
