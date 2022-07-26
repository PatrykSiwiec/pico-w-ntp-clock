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
import _thread
import neopixel
import dht

print("WiFi SSID: {}".format(config.WIFI_SSID))

led_external = Pin(15, Pin.OUT)
sensor_pir = Pin(28, Pin.IN, Pin.PULL_DOWN)
# led_external.toggle()

# global vars
TEMP = 0
HUM = 0
LAST_TEMP_SYNC = 0
LAST_PIR_DETECTION = time.time()

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
        print("Waiting for connection...")
        lcd.clear()
        lcd.putstr("Waiting for WiFi connection...")
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError("Network connection failed!")
    else:
        print("WiFi connected!")
        lcd.clear()
        lcd.putstr("WiFi connected!")
        status = wlan.ifconfig()
        print("IP = {}".format(status[0]))
        lcd.move_to(0, 1)
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

# clear WS2812 LEDs
def leds_clear():
    for i in range(LEDS_COUNT):
        np[i] = (0, 0, 0)
    np.write()

def leds_turn_on():
    np[0] = (1, 0, 0)
    np[1] = (0, 1, 0)
    np[2] = (0, 0, 1)
    np[3] = (1, 1, 1)
    np[4] = (120, 153, 23)
    np[5] = (0, 0, 128)
    np[6] = (0, 128, 0)
    np[7] = (128, 0, 0)

    np.write()

# init WS2812 LEDs
LEDS_COUNT = 8
np = neopixel.NeoPixel(Pin(4), LEDS_COUNT)
# np.brightness = 0.1
leds_clear()

# sync time from NTP server
connect_to_wifi()
sleep(0.5)

print("Time before NTP sync: {}".format(time.localtime()))
set_time_from_ntp()
print("Time after NTP sync: {}".format(time.localtime()))
time_seconds = time.time() + 7200 # 2h (7200s)
print("Time after NTP sync [UTC+2]: {}".format(time.localtime(time_seconds)))

disconnect_from_wifi()

## temperature sensor
# ds_pin = machine.Pin(17)
# ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
# roms = ds_sensor.scan()
# print("Found ({}) DS devices: ".format(len(roms)), roms)

lcd.clear()
lcd.putstr("T: 00.0{}C H: 00%".format(chr(0)))

# DHT22 temperature & humidity sensor
dht22 = dht.DHT22(Pin(2))

baton = _thread.allocate_lock()

# def get_temperature_thread():
#     baton.acquire()
#     ds_sensor.convert_temp()
#     time.sleep_ms(750)

#     global TEMP, LAST_TEMP_SYNC
#     TEMP = ds_sensor.read_temp(roms[0])
#     LAST_TEMP_SYNC = time.time()
#     baton.release()

def get_dht_data_thread():
    baton.acquire()

    global TEMP, HUM, LAST_TEMP_SYNC
    if LAST_TEMP_SYNC == 0: #
        # should wait at least 2s before first read
        LAST_TEMP_SYNC = time.time()
        baton.release()
        return

    try:
        dht22.measure()
        TEMP = dht22.temperature()
        HUM = dht22.humidity()
        print("[{}] T: {} C, H: {}%".format(datetime_str(current_time()), TEMP, HUM))
    except Exception as ex:
        print(ex)

    LAST_TEMP_SYNC = time.time()
    
    baton.release()

def main():
    global LAST_PIR_DETECTION
    while True:

        if time.time() - LAST_TEMP_SYNC >= 5 and not baton.locked():
            _thread.start_new_thread(get_dht_data_thread, ())

        lcd.move_to(3, 0)
        lcd.putstr("{:2.1f}".format(TEMP))
        
        lcd.move_to(13, 0)
        lcd.putstr("{:2.0f}".format(HUM))

        lcd.move_to(0, 1)
        lcd.putstr(datetime_str(current_time()))

        time_diff = time.time() - LAST_PIR_DETECTION
        # print("PIR value: {}, time diff: {}".format(sensor_pir.value(), time_diff))
        
        if sensor_pir.value() > 0 and time_diff > 1:
            leds_turn_on()
            LAST_PIR_DETECTION = time.time()
        elif sensor_pir.value() < 1 and time_diff > 60:
            leds_clear()

        sleep(0.2)

# run main loop
try:
    main()
except KeyboardInterrupt:
    print("KeyboardInterrupt")
    led_external.off()

    leds_clear()