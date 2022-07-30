from machine import I2C, Pin
from time import sleep
from pico_i2c_lcd import I2cLcd
import onewire
import machine
import ds18x20
import time
import config

print("WiFi SSID: {}".format(config.WIFI_SSID))

# LCD
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)

I2C_ADDR = i2c.scan()[0]
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
print("I2C address: {}".format(I2C_ADDR))

# temperature sensor
ds_pin = machine.Pin(17)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()
print("Found ({}) DS devices: ".format(len(roms)), roms)

lcd.clear()
lcd.putstr("Temp: 00.000 C")

while True:

    ds_sensor.convert_temp()
    time.sleep_ms(750)

    temp = ds_sensor.read_temp(roms[0])

    # lcd.clear()
    lcd.move_to(6, 0)
    lcd.putstr("{:2.3f}".format(temp))

    # for i in range(16):
    #     if i % 2:
    #         lcd.putchar("_")
    #     else:
    #         lcd.putchar("-")
    #     sleep(0.25)

    sleep(2)
