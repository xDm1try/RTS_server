from machine import Pin, PWM


class L298N_short:
    def __init__(self, pwm_pim: PWM, freq: int):
        self.pwm = pwm_pim
        self.freq = freq
        self.duty = 0
        self.set_duty(self.duty)

    def set_duty(self, percentage) -> None:
        self.pwm.duty(percentage)
        self.duty = percentage
