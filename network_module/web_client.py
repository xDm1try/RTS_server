from network_module.web_client.mp_server.micropyserver import MicroPyServer
from network_module.web_client.api.routes import add_routes
from main_former import settings_Controller

port = settings_Controller.device_environ.get("DEVICE_PORT", None)
assert port, "DEVICE_PORT is not found"

client = MicroPyServer("0.0.0.0", port)
add_routes(client)


def start_client():
    try:
        client.start()
    except KeyboardInterrupt:
        print("KI")
        client.stop()
    except Exception as e:
        print(f"Captured exc {e}")
