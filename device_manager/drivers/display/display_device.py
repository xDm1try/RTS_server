from device_manager.drivers.display.ST7735 import TFT
from device_manager.drivers.display.sysfont import sysfont
from machine import SPI, Pin
import time
import math

# spi = SPI(2, baudrate=20000000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
# tft = self.tft(spi, 33, 25, 15)
# tft.initr()
# tft.rgb(True)


class DisplayDevice:
    def __init__(self, spi: SPI, aDC: int, aRESET: int, aCS: int):
        self.spi = spi
        self.tft = TFT(spi, aDC, aRESET, aCS)
        self.tft.initr()
        self.tft.rgb(True)
        self.tft.fill(TFT.BLACK)
        v = 0
        self.tft.text((0, v), "Display initialized", self.tft.WHITE, sysfont, 1, nowrap=True)

    def show(self, time_value: str, chg_status: str, v_bat: int, current_bat: int, input_status: str, temp_env: float,
             temp_bat: float, temp_load: float, load_current: float, load_voltage: float,
             load_duty: int, ip: str, device_name: str):
        self.tft.fill(TFT.BLACK)
        v = 0
        self.tft.text((0, v), f"{device_name} {time_value}", self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
        self.tft.text((0, v), f"IP: {ip}", self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
        self.tft.text((0, v), f"Charge status: {chg_status}",
                      self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
        self.tft.text((0, v), f"Charger input {input_status}",
                      self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
        self.tft.text((0, v), f"mV bat: {v_bat}", self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
        self.tft.text((0, v), f"mA bat: {current_bat}", self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
        self.tft.text((0, v), f"Temp bat: {temp_bat}", self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
        self.tft.text((0, v), f"Temp env: {temp_env}", self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
        self.tft.text((0, v), f"Temp load: {temp_load}", self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
        self.tft.text((0, v), f"Duty load: {load_duty}", self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
        self.tft.text((0, v), f"Load mA: {load_current}", self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
        self.tft.text((0, v), f"Load mV: {load_voltage}", self.tft.WHITE, sysfont, 1, nowrap=True)
        v += sysfont["Height"]
