import gc


def garbage_collect(func):
    def decorator():
        func()
        gc.collect()
    return decorator


def get_env_dict(device_settings_file: str = "/core/device_settings.env") -> dict:
    new_dict = dict()
    with open(device_settings_file, "r") as f:
        lines = f.readlines()
        lines = list(map(lambda line: line.strip(), lines))
        items: list[(str, str)] = list(map(lambda line: line.split("="), lines))
        for name, value in items:
            new_dict[name.strip()] = value.strip()

    return new_dict
