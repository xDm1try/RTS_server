# import aiohttp
# from device_manager.drivers.bq25895 import ChargerSettings
# from server.microdot import Microdot
from device_manager.device_manager import DeviceManager, DeviceSettings
# import json
from utils import garbage_collect, get_env_dict
# import machine
import gc
import network
import ntptime
# import asyncio
import time
print("READY")


gc.collect()
time.sleep(3)
gc.collect()
time.sleep(3)
gc.collect()
print(gc.mem_free())
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("MDV", "QAZwsxedc")
while not wlan.isconnected():
    print('Connecting to WIFI')
    time.sleep(0.3)
time.sleep(0.3)

gc.collect()
while ntptime.gmtime()[0] == 2000:
    ntptime.settime()
    time.sleep(0.3)
print("DONE")

d = get_env_dict()

s = DeviceSettings(
    server_ip=d.get("SERVER_IP"),
    server_port=int(d.get("SERVER_PORT")),
    wifi_name=d.get("WIFI_NAME"),
    wifi_passw=d.get("WIFI_PASSW"),
    device_name=d.get("DEVICE_NAME"),
    device_port=int(d.get("DEVICE_PORT")),
    broadcast_port=int(d.get("BROADCAST_PORT")),
    i2c_sda=int(d.get("I2C_SDA")),
    i2c_scl=int(d.get("I2C_SCL")),
    charger_intr=int(d.get("CHARGER_INTR")),
    temp_pin=int(d.get("TEMP_PIN")),
    temp_bat_addr=d.get("TEMP_BAT_ADDR"),  # yellow, blue, green
    temp_load_addr=d.get("TEMP_LOAD_ADDR"),  # whites
    temp_env_addr=d.get("TEMP_ENV_ADDR"),  # red, orange
    pwm_pin=int(d.get("PWM_PIN")),
    display_spi=int(d.get("DISPLAY_SPI")),
    display_DC=int(d.get("DISPLAY_DC")),
    display_RESET=int(d.get("DISPLAY_RESET")),
    display_CS=int(d.get("DISPLAY_CS")),
)

cfg = wlan.ipconfig('addr4')

print(gc.mem_free())
print(cfg)
d = DeviceManager(cfg[0], s)