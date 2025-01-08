from machine import I2C, Pin
import time

VBUS_TYPE = ['NONE',
             'SDP',
             'CDP (1.5A)',
             'USB_DCP (3.25A)',
             'MAXC (1.5A)',
             'UNKNOWN (500mA)',
             'NONSTAND (1A/2A/2.1A/2.4A)',
             'VBUS_OTG']

CHRG_STAT = ['Not Charging',
             'Pre-charge',
             'Fast Charging',
             'Charge Termination Done']

PG_STAT = ['Not Power Good',
           'Power Good']

regs = [None for _ in range(21)]


class BQ25895:
    I2CADDR = 0x6A

    def __init__(self, sda_pin, scl_pin, intr_pin, not_ce_pin, handler=None):
        self.i2c = I2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
        self.not_ce_pin = Pin(not_ce_pin, mode=Pin.OUT)
        self._user_handler = handler
        self.reset()
        self.pg_stat_last = self.read_byte(0x0B) & 0b00000100
        self.pin_intr = Pin(intr_pin, mode=Pin.IN, pull=Pin.PULL_UP)
        self.pin_intr.irq(trigger=Pin.IRQ_FALLING, handler=self._int_handler)

    def _int_handler(self, pin):
        reg0b = self.read_byte(0x0B)

        if self.pg_stat_last != reg0b & 0b00000100:
            self.pg_stat_last = reg0b & 0b00000100
            if reg0b & 0b00000100 > 1:
                print("Power reset detected")

        if self._user_handler is not None:
            self._user_handler(self)

    def read_byte(self, reg):
        return self.i2c.readfrom_mem(self.I2CADDR, reg, 1)[0]

    def get_byte_bin(self, val):
        bin_value = "{:08b}".format(val)
        return bin_value

    def get_reg_bin(self, reg):
        bin_value = "{:08b}".format(self.read_byte(reg))
        return bin_value

    def write_byte(self, reg, value):
        self.i2c.writeto_mem(self.I2CADDR, reg, bytearray([value]))

    def reset(self):
        self._set_bit(0x14, [1, None, None, None, None, None, None, None])
        self._set_bit(0x02, [None, 1, None, None, None, None, None, None])
        self._set_bit(0x07, [None, None, 0, 0, None, None, None, None])
        self._set_bit(0x03, [None, 1, None, None, None, None, None, None])

        for i in range(21):
            regs[i] = self.read_byte(i)

    def set_baterry_charge(self, mode: bool):
        if not mode:
            self.not_ce_pin.on()
        else:
            self.not_ce_pin.off()

    def _set_bit(self, reg, values):
        if len(values) == 8:
            reg_val = self.read_byte(reg)
            reg_val_old = reg_val

            for i, value in enumerate(values):
                if value is not None:
                    mask = 1 << i
                    reg_val = (reg_val | mask) if value else (reg_val & ~mask)

            if reg_val != reg_val_old:
                self.write_byte(reg, reg_val)

    def vbus_type(self):
        ret = self.read_byte(0x0B)
        return ret >> 5

    def vbus_type_str(self):
        return VBUS_TYPE[self.vbus_type()]

    def chrg_stat(self):
        ret = self.read_byte(0x0B)
        return (ret & 0b00011000) >> 3

    def chrg_stat_str(self):
        return CHRG_STAT[self.chrg_stat()]

    def pg_stat(self):
        ret = self.read_byte(0x0B)
        return (ret & 0b00000100) >> 2

    def pg_stat_str(self):
        return PG_STAT[self.pg_stat()]

    def read_battery_volt(self):
        ret = self.read_byte(0x0E)
        return 2304 + (int(ret & 0b01111111) * 20)

    def read_vbus_volt(self):
        ret = self.read_byte(0x11)
        return 2600 + (int(ret & 0b01111111) * 100)

    def read_charge_current(self):
        ret = self.read_byte(0x12)
        return int(ret & 0b01111111) * 50

    def set_charge_current(self, m_A):
        if m_A > 5056:
            m_A = 5056
        reg_val = int(m_A / 64)
        self._set_bit(0x04, [
            None,
            1 if reg_val & 0b01000000 else 0,
            1 if reg_val & 0b00100000 else 0,
            1 if reg_val & 0b00010000 else 0,
            1 if reg_val & 0b00001000 else 0,
            1 if reg_val & 0b00000100 else 0,
            1 if reg_val & 0b00000010 else 0,
            1 if reg_val & 0b00000001 else 0
        ])

    def set_current_cut_off(self, m_A):
        assert m_A <= 1024, f"Cut off current more than 1024 ({m_A})"
        assert m_A >= 64, f"Cut off current less than 64 ({m_A})"
        assert m_A % 64 == 0, f"Cut off current step is 64 ({m_A})"

        reg_val = m_A - 64
        reg_val = int(reg_val / 64)

        self._set_bit(0x04, [
            None,
            None,
            None,
            None,
            1 if reg_val & 0b00001000 else 0,
            1 if reg_val & 0b00000100 else 0,
            1 if reg_val & 0b00000010 else 0,
            1 if reg_val & 0b00000001 else 0
        ])

    def set_current_precharge_limit(self, m_A):
        assert m_A <= 1024, f"Precharge current limit more than 1024 ({m_A})"
        assert m_A >= 64, f"Precharge current limit less than 64 ({m_A})"
        assert m_A % 64 == 0, f"Precharge current limit step is 64 ({m_A})"

        reg_val = m_A - 64
        reg_val = int(reg_val / 64)

        self._set_bit(0x04, [
            1 if reg_val & 0b00001000 else 0,
            1 if reg_val & 0b00000100 else 0,
            1 if reg_val & 0b00000010 else 0,
            1 if reg_val & 0b00000001 else 0,
            None,
            None,
            None,
            None
        ])

    def set_charging_termination(self, mode: bool):
        self._set_bit(0x07, [
            mode,
            None,
            None,
            None,
            None,
            None,
            None,
            None
        ])


def handler_all_regs(bq: BQ25895):
    print("INTERRUPTION: ", "=" * 5)
    for i, old_val in enumerate(regs):
        new_val = bq.read_byte(i)
        if new_val != old_val:
            print(f"INT: REG{hex(i)}: ", bq.get_byte_bin(old_val), " -> ", bq.get_byte_bin(new_val))
            regs[i] = new_val
    print("=" * 10)


# from bqv3 import *;bq = BQ25895(sda_pin=4, scl_pin=5, intr_pin=14, not_ce_pin=12, handler=handler_all_regs)

def set_current_limits(bq: BQ25895):
    bq.set_charging_termination(False)
    bq.set_charge_current(128)
    bq.set_current_cut_off(64)


def test_bq(bq):
    for i in range(5):
        print("VBUS Type:", bq.vbus_type_str())
        print("Charge Status:", bq.chrg_stat_str())
        print("Battery Voltage (mV):", bq.read_battery_volt())
        print("Charge Current (mA):", bq.read_charge_current())
        time.sleep(1)
