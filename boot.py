"""This file is executed on every boot (including wake-boot from deepsleep)"""
import os
import machine
from main_former import main
# import esp
# esp.osdebug(None)
# os.dupterm(None, 1) # disable REPL on UART(0)
# import webrepl
# webrepl.start()
import gc
gc.collect()

# main()
