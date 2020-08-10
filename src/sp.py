from machine import I2C, RTC, Pin
from network import WLAN, AP_IF, STA_IF
import ds3231
import pulseclock
i2c = I2C(0, scl=22, sda=21)
ds = ds3231.DS3231(i2c)
rtc = RTC()
ds.alarm1_tm

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

# Does the display work and sub-classing work as I expect?
import ttgodisplay

tft = display.TFT() 
tft.init(tft.ST7789,bgr=False,rot=tft.LANDSCAPE, miso=17,backl_pin=4,backl_on=1, mosi=19, clk=18, cs=5, dc=16)
tft.setwin(40,52,320,240)

text_centred("Some simple text", 90)