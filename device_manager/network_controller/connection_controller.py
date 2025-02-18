import socket
import network
import ntptime
import urequests
import asyncio
import json
from device_manager.network_controller.models.models import UdpRequest, UdpResponse

class ConnectionController:
    def __init__(self, device_name, wifi_name, wifi_passw):
        self.device_name = device_name
        self.wifi_name = wifi_name
        self.wifi_passw = wifi_passw
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.cfg = None
        self.udp_request = None
        self.udp_response = None
        self._udp_handler_task = None
        self._lock = asyncio.Lock()
        self.connect()

    async def connect(self) -> None:
        self.wlan.connect(self.wifi_name, self.wifi_passw)
        while True:
            if self.wlan.isconnected():
                ntptime.settime()
                break
            else:
                print(f'Connecting to WIFI ({self.wifi_name})...')
                await asyncio.sleep(0.3)

        self.cfg = self.wlan.ipconfig('addr4')

    async def get_device_ip(self) -> str | None:
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

    async def check_connection(self) -> bool:
        return self.wlan.isconnected()

    async def stop_udp_handler(self) -> None:
        if self._udp_handler_task is not None:
            self._udp_handler_task.cancel()
            self._udp_handler_task = None

    def run_udp_handler(self, port) -> None:
        while not self.wlan.isconnected():
            self.connect()
        self._udp_handler_task = asyncio.create_task(self.handler_udp(port))

    async def udp_handler(self, broadcast_addr, port):
        print(f"UDP server started on {self.cfg}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)  # Неблокирующий режим
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        sock.bind((broadcast_addr, port))  # Привязка к порту 9999

        while True:
            try:
                # Проверяем, есть ли данные в сокете
                data, addr = sock.recvfrom(1024)
                if data:
                    print("UDP data received from {}: {}".format(addr, data))
                    data_dict: UdpRequest = json.loads(data)
                    self.set_udp_request(UdpRequest(data_dict.server_ip, data_dict.server_port))
                    self.send_udp_response()
            except OSError as e:
                if e.errno == 11:  # EAGAIN - нет данных для чтения
                    await asyncio.sleep(0.1)  # Ждем немного перед повторной проверкой
                else:
                    print("UDP error:", e)
                    break
        print("UDP server ended")
        sock.close()

    async def set_udp_response(self, response: UdpResponse) -> None:
        async with self._lock:
            self.udp_response = response

    async def get_udp_response(self) -> UdpResponse | None:
        async with self._lock:
            self.udp_response

    async def set_udp_request(self, request: UdpRequest) -> None:
        async with self._lock:
            self.udp_request = request

    async def get_udp_request(self) -> UdpRequest | None:
        async with self._lock:
            return self.udp_request

    async def send_udp_response(self) -> None:
        try:
            response: UdpResponse = self.get_udp_response()
            server_data: UdpRequest = self.get_udp_request()
            if response is None or server_data is None:
                raise Exception("Udp response is None")

            data = response.__dict__

            json_data = json.dumps(data)

            try:

                url = f"http://{server_data.server_ip}:{server_data.server_port}/annoncement_resp"
                # print(url)
                response = urequests.post(url,
                                          data=json_data,
                                          headers={"Content-Type": "application/json"})
                print(response.json())
            except Exception as e:
                print("Exc2 in send_task_response ", e)
        except Exception as e:
            print("Exc in send_task_response ", e)
