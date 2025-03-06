import json
from microdot import Microdot
import network
import asyncio
import ntptime
import time
from utils import garbage_collect

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("POCOF3", "22222222")
while not wlan.isconnected():
    print('Connecting to WIFI')
    time.sleep(0.3)
time.sleep(0.3)
ntptime.settime()

cfg = wlan.ipconfig('addr4')

print(cfg)

app = Microdot()


@app.route("/health")
async def health(request):
    date = str(ntptime.gmtime())
    resp = json.dumps({"state": True, "date": date})
    return resp


@garbage_collect
@app.route("/stop_charge")
async def stop_charge(request):
    date = str(ntptime.gmtime())
    resp = json.dumps({"state": True, "date": date})
    return resp


@garbage_collect
@app.route("/start_charge")
async def start_charge(request):
    date = str(ntptime.gmtime())
    resp = json.dumps({"state": True, "date": date})
    return resp


@garbage_collect
@app.route("/set_load_duty")
async def set_load_duty(request):
    date = str(ntptime.gmtime())
    resp = json.dumps({"state": True, "date": date})
    return resp


@garbage_collect
@app.route("/stop_sensors")
async def stop_sensors(request):
    date = str(ntptime.gmtime())
    resp = json.dumps({"state": True, "date": date})
    return resp


@garbage_collect
@app.route("/start_sensors")
async def start_sensors(request):
    date = str(ntptime.gmtime())
    resp = json.dumps({"state": True, "date": date})
    return resp


@garbage_collect
@app.route('/heartbeat')
async def heartbeat_route(request):
    date = str(ntptime.gmtime())
    resp = json.dumps({"state": True, "date": date})
    return resp


@garbage_collect
@app.route("/reset")
async def reset_rout(request):
    date = str(ntptime.gmtime())
    resp = json.dumps({"state": True, "date": date})
    return resp


@garbage_collect
@app.route('/reboot')
async def reboot_route(request):
    date = str(ntptime.gmtime())
    resp = json.dumps({"state": True, "date": date})
    return resp
