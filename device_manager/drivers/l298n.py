import gc
from machine import Pin, PWM


class L298N_short:
    def __init__(self, pwm_pim: PWM, freq: int):
        self.pwm = pwm_pim
        self.freq = freq
        self.duty = 0
        self.set_duty(self.duty)

    def set_duty(self, percentage) -> None:
        assert 0 <= percentage <= 100, f"PWM duty have to be in range [0..100]. Not {percentage}"
        self.pwm.duty(1023 * percentage // 100)
        self.duty = percentage

    def increase_current(self, step: int = 5) -> None:
        if self.duty == 100:
            return
        new_duty = 100 if self.duty + step > 100 else self.duty + step
        self.set_duty(new_duty)

    def decrease_current(self, step: int = 5) -> None:
        new_duty = 0 if self.duty - step <= 0 else self.duty - step
        self.set_duty(new_duty)

    def get_duty(self) -> int:
        return self.duty
