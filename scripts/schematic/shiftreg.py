"""One-off: relay lines from 2x 74HC595 on SPI instead of 16 Pico GPIOs (Pico 2 / ESP32-S3-ETH compatible pin map).

Adds U27/U28 (74HC595), R76 (RLY_OE pull-up), C62/C63; removes J12 (CTL fallback header); J13 becomes a 2x8
right-angle box header carrying RLY_LATCH/RLY_OE too; re-terminates A1 (new pin map) and J17 (signals on the
even row).  Nets come from scripts/design.py.
"""
from redraw import *  # noqa
from hat_split import prune


def main():
    s = Sch()
    for ref in ('J12', 'J13'):
        strip(s, [ref])
        s.remove(s.sym(ref))
    s.add_symbol('Connector_Generic:Conn_02x08_Odd_Even', 'J13', 'SPI/AUX', 'Connector_IDC:IDC-Header_2x08_P2.54mm_Horizontal',
                 693.42, 454.66, 0, {'MPN': '2x8 shrouded box header, right angle',
                                     'Note': 'external SPI master port: HAT and relays with the controller absent or in reset'})
    s.add_symbol('74xx:74HC595', 'U27', '74HC595', 'Package_DIP:DIP-16_W7.62mm_Socket', 523.24, 452.12, 0)
    s.add_symbol('74xx:74HC595', 'U28', '74HC595', 'Package_DIP:DIP-16_W7.62mm_Socket', 574.04, 452.12, 0,
                 {'Note': 'QH (pin 9) unused'})
    s.add_symbol('Device:R', 'R76', '10k', design.FP['R'], 607.06, 441.96, 0,
                 {'Note': '595 outputs off (Hi-Z) until firmware drives RLY_OE low'})
    s.add_symbol('Device:C', 'C62', '100n', design.FP['C'], 607.06, 469.9, 0)
    s.add_symbol('Device:C', 'C63', '100n', design.FP['C'], 619.76, 469.9, 0)
    s.set_prop('A1', 'Footprint', 'afe:Pico2_ESP32-S3-ETH_THT')
    s.set_prop('A1', 'Value', 'Pico 2 / ESP32-S3-ETH')
    s.set_prop('A1', 'MPN', 'SC1631 (Pico 2) or Waveshare ESP32-S3-ETH, on 2x 1x20 sockets')

    b = Block(s, ['A1', 'J17', 'J13', 'U27', 'U28', 'R76', 'C62', 'C63'])
    for ref in ('U27', 'U28'):
        x, y, _ = s.at(s.sym(ref))
        b.F(ref, (x + 2.54, y - 16.51), (x + 2.54, y - 13.97))
    for n in (3, 8, 13, 18, 23, 28, 33, 38):   # GND pins: symbol clear of the signal labels
        b.term('A1', n, 17.78)
    b.finish()
    prune(s)

    for t in s.items('text'):
        v = val(t)
        if v.startswith('CONTROL: Pico 2'):
            t[1] = S('CONTROL: Pico 2 or Waveshare ESP32-S3-ETH (socketed; same header pins) -> SPI -> U27/U28 74HC595 -> CTL0..15 -> '
                     '2x TBD62783A high-side drivers -> relay coils.\\n'
                     'U27 QA..QH = CTL0..7, U28 QA..QH = CTL8..15 (MOSI -> U27 -> U28). Driver channel m (KDm) is driven by CTL(15-m); '
                     'the order is for routing, firmware maps it.\\n'
                     'RLY_OE is pulled high (595 outputs Hi-Z) until firmware loads the latches and drives it low; the 4.7k pulls set '
                     'the power-up state: ON = CTL3 (1M), CTL6 (DEV), CTL8 (RE_LOCAL).\\n'
                     'Pins (Pico GP / ESP32 IO): 4 RLY_LATCH (GP2/IO48), 5 RLY_OE (GP3/IO47), 21 AUX (GP16/IO43), 22 SYNC_IN (GP17/IO44), '
                     '24 ADC_SYNC (GP18/IO0), 25 MOSI (GP19/IO1),\\n'
                     '26 MISO (GP20/IO2), 27 clock (GP21 GPOUT0/IO3), 29 SCK (GP22/IO15), 31 CS_ADC (GP26/IO18), 32 CS_DAC (GP27/IO16), '
                     '34 ADC_DRDY (GP28/IO17).\\n'
                     'J13 = external SPI master port (relays + HAT with the controller absent or held in reset).')
        elif v.startswith('J16: ADC/DAC sub-board'):
            t[1] = S(v.replace('J17: analog link to the sub-board (ADCn N tied to GND here).',
                               'J17: analog link to the sub-board; signals on the even pins, GND on the odd pins (ADCn N tied to GND here).'))
        elif v.startswith('ADC (on the HAT'):
            t[1] = S(v.replace('Clock: Pico GP21 8.000 MHz (R47 -> J16 pin 7) or the HAT oscillator.',
                               'Clock: Pico GP21 8.000 MHz (R47 -> J16 pin 7) or the HAT oscillator (needed with the ESP32-S3).'))
    s.save()



if __name__ == '__main__':
    main()
