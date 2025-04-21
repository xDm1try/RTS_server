~/NodeMCU_scripts/mp_compiling/mpy-cross/build/mpy-cross ~/NodeMCU_scripts/WebServer2/device_manager/drivers/display/ST7735.py
~/NodeMCU_scripts/mp_compiling/mpy-cross/build/mpy-cross ~/NodeMCU_scripts/WebServer2/device_manager/drivers/ina3221.py
~/NodeMCU_scripts/mp_compiling/mpy-cross/build/mpy-cross ~/NodeMCU_scripts/WebServer2/device_manager/drivers/bq25895.py
~/NodeMCU_scripts/mp_compiling/mpy-cross/build/mpy-cross ~/NodeMCU_scripts/WebServer2/device_manager/drivers/sdcard.py
~/NodeMCU_scripts/mp_compiling/mpy-cross/build/mpy-cross ~/NodeMCU_scripts/WebServer2/server/microdot.py

time rshell --port /dev/ttyUSB0 << EOF

cp -r aiohttp /pyboard
cp -r core /pyboard
cp -r device_manager /pyboard
cp -r server /pyboard
cp main* /pyboard

rm /pyboard/device_manager/drivers/display/ST7735.py
rm /pyboard/device_manager/drivers/bq25895.py
rm /pyboard/device_manager/drivers/ina3221.py
rm /pyboard/device_manager/drivers/sdcard.py
rm /pyboard/server/microdot.py
EOF
echo "ESP32 FLASHED"