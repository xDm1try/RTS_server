
import httpx
from database.models.models import SimpleTask


def start_simple_task(period, gap, ip, port):
    url = f"http://{ip}:{port}/do_simple_task"
    try:
        with httpx.Client() as client:
            response = client.post(url, json=SimpleTask(period=period, led_gap=gap).model_dump())
            if response.status_code != 200:
                print(f"Error send leader on {url}")
            else:
                print(response)
            
    except Exception as e:
        print(f"Failed to reach {url}: {e}")
