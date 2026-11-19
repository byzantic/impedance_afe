"""Redraw the TIA block (U5 high-gain TIA with K1..K6 range ladder, Q1/Q2 steering, U6 low-gain TIA) fully wired."""
from redraw import *  # noqa

REFS = (['J7', 'U5', 'R32', 'J9', 'Q1', 'Q2', 'U6', 'R33', 'C27', 'R34', 'J10'] +
        [f'R{40+i}' for i in range(1, 7)] + [f'C{40+i}' for i in range(1, 7)] + [f'K{i}' for i in range(1, 7)])


def F(s, ref, ref_xy, val_xy, just='left'):
    """place Reference/Value at absolute points, horizontal text (field angle compensates symbol rotation)"""
    r = s.at(s.sym(ref))[2] % 360
    a = (-r) % 360 if r in (90, 270) else 0
    if r == 180:                       # KiCad mirrors the justification of 180-degree symbols
        just = {'left': 'right', 'right': 'left'}.get(just, just)
    s.field_at(ref, 'Reference', *ref_xy, angle=a, justify=just)
    s.field_at(ref, 'Value', *val_xy, angle=a, justify=just)


def draw(s):
    strip(s, REFS)
    d = Drawing(s)
    Y_IHI, Y_SUM = 45.72, 86.36
    X0, PITCH = 609.6, 30.48

    # ---------------- range ladder: relay contact -> FBn -> Rf || Cf -> SUM_HI
    cols = []
    for i in range(6):
        xk = X0 + PITCH * i
        k, r, c = f'K{i+1}', f'R{41+i}', f'C{41+i}'
        s.move(k, xk, 58.42, 0)
        xr, xc = xk + 5.08, xk + 12.7
        s.move(r, xr, 78.74, 180)      # pin2 (FBn) top, pin1 (SUM_HI) bottom
        s.move(c, xc, 78.74, 180)
        p7, p1, p5, p3 = (s.pin(k, n) for n in (7, 1, 5, 3))
        d.w(p7, (p7[0], Y_IHI))
        d.w(p1, (p1[0], 71.12), (xc, 71.12), s.pin(c, 2))
        d.w((xr, 71.12), s.pin(r, 2))
        d.w(s.pin(r, 1), (xr, Y_SUM)); d.w(s.pin(c, 1), (xc, Y_SUM))
        d.w(p5, (p5[0], 48.26), (xk - 10.16, 48.26))
        s.power('power:GND', 'GND', xk - 10.16, 48.26)
        d.w(p3, (p3[0], 67.31))
        s.label(f'KD{i}', p3[0], 67.31, 270)
        s.label(f'FB{i+1}', xr + 1.27, 71.12, 0)
        cols.append((xr, xc))

    # ---------------- U5 high-gain TIA, WE BNC
    s.move('U5', 609.6, 106.68, 0)
    XS = 594.36                                        # SUM_HI riser
    XO = 787.4                                         # output riser
    u2, u3, u6 = s.pin('U5', 2), s.pin('U5', 3), s.pin('U5', 6)
    d.w((XS, Y_SUM), (cols[-1][1], Y_SUM))
    d.w((XS, Y_SUM), (XS, u2[1]), u2)
    d.w(u3, (u3[0] - 2.54, u3[1])); s.power('power:GND', 'GND', u3[0] - 2.54, u3[1])
    s.power('power:+15V', '+15V', *s.pin('U5', 7))
    s.power('power:-15V', '-15V', *s.pin('U5', 4), 180)
    for n in (1, 5, 8):
        s.no_connect(*s.pin('U5', n))
    s.move('J7', XS, 124.46, 270)                      # pin1 up, shield left
    d.w((XS, u2[1]), s.pin('J7', 1))
    js = s.pin('J7', 2); d.w(js, (js[0], js[1])); s.power('power:GND', 'GND', *js)
    d.w((XS, Y_SUM), (XS - 7.62, Y_SUM)); s.label('SUM_HI', XS - 7.62, Y_SUM, 180)
    # output: right under the ladder, up to the IHI_OUT bus; R32 -> I_HI BNC
    d.w(u6, (XO, u6[1]), (XO, Y_IHI), (X0 + 5.08, Y_IHI))
    d.w((XO, Y_IHI), (XO + 7.62, Y_IHI)); s.label('IHI_OUT', XO + 7.62, Y_IHI, 0)
    s.move('R32', 797.56, u6[1], 90)
    s.move('J9', 816.61, u6[1], 0)
    d.w((XO, u6[1]), s.pin('R32', 1)); d.w(s.pin('R32', 2), s.pin('J9', 1))
    s.label('IHI_BNC', s.pin('R32', 2)[0] + 1.27, u6[1], 0)
    s.power('power:GND', 'GND', *s.pin('J9', 2))

    # ---------------- Q1/Q2 C-B junctions (B+E tied), anti-parallel between SUM_HI and SUM_LO
    # 2N3904 pins: 1 = E, 2 = B, 3 = C.  Q1: B,E = SUM_HI, C = SUM_LO.  Q2: B,E = SUM_LO, C = SUM_HI.
    Y_HI, Y_LO = 132.08, 147.32
    s.move('Q1', 614.68, 137.16, 180)      # E top, C bottom, B right
    s.move('Q2', 637.54, 137.16, 0)        # C top, E bottom, B left
    XB = 599.44
    d.w((XB, u2[1]), (XB, Y_HI), s.pin('Q2', 3))
    qb = s.pin('Q1', 2); d.w(qb, (qb[0] + 2.54, qb[1]), (qb[0] + 2.54, Y_HI))
    d.w(s.pin('Q1', 3), (s.pin('Q1', 3)[0], Y_LO))
    d.w(s.pin('Q2', 1), (s.pin('Q2', 1)[0], Y_LO))
    qb = s.pin('Q2', 2); d.w(qb, (qb[0] - 2.54, qb[1]), (qb[0] - 2.54, Y_LO))

    # ---------------- U6 low-gain TIA, R33 || C27, R34 -> I_LO BNC
    s.move('U6', 670.56, 144.78, 0)
    v2, v3, v6 = s.pin('U6', 2), s.pin('U6', 3), s.pin('U6', 6)
    d.w((s.pin('Q1', 3)[0], Y_LO), v2)
    s.label('SUM_LO', 647.7, Y_LO, 0)
    d.w(v3, (v3[0] - 2.54, v3[1])); s.power('power:GND', 'GND', v3[0] - 2.54, v3[1])
    s.power('power:+15V', '+15V', *s.pin('U6', 7))
    s.power('power:-15V', '-15V', *s.pin('U6', 4), 180)
    for n in (1, 5, 8):
        s.no_connect(*s.pin('U6', n))
    XL, XR = 655.32, 683.26
    s.move('R33', 668.02, 160.02, 90)
    s.move('C27', 668.02, 167.64, 90)
    d.w((XL, Y_LO), (XL, 167.64), s.pin('C27', 1)); d.w((XL, 160.02), s.pin('R33', 1))
    d.w(s.pin('C27', 2), (XR, 167.64), (XR, v6[1])); d.w(s.pin('R33', 2), (XR, 160.02))
    d.w(v6, (XR, v6[1]))
    s.move('R34', 693.42, v6[1], 90)
    s.move('J10', 712.47, v6[1], 0)
    d.w((XR, v6[1]), s.pin('R34', 1)); d.w(s.pin('R34', 2), s.pin('J10', 1))
    s.label('ILO_BNC', s.pin('R34', 2)[0] + 1.27, v6[1], 0)
    s.power('power:GND', 'GND', *s.pin('J10', 2))
    d.w((XR, 167.64), (XR, 172.72)); s.label('ILO_OUT', XR, 172.72, 270)


    # ---------------- field placement
    for i in range(6):
        xk = X0 + PITCH * i
        xr, xc = cols[i]
        F(s, f'K{i+1}', (xk - 8.89, 57.15), (xk - 8.89, 59.69), 'right')
        F(s, f'R{41+i}', (xr - 2.54, 73.66), (xr - 2.54, 76.2), 'right')
        F(s, f'C{41+i}', (xc + 2.54, 80.01), (xc + 2.54, 82.55), 'left')
    F(s, 'J7', (XS + 3.81, 123.19), (XS + 3.81, 125.73), 'left')
    F(s, 'Q1', (609.6, 139.7), (609.6, 142.24), 'right')
    F(s, 'Q2', (642.62, 129.54), (642.62, 132.08 - 4.0), 'left')
    F(s, 'U6', (671.83, 134.62), (671.83, 137.16), 'left')
    F(s, 'R32', (795.02, 101.6), (795.02, 104.14), 'left')
    F(s, 'R34', (690.88, 139.7), (690.88, 142.24), 'left')
    F(s, 'R33', (662.94, 163.83), (670.56, 163.83), 'left')
    F(s, 'C27', (662.94, 171.45), (670.56, 171.45), 'left')

    d.pins_of(REFS)
    return d.emit()


if __name__ == '__main__':
    s = Sch()
    print('wires', draw(s))
    s.save()
