import asyncio
import aiohttp
from device_manager.device_manager import DeviceManager
import machine
import json


async def heartbeat_handler(device_manager: DeviceManager, requset):
    resp = await device_manager.get_status()
    resp = json.dumps(resp)
    return resp


async def reset_handler(device_manager: DeviceManager, request):
    device_manager.reset_all()


async def reboot_handler(device_manager, request):
    machine.reset()


async def send_heartbeat_response_loop(device_manager: DeviceManager):
    data = device_manager.settings
    while True:
        resp = await device_manager.get_status()
        resp = json.dumps(resp)
        async with aiohttp.ClientSession() as session:
            async with session.put(f'http://{data.server_ip}:{data.server_port}/device_announce',
                                   json=resp) as response:
                print("Status:", response.status)
        await asyncio.sleep(5)
