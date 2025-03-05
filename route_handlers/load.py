from device_manager.device_manager import DeviceManager


async def set_load_duty_handler(device_manager: DeviceManager, request):
    data = request.json
    new_duty = data.get("new_duty")
    device_manager.set_load_duty(new_duty)
