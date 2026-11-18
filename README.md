# Impedance / C-V / DLTS / Electrochemistry Analog Front End: Rev B

**Status:** the Rev B **schematic** is done; **PCB layout has not been started.** The schematic is generated in KiCad 7 format. KiCad 9/10 opens it and offers to upgrade it. Rev A (schematic plus routed board, converted to KiCad 9/10) is kept in [`revA/`](revA/).

Fabrication outputs go in [GitHub Releases](../../releases), not in the repo. The parts list with debug and precision columns is in [`docs/BOM_revB.csv`](docs/BOM_revB.csv).

## Changes from Rev A
| Area | Rev A | Rev B |
|---|---|---|
| Drive input | single VIN BNC | **BIAS/PULSE** (DC) + **AC PROBE** (AC-coupled, ×1/×0.1 jumper) + **on-board 16-bit bias DAC**, summed (U9/U10) |
| C/G null | none | **vector nuller**: RV1 → fixed C (100 pF / 1 nF) and RV2 → fixed R (20 k / 2 k, AC-coupled), driven from the measured RE voltage |
| Calibration | none | T-switched on-board **10 k 0.1 %** and **100 pF 1 %** loads (CE_INT → WE) |
| Cell | always connected | **CELL relay** (K10) disconnects CE |
| High-gain ranges | 10k…100M | **1k**, 10k, 100k, 1M, 10M, 100M |
| V monitor | V_RE/2 only | V_OUT BNC switched by **VMODE**: DC (V_RE/2) or **AC ×10.1** (100 Hz HPF) |
| Control | 8 GPIOs → 74HCT541 | **Pico 2** (socketed), 16 lines → 2× TBD62783A source drivers, plus a fallback header |
| Digitiser | scope only | adds an on-board **ADS131M04** (4-ch simultaneous, 24-bit) for standalone potentiostat work |
| Parts | SMD | **through-hole** throughout, except DAC/ADC (JLC-placed) and the SOIC half of the op-amp footprints |
| Op-amp footprint | SOIC-8 | **DIP-8 + SOIC-8 combo** (`afe:DIP-8_SOIC-8_Combo`): fit one package |
| Steering diodes | BAV199 (SOT-23) | 2N3904 collector-base junctions (TO-92) |

## Specifications (design values, not measured)
| Parameter | Value |
|---|---|
| Supplies | external ±15 V (screw terminal). On board: +5 V (L7805) and +3.3 V (MCP1700). Estimated ≲300 mA from +15 V (relays + Pico), ≲120 mA from −15 V |
| DUT drive | ±10 V, ≥ ±20 mA (op-amp limited), 47 Ω series to CE |
| BIAS/PULSE input | DC-coupled, Z_in ≈ 9.1 kΩ (10 k to virtual ground ∥ 100 k). JP1 = 50 Ω termination |
| AC PROBE input | AC-coupled. ×1: Z_in ≈ 9.1 kΩ, corner 16 Hz. ×0.1: Z_in ≈ 50 kΩ, corner 1.6 Hz. JP2 = 50 Ω termination, JP3 = gain |
| Bias DAC | DAC80501M, 16-bit, +10.05 V … −10.05 V (≈0.31 mV/LSB), 0 V at midscale power-up; K21 connects it |
| High-gain TIA (±5 V out) | 1k: ±5 mA · 10k: ±500 µA · 100k: ±50 µA · 1M: ±5 µA · 10M: ±500 nA · 100M: ±50 nA |
| TIA feedback pole (precision Cf) | 1k: 7.2 MHz · 10k: 1.6 MHz · 100k: 720 kHz · 1M: 160 kHz · 10M/100M: set by strays (tens of kHz or less) |
| 1 MHz C-V ranges | **1k and 10k only**; calibrate gain and phase per range with the cal loads |
| Low-gain TIA | 499 Ω ∥ 68 pF, ±10 mA FS, takes over via the steering diodes when the high-gain TIA saturates (WE then sits ≈0.6 V off ground) |
| Null range | C: 0–100 pF, or 0–1.01 nF (NULL_RNG). G: ±50 µS, or ±505 µS (NULL_RNG) |
| Outputs (BNC, 50 Ω back-terminated) | V_OUT (DC: V_RE/2 · AC: ×10.1 V_RE), I_HI, I_LO |
| Other BNCs | CE, RE (shell = driven guard), GUARD, WE, BIAS/PULSE, AC PROBE, SYNC_IN (to Pico GP26, clamped) |
| On-board ADC | ADS131M04, ±1.2 V FS behind /5.02 dividers (±6 V at the outputs). CH0 V_DC, CH1 I_HI, CH2 I_LO, CH3 V_AC. 8.192 MHz clock |

## Blocks (schematic sheet regions)
| Block | Refs | Notes |
|---|---|---|
| Power | J1, D1–D3, FB1–FB5, U25, U26 | Pico VSYS fed via D3. Pico ground via FB5 (JP5 hard-ties it) |
| Inputs / summer | J2, J3, U9, U10, K21 | VSET = V_bias + V_dac + k·V_ac (two inverting stages) |
| Bias DAC | U20, U11 | level shift: V = 10.05 V − 4.02·V_DAC. JP4 = SPI2C select |
| Control amp | U1, K7 (DEV), K8 (PSTAT) | DEV: follower. PSTAT: PI (C15 100 p, R15 1 k, R16 10 k): retune for your cells |
| Cell / cal | K9 (RE_LOCAL), K10 (CELL), K11–K14, R18, C16 | cal mid-nodes are grounded by NC relays when off, so the open contacts see 0 V across them (no leakage into WE) |
| RE / guard / monitors | U2, U3, U7, U4, U8, K19/K20 | U7 (RE_MON) feeds the monitors and the nuller, keeping their load off the electrometer U2 |
| Nuller | U12–U14, RV1, RV2, K15–K18 | inject at SUM_HI. C path: −jωC·V. G path: AC-coupled, bipolar |
| TIAs | U5 (K1–K6, R41–R46, C41–C46), Q1/Q2, U6 | relays on the output side of the feedback networks |
| ADC | U21, X1, R50–R57 | dividers + 10 nF (≈20 kHz) |
| Controller | A1 (Pico 2), U22/U23, J12, J13 | 4.7 k pulls set the power-up state |

## Control map
16 relay lines, CTL*n* = Pico GP*n*. The same lines are on J12 (pins 1–16, GND on 17–20) for use with the Pico removed. Exactly one range at a time; use break-before-make, ~2 ms per reed operation.

| CTL / GP | Pico pin | Function | Relays | Power-up |
|---|---|---|---|---|
| 0 | 1 | range 1k | K1 | off |
| 1 | 2 | range 10k | K2 | off |
| 2 | 4 | range 100k | K3 | off |
| 3 | 5 | range 1M | K4 | **on** |
| 4 | 6 | range 10M | K5 | off |
| 5 | 7 | range 100M | K6 | off |
| 6 | 9 | DEV (U1 follower) | K7 | **on** |
| 7 | 10 | PSTAT (PI loop) | K8 | off |
| 8 | 11 | RE_LOCAL (RE ↔ CE_INT) | K9 | **on** |
| 9 | 12 | CELL (CE_INT ↔ CE BNC) | K10 | off |
| 10 | 14 | CAL_R | K11 + K12 | off |
| 11 | 15 | CAL_C | K13 + K14 | off |
| 12 | 16 | NULL_EN | K15 + K16 | off |
| 13 | 17 | NULL_RNG (1 nF / 2 k) | K17 + K18 | off |
| 14 | 19 | VMODE_AC | K19 (NC) + K20 | off (= DC) |
| 15 | 20 | DAC_EN | K21 | off |

Other Pico pins (SPI0): GP16 MISO, GP17 CS_ADC, GP18 SCK, GP19 MOSI, GP20 CS_DAC, GP21 ADC_DRDY, GP22 ADC_SYNC/RESET, GP26 SYNC_IN, GP27/GP28 spare (on J13). J13 also carries SPI, RUN and GND.

**Mode recipes**
- **Device mode (C-V, DLTS):** DEV=1, PSTAT=0, RE_LOCAL=1 (or 0 with a separate RE lead to the DUT), CELL=1.
- **Potentiostat:** DEV=0, PSTAT=1, RE_LOCAL=0, CELL=1. Switch CELL on last and off first.
- **Calibrate:** CELL=0, RE_LOCAL=1, DEV=1, then CAL_R=1 (or CAL_C=1). Record I/V gain and phase for each range at the probe frequency.
- **Null (C-DLTS):** DUT connected at the bias point, NULL_RNG as needed, NULL_EN=1. Adjust RV1 for minimum 1 MHz on I_HI, then RV2, then iterate.

## Build variants
Each BOM line has a **debug** and a **precision** column.

| Position | Debug | Precision |
|---|---|---|
| U1, U2, U3, U5, U6, U7, U8, U13 (1 MHz or sensitive path) | OPA134PA | OPA828ID (SOIC half) or OPA627AP (DIP) |
| U4, U9, U10, U11, U12, U14 | OPA134PA | OPA134PA |
| TIA Cf (1k/10k/100k/1M) | 47p / 15p / 4.7p / 1.5p | 22p / 10p / 2.2p / 1p |
| Rf | 1 % metal film | 1k–100k metal foil; 1M–100M glass high-megohm |
| K5, K6 (10M, 100M) | generic SIP-1A05 | Coto 9007-class ≥10¹² Ω (**footprint differs: check**) |
| RV1, RV2 | Bourns 3296W trimmers | 10-turn panel pots with counting dials, off-board |

The NE5534 can't be used: it needs compensation pins, which this footprint doesn't wire.

**Rough cost per board** (from memory, not quoted): debug ≈ $110–190; precision adds ≈ $150–260 (8× OPA828 is about $65–95 of that). A batch of bare PCBs is about $40–80, plus about $20–35 if JLC places the two SMD ICs.

## Layout notes for Rev B (to do)
- Guard rings (driven RE_BUF around U2's input; GND or SUM-level ring around SUM_HI) and solder mask removed over the guards. Mount the WE/SUM_HI node on a PTFE standoff if the 100M range matters.
- Combo footprint: the SOIC pads are rotated 90° inside the DIP rows. Same-numbered pads **must be joined with copper**. Keep pin 2 (−IN) short on U2 and U5.
- Pico, ADC, DAC and the oscillator go at the far edge from U2/U5, with their own ground return to the star point. No clocks or SPI near the input area.
- The L7805 dissipates about 1.5 W: fit a heatsink.
- Board will be larger than Rev A (DIP parts, 21 relays, 10 BNCs). Two layers should still work.

## Verification status
- Exported netlist checked against `scripts/design.py` by script: **176 nets, 0 mismatches**.
- **KiCad ERC not run.** The KiCad 7 CLI here has no ERC; run it in KiCad 9/10. Expected flags: none intended; the unused Pico pins carry no-connect markers.
- Not simulated. Compensation values are hand calculations.

## Open items / things to verify before layout
1. **DAC80501 SPI2C level** for SPI mode (JP4 selects GND or +5 V; default R36 pulls low). The level shift assumes the 0–5 V output range (VDD = 5 V). The top few codes may clip, so firmware should limit them. K21 stays open until the DAC is configured.
2. **Reed relay pinout** (Standex/Meder SIL, 1A and 1B): contact on 1–7, coil on 3–5.
3. **2N3904 C-B leakage** isn't a datasheet guarantee. Measure it, or fit an SMD BAV199 on an adapter.
4. **RP2350 GPIO pull-down erratum:** that's why the external pulls are 4.7 k. Check the current RP2350 errata.
5. TBD62783A has internal output clamp diodes and VIN(on) of 2.0 V minimum, so it works with 3.3 V GPIO.
6. **PI loop** (C15/R15/R16) and the AC monitor/TIA phase matching need tuning and calibration on real hardware.
7. Firmware is not written yet (MicroPython suggested: relay sequencing, DAC/ADC drivers, calibration).

## Regenerating
`scripts/design.py` is the source of truth for Rev B. Run from the repo root:
```
python3 scripts/make_lib.py      # afe.kicad_sym, afe.pretty/, lib tables
python3 scripts/gen_sch.py       # impedance_afe.kicad_sch (KiCad 7 format)
kicad-cli sch export netlist -o afe.net impedance_afe.kicad_sch && python3 scripts/check_net.py afe.net
python3 scripts/make_bom.py      # BOM_revB.csv (copy to docs/)
```
Regenerating overwrites the schematic and assigns new wire/label UUIDs. Once you start editing in KiCad, treat the KiCad files as the source and stop using the generator.
