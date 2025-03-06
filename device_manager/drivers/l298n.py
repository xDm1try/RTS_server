from machine import Pin, PWM


class L298N_short:
    def __init__(self, pwm_pim: PWM, freq: int):
        self.pwm = pwm_pim
        self.freq = freq
        self.duty = 0
        self.set_duty(self.duty)

    def set_duty(self, percentage) -> None:
        assert 0 <= percentage <= 100, f"PWM duty have to be in range [0..100]. Not {percentage}"
        self.pwm.duty(percentage)
        self.duty = percentage

    def increase_current(self) -> None:
        if self.duty == 100:
            return
        new_duty = self.duty + 1
        self.set_duty(new_duty)

    def decrease_current(self) -> None:
        new_duty = self.duty - 1
        if new_duty <= 0:
            return
        self.set_duty(new_duty)