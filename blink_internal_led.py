import machine
import utime

led_pin = machine.Pin('LED', machine.Pin.OUT)

while True:
    led_pin.on()
    print('on')
    utime.sleep(1)
    led_pin.off()
    print('off')
    utime.sleep(1)
