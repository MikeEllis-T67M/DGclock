from machine import I2C, Pin, RTC
from utime import sleep_ms, time, mktime
import ujson
import display

import ds3231
import dgclock
import dgui
import settings
import wifi

def align_clocks(rtc, ds):
    if rtc.synced():
        print("RTC synced    : DS {} <- RTC {}".format(ds.rtc_tm, rtc.now())) # DEBUG
        ds.rtc_tm   = rtc.now() # Copy from RTC to DS if the RTC is NTP synced
    else:
        print("RTC non-sync  : DS {} -> RTC {}".format(ds.rtc_tm, rtc.now())) # DEBUG
        rtc.init(ds.rtc_tm) # Otherwise copy from the DS to the RTC

def main():
    # Connect to the WiFi 
    wifi_settings = settings.load_settings("wifi.json")
    ip_addr       = wifi.connect_sta(wifi_settings['SSID'], wifi_settings['Password'], wifi_settings['Hostname'])

    # Initialise the DS3231 battery-backed RTC
    i2c = I2C(0, scl=22, sda=21)
    ds  = ds3231.DS3231(i2c)
    print("DS3231 time   : {}".format(ds.rtc_tm))
    print("Hands position: {}".format(ds.alarm1_tm))

    # Initialised the FreeRTOS RTC from the DS3231 battery-backed RTC, and set up NTP sync every 15 minutes
    rtc = RTC()
    rtc.init(ds.rtc_tm)
    print("RTC set to    : {}".format(rtc.now()))
    rtc.ntp_sync("pool.ntp.org", update_period = 900)

    # Initialise the mechanical clock
    clock = dgclock.DGClock("clock.json", ds.alarm1) # Read the config file, and initialise hands at last known position

    # Intialise the display
    ui = dgui.DGUI(clock.hands_tm)

    # Initialise "not too often" counters
    last_sync = last_update = mktime(rtc.now())

    try:
        while True:
            now_tm = rtc.now()
            now = now_tm[3] * 3600 + now_tm[4] * 60 + now_tm[5]
            
            # Move the clock forward if needed
            if ui.mode == 'Normal' or ui.mode == 'Info':
                clock.move(now)

            # Update the non-volatile copy of the hand position
            ds.alarm1_tm = clock.hands_tm

            # Tell the UI where the clock thinks the hands are
            ui.hands_tm   = clock.hands_tm
            ui.clock_mode = clock.mode

            # Periodically re-sync the clocks
            if now > last_sync + 900:
                last_sync = now
                align_clocks(rtc, ds)

            # Handle any button presses
            ui.handle_buttons()


            # Update the screen
            ui.update_screen()

    except KeyboardInterrupt:
        # Try to relinquish the I2C bus
        print("Hand position: {}".format(ds.alarm1_tm))
        i2c.deinit()

if __name__ == "__main__":
    dgclock()