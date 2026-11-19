"""Redraw every remaining block as a wired schematic (TIA is done by tia.py).

Each function strips its block's pin stubs/labels, places the symbols, draws the local wiring,
and lets Block.finish() terminate the remaining pins (labels / power symbols / no-connects)
and name every wired net.
"""
from redraw import *  # noqa

DN, UP, LT, RT = (0, 1), (0, -1), (-1, 0), (1, 0)


def move_text(s, prefix, x, y):
    for t in s.items('text'):
        if val(t).startswith(prefix):
            find1(t, 'at')[1:3] = [A(fmt(x)), A(fmt(y))]


# ---------------------------------------------------------------------------------------- decoupling
def decoupling(s):
    order = ['U9', 'U10', 'U11', 'U1', 'U2', 'U3', 'U7', 'U4', 'U8', 'U12', 'U13', 'U14', 'U5', 'U6']
    caps = [(f'C{100+2*i}', f'C{101+2*i}') for i in range(14)]
    b = Block(s, [c for pr in caps for c in pr])
    move_text(s, 'Op-amp decoupling', 580, 504.19)
    for i, (cp, cn) in enumerate(caps):
        x = 586.74 + 17.78 * i
        b.pl(cp, x, 519.43); b.pl(cn, x, 529.59)
        b.at_pin(cp, 1, UP)
        b.w(b.p(cp, 2), b.p(cn, 1))
        b.w((x, 524.51), (x + 3.81, 524.51)); b.rail('GND', (x + 3.81, 524.51), DN)
        b.at_pin(cn, 2, DN)
        b.F(cp, (x - 2.54, 518.16), (x - 2.54, 520.7), 'right')
        b.F(cn, (x - 2.54, 528.32), (x - 2.54, 530.86), 'right')
        s.text(order[i], x - 1.27, 544.83)
    return b.finish()


# ---------------------------------------------------------------------------------------- power
def power(s):
    flg = {f'#FLG{i+1}': n for i, n in enumerate(['+15V', '-15V', 'GND', 'P15_RAW', 'N15_RAW', '+3V3A', '+3V3D', 'VSYS', 'PICO_GND'])}
    refs = ['J1', 'D1', 'D2', 'C1', 'C2', 'FB1', 'FB2', 'C3', 'C4', 'U25', 'C5', 'C6', 'C7', 'U26', 'C8', 'C9', 'FB3', 'FB4',
            'C10', 'C11', 'D3', 'FB5', 'JP5', 'H1', 'H2', 'H3', 'H4'] + list(flg)
    b = Block(s, refs)
    YN, YP, Y5 = 45.72, 76.2, 106.68
    b.pl('J1', 25.4, 60.96, 180); b.F('J1', (22.86, 53.34), (22.86, 55.88), None)
    b.w(b.p('J1', 3), (33.02, 58.42), (33.02, YN), (39.37, YN))
    b.w(b.p('J1', 1), (35.56, 63.5), (35.56, YP), (39.37, YP))
    b.w(b.p('J1', 2), (40.64, 60.96)); b.rail('GND', (38.1, 60.96), DN); b.pl('#FLG3', 40.64, 60.96)
    # -15 V chain
    b.pl('D2', 43.18, YN, 0)
    b.pl('C2', 55.88, 49.53, 180); b.at_pin('C2', 1, DN)
    b.pl('FB2', 83.82, YN, 90)
    b.pl('C4', 101.6, 49.53, 180); b.at_pin('C4', 1, DN)
    b.w((46.99, YN), (80.01, YN)); b.w((87.63, YN), (114.3, YN)); b.rail('-15V', (114.3, YN), UP)
    b.pl('#FLG5', 73.66, YN); b.pl('#FLG2', 109.22, YN)
    # +15 V chain
    b.pl('D1', 43.18, YP, 180)
    b.pl('C1', 55.88, 80.01); b.at_pin('C1', 2, DN)
    b.pl('C5', 68.58, 80.01); b.at_pin('C5', 2, DN)
    b.pl('FB1', 83.82, YP, 90)
    b.pl('C3', 101.6, 80.01); b.at_pin('C3', 2, DN)
    b.w((46.99, YP), (80.01, YP)); b.w((87.63, YP), (114.3, YP)); b.rail('+15V', (114.3, YP), UP)
    b.pl('#FLG4', 76.2, YP); b.pl('#FLG1', 109.22, YP)
    # +5 V, +3V3
    b.w((48.26, YP), (48.26, Y5))
    b.pl('U25', 55.88, Y5); b.at_pin('U25', 2, DN)
    b.pl('C6', 71.12, 110.49); b.at_pin('C6', 2, DN)
    b.pl('C7', 83.82, 110.49); b.at_pin('C7', 2, DN)
    b.pl('C8', 104.14, 110.49); b.at_pin('C8', 2, DN)
    b.pl('U26', 124.46, Y5); b.F('U26', (124.46, 114.3), (124.46, 116.84), None)
    b.w((63.5, Y5), b.p('U26', 2)); b.rail('+5V', (93.98, Y5), UP)
    b.w(b.p('U26', 1), (124.46, 93.98), (134.62, 93.98)); b.rail('GND', (134.62, 93.98), DN)
    b.pl('C9', 139.7, 110.49); b.at_pin('C9', 2, DN)
    b.w(b.p('U26', 3), (149.86, Y5)); b.rail('+3V3', (134.62, Y5), UP)
    b.pl('FB3', 153.67, Y5, 90)
    b.pl('C10', 162.56, 110.49); b.at_pin('C10', 2, DN)
    b.w((157.48, Y5), (175.26, Y5)); b.rail('+3V3A', (175.26, Y5), UP); b.pl('#FLG6', 170.18, Y5)
    b.w((149.86, Y5), (149.86, 91.44))
    b.pl('FB4', 153.67, 91.44, 90)
    b.pl('C11', 162.56, 95.25); b.at_pin('C11', 2, DN)
    b.w((157.48, 91.44), (175.26, 91.44)); b.rail('+3V3D', (175.26, 91.44), UP); b.pl('#FLG7', 170.18, 91.44)
    # Pico VSYS feed
    b.rail('+5V', (190.5, YN), UP)
    b.pl('D3', 198.12, YN, 180)
    b.w((190.5, YN), (194.31, YN)); b.w((201.93, YN), (213.36, YN)); b.lab('VSYS', (213.36, YN), RT)
    b.pl('#FLG8', 207.01, YN)
    # Pico ground: FB5 (JP5 hard-tie)
    b.rail('PICO_GND', (190.5, YP), DN)
    b.pl('FB5', 203.2, 80.01); b.at_pin('FB5', 2, DN)
    b.pl('JP5', 231.14, YP)
    b.w((190.5, YP), b.p('JP5', 1)); b.pl('#FLG9', 196.85, YP)
    b.w(b.p('JP5', 2), (223.52, 78.74)); b.rail('GND', (223.52, 78.74), DN)
    s.text('Pico ground joins GND only via FB5 (JP5 hard-tie)', 190.5, 68.58)
    for i in range(4):
        b.pl(f'H{i+1}', 205.74 + 10.16 * i, 104.14); b.at_pin(f'H{i+1}', 1, DN)
    s.text('Mounting holes', 205.74, 96.52)
    return b.finish()


# ---------------------------------------------------------------------------------------- inputs / summer
def inputs(s):
    refs = ['J2', 'R1', 'JP1', 'R2', 'R3', 'J3', 'R4', 'JP2', 'R5', 'C12', 'R6', 'R7', 'R8', 'JP3', 'K21', 'R9', 'R10',
            'U9', 'R11', 'C13', 'U10', 'R12', 'R13', 'C14', 'R14']
    b = Block(s, refs)
    XS = 114.3                                     # SUMIN bus
    # BIAS/PULSE
    b.pl('J2', 30.48, 157.48, 270); b.at_pin('J2', 2, DN); b.F('J2', (30.48, 146.05), (30.48, 148.59), None)
    b.pl('R1', 45.72, 156.21); b.F('R1', (43.18, 154.94), (43.18, 157.48), 'right')
    b.pl('JP1', 63.5, 160.02)
    b.w(b.p('R1', 2), b.p('JP1', 1)); b.w(b.p('JP1', 2), (55.88, 162.56)); b.rail('GND', (55.88, 162.56), DN)
    b.pl('R2', 71.12, 156.21); b.at_pin('R2', 2, DN)
    b.pl('R3', 106.68, 152.4, 90)
    b.w(b.p('J2', 1), (30.48, 152.4), b.p('R3', 1)); b.w(b.p('R3', 2), (XS, 152.4), (XS, 205.74))
    # AC PROBE
    b.pl('J3', 30.48, 180.34, 270); b.at_pin('J3', 2, DN); b.F('J3', (30.48, 168.91), (30.48, 171.45), None)
    b.pl('R4', 45.72, 179.07); b.F('R4', (43.18, 177.8), (43.18, 180.34), 'right')
    b.pl('JP2', 63.5, 182.88)
    b.w(b.p('R4', 2), b.p('JP2', 1)); b.w(b.p('JP2', 2), (55.88, 185.42)); b.rail('GND', (55.88, 185.42), DN)
    b.pl('R5', 71.12, 179.07); b.at_pin('R5', 2, DN)
    b.pl('C12', 80.01, 175.26, 90); b.F('C12', (80.01, 170.18), (80.01, 172.72), None)
    b.w(b.p('J3', 1), b.p('C12', 1))
    b.w(b.p('C12', 2), (91.44, 175.26), (91.44, 187.96))
    b.pl('R6', 86.36, 179.07); b.at_pin('R6', 2, DN); b.F('R6', (83.82, 182.88), (83.82, 185.42), 'right')
    b.pl('R8', 95.25, 182.88, 90); b.F('R8', (95.25, 177.8), (95.25, 180.34), None)
    b.pl('R7', 95.25, 187.96, 90); b.F('R7', (95.25, 190.5), (95.25, 193.04), None)
    b.pl('JP3', 109.22, 182.88, 270)
    b.w(b.p('R8', 2), (106.68, 182.88), b.p('JP3', 3))
    b.w(b.p('R7', 2), (111.76, 187.96), b.p('JP3', 1))
    b.w(b.p('JP3', 2), (109.22, 167.64), (XS, 167.64))
    # DAC switch
    b.pl('K21', 60.96, 213.36)
    b.at_pin('K21', 1, DN); b.at_pin('K21', 3, DN)
    b.w(b.p('K21', 5), (55.88, 203.2), (50.8, 203.2)); b.rail('GND', (50.8, 203.2), DN)
    b.pl('R10', 78.74, 209.55); b.at_pin('R10', 2, DN)
    b.pl('R9', 96.52, 205.74, 90)
    b.w(b.p('K21', 7), b.p('R9', 1)); b.w(b.p('R9', 2), (XS, 205.74))
    # U9 summer
    b.pl('U9', 129.54, 203.2)
    b.w((XS, 205.74), b.p('U9', 2))
    b.w(b.p('U9', 3), (119.38, 200.66)); b.rail('GND', (119.38, 200.66), DN)
    b.at_pin('U9', 7, UP); b.at_pin('U9', 4, DN)
    b.pl('R11', 129.54, 180.34, 90); b.pl('C13', 129.54, 172.72, 90); b.F('C13', (129.54, 167.64), (129.54, 170.18), None)
    b.w((XS, 180.34), b.p('R11', 1)); b.w((XS, 172.72), b.p('C13', 1))
    b.w(b.p('C13', 2), (142.24, 172.72), (142.24, 203.2)); b.w(b.p('R11', 2), (142.24, 180.34))
    b.pl('R12', 152.4, 203.2, 90)
    b.w(b.p('U9', 6), b.p('R12', 1))
    # U10 re-inverter
    b.pl('U10', 172.72, 200.66)
    b.w(b.p('R12', 2), b.p('U10', 2))
    b.w(b.p('U10', 3), (162.56, 198.12)); b.rail('GND', (162.56, 198.12), DN)
    b.at_pin('U10', 7, UP); b.at_pin('U10', 4, DN)
    b.pl('R13', 172.72, 177.8, 90); b.pl('C14', 172.72, 170.18, 90); b.F('C14', (172.72, 165.1), (172.72, 167.64), None)
    b.w((160.02, 203.2), (160.02, 170.18), b.p('C14', 1)); b.w((160.02, 177.8), b.p('R13', 1))
    b.w(b.p('C14', 2), (185.42, 170.18), (185.42, 200.66)); b.w(b.p('R13', 2), (185.42, 177.8))
    b.pl('R14', 193.04, 200.66, 90)
    b.w(b.p('U10', 6), b.p('R14', 1))
    b.term('R14', 2)
    return b.finish()


# ---------------------------------------------------------------------------------------- bias DAC
def dac(s):
    refs = ['U20', 'JP4', 'R36', 'C24', 'C25', 'C26', 'R37', 'R38', 'C22', 'R39', 'R40', 'C23', 'U11']
    b = Block(s, refs)
    b.pl('U20', 68.58, 350.52); b.F('U20', (68.58, 337.82), (68.58, 340.36), None)
    b.at_pin('U20', 1, UP)
    b.term('U20', 4)
    b.pl('JP4', 35.56, 350.52, 180); b.F('JP4', (31.75, 346.71), (31.75, 349.25), 'right')
    b.w(b.p('U20', 5), b.p('JP4', 2))
    b.at_pin('JP4', 3, UP); b.at_pin('JP4', 1, DN)
    b.pl('R36', 45.72, 354.33); b.at_pin('R36', 2, DN)
    # VOUT -> R37 -> LS_INV (U11 -, mirrored so - is on top)
    b.pl('U11', 167.64, 347.98, 0, 'x')
    b.pl('R37', 106.68, 345.44, 90)
    b.w(b.p('U20', 2), b.p('R37', 1)); b.w(b.p('R37', 2), b.p('U11', 2))
    # REF -> C26 (to GND), R39 -> LS_Y (U11 +), R40 || C23 to GND
    b.w(b.p('U20', 10), (91.44, 347.98), (91.44, 363.22), (110.49, 363.22)); b.lab('DAC_REF', (92.71, 363.22), RT)
    b.pl('C26', 101.6, 367.03); b.at_pin('C26', 2, DN)
    b.pl('R39', 114.3, 363.22, 90)
    b.w(b.p('R39', 2), (157.48, 363.22), (157.48, 350.52), b.p('U11', 3))
    b.pl('R40', 124.46, 367.03); b.at_pin('R40', 2, DN)
    b.pl('C23', 142.24, 367.03); b.at_pin('C23', 2, DN)
    # feedback R38 || C22 over the top
    b.pl('R38', 167.64, 330.2, 90); b.pl('C22', 167.64, 322.58, 90)
    b.w((152.4, 345.44), (152.4, 322.58), b.p('C22', 1)); b.w((152.4, 330.2), b.p('R38', 1))
    b.w(b.p('C22', 2), (182.88, 322.58), (182.88, 347.98)); b.w(b.p('R38', 2), (182.88, 330.2))
    b.w(b.p('U11', 6), (190.5, 347.98)); b.lab('DAC_BIAS', (190.5, 347.98), RT)
    b.at_pin('U11', 4, UP); b.at_pin('U11', 7, DN)
    # DAC supply decoupling
    for c, x in (('C24', 53.34), ('C25', 66.04)):
        b.pl(c, x, 377.19); b.at_pin(c, 1, UP); b.at_pin(c, 2, DN)
    s.text('U20 decoupling', 72.39, 378.46)
    return b.finish()


# ---------------------------------------------------------------------------------------- control amp, cell, cal
def control(s):
    refs = ['U1', 'C15', 'R15', 'R16', 'K7', 'K8', 'R17', 'K10', 'J4', 'K9', 'R18', 'K11', 'K12', 'C16', 'K13', 'K14']
    b = Block(s, refs)
    b.pl('K8', 320.04, 144.78, 90); b.at_pin('K8', 5, DN); b.at_pin('K8', 3, DN)
    b.pl('K7', 320.04, 165.1, 90); b.at_pin('K7', 5, DN); b.at_pin('K7', 3, DN)
    b.pl('C15', 314.96, 182.88, 90); b.pl('R15', 325.12, 182.88, 90)
    b.pl('U1', 320.04, 200.66, 0, 'x')
    b.at_pin('U1', 4, UP); b.at_pin('U1', 7, DN)
    b.term('U1', 3, 5.08)
    XI, XO = 307.34, 332.74
    b.w(b.p('U1', 2), (XI, 198.12), (XI, 139.7), b.p('K8', 7))
    b.w((XI, 160.02), b.p('K7', 7)); b.w((XI, 182.88), b.p('C15', 1))
    b.w(b.p('C15', 2), b.p('R15', 1))
    b.w(b.p('U1', 6), (XO, 200.66), (XO, 160.02), b.p('K7', 1)); b.w(b.p('R15', 2), (XO, 182.88))
    b.pl('R16', 340.36, 139.7, 270)
    b.w(b.p('K8', 1), b.p('R16', 2)); b.term('R16', 1)
    b.pl('R17', 340.36, 200.66, 90)
    b.w((XO, 200.66), b.p('R17', 1))
    # CE_INT bus -> K10 -> CE BNC
    b.pl('K10', 449.58, 195.58, 270)
    b.w(b.p('R17', 2), b.p('K10', 1))
    b.at_pin('K10', 3, UP)
    b.w(b.p('K10', 5), (459.74, 190.5)); b.rail('GND', (459.74, 190.5), DN)
    b.pl('J4', 467.36, 200.66); b.at_pin('J4', 2, DN)
    b.w(b.p('K10', 7), b.p('J4', 1))
    # cal R: R18 -> CALR_MID -> K11 -> SUM_HI ; K12 (NC) CALR_MID -> GND
    b.w((350.52, 200.66), (350.52, 165.1), (351.79, 165.1))
    b.pl('R18', 355.6, 165.1, 90)
    b.pl('K11', 373.38, 160.02, 270)
    b.w(b.p('R18', 2), b.p('K11', 1)); b.term('K11', 7)
    b.at_pin('K11', 3, UP); b.w(b.p('K11', 5), (383.54, 154.94)); b.rail('GND', (383.54, 154.94), DN)
    b.pl('K12', 368.3, 182.88, 180)
    b.w((363.22, 165.1), b.p('K12', 1)); b.at_pin('K12', 7, DN)
    b.w(b.p('K12', 3), (378.46, 175.26)); b.lab('KD10', (378.46, 175.26), RT)
    b.w(b.p('K12', 5), (375.92, 190.5)); b.rail('GND', (375.92, 190.5), DN)
    # cal C: C16 -> CALC_MID -> K13 -> SUM_HI ; K14 (NC) CALC_MID -> GND
    b.w((401.32, 200.66), (401.32, 165.1), (402.59, 165.1))
    b.pl('C16', 406.4, 165.1, 90)
    b.pl('K13', 424.18, 160.02, 270)
    b.w(b.p('C16', 2), b.p('K13', 1)); b.term('K13', 7)
    b.at_pin('K13', 3, UP); b.w(b.p('K13', 5), (434.34, 154.94)); b.rail('GND', (434.34, 154.94), DN)
    b.pl('K14', 419.1, 182.88, 180)
    b.w((414.02, 165.1), b.p('K14', 1)); b.at_pin('K14', 7, DN)
    b.w(b.p('K14', 3), (429.26, 175.26)); b.lab('KD11', (429.26, 175.26), RT)
    b.w(b.p('K14', 5), (426.72, 190.5)); b.rail('GND', (426.72, 190.5), DN)
    # K9 RE_LOCAL: CE_INT -> RE_BNC
    b.pl('K9', 368.3, 220.98, 270)
    b.w((353.06, 200.66), (353.06, 226.06), b.p('K9', 1)); b.term('K9', 7)
    b.at_pin('K9', 3, UP); b.w(b.p('K9', 5), (378.46, 215.9)); b.rail('GND', (378.46, 215.9), DN)
    return b.finish()


# ---------------------------------------------------------------------------------------- RE, guard, monitors
def follower(b, u, x, y, loop_y):
    """mirrored op-amp (- on top) wired as a follower with the loop over the top"""
    b.pl(u, x, y, 0, 'x')
    p2, p6 = b.p(u, 2), b.p(u, 6)
    b.w(p2, (p2[0] - 2.54, p2[1]), (p2[0] - 2.54, loop_y), (p6[0] + 5.08, loop_y), (p6[0] + 5.08, p6[1]), p6)
    b.at_pin(u, 4, UP); b.at_pin(u, 7, DN)
    return p6[0] + 5.08


def re_mon(s):
    refs = ['J5', 'R19', 'U2', 'U3', 'R20', 'J6', 'U7', 'R21', 'R22', 'U4', 'C17', 'R23', 'U8', 'R24', 'R25', 'R26', 'R27',
            'K19', 'K20', 'J8']
    b = Block(s, refs)
    b.pl('J5', 299.72, 281.94, 180); b.F('J5', (299.72, 288.29), (299.72, 290.83), None)
    b.w(b.p('J5', 2), (299.72, 274.32)); b.lab('GUARD', (299.72, 274.32), UP)
    b.pl('R19', 314.96, 281.94, 90)
    b.w(b.p('J5', 1), b.p('R19', 1)); b.lab('RE_BNC', (306.07, 281.94), RT)
    xa = follower(b, 'U2', 332.74, 279.4, 261.62)
    b.w(b.p('R19', 2), b.p('U2', 3)); b.lab('RE_BUF', (334.01, 261.62), RT)
    xb = follower(b, 'U3', 360.68, 276.86, 259.08)
    b.w((xa, 279.4), b.p('U3', 3))
    b.pl('R20', 378.46, 276.86, 90)
    b.w((xb, 276.86), b.p('R20', 1))
    b.pl('J6', 401.32, 276.86); b.at_pin('J6', 2, DN)
    b.w(b.p('R20', 2), b.p('J6', 1)); b.lab('GUARD', (383.54, 276.86), RT)
    # U7 RE_MON buffer
    xc = follower(b, 'U7', 360.68, 317.5, 299.72)
    b.w((347.98, 279.4), (347.98, 320.04), b.p('U7', 3)); b.lab('RE_MON', (354.33, 299.72), RT)
    # DC monitor: R21/R22 /2 -> U4 -> R26 -> K19 (NC)
    b.pl('R21', 378.46, 317.5, 90)
    b.w((xc, 317.5), b.p('R21', 1))
    b.pl('R22', 388.62, 321.31); b.at_pin('R22', 2, DN)
    xd = follower(b, 'U4', 403.86, 314.96, 297.18)
    b.w(b.p('R21', 2), b.p('U4', 3)); b.lab('VDC_DRV', (397.51, 297.18), RT)
    b.pl('R26', 421.64, 314.96, 90)
    b.w((xd, 314.96), b.p('R26', 1))
    b.pl('K19', 444.5, 309.88, 270)
    b.w(b.p('R26', 2), b.p('K19', 1))
    b.at_pin('K19', 3, UP); b.w(b.p('K19', 5), (454.66, 304.8)); b.rail('GND', (454.66, 304.8), DN)
    # AC monitor: C17/R23 HPF -> U8 x10.1 -> R27 -> K20
    b.w((370.84, 317.5), (370.84, 345.44), (374.65, 345.44))
    b.pl('C17', 378.46, 345.44, 90)
    b.pl('R23', 386.08, 349.25); b.at_pin('R23', 2, DN)
    b.pl('U8', 403.86, 347.98)
    b.w(b.p('C17', 2), b.p('U8', 3))
    b.at_pin('U8', 7, UP); b.at_pin('U8', 4, DN)
    b.pl('R24', 406.4, 365.76, 270)
    b.pl('R25', 393.7, 369.57); b.at_pin('R25', 2, DN)
    b.w(b.p('U8', 2), (393.7, 350.52), (393.7, 365.76), b.p('R24', 2))
    b.w(b.p('R24', 1), (416.56, 365.76), (416.56, 347.98)); b.w((416.56, 365.76), (419.1, 365.76))
    b.lab('VAC_DRV', (419.1, 365.76), RT)
    b.pl('R27', 421.64, 347.98, 90)
    b.w(b.p('U8', 6), b.p('R27', 1))
    b.pl('K20', 444.5, 342.9, 270)
    b.w(b.p('R27', 2), b.p('K20', 1))
    b.at_pin('K20', 3, UP); b.w(b.p('K20', 5), (454.66, 337.82)); b.rail('GND', (454.66, 337.82), DN)
    b.pl('J8', 477.52, 330.2); b.at_pin('J8', 2, DN)
    b.w(b.p('K19', 7), (457.2, 314.96), (457.2, 347.98), b.p('K20', 7)); b.w((457.2, 330.2), b.p('J8', 1))
    return b.finish()


# ---------------------------------------------------------------------------------------- nuller
def nuller(s):
    refs = ['U12', 'R28', 'R29', 'RV1', 'U13', 'C18', 'C19', 'K17', 'K15', 'RV2', 'U14', 'C20', 'R30', 'R31', 'K18', 'K16',
            'J14', 'J15']
    b = Block(s, refs)
    # U12: NULL_NEG = -RE_MON
    b.pl('U12', 604.52, 256.54)
    b.w(b.p('U12', 3), (594.36, 254.0)); b.rail('GND', (594.36, 254.0), DN)
    b.at_pin('U12', 7, UP); b.at_pin('U12', 4, DN)
    b.pl('R28', 584.2, 259.08, 90); b.term('R28', 1)
    b.w(b.p('R28', 2), b.p('U12', 2))
    b.pl('R29', 604.52, 274.32, 90)
    b.w((591.82, 259.08), (591.82, 274.32), b.p('R29', 1))
    b.w(b.p('R29', 2), (617.22, 274.32), (617.22, 256.54))
    b.w(b.p('U12', 6), (624.84, 256.54)); b.lab('NULL_NEG', (624.84, 256.54), RT)
    # pot connectors
    b.pl('J14', 655.32, 251.46)
    b.term('J14', 1); b.term('J14', 2)
    b.w(b.p('J14', 3), (647.7, 254.0), (647.7, 256.54)); b.w(b.p('J14', 4), (647.7, 256.54)); b.rail('GND', (647.7, 256.54), DN)
    b.pl('J15', 655.32, 276.86)
    for n in (1, 2, 3):
        b.term('J15', n)
    b.w(b.p('J15', 4), (647.7, 281.94)); b.rail('GND', (647.7, 281.94), DN)
    # front-panel pots (off-board)
    s.rect(571.5, 292.1, 640.08, 340.36)
    s.text('FRONT PANEL (off-board): 10-turn 10k pots + counting dials', 574.04, 297.18)
    s.text('(Bourns 3590S-2-103). Shielded 3-core cable to J14/J15,', 574.04, 299.72)
    s.text('shield to pin 4 (GND) at the board end only.', 574.04, 302.26)
    for rv, x in (('RV1', 590.55), ('RV2', 621.03)):
        b.pl(rv, x, 322.58, 180)
        b.term(rv, 3); b.term(rv, 2); b.term(rv, 1)
    # C null: U13 follower -> C18 (100p) / C19 (910p via K17) -> K15 -> SUM_HI
    xc = follower(b, 'U13', 683.26, 246.38, 228.6)
    b.term('U13', 3, 5.08)
    b.pl('C18', 703.58, 246.38, 90)
    b.w((xc - 5.08, 246.38), b.p('C18', 1))
    b.pl('K15', 728.98, 241.3, 270); b.F('K15', (719.48, 238.76), (719.48, 241.3), 'right')
    b.w(b.p('C18', 2), b.p('K15', 1)); b.term('K15', 7)
    b.at_pin('K15', 3, UP); b.w(b.p('K15', 5), (739.14, 236.22)); b.rail('GND', (739.14, 236.22), DN)
    b.pl('C19', 703.58, 279.4, 90)
    b.w((xc, 246.38), (xc, 279.4), b.p('C19', 1))
    b.pl('K17', 716.28, 261.62, 0, 'y')          # mirrored: contacts left, coil right
    b.w(b.p('K17', 7), (711.2, 246.38)); b.w(b.p('C19', 2), (711.2, 279.4), b.p('K17', 1))
    b.w(b.p('K17', 5), (726.44, 254.0)); b.rail('GND', (726.44, 254.0), DN)
    b.at_pin('K17', 3, DN)
    # G null: U14 follower -> C20 -> R30 (20k) / R31 (2.2k via K18) -> K16 -> SUM_HI
    xg = follower(b, 'U14', 683.26, 302.26, 284.48)
    b.term('U14', 3, 5.08)
    b.pl('C20', 703.58, 302.26, 90)
    b.w((xg - 5.08, 302.26), b.p('C20', 1))
    b.pl('R30', 723.9, 302.26, 90)
    b.w(b.p('C20', 2), b.p('R30', 1))
    b.pl('K16', 749.3, 297.18, 270); b.F('K16', (739.82, 294.64), (739.82, 297.18), 'right')
    b.w(b.p('R30', 2), b.p('K16', 1)); b.term('K16', 7)
    b.at_pin('K16', 3, UP); b.w(b.p('K16', 5), (759.46, 292.1)); b.rail('GND', (759.46, 292.1), DN)
    b.pl('R31', 718.82, 335.28, 90)
    b.w((711.2, 302.26), (711.2, 335.28), b.p('R31', 1))
    b.pl('K18', 736.6, 317.5, 0, 'y')
    b.w(b.p('K18', 7), (731.52, 302.26)); b.w(b.p('R31', 2), (731.52, 335.28), b.p('K18', 1))
    b.w(b.p('K18', 5), (746.76, 309.88)); b.rail('GND', (746.76, 309.88), DN)
    b.at_pin('K18', 3, DN)
    return b.finish()


# ---------------------------------------------------------------------------------------- ADC
def adc(s):
    refs = ['U21', 'X1', 'R35', 'C54', 'C55', 'C56', 'C57', 'C58', 'C59'] + [f'R{50+i}' for i in range(8)] + [f'C{50+i}' for i in range(4)]
    b = Block(s, refs)
    b.pl('U21', 165.1, 482.6); b.F('U21', (165.1, 463.55), (165.1, 466.09), None)
    b.at_pin('U21', 1, UP); b.at_pin('U21', 20, UP)
    src = ['VDC_DRV', 'IHI_OUT', 'ILO_OUT', 'VAC_DRV']
    ain = [3, 6, 7, 10]
    for k in range(4):
        y = 419.1 + 17.78 * k
        r1, r2, c = f'R{50+2*k}', f'R{51+2*k}', f'C{50+k}'
        b.pl(r1, 43.18, y, 90); b.term(r1, 1, 5.08)
        b.pl(r2, 55.88, y + 3.81); b.at_pin(r2, 2, DN)
        b.pl(c, 71.12, y + 3.81); b.at_pin(c, 2, DN)
        xk = 140.97 - 5.08 * k
        b.w(b.p(r1, 2), (xk, y), (xk, b.p('U21', ain[k])[1]), b.p('U21', ain[k]))
    b.w(b.p('U21', 18), (189.23, 474.98), (189.23, 459.74), (194.31, 459.74))
    b.pl('C54', 194.31, 463.55); b.at_pin('C54', 2, DN)
    # 8.192 MHz clock
    b.pl('X1', 218.44, 452.12); b.F('X1', (226.06, 457.2), (226.06, 459.74), 'left')
    b.at_pin('X1', 14, UP); b.at_pin('X1', 7, DN)
    b.w(b.p('X1', 1), (203.2, 452.12), (203.2, 449.58)); b.rail('+3V3D', (203.2, 449.58), UP)
    b.pl('R35', 233.68, 452.12, 90)
    b.w(b.p('X1', 8), b.p('R35', 1)); b.term('R35', 2)
    b.pl('C59', 246.38, 472.44); b.at_pin('C59', 1, UP); b.at_pin('C59', 2, DN)
    s.text('X1 decoupling', 241.3, 463.55)
    # ADC supply decoupling
    for c, x in (('C55', 147.32), ('C56', 154.94), ('C57', 167.64), ('C58', 175.26)):
        b.pl(c, x, 516.89); b.at_pin(c, 1, UP); b.at_pin(c, 2, DN)
    s.text('U21 decoupling: AVDD (C55, C56), DVDD (C57, C58)', 144.78, 505.46)
    return b.finish()


# ---------------------------------------------------------------------------------------- controller
def controller(s):
    pulls = [f'R{60+i}' for i in range(16)]
    refs = ['A1', 'U22', 'U23', 'C60', 'C61', 'J12', 'J13', 'R80', 'R81', 'R82', 'J11', 'R83', 'R84', 'D4', 'D5'] + pulls
    b = Block(s, refs)
    b.pl('A1', 330.2, 452.12); b.F('A1', (330.2, 419.1), (330.2, 421.64), None)
    for n in [k for k, v in PINNET.items() if k[0] == 'A1' and v == 'PICO_GND']:
        b.term('A1', n[1], 15.24)   # clear of the neighbouring pin labels
    b.pl('U22', 391.16, 436.88); b.pl('U23', 391.16, 485.14)
    b.F('U22', (396.24, 422.91), (396.24, 425.45), 'left'); b.F('U23', (396.24, 471.17), (396.24, 473.71), 'left')
    for u in ('U22', 'U23'):
        b.term(u, 9, 2.54, UP); b.term(u, 10, 2.54, DN)
    for c, y in (('C60', 425.45), ('C61', 473.71)):
        b.pl(c, 426.72, y); b.at_pin(c, 1, UP); b.at_pin(c, 2, DN)
    s.text('Driver decoupling', 419.1, 416.56)
    # power-up pulls: pull-downs pin1 (CTL) on top; pull-ups (R63, R66, R68) flipped so +3V3D is on top
    for i, r in enumerate(pulls):
        x = 449.58 + 10.16 * i
        up = PINNET[(r, '2')] == '+3V3D'
        b.pl(r, x, 414.02, 180 if up else 0)
        b.term(r, 1); b.at_pin(r, 2, UP if up else DN)
    for i, r in enumerate(['R80', 'R81', 'R82']):
        b.pl(r, 734.06 + 10.16 * i, 427.99, 180); b.at_pin(r, 2, UP); b.term(r, 1)
    s.text('R80-R82: CS / SYNC pull-ups', 728.98, 412.75)
    b.pl('J12', 642.62, 457.2); b.pl('J13', 693.42, 452.12)
    b.F('J12', (643.89, 441.96), (643.89, 439.42), None); b.F('J13', (694.69, 441.96), (694.69, 439.42), None)
    # SYNC_IN: J11 -> R84 10k, R83 100k to GND, D4/D5 clamp to +3V3D / GND
    b.pl('J11', 447.04, 485.14, 270); b.at_pin('J11', 2, DN); b.F('J11', (449.58, 492.76), (449.58, 495.3), 'left')
    b.w(b.p('J11', 1), (447.04, 477.52), (462.28, 477.52))
    b.pl('R83', 454.66, 481.33); b.at_pin('R83', 2, DN)
    b.pl('R84', 466.09, 477.52, 90)
    b.pl('D4', 477.52, 473.71, 270); b.at_pin('D4', 1, UP)
    b.pl('D5', 482.6, 481.33, 270); b.at_pin('D5', 2, DN)
    b.w(b.p('R84', 2), (490.22, 477.52)); b.lab('SYNC_IN', (490.22, 477.52), RT)
    return b.finish()


BLOCKS = [decoupling, power, inputs, dac, control, re_mon, nuller, adc, controller]

if __name__ == '__main__':
    import sys as _s
    s = Sch()
    want = _s.argv[1:] or [f.__name__ for f in BLOCKS]
    for f in BLOCKS:
        if f.__name__ in want:
            print(f.__name__, f(s))
    s.save()
