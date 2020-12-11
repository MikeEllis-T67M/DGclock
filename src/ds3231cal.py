from machine import I2C, Pin, RTC
from utime import sleep, time, mktime
import ujson
import display

import ds3231
import settings
import wifi
import ntptime

def get_timetuple(ds):
    # Poll NTP until we see a SECOND second's edge
    ntp_time = None
    while ntp_time is None:
        ntp_time  = ntptime.ntp_query("192.168.16.10")
    first_ntp_time = ntp_time

    while ntp_time < first_ntp_time + 2:
        ntp_time  = ntptime.ntp_query("192.168.16.10")
        if ntp_time is None:
            ntp_time = 0

    # Read the DS3231
    ds_time = ds.rtc + 1 # Reading takes a little while, so allow a 1 second margin

    return (ds_time, ntp_time)

def main():
    # Initialise the DS3231 battery-backed RTC
    i2c = I2C(0, scl=22, sda=21)
    ds  = ds3231.DS3231(i2c)

    # Connect to the WiFi 
    wifi_settings = settings.load_settings("wifi.json")
    ip_addr       = wifi.connect_sta("Claremont", "1025Anne2018", "DGClock")

    start_time = 1605987450

    # Wait for a while
    print("Starting from {}".format(start_time))

    while True:
        # Poll NTP until we see a SECOND second's edge
        (ntp_time, ds_time) = get_timetuple(ds)
        
        print("Check at   {} when DS3231 read {}".format(ntp_time, ds_time))

        # Compare the two values
        # start_time applies to both NTP and DS3231
        # ntp_time   is the NTP at the end
        # ds_time    is the DS3231
        drift = ds_time - ntp_time # Positive value means the DS3231 is fast
        rate  = drift / (ntp_time - start_time) * 1e6

        print("Drift was {} in {} secs: {}ppm".format(drift, ntp_time - start_time, rate))

        sleep(60)

if __name__ == "__main__":
    dgclock()