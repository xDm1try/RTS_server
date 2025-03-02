from machine import PWM, Pin
from device_manager.interfaces.load_abc import LoadABC
from device_manager.drivers.l298n import L298N_short


class LoadL298N(LoadABC):
    def __init__(self, pwm_pin: PWM, freq=15000):
        self.pwm = pwm_pin
        self.freq = freq
        self.l298 = L298N_short(self.pwm, freq)

    def increase_current(self) -> None:
        if self.l298.duty == 100:
            return
        new_duty = self.l298.duty + 1
        self.l298.set_duty(new_duty)

    def decrease_current(self) -> None:
        new_duty = self.l298.duty - 1
        if new_duty <= 0:
            return
        self.l298.set_duty(new_duty)

    def set_duty(self, new_duty: int) -> None:
        self.l298.set_duty(new_duty)

    def get_duty(self) -> int:
        return self.l298.duty
