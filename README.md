# Impedance / C-V / DLTS / Electrochemistry Analog Front End: Rev B

**Status:** the Rev B **schematic** is done; the **PCB** is placed with the critical nets pre-routed and locked, not yet autorouted. Rev A (schematic plus routed board, converted to KiCad 9/10) is kept in [`revA/`](revA/).

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
| Control | 8 GPIOs → 74HCT541 | **Pico 2 or ESP32-S3-ETH** (socketed), SPI → 2× 74HC595 → 16 lines → 2× TBD62783A source drivers |
| Digitiser | scope only | adds an on-board **ADS131M04** (4-ch simultaneous, 24-bit) for standalone potentiostat work |
| Parts | SMD | **through-hole** throughout, except DAC/ADC (JLC-placed) and the SOIC half of the op-amp footprints |
| Op-amp footprint | SOIC-8 | **DIP-8 + SOIC-8 combo** (`afe:DIP-8_SOIC-8_Combo`): fit one package |
| Steering diodes | BAV199 (SOT-23) | 2N3904 collector-base junctions (TO-92) |

## Specifications (design values, not measured)
| Parameter | Value |
|---|---|
| Supplies | external ±15 V (screw terminal). On board: +5 V (L7805) and +3.3 V (MCP1700). Estimated ≲300 mA from +15 V (relays + Pico 2; an ESP32-S3-ETH adds roughly 150–350 mA on +5 V), ≲120 mA from −15 V |
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
| Other BNCs | CE, RE (shell = driven guard), GUARD, WE, BIAS/PULSE, AC PROBE, SYNC_IN (to controller pin 22, clamped) |
| ADC / DAC | On the **ADC/DAC HAT** (`adc_hat/`, Pi Zero pHAT outline) plugged onto J16/J17. ADS131M04, ±1.2 V FS behind the main board's /5.02 dividers (±6 V at the outputs). CH0 V_DC, CH1 I_HI, CH2 I_LO, CH3 V_AC. Clock: Pico GP21 GPOUT0 at 8.000 MHz (USB PLL / 6; data rates ×0.977) via J16-7 by default, or the HAT's 8.192 MHz oscillator (HAT JP1). DAC80501 bias DAC also on the HAT |

## Blocks (schematic sheet regions)
| Block | Refs | Notes |
|---|---|---|
| Power | J1, D1–D3, FB1–FB5, U25, U26 | Controller VSYS fed via D3. Controller ground via FB5 (JP5 hard-ties it) |
| Inputs / summer | J2, J3, U9, U10, K21 | VSET = V_bias + V_dac + k·V_ac (two inverting stages). J2/J3 are on the back edge |
| Bias DAC | HAT U2, U11 | level shift on the main board: V = 10.05 V − 4.02·V_DAC. DAC_OUT/DAC_REF arrive on J17. SPI2C strap is on the HAT (R2 + JP2) |
| Control amp | U1, K7 (DEV), K8 (PSTAT) | DEV: follower. PSTAT: PI (C15 100 p, R15 1 k, R16 10 k): retune for your cells |
| Cell / cal | K9 (RE_LOCAL), K10 (CELL), K11–K14, R18, C16 | cal mid-nodes are grounded by NC relays when off, so the open contacts see 0 V across them (no leakage into WE) |
| RE / guard / monitors | U2, U3, U7, U4, U8, K19/K20 | U7 (RE_MON) feeds the monitors and the nuller, keeping their load off the electrometer U2 |
| Nuller | U12–U14, RV1, RV2, J14, J15, K15–K18 | inject at SUM_HI. C path: −jωC·V. G path: AC-coupled, bipolar. RV1/RV2 are front-panel 10-turn pots on J14/J15 (Molex KK 254: 1 CW, 2 wiper, 3 CCW, 4 cable shield) |
| TIAs | U5 (K1–K6, R41–R46, C41–C46), Q1/Q2, U6 | relays on the output side of the feedback networks |
| ADC link | J16 (Pi 40-pin, male), J17 (2×6 analog, male), R47, R50–R57, C50–C53 | dividers + 10 nF (≈20 kHz) on the main board. J17: 2 DAC_OUT, 4 DAC_REF, 6/8/10/12 ADC3P/2P/1P/0P, odd pins GND (ADCn N tied to GND here); the signal row faces the dividers |
| Controller | A1 (Pico 2 or ESP32-S3-ETH), U27/U28 (74HC595), U22/U23, R76, J13 | 4.7 k pulls set the power-up state; RLY_OE (R76 pull-up) holds the 595 outputs off until firmware enables them |

## Control map
The 16 relay lines CTL*n* come from two 74HC595s on SPI0 (MOSI → U27 → U28; SCK shared with the HAT, latch = RLY_LATCH). Shift 16 bits, pulse RLY_LATCH, then drive RLY_OE low. RLY_OE is pulled high (R76), so the 595 outputs stay Hi-Z through power-up and reset and the 4.7 k pulls set the state. **CTL*n* drives driver channel 15−*n*** (KD(15−*n*)); the order is for routing, and firmware maps it. Exactly one range at a time; use break-before-make, ~2 ms per reed operation.

| CTL | 595 output | Driver ch (KD) | Function | Relays | Power-up |
|---|---|---|---|---|---|
| 0 | U27 QA | 15 | DAC_EN | K21 | off |
| 1 | U27 QB | 14 | VMODE_AC | K19 (NC) + K20 | off (= DC) |
| 2 | U27 QC | 13 | NULL_RNG (1 nF / 2 k) | K17 + K18 | off |
| 3 | U27 QD | 12 | NULL_EN | K15 + K16 | off |
| 4 | U27 QE | 11 | CAL_C | K13 + K14 | off |
| 5 | U27 QF | 10 | CAL_R | K11 + K12 | off |
| 6 | U27 QG | 9 | CELL (CE_INT ↔ CE BNC) | K10 | off |
| 7 | U27 QH | 8 | RE_LOCAL (RE ↔ CE_INT) | K9 | **on** |
| 8 | U28 QA | 7 | PSTAT (PI loop) | K8 | off |
| 9 | U28 QB | 6 | DEV (U1 follower) | K7 | **on** |
| 10 | U28 QC | 5 | range 100M | K6 | off |
| 11 | U28 QD | 4 | range 10M | K5 | off |
| 12 | U28 QE | 3 | range 1M | K4 | **on** |
| 13 | U28 QF | 2 | range 100k | K3 | off |
| 14 | U28 QG | 1 | range 10k | K2 | off |
| 15 | U28 QH | 0 | range 1k | K1 | off |

**Controller header (A1).** The pins are chosen so that a Pico 2 and a Waveshare ESP32-S3-ETH (same header, 72.8 mm long, RJ45/USB-C at the USB end) both work. ESP32 pins avoided: 1–2 (USB), 6–7 (straps), 15–17 and 19–20 (octal PSRAM), 35 (RGB LED).

| Pin | Pico 2 | ESP32-S3-ETH | Net |
|---|---|---|---|
| 4 | GP2 | IO48 | RLY_LATCH |
| 5 | GP3 | IO47 | RLY_OE |
| 21 | GP16 | IO43 (UART0 TX: boot log) | AUX (J13-10) |
| 22 | GP17 | IO44 | SYNC_IN |
| 24 | GP18 | IO0 (boot strap; HAT R5 pulls it high) | ADC_SYNC |
| 25 | GP19 (SPI0 TX) | IO1 | MOSI |
| 26 | GP20 (SPI0 RX) | IO2 | MISO |
| 27 | GP21 (GPOUT0, 8.000 MHz) | IO3 (leave as input) | PICO_GPCLK → R47 → HAT_CLK |
| 29 | GP22 (SPI0 SCK) | IO15 | SCK |
| 31 | GP26 | IO18 | CS_ADC |
| 32 | GP27 | IO16 | CS_DAC |
| 34 | GP28 | IO17 | ADC_DRDY |

Free on both: pins 9–12 (GP6–GP9 / IO42–IO39). With an ESP32-S3 the HAT runs from its own 8.192 MHz oscillator (fit Y1, HAT JP1 2-3).

J16 uses the Raspberry Pi pinout, so the HAT also stacks on a Pi Zero: SPI0 on 19/21/23, CE0 (24) = CS_ADC, CE1 (26) = CS_DAC, GPIO4 (7, GPCLK0) = clock, GPIO24 (18) = SYNC/RESET, GPIO25 (22) = DRDY, 3V3 on 1/17 (HAT logic), 5V on 2/4 (HAT AVDD LDO and DAC).

J13 (2×8 right-angle box header, back-right corner) carries SPI, CS_ADC, CS_DAC, DRDY, ADC_SYNC, SYNC_IN, HAT_CLK (9), AUX (10), RLY_LATCH (11), RLY_OE (12), RUN (13) and GND (14–16): an external 3.3 V SPI master can run the relays and the HAT with the controller absent or held in reset (RUN low), using the HAT oscillator (HAT JP1 2-3) or its own clock on J13-9.

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
| RV1, RV2 | 10-turn panel pots with counting dials (Bourns 3590S-2-103), off-board via J14/J15 | same |

The NE5534 can't be used: it needs compensation pins, which this footprint doesn't wire.

**Rough cost per board** (from memory, not quoted): debug ≈ $110–190; precision adds ≈ $150–260 (8× OPA828 is about $65–95 of that). A batch of bare PCBs is about $40–80, plus the ADC/DAC HAT (all SMD, JLC-assembled; ADS131M04 + DAC80501 are most of its cost).

## Layout (Rev B, first pass: placed + critical nets, not yet autorouted)
- **Front edge (bottom):** CE, RE (shell = GUARD), GUARD, WE, I_LO, I_HI, V_OUT. I_LO and I_HI are swapped relative to the schematic order so that their lanes, and V_OUT's, run down to the BNCs to the right of the SUM_HI bus end, with no crossings of SUM_HI.
- **Board:** 248 × 150 mm. Front BNC pitch 26.5 mm either side of RE (insulated GUARD-shell socket), 24 mm on the output group. GUARD (J6) stays left of K11, the left end of the SUM_HI bus, so the guard run never crosses the bus.
- **Back edge (top):** J1 power, AC PROBE and BIAS/PULSE (24 mm pitch), the 74HC595s, controller (RJ45/USB end), SYNC_IN (~23 mm clear of the controller), J13 (back-right corner). Nuller pots on cables (J14/J15) to the front panel.
- **Controller (A1):** footprint `afe:Pico2_ESP32-S3-ETH_THT`. The ESP32-S3-ETH's RJ45/USB-C end reaches the back edge; a Pico 2's USB socket then sits ~18 mm in from the edge. The ESP32's microSD slot is underneath at the far end and the card goes in from that end: keep the 15 mm area below the module (User.Comments) free of tall parts.
- **Relay control:** 595 (outputs on its lower row) → pull resistor → driver input, one column per line, 3 mm in from the back edge so tracks can pass above the 595s. The area under the drivers is left clear for the 16 coil lines.
- **Op-amp decoupling** book-ends each socket: C+ at the pin-7 end, C− at the pin-4 end. U2, U5 and U6 (RE input and the two TIAs) keep hand-placed caps.
- **Nuller:** U12 sits between the null buffers U13/U14, with J14/J15 either side of it. A Bourns 3296W multi-turn trimmer fits J14/J15 pads 1–3 (in-line, 2.54 mm, wiper in the middle) for a permanent fixture; check the CW sense against the panel-pot wiring.
- **TIA ladder:** about 10–11 mm column pitch, ≥1.4 mm between parts, and a ~4 mm clear area between U5 −IN and R46 for an optional PTFE standoff. The SUM_HI guard is a GND pour with stitching vias and a mask-free band (a closed ring can't fit inside the combo footprint).
- **HAT:** below J13 at the back-right, rotated 90°, on 11 mm M2.5 standoffs (H10–H13). Keep parts under it short. The ADC dividers sit in one row per channel to the left of J17.
- **Mounting holes:** H1 (by J1, the star point) is the only chassis bond. H2–H9 are isolated M3 NPTH holes: front edge ×5 (H2, H7, H3, H4, H5), back edge ×1, centre ×2.
- Combo footprints: same-numbered DIP and SOIC pads are joined with copper on every op-amp.
- The L7805 dissipates about 1.5 W: fit a heatsink (keep-clear area on User.Comments).

## Verification status
- Main schematic: netlist checked against `scripts/design.py` (**208 nets, 0 problems**); KiCad 9 ERC 0 errors (16 `lib_symbol_mismatch` warnings from the local KiCad 9 libraries).
- HAT schematic: checked against `scripts/hat/design.py` (**59 nets, 0 problems**); ERC 0 errors.
- HAT/main connectors: pad positions match under the mounting transform (0.000 mm), pin nets match.
- Not simulated. Compensation values are hand calculations.

## Open items / things to verify before layout
1. **DAC80501 SPI2C level** for SPI mode (HAT: R2 pulls low, JP2 ties to +5VA). The level shift assumes the 0–5 V output range (VDD = 5 V). The top few codes may clip, so firmware should limit them. K21 stays open until the DAC is configured.
2. **Reed relay pinout** (Standex/Meder SIL, 1A and 1B): contact on 1–7, coil on 3–5.
3. **2N3904 C-B leakage** isn't a datasheet guarantee. Measure it, or fit an SMD BAV199 on an adapter.
4. **Controller supply with an ESP32-S3-ETH:** it draws roughly 150–350 mA from +5 V (W5500 plus Wi-Fi peaks), which adds 1.5–3.5 W to the L7805 (from +15 V). Check the heatsink, or feed the module from its own USB-C/PoE. The ESP32 header map is from Waveshare's dimension drawing (underside silk); confirm on a real module.
5. TBD62783A has internal output clamp diodes and VIN(on) of 2.0 V minimum; the 74HC595 runs from +3V3D.
6. **PI loop** (C15/R15/R16) and the AC monitor/TIA phase matching need tuning and calibration on real hardware.
7. **ADS131M04 at 8.000 MHz:** confirm the CLKIN range in the datasheet. HAT oscillator Y1 part number is TBD.
8. Firmware is not written yet (MicroPython suggested: relay sequencing, DAC/ADC drivers, calibration).

## Regenerating / checking
The KiCad files are the source. `scripts/design.py` is the record of intent that the netlist is checked against; don't run `scripts/gen_sch.py` or `scripts/make_lib.py` (they write KiCad 7 files over the KiCad 10 ones). From the repo root:
```
kicad-cli sch export netlist -o afe.net impedance_afe.kicad_sch && python3 scripts/check_net.py afe.net
(cd docs && PYTHONPATH=../scripts python3 ../scripts/make_bom.py)     # docs/BOM_revB.csv
cd scripts/layout && /usr/bin/python3 place.py ../../afe.net && /usr/bin/python3 preroute.py && /usr/bin/python3 check.py
```
`place.py` and `preroute.py` rebuild the board from scratch, so they overwrite any placement or routing done by hand in KiCad.
