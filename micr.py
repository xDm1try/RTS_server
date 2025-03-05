import ntptime
import asyncio

import network
from microdot import Microdot
# from device_manager.network_controller.connection_controller import ConnectionController


wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("MDV", "QAZwsxedc")
while not wlan.isconnected():
    print("Connecting")

print(wlan.ipconfig('addr4'))
ntptime.settime()

app = Microdot()


@app.route('/')
async def index(request):
    return f'Hello, world {ntptime.gmtime()}!'


async def main():
    # start the server in a background task
    corut = app.start_server("0.0.0.0", 5632)
    server = asyncio.create_task(corut)

    # ... do other asynchronous work here ...

    # cleanup before ending the application
    await server

asyncio.run(main())
