# Last NTP check started at 1605987450 (21st November)
# Check at   1607715597 when DS3231 read 1607715599
# Drift was 2 in 1728147 secs: 1.15730895577749ppm  (11th December)
# Cal factor adjusted to -12 (== -1.2ppm)

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

import settings
import wifi
wifi_settings = settings.load_settings("wifi.json")
ip_addr       = wifi.connect_sta(wifi_settings['SSID'], wifi_settings['Password'], wifi_settings['Hostname'])

print(''.join('{:02x} '.format(x) for x in ds.read_ds3231_rtc()))