import network
import time


def connect(wifi_name, wifi_passw, timeout=15) -> None:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(wifi_name, wifi_passw)
    time.sleep(1)
    for _ in range(timeout):
        if not wlan.isconnected():
            print(f'Connecting to WIFI ({wifi_name})...')
            time.sleep(1)
    if not wlan.isconnected():
        print("Didn't connect successfull. Try again")
        return None
    cfg = wlan.ipconfig('addr4')
    print('Network config:', cfg)
    return cfg
