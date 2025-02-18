
class AnnounceRequest:
    def __init__(self, server_ip: str, server_port: int):
        self.server_ip = server_ip
        self.server_port = server_port


class AnnounceResponse:
    def __init__(self, device_status: str, device_name: str, device_ip: str):
        self.device_status = device_status
        self.device_name = device_name
        self.device_ip = device_ip

class AnnounceAnswer:
    def __init__(self):
        pass