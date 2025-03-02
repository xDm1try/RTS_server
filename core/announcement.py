import asyncio
from contextlib import asynccontextmanager
import socket
from apscheduler.schedulers.background import BackgroundScheduler
import netifaces
import httpx
from datetime import datetime
from database.models.models import AnnouncementModel, AnnouncementResponseModel
from core.settings import settings


async def send_announce_msg():
    broadcast_addr = get_broadcast_address()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        while True:
            # Отправляем сообщение
            dt_now = datetime.now()
            announcement = AnnouncementModel(server_ip=str(settings.SERVER_IP),
                                             server_port=str(settings.SERVER_PORT), date=dt_now.strftime("%Y-%m-%d %H:%M:%S"))

            message = announcement.model_dump_json()
            sock.sendto(message.encode('utf-8'), (broadcast_addr, int(settings.DEVICE_PORT)))
            print(f"Отправлено сообщение: {message} на {broadcast_addr}:{int(settings.DEVICE_PORT)}")
            await asyncio.sleep(2)  # Отправляем сообщение каждые 2 секунды
    except asyncio.CancelledError:
        print("Отправка сообщений остановлена.")
    finally:
        sock.close()


def get_addreses():
    found_interfaces = netifaces.interfaces()
    wifi_interfaces = [interface for interface in found_interfaces if "w" == interface[0]]
    # print(netifaces.ifaddresses(wifi_interfaces[0]))
    return [netifaces.ifaddresses(wifi_interface)[netifaces.AF_INET] for wifi_interface in wifi_interfaces]


def get_broadcast_address() -> str:
    addreses = get_addreses()

    settings.SERVER_IP = addreses[0][0]["addr"]
    return addreses[0][0]["broadcast"]


def get_server_ip() -> str:
    addreses = get_addreses()
    return addreses[0][0]["addr"]


async def annoncement_cycle():
    while True:

        try:
            await send_announce_msg()
        except:
            ...
        await asyncio.sleep(5)
