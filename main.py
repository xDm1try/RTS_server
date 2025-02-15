import gc
import uasyncio as asyncio
from network_module.connection import connect
from network_module.web_client.mp_server.micropyserver import MicroPyServer
from network_module.web_client.api.routes import add_routes
import socket
import time
from core.settings_manager import SettingsManager
settings_manager = SettingsManager()
settings_manager


timeout = int(settings_manager.device_environ.get("CONNECTION_TIMEOUT", None))
assert timeout, "Connection timeout must be entered in CONNECTION_TIMEOUT"
wifi_ssid = settings_manager.device_environ.get("WIFI_SSID", None)
assert wifi_ssid, "Wi-Fi SSID must be entered in WIFI_SSID"
wifi_passw = settings_manager.device_environ.get("WIFI_PASSW", None)
assert wifi_passw, "Wi-Fi password must be entered in WIFI_PASSW"

device_ip, net_mask = connect(wifi_name=wifi_ssid, wifi_passw=wifi_passw, timeout=timeout)

settings_manager.device_environ["DEVICE_IP"] = device_ip
server_ip = None


def calculate_broadcast_address(device_ip, subnet_mask):

    ip_bits = list(map(int, device_ip.split(".")))
    mask_bits = list(map(int, subnet_mask.split(".")))

    broadcast_bits = [
        ip_bits[i] | (~mask_bits[i] & 255) for i in range(4)
    ]

    broadcast_address = ".".join(map(str, broadcast_bits))
    return broadcast_address


broadcast = calculate_broadcast_address(device_ip, net_mask)


server = MicroPyServer()
add_routes(server)

from network_module.web_client.mp_server.announce_listener import listen_broadcast


async def start_all():
    device_port = settings_manager.device_environ.get("DEVICE_PORT", None)
    if device_port is None:
        raise ValueError("No DEVICE_PORT in envs.")
    device_port = int(device_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((broadcast, device_port))
    sock.settimeout(350)
    while True:
        server_ip = settings_manager.server_environ.get("SERVER_IP", None)
        server_port = settings_manager.server_environ.get("SERVER_PORT", None)

        await server.start(host=device_ip, port=server_port)
        await listen_broadcast(sock)
        gc.collect()


def main():
    asyncio.run(start_all())
    # start_all()

