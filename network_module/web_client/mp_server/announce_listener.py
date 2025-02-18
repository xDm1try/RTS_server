import ujson
import uasyncio as asyncio
from network_module.web_client.mp_server.send_funcs import send_announce_response
from main_former import settings_Controller


async def udp_server(sock):
    try:
        data, addr = sock.recvfrom(200)
        data_dict = ujson.loads(data.decode())
        print(f"Получено сообщение: {data_dict} от {addr}")
        server_port = data_dict["server_port"]
        server_ip = addr[0]
        if port_or_ip_is_new(server_ip, server_port):
            settings_Controller.server_environ["SERVER_PORT"] = server_port
            settings_Controller.server_environ["SERVER_IP"] = addr[0]
            settings_Controller.record_environments()

        send_announce_response(addr[0], data_dict["server_port"])
    except OSError as e:
        print(f"Exception in udp_server {e}")


async def listen_broadcast(sock):
    await udp_server(sock)


def port_or_ip_is_new(ip, port):
    if port not in list(settings_Controller.server_environ.values()) or \
            ip not in list(settings_Controller.server_environ.values()):
                return True
    else:
        return False
