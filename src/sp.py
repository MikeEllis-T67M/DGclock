Last NTP check started at 1605987450 (21st November)
Check at   1607715597 when DS3231 read 1607715599
Drift was 2 in 1728147 secs: 1.15730895577749ppm  (11th December)
Cal factor adjusted to -12 (== -1.2ppm)

from machine import I2C, RTC, Pin
from network import WLAN, AP_IF, STA_IF
import ds3231
i2c = I2C(0, scl=22, sda=21)
ds = ds3231.DS3231(i2c)
rtc = RTC()
ds.alarm1_tm
ds.rtc_tm

import settings
import wifi
wifi_settings = settings.load_settings("wifi.json")
ip_addr       = wifi.connect_sta(wifi_settings['SSID'], wifi_settings['Password'], wifi_settings['Hostname'])

import ntptime
ntp_settings = settings.load_settings("ntp.json")
ntptime.ntp_query("192.168.16.10")
ds.rtc

import dgclock
clock = dgclock.DGClock("clock.json", ds.alarm1)

import dgui
ui = dgui.DGUI(clock.hands_tm)

pc = pulseclock.Pulseclock(Pin(26, Pin.OUT), Pin(25, Pin.OUT), Pin(27, Pin.OUT), 200, 200, False)

import settings
import wifi
wifi_settings = settings.load_settings("wifi.json")
ip_addr       = wifi.connect_sta(wifi_settings['SSID'], wifi_settings['Password'], wifi_settings['Hostname'])


ntp_settings = settings.load_settings("ntp.json")
ntptime.ntp_query("192.168.16.10")
ds.rtc

rtc = RTC()
rtc.now()
rtc.init(ds.rtc_tm)
rtc.ntp_sync(ntp_settings['NTP'], update_period = 900)

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


def timegm(tuple):
    """Unrelated but handy function to calculate Unix timestamp from GMT."""
    year, month, day, hour, minute, second = tuple[:6]
    days = datetime.date(year, month, 1).toordinal() - _EPOCH_ORD + day - 1
    hours = days*24 + hour
    minutes = hours*60 + minute
    seconds = minutes*60 + second
    return seconds


from machine import Pin

count = 0
def irq(pin):
    count += 1


sense = Pin(38, Pin.IN, handler = irq, trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING)

Expect: 01  Sense: 0 Edges: 0
Expect: 02  Sense: 0 Edges: 3      3
Expect: 03  Sense: 0 Edges: 8      5
Expect: 04  Sense: 1 Edges: 14     6
Expect: 05  Sense: 0 Edges: 19     5
Expect: 06  Sense: 0 Edges: 25     6
Expect: 07  Sense: 0 Edges: 30     5
Expect: 08  Sense: 1 Edges: 36     6
Expect: 09  Sense: 0 Edges: 41     5
Expect: 10  Sense: 0 Edges: 47     6
Expect: 11  Sense: 0 Edges: 52     5
Expect: 12  Sense: 1 Edges: 58     6
Expect: 13  Sense: 0 Edges: 63     5
Expect: 14  Sense: 0 Edges: 69     6
Expect: 15  Sense: 0 Edges: 74     5
Expect: 16  Sense: 1 Edges: 79     5
Expect: 17  Sense: 0 Edges: 83     4
Expect: 18  Sense: 0 Edges: 89     6
Expect: 19  Sense: 0 Edges: 94     5

