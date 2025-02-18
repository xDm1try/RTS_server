import asyncio
from onewire import OneWire
from ds18x20 import DS18X20


class TemperatureSensors:

    def __init__(self, onewire: OneWire):
        self.temp = DS18X20(onewire)
        self.roms = self.temp.scan()
        if len(self.roms) == 0:
            raise Exception("Not found temperature sensors")

    async def read_temperature(self) -> dict[str, int]:
        self.temp.convert_temp()
        d = dict()
        await asyncio.sleep(0.75)
        for rom in self.roms:
            d[rom] = self.temp.read_temp(rom)
        return d
