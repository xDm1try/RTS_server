from device_manager.device_manager import DeviceManager, TemperatureOf
from models import TestData
from device_manager.drivers.bq25895 import ChargerSettings
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


async def stop_sensor_handler(device_manager, request):
    if not DeviceManager.SENSOR_LOOP:
        DeviceManager.SENSOR_LOOP.cancel()


async def start_sensor_handler(device_manager, request):
    task = asyncio.create_task(parameters_loop(device_manager=device_manager, request=request))
    DeviceManager.SENSOR_LOOP = task


async def parameters_loop(device_manager: DeviceManager, request):
    req_data = request.json
    while True:
        resp = await collect_parameters(device_manager)
        data = await device_manager.get_udp_request()

        async with aiohttp.ClientSession() as session:
            async with session.put(f'http://{data.server_ip}:{data.server_port}/' +
                                   f'{req_data.bat_id}/{req_data.test_id}/add_data', json=resp) as response:
                print("Status:", response.status)
        await asyncio.sleep(req_data.sleep_time)


async def collect_parameters(device_manager: DeviceManager):
    voltage = await device_manager.get_battery_mV()
    current = await device_manager.get_battery_mA()
    duty = await device_manager.get_load_duty()
    status = await device_manager.get_charging_status()
    temp = await device_manager.get_temperatures()
    response = TestData(
        temp_bat=temp[TemperatureOf.BATTERY],
        temp_env=temp[TemperatureOf.ENVIRONMENT],
        temp_load=temp[TemperatureOf.LOAD],
        bat_current=current,
        bat_voltage=voltage,
        load_duty=duty,
        charge_status=status
    )
    try:
        await parameters_validation(test_data=response)
    except AssertionError as e:
        print(e)
        device_manager.reset_all()
    return json.dumps(response)


async def parameters_validation(test_data: TestData, device_manager: DeviceManager):
    settings: ChargerSettings = await device_manager.get_charging_settings()
    assert settings.const_current_mA < test_data.bat_current, "The current has reached the cut-off current"
    assert settings.const_volt_mV < test_data.bat_voltage * 1.15, "The voltage exceeds by 15 percent of entered"
    assert test_data.temp_bat < settings.temp_bat_limit, f"Battery overheating ({test_data.temp_bat})"


async def set_load_duty_handler(device_manager: DeviceManager, request):
    data = request.json
    new_duty = data.get("new_duty")
    device_manager.set_load_duty(new_duty)


async def stop_charge_handler(device_manager: DeviceManager, request):
    device_manager.stop_charging()


async def start_charger_handler(device_manager: DeviceManager, request):
    data: ChargerSettings = request.json
    device_manager.start_charging(data)
