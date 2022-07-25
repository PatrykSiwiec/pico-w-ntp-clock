from machine import I2C, Pin
from time import sleep
from pico_i2c_lcd import I2cLcd
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)

I2C_ADDR = i2c.scan()[0]
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

print("I2C address: {}".format(I2C_ADDR))

while True:
    lcd.putstr("First line text\n")
    lcd.blink_cursor_on()
    # lcd.backlight_off()
    sleep(2)
    # lcd.backlight_on()
    lcd.putstr("Second line")
    lcd.hide_cursor()
    sleep(2)
    lcd.clear()
