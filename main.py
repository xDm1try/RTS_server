import network
import ntptime
import time

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("MDV", "QAZwsxedc")
while not wlan.isconnected():
    print(f'Connecting to WIFI')
    time.sleep(0.3)
time.sleep(0.3)
ntptime.settime()

cfg = wlan.ipconfig('addr4')

print(cfg)
