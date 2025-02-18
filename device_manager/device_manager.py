from device_manager.device_settings_model import DeviceSettings
from device_manager.network_controller.connection_controller import ConnectionController


class DeviceSettings:

    def __init__(self, device_name: str, device_port: int):
        self.device_name = device_name
        self.device_port = device_port


class DeviceController:

    def __init__(self, settings: DeviceSettings = None):
        assert settings, "No settings in DeviceController"
        self.settings = settings
        self.start_controllers(self.settings)

    def start_controllers(self, settings: DeviceSettings):
        self.connection_c = ConnectionController(settings.device_name)
        self.connection_c.run_udp_handler(settings.device_port)

    def stop_controllers(self):
        self.connection_c.stop_udp_handler()

    def start_testing(self):
        ...

    def stop_testing(self):
        ...
