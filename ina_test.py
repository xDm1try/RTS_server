"""Sample code and test for barbudor_ina3221"""

from bqv3 import *
import time
import sys
from machine import Pin, SoftI2C
from ina3221 import *
i2c_bus = SoftI2C(scl=Pin(5), sda=Pin(4), freq=400000)
ina1 = INA3221(i2c_bus)
# ina2 = INA3221(i2c_bus, 65)
# change configuration (requires 'full' version of the lib)
if INA3221.IS_FULL_API:
    print("full API sample: improve accuracy")
    # improve accuracy by slower conversion and higher averaging
    # each conversion now takes 128*0.008 = 1.024 sec
    # which means 2 seconds per channel
ina1.update(reg=C_REG_CONFIG,
                mask=C_AVERAGING_MASK |
                C_VBUS_CONV_TIME_MASK |
                C_SHUNT_CONV_TIME_MASK |
                C_MODE_MASK,
                value=C_AVERAGING_1024_SAMPLES |
                C_VBUS_CONV_TIME_8MS |
                C_SHUNT_CONV_TIME_8MS |
                C_MODE_SHUNT_AND_BUS_CONTINOUS)
    # ina2.update(reg=C_REG_CONFIG,
    #             mask=C_AVERAGING_MASK |
    #             C_VBUS_CONV_TIME_MASK |
    #             C_SHUNT_CONV_TIME_MASK |
    #             C_MODE_MASK,
    #             value=C_AVERAGING_256_SAMPLES |
    #             C_VBUS_CONV_TIME_8MS |
    #             C_SHUNT_CONV_TIME_8MS |
    #             C_MODE_SHUNT_AND_BUS_CONTINOUS)


# enable all 3 channels. You can comment (#) a line to disable one
# bq = BQ25895(sda_pin=4, scl_pin=5, intr_pin=14, not_ce_pin=12)

ina1.enable_channel(1)
ina1.enable_channel(2)
ina1.enable_channel(3)

# ina2.enable_channel(1)
# ina2.enable_channel(2)
# ina2.enable_channel(3)
# pylint: disable=bad-whitespace


def show_ina(ina3221):
    while True:
        if INA3221.IS_FULL_API:  # is_ready available only in "full" variant
            while not ina3221.is_ready:
                print(".", end='')
                time.sleep(0.1)
            print("")

        print("------------------------------")
        line_title = "Measurement   "
        line_psu_voltage = "PSU voltage   "
        line_load_voltage = "Load voltage  "
        line_shunt_voltage = "Shunt voltage "
        line_current = "Current       "

        for chan in range(1, 4):
            if ina3221.is_channel_enabled(chan):
                #
                bus_voltage = ina3221.bus_voltage(chan)
                shunt_voltage = ina3221.shunt_voltage(chan)
                current = ina3221.current(chan)
                #
                line_title += "| Chan#{:d}      ".format(chan)
                # line_psu_voltage += "| {:6.3f}  mV ".format((bus_voltage + shunt_voltage) * 1000)
                line_load_voltage += "| {:6.3f}  mV ".format(bus_voltage * 1000)
                line_shunt_voltage += "| {:9.3f} mV ".format(shunt_voltage * 1000)
                line_current += "| {:9.3f} mA ".format(current * 1000)

        print(line_title)
        print(line_psu_voltage)
        print(line_load_voltage)
        print(line_shunt_voltage)
        print(line_current)

        time.sleep(2.0)

# from ina_test import *;bq.set_charge_enable(True);show_ina(ina1)