from machine import I2C 
import ds3231
i2c = I2C(0, scl=22, sda=21)
ds = ds3231.DS3231(i2c)

print(i2c)
print(ds)

from machine import Pin
import pulseclock

pc = pulseclock.Pulseclock(Pin(26, Pin.OUT), Pin(25, Pin.OUT), Pin(27, Pin.OUT), 200, 200, False)
