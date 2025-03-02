import threading
from fastapi.responses import HTMLResponse
import uvicorn
from core.settings import settings
import asyncio
from fastapi import FastAPI
from database.models.models import AnnouncementResponseModel
from core.announcement import annoncement_cycle, get_server_ip
from sender import start_simple_task
from taipy import Gui

app = FastAPI()
gui = Gui()

devices: dict[str: AnnouncementResponseModel] = dict()


@app.post("/annoncement_resp")
async def annoncement_resp(response: AnnouncementResponseModel):
    print(response)
    devices[response.device_name] = response
    return {"resp": True}


@app.get("/heath")
async def annoncement_resp():
    print("HEATH")
    return {"HEALTH": True}


async def main():
    # asyncio.create_task(annoncement_cycle())
    config = uvicorn.Config(app, host=get_server_ip(), port=settings.SERVER_PORT, )  # log_level="critical"
    server = uvicorn.Server(config)
    await server.serve()


def handle_user_input():
    while True:
        inp = input()
        if inp == " ":
            print(devices)
            continue
        if inp == "c":
            devices.clear()
            print(devices)
            continue
        words = inp.split(" ")
        if len(words) == 2:
            try:
                period = int(words[0])
                gap = int(words[1])
                if len(devices) != 0:
                    dev = list(devices.values())[0]
                    start_simple_task(period=period, gap=gap, ip=dev.device_ip, port=settings.SERVER_PORT)
                else:
                    print("list empty")
            except Exception as e:
                print(e)

            continue


if __name__ == "__main__":
    thread = threading.Thread(target=handle_user_input, daemon=True)
    thread.start()
    asyncio.run(main())
