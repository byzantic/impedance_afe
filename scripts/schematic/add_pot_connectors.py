"""One-off: nuller pots go off-board (panel 10-turn), each via a 4-pin Molex KK 254 connector.
J14 (C null, RV1): 1 NULL_NEG (CW), 2 NC_WIP (wiper), 3 GND (CCW), 4 GND (cable shield)
J15 (G null, RV2): 1 NULL_NEG (CW), 2 NG_WIP (wiper), 3 RE_MON (CCW), 4 GND (cable shield)
Connections are made with labels here; nuller.py redraws them.
"""
from sch import *  # noqa
from rails_to_power import RAILS, orient, lib_power

KK = 'Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical'
PANEL = 'Bourns 3590S-2-103 10-turn 10k + counting dial (panel, off-board)'


def add(s):
    for ref, wip, ccw, x, y, what in [('J14', 'NC_WIP', 'GND', 759.46, 299.72, 'C-null pot RV1'),
                                      ('J15', 'NG_WIP', 'RE_MON', 759.46, 320.04, 'G-null pot RV2')]:
        s.add_symbol('Connector_Generic:Conn_01x04', ref, 'POT ' + what.split()[0], KK, x, y, 0,
                     {'MPN': 'Molex 22-27-2041 (KK 254 header); mate 22-01-3047 + 08-50-0114 crimps',
                      'Note': f'{what}: 1 CW, 2 wiper, 3 CCW, 4 cable shield (GND, board end only)'})
        for n, net in zip('1234', ['NULL_NEG', wip, ccw, 'GND']):
            px, py = s.pin(ref, n)
            dx, dy = s.pin_dir(ref, n)
            q = (px + 2.54 * dx, py + 2.54 * dy)
            s.wire([(px, py), q])
            if net in RAILS:
                s.power(RAILS[net], net, *q, orient(RAILS[net], dx, dy))
            else:
                s.label(net, *q, 180 if dx < 0 else 0)
    for rv in ('RV1', 'RV2'):
        s.set_flag(rv, 'on_board', False)
        s.set_prop(rv, 'Footprint', '')
        s.set_prop(rv, 'Value', '10k 10-turn panel')
        s.set_prop(rv, 'MPN', PANEL)
        s.set_prop(rv, 'Note', 'off-board front-panel pot, wired to ' + ('J14' if rv == 'RV1' else 'J15'))


if __name__ == '__main__':
    s = Sch()
    add(s)
    s.save()
    print(s.lib_pins('Connector_Generic:Conn_01x04'))
