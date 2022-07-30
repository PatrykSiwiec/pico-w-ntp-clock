from machine import I2C, Pin
from time import sleep
from pico_i2c_lcd import I2cLcd
import onewire
import machine
import ds18x20
import time
import config
import network
import socket
import struct

print("WiFi SSID: {}".format(config.WIFI_SSID))

# LCD
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)

I2C_ADDR = i2c.scan()[0]
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
print("I2C address: {}".format(I2C_ADDR))
# https://maxpromer.github.io/LCD-Character-Creator/
DEGREE_CHAR = bytearray([0x0E, 0x0A, 0x0E, 0x00, 0x00, 0x00, 0x00, 0x00])
lcd.custom_char(0, DEGREE_CHAR)

def set_time_from_ntp():
    NTP_DELTA = 2208988800

    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(config.NTP_SERVER, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    t = val - NTP_DELTA    
    tm = time.gmtime(t)
    # (year, month, day, weekday, hours, minutes, seconds, subseconds)
    # tm[6] + 1
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.WIFI_SSID, config.WIFI_PASS)

    max_wait = 10 # in seconds
    
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        lcd.clear()
        lcd.putstr("Waiting for WiFi connection...")
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        lcd.clear()
        lcd.putstr("WiFi connected!\n")
        status = wlan.ifconfig()
        print( 'ip = ' + status[0] )
        lcd.putstr(status[0])

def disconnect_from_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)

def datetime_str(time_tuple):
    year = time_tuple[0]
    month = time_tuple[1]
    mday = time_tuple[2]
    hour = time_tuple[3]
    minute = time_tuple[4]
    second = time_tuple[5]
    weekday = time_tuple[6]
    yearday = time_tuple[7]

    # return "{}-{:02d}-{:02d} {:02d}:{:02d}".format(year, month, mday, hour, minute)
    return "{:02d}/{:02d} {:02d}:{:02d}:{:02d}".format(mday, month, hour, minute, second)

def current_time():
    time_seconds = time.time() + 7200 # 2h (7200s)
    return time.localtime(time_seconds)

# sync time from NTP server
connect_to_wifi()
sleep(0.5)

print("Time before NTP sync: {}".format(time.localtime()))
set_time_from_ntp()
print("Time after NTP sync: {}".format(time.localtime()))
time_seconds = time.time() + 7200 # 2h (7200s)
print("Time after NTP sync [UTC+2]: {}".format(time.localtime(time_seconds)))

disconnect_from_wifi()

# temperature sensor
ds_pin = machine.Pin(17)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()
print("Found ({}) DS devices: ".format(len(roms)), roms)

lcd.clear()
lcd.putstr("Temp: 00.000{}C".format(chr(0)))

while True:

    ds_sensor.convert_temp()
    time.sleep_ms(750)

    temp = ds_sensor.read_temp(roms[0])

    # lcd.clear()
    lcd.move_to(6, 0)
    lcd.putstr("{:2.3f}".format(temp))

    lcd.move_to(0, 1)
    lcd.putstr(datetime_str(current_time()))

    # sleep(2)
