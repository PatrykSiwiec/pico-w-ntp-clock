from machine import I2C, Pin
from time import sleep
from pico_i2c_lcd import I2cLcd
import onewire
import machine
import ds18x20
import time

# LCD
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)

I2C_ADDR = i2c.scan()[0]
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
print("I2C address: {}".format(I2C_ADDR))

# temperature sensor
ds_pin = machine.Pin(17)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()
print('Found DS devices: ', roms)

while True:

    ds_sensor.convert_temp()
    time.sleep_ms(750)
    lcd.clear()
    
    temp = None
    for rom in roms:
        # print(rom)
        temp = ds_sensor.read_temp(rom)

    lcd.putstr("Temp: {:2.3f} C\n".format(temp))
    # lcd.blink_cursor_on()
    # lcd.backlight_off()
    sleep(5)
    # lcd.backlight_on()
    # lcd.putstr("Second line")
    # lcd.hide_cursor()
    # sleep(2)
