import time
import machine
import onewire
import ds18x20
# the device is on GPIO2
dat = machine.Pin(2)
# create the onewire object
ds = ds18x20.DS18X20(onewire.OneWire(dat))
# scan for devices on the bus
roms = ds.scan()
print('found devices:', roms)

# loop 10 times and print all temperatures
# [bytearray(b'(\x9fEfT$\x06\xeb'), bytearray(b'(LV\x8fT$\x06\x9e'), bytearray(b'(\xb8\x9d\x9dT$\x06]')]

def scan_temperature():
    print('temperatures:', end=' ')
    ds.convert_temp()
    time.sleep_ms(750)
    for rom in roms:
        print(rom, "вывел: ", ds.read_temp(rom), end='\n')
    print("====")
