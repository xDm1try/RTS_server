import time
from network_module.web_client.mp_server.micropyserver import MicroPyServer
from network_module.web_client.request_parsers import get_request_json
from machine import Pin


def add_anoncement_routes(server: MicroPyServer) -> None:
    def do_simple_task(response):
        try:
            response_dict = get_request_json(response)
            print(response_dict)
            period = int(response_dict.get("period"))
            led_gap = int(response_dict.get("led_gap"))
            start = time.time()
            LED = Pin(2, Pin.OUT)
            while time.time() - start < period:
                time.sleep(led_gap)
                LED.value(not LED.value())
            LED.value(1)
            
        except Exception as e:
            print(f"Catched exc in annoncement_handler: {e}")

    server.add_route("/do_simple_task", do_simple_task, method="POST")

    def heath(response):
        print("I AM HEALTHY")
        LED = Pin(2, Pin.OUT)
        LED.value(not LED.value())
        time.sleep(0.5)
        LED.value(not LED.value())
        LED.value(1)

    server.add_route("/health", heath, method="POST")