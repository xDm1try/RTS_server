from microdot import Microdot
import gc
import json
import network
import asyncio
import time
gc.collect()
time.sleep(3)
gc.collect()
print(gc.mem_free())
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("POCOF3", "22222222")
while not wlan.isconnected():
    print('Connecting to WIFI')
    time.sleep(0.3)
time.sleep(0.3)

gc.collect()


cfg = wlan.ipconfig('addr4')

print(gc.mem_free())
print(cfg)

app = Microdot()


@app.route("/health")
async def health(request):
    resp = json.dumps({"state": True, "heap_free": gc.mem_free()})
    return resp


gc.collect()


async def main():
    asyncio.create_task(app.start_server("0.0.0.0", 21216))
    while True:
        gc.collect()
        print(gc.mem_free())
        await asyncio.sleep(2)
