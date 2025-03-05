from device_manager.device_manager import DeviceManager, DeviceSettings
from device_manager.network_controller.models.models import HeartBeatResponse
import machine
import json


async def heartbeat_handler(device_manager: DeviceManager, request):
    ip = device_manager.get_device_ip()
    if ip:
        resp = HeartBeatResponse(device_manager.STATUS, device_manager.settings.device_name, device_ip=ip)
        return json.dumps(resp)
    else:
        print("No device ip")
        raise Exception("No device ip for hb response")


async def reset_handler(device_manager: DeviceManager, request):
    device_manager.reset_all()


async def reboot_handler(device_manager, request):
    machine.reset()
