from device_settings import DeviceSettings


class DeviceManager:

    def __init__(self, settings: DeviceSettings = None):
        assert settings, "No settings in DeviceManager"
        self.settings = settings
        

    def start_testing(self):
        ...
    
    def stop_testing(self):
        ...