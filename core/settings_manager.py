
class SettingsManager:
    def __init__(self):
        self.device_settings_file = "/core/device_settings.env"
        self.server_settings_file = "/core/server_settings.env"
        self.server_environ = None
        self.device_environ = None
        self.set_environ()

    @staticmethod
    def get_env_dict(file: str) -> dict:
        new_dict = dict()
        with open(file, "r") as f:
            lines = f.readlines()
            lines = list(map(lambda line: line.strip(), lines))
            items: list[(str, str)] = list(map(lambda line: line.split("="), lines)) 
            for name, value in items:
                new_dict[name] = value

        return new_dict

    def set_environ(self):
        self.device_environ = SettingsManager.get_env_dict(self.device_settings_file)
        self.server_environ = SettingsManager.get_env_dict(self.server_settings_file)

    def record_environments(self):
        self._write_environ(self.device_settings_file, self.device_environ)
        self._write_environ(self.server_settings_file, self.server_environ)

    def _write_environ(self, file: str, envs: dict) -> None:
        with open(file, "w") as f:
            for name, value in envs.items():
                f.write(f"{name}={value}\n")

    