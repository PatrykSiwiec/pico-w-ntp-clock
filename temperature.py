import machine, onewire, ds18x20, time
 
ds_pin = machine.Pin(17)
led_pin = machine.Pin('LED', machine.Pin.OUT)
 
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()
print('Found DS devices: ', roms)

led_pin.on()
time.sleep_ms(500)
led_pin.off()
 
while True:
 
  ds_sensor.convert_temp()
 
  time.sleep_ms(750)
 
  for rom in roms:
 
    # print(rom)
 
    print(ds_sensor.read_temp(rom))
 
  time.sleep(5)