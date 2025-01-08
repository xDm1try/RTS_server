from bqv3 import BQ25895, test_bq
from time import sleep

# bq = BQ25895(sda_pin=4, scl_pin=5, intr_pin=14, not_ce_pin=12)


def charge(bq):
    bq.set_baterry_charge(False)
    # charge voltage default is 4,20

    bq.set_charge_current(128)
    # set current limin, disable termination
    bq._set_bit(0x07, [0, None, None, None, None, None, None, None])
    bq._set_bit(0x05, [None, None, None, None, 0, 0, 0, 0])

    bq.set_baterry_charge(True)
    current = bq.read_charge_current()
    while current >= 50:
        print(f"Vbat={bq.read_battery_volt} Ichg={current}")
        current = bq.read_charge_current()
    bq.set_baterry_charge(False)
