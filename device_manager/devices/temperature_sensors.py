import time
from onewire import OneWire
from ds18x20 import DS18X20


class TemperatureSensors:

    def __init__(self, onewire: OneWire):
        self.temp = DS18X20(onewire)
        self.roms = self.temp.scan()
        if len(self.roms) == 0:
            raise Exception("Not found temperature sensors")

    def read_temperature(self) -> dict[str, int]:
        self.temp.convert_temp()
        time.sleep_ms(750) # TODO await.sleep()
        d = dict()
        for rom in self.roms:
            d[rom] = self.temp.read_temp(rom)

        return d

# def scan_temperature():
#     print('temperatures:', end=' ')
#     ds.convert_temp()
#     time.sleep_ms(750)
#     for rom in roms:
#         print(rom, "вывел: ", ds.read_temp(rom), end='\n')
#     print("====")
