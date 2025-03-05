from device_manager.device_manager import DeviceManager
from device_manager.devices.charger_bq import ChargerSettings


async def stop_charge_handler(device_manager: DeviceManager, request):
    device_manager.stop_charging()


async def start_charger_handler(device_manager: DeviceManager, request):
    data: ChargerSettings = request.json
    device_manager.start_charging(data)
