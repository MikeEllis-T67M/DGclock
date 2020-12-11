from machine import I2C, Pin, RTC
from utime import sleep_ms, time, mktime
import ujson
import display

import ds3231
import pulseclock_new
import settings
import wifi

def clock_test():
    # Initialise the DS3231 battery-backed RTC
    i2c = I2C(0, scl=22, sda=21)
    ds  = ds3231.DS3231(i2c)
    print("DS3231 time   : {}".format(ds.rtc_tm))
    print("Hands position: {}".format(ds.alarm1_tm))

    # Initialise the hand position using the value stored in NV-RAM in the DS chip
    hand_position = ds.alarm1_tm
    hands         = hand_position[3] * 3600 + hand_position[4] * 60 + hand_position[5]  % 43200

    # Initialise the pulse clock itself - pulses of 200/100 seem reliable
    clock_settings = settings.load_settings("clock.json")
    pc = pulseclock_new.PulseClock(clock_settings, 0)

    try:
        while True:
            pc.step()
            sleep_ms(500)


    except KeyboardInterrupt:
        # Try to relinquish the I2C bus
        print("Hand position: {}".format(ds.alarm1_tm))
        i2c.deinit()
        tft.deinit()
        # del i2c

if __name__ == "__main__":
    dgclock()