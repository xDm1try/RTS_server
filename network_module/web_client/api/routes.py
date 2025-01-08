from network_module.web_client.mp_server.micropyserver import MicroPyServer
from network_module.web_client.api.v1.annoncement import add_anoncement_routes


def add_routes(server: MicroPyServer):
    add_anoncement_routes(server=server)
