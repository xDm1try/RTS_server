import socket
import time
import network
import ntptime
import urequests
import asyncio
import json
from device_manager.network_controller.models.models import AnnounceRequest, HeartBeatResponse


class ConnectionController:
    def __init__(self, device_name, wifi_name, wifi_passw):
        self.device_name = device_name
        self.wifi_name = wifi_name
        self.wifi_passw = wifi_passw
        self.wlan = network.WLAN(network.WLAN.IF_STA)
        self.wlan.active(True)
        self.cfg = None
        self._udp_handler_task = None
        self._lock = asyncio.Lock()
        self.connect()

    async def a_connect(self) -> None:
        self.wlan.connect(self.wifi_name, self.wifi_passw)
        while True:
            if self.wlan.isconnected():
                ntptime.settime()
                break
            else:
                print(f'Connecting to WIFI ({self.wifi_name})...')
                await asyncio.sleep(0.3)

    def connect(self) -> None:
        self.wlan.connect(self.wifi_name, self.wifi_passw)
        while True:
            if self.wlan.isconnected():
                ntptime.settime()
                break
            else:
                print(f'Connecting to WIFI ({self.wifi_name})...')
                time.sleep(0.3)

        self.cfg = self.wlan.ipconfig('addr4')

    def get_device_ip(self) -> str | None:
        self.check_connection()
        if self.cfg is not None:
            return self.cfg[0]

    async def get_network_mask(self) -> str | None:
        if self.cfg is not None:
            return self.cfg[1]

    async def get_broadcast_addr(self) -> str | None:
        mask: str = self.get_network_mask()
        addr: str = self.get_device_ip()
        if mask or addr in None:
            return None
        else:
            mask_array = mask.split(".")
            addr_array = mask.split(".")
            res = []
            for oct1, oct2 in zip(addr_array, mask_array):
                if "255" in oct2:
                    res.append(oct1)
                else:
                    res.append("255")
            broadcast = ".".join(res)
            return broadcast

    def disconnect(self):
        raise Exception("Network Controller has no disconnect yet.")

    def check_connection(self) -> bool:
        return self.wlan.isconnected()
