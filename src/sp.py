from machine import I2C, RTC, Pin
from network import WLAN, AP_IF, STA_IF
import ds3231
i2c = I2C(0, scl=22, sda=21)
ds = ds3231.DS3231(i2c)
rtc = RTC()

import pulseclock

pc = pulseclock.Pulseclock(Pin(26, Pin.OUT), Pin(25, Pin.OUT), Pin(27, Pin.OUT), 200, 200, False)

print(''.join('{:02x} '.format(x) for x in ds.read_ds3231_rtc()))


# Turn off the access point
ap_if = WLAN(AP_IF)
ap_if.active(False)

# set up background NTP synchronisations
rtc.ntp_sync("ntp.pool.org", update_period = 900)

# Check for NTP sync
rtc.synced()

# Copy DS -> RTC
rtc.init(ds.rtc_tm)

# Copy RTC -> DS
ds.rtc_tm = rtc.now()

# Compare RTC and DS
ds.rtc_tm, rtc.now()