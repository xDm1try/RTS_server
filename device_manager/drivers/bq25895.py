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

    @classmethod
    def is_enabled(cls, i2c) -> bool:
        return cls.I2CADDR in i2c.scan()

    def __init__(self, i2c: I2C, int_pin: Pin, handler=None):
        # self.i2c = I2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=400000)
        # self.not_ce_pin = Pin(not_ce_pin, mode=Pin.OUT)
        # self._user_handler = handler
        self.i2c = i2c
        self._user_handler = handler
        self.pin_intr = int_pin
        self.reset()
        self.pg_stat_last = self._read_byte(0x0B) & 0b00000100
        # self.pin_intr = Pin(intr_pin, mode=Pin.IN, pull=Pin.PULL_UP)
        self.pin_intr.irq(trigger=Pin.IRQ_FALLING, handler=self._int_handler)

    def _int_handler(self, pin):
        reg0b = self._read_byte(0x0B)

        if self.pg_stat_last != reg0b & 0b00000100:
            self.pg_stat_last = reg0b & 0b00000100
            if reg0b & 0b00000100 > 1:
                print("Power reset detected")

        if self._user_handler is not None:
            self._user_handler(self)

    def _read_byte(self, reg) -> int:
        return self.i2c.readfrom_mem(self.I2CADDR, reg, 1)[0]

    def _write_byte(self, reg, value) -> None:
        self.i2c.writeto_mem(self.I2CADDR, reg, bytearray([value]))

    def _set_bit(self, reg, values) -> None:
        assert len(values) == 8, f"Reg has 8 bit (not {len(values)})"
        if len(values) == 8:
            reg_val = self._read_byte(reg)
            reg_val_old = reg_val

            values.reverse()
            for i, value in enumerate(values):
                if value is not None:
                    mask = 1 << i
                    reg_val = (reg_val | mask) if value else (reg_val & ~mask)

            if reg_val != reg_val_old:
                self._write_byte(reg, reg_val)

    def get_byte_bin(self, val) -> str:
        bin_value = "{:08b}".format(val)
        return bin_value

    def get_reg_bin(self, reg) -> str:
        bin_value = "{:08b}".format(self._read_byte(reg))
        return bin_value

    def reset(self) -> None:
        self._set_bit(0x14, [1, None, None, None, None, None, None, None])  # reset chip
        # ADC Conversion Rate Selection  – Start 1s Continuous Conversion
        self._set_bit(0x02, [None, 1, None, None, None, None, None, None])
        self._set_bit(0x07, [None, None, 0, 0, None, None, None, None])  # disable watchdog
        self.set_charge_enable(False)
        self.set_batfet_mode(False)
        # self.set_charge_current(64)
        self.set_charging_termination(False)
        # self.set_charge_voltage(4176)
        # self._set_bit(0x14, [1, None, None, None, None, None, None, None])
        # self._set_bit(0x02, [None, 1, None, None, None, None, None, None])
        # self._set_bit(0x07, [None, None, 0, 0, None, None, None, None])
        # self._set_bit(0x03, [None, 1, None, None, None, None, None, None])

        for i in range(21):
            regs[i] = self._read_byte(i)

    def set_charge_enable(self, mode: bool) -> None:
        self._set_bit(0x03, [None, None, None, mode, None, None, None, None])
        if not mode:
            self.not_ce_pin.on()
        else:
            self.not_ce_pin.off()

    def get_charge_enable(self) -> bool:
        value = int(self.get_reg_bin(0x03)[3])
        return value and not self.not_ce_pin.value()

    def input_type(self) -> int:
        ret = self._read_byte(0x0B)
        return ret >> 5

    def get_input_type_str(self) -> str:
        return VBUS_TYPE[self.input_type()]

    def charge_state(self) -> int:
        ret = self._read_byte(0x0B)
        return (ret & 0b00011000) >> 3

    def get_charge_state(self) -> str:
        return CHRG_STAT[self.charge_state()]

    def power_good_stat(self) -> int:
        ret = self._read_byte(0x0B)
        return (ret & 0b00000100) >> 2

    def power_good_stat_str(self) -> str:
        return PG_STAT[self.power_good_stat()]

    def adc_battery_volt(self) -> int:
        ret = self._read_byte(0x0E)
        return 2304 + (int(ret & 0b01111111) * 20)

    def adc_vbus_volt(self) -> int:
        ret = self._read_byte(0x11)
        return 2600 + (int(ret & 0b01111111) * 100)

    def adc_charge_current(self) -> int:
        ret = self._read_byte(0x12)
        return int(ret & 0b01111111) * 50

    def set_charge_current(self, m_A) -> None:
        assert 64 <= m_A <= 5056, f"Charge current range is [64, 5056] mA. ({m_A})"
        m_A -= m_A % 64
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

    def get_charge_current(self) -> int:
        reg_val = self._read_byte(0x04)
        current_bin = reg_val & 0b01111111
        current = current_bin * 64
        return current

    def set_precharge_threshold(self, precharge_mV) -> None:
        assert precharge_mV == 2800 or precharge_mV == 3000, "Precharge to Fast Charge Threshold"
        mode = 1 if precharge_mV == 3000 else 2800
        self._set_bit(0x06, [
            None,
            None,
            None,
            None,
            None,
            None,
            mode,
            None,
        ])

    def get_precharge_threshold(self) -> int:
        reg_val = self._read_byte(0x06)
        mode = reg_val & 0b00000010
        return 3000 if mode else 2800

    def set_current_cut_off(self, m_A) -> None:
        assert 64 <= m_A <= 1024, f"Cut off current must be in range [64, 1024] mA ({m_A})"
        m_A -= m_A % 64

        reg_val = m_A - 64
        reg_val = int(reg_val / 64)

        self._set_bit(0x05, [
            None,
            None,
            None,
            None,
            1 if reg_val & 0b00001000 else 0,
            1 if reg_val & 0b00000100 else 0,
            1 if reg_val & 0b00000010 else 0,
            1 if reg_val & 0b00000001 else 0
        ])

    def get_current_cut_off(self) -> int:
        reg_val = self._read_byte(0x05)
        current_bin = reg_val & 0b00001111
        current = current_bin * 64
        return current

    def set_current_precharge_limit(self, m_A):
        assert 64 <= m_A <= 1024, f"Precharge current must be in range [64, 1024] mA ({m_A})"
        m_A -= m_A % 64

        reg_val = m_A - 64
        reg_val = int(reg_val / 64)

        self._set_bit(0x05, [
            1 if reg_val & 0b00001000 else 0,
            1 if reg_val & 0b00000100 else 0,
            1 if reg_val & 0b00000010 else 0,
            1 if reg_val & 0b00000001 else 0,
            None,
            None,
            None,
            None
        ])

    def get_current_precharge_limit(self) -> int:
        reg_val = self._read_byte(0x05)
        current_bin = reg_val & 0b11110000
        current = current_bin * 64
        return current

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

    def get_charging_termination(self) -> int:
        reg_val: int = self._read_byte(0x07)
        mode: int = (reg_val & 0b10000000)
        return mode

    def get_batfet_mode(self) -> None:
        reg_val = self._read_byte(0x09)
        mode = reg_val & 0b00100000
        return mode

    def set_batfet_mode(self, mode) -> None:
        self._set_bit(0x09, [None, None, mode, None, None, None, None, None])

    def set_charge_voltage(self, voltage) -> None:
        assert 3840 <= voltage <= 4608, "Charge voltage must be in range [3840, 4608]"
        voltage_additional = voltage - 3840
        reg_val = int(voltage_additional / 16)
        voltage -= voltage % 16

        self._set_bit(0x06, [
            1 if reg_val & 0b00100000 else 0,
            1 if reg_val & 0b00010000 else 0,
            1 if reg_val & 0b00001000 else 0,
            1 if reg_val & 0b00000100 else 0,
            1 if reg_val & 0b00000010 else 0,
            1 if reg_val & 0b00000001 else 0,
            None,
            None
        ])

    def get_charge_voltage(self) -> float:
        reg_val: int = self._read_byte(0x06)
        voltage_bin: int = (reg_val & 0b11111100) >> 2
        voltage = (voltage_bin * 16) + 3840
        return voltage


def handler_all_regs(bq: BQ25895):
    print("INTERRUPTION: ", "=" * 5)
    for i, old_val in enumerate(regs):
        new_val = bq._read_byte(i)
        if new_val != old_val:
            print(f"INT: REG{hex(i)}: ", bq.get_byte_bin(old_val), " -> ", bq.get_byte_bin(new_val))
            regs[i] = new_val

    print("Ichg: ", bq.adc_charge_current())
    print("Vbat: ", bq.adc_battery_volt())
    print("=" * 10)


# def get_current(bq: BQ25895, sleep: int, func=None):
#     import time
#     bq.set_baterry_charge(True)
#     time.sleep(sleep//2)
#     print("CURRENT: ", bq.adc_charge_current())
#     time.sleep(sleep//2)
#     bq.set_baterry_charge(False)


# from bqv3 import *;bq = BQ25895(sda_pin=4, scl_pin=5, intr_pin=14, not_ce_pin=12, handler=handler_all_regs)

def set_current_limits(bq: BQ25895):
    bq.set_charging_termination(False)
    bq.set_charge_current(128)
    bq.set_current_cut_off(64)


def test_bq(bq: BQ25895):
    for i in range(5):
        print("VBUS Type:", bq.vbus_type_str())
        print("Charge Status:", bq.chrg_stat_str())
        print("Battery Voltage (mV):", bq.adc_battery_volt())
        print("Charge Current (mA):", bq.adc_charge_current())
        time.sleep(1)
