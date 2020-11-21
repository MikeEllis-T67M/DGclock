from machine import I2C, Pin, RTC
from utime import sleep_ms, time, mktime
import ujson
import display
import gc

import ds3231
import dgclock
import dgui
import settings
import wifi
import ntptime

def align_clocks(rtc, ds):
    if rtc.synced():
        print("RTC synced    : DS {} <- RTC {}".format(ds.rtc_tm, rtc.now())) # DEBUG
        ds.rtc_tm   = rtc.now() # Copy from RTC to DS if the RTC is NTP synced
    else:
        print("RTC non-sync  : DS {} -> RTC {}".format(ds.rtc_tm, rtc.now())) # DEBUG
        rtc.init(ds.rtc_tm) # Otherwise copy from the DS to the RTC

def main():
    # LED output - turn it on whilst we're booting...
    led = Pin(2, Pin.OUT)
    led.value(1)

    # Initialise the DS3231 battery-backed RTC
    i2c = I2C(0, scl=22, sda=21)
    ds  = ds3231.DS3231(i2c)
    print("DS3231 time   : {}".format(ds.rtc_tm))
    print("Hands position: {}".format(ds.alarm1_tm))

    # Initialise the mechanical clock
    clock = dgclock.DGClock("clock.json", ds.alarm1) # Read the config file, and initialise hands at last known position

    # Intialise the display
    ui = dgui.DGUI(clock.hands_tm)

    # Connect to the WiFi 
    wifi_settings = settings.load_settings("wifi.json")
    ip_addr       = wifi.connect_sta(wifi_settings['SSID'], wifi_settings['Password'], wifi_settings['Hostname'])

    # Initialised the FreeRTOS RTC from the DS3231 battery-backed RTC, and set up NTP sync every 15 minutes
    ntp_settings = settings.load_settings("ntp.json")
    #rtc = RTC()
    #rtc.init(ds.rtc_tm)
    #print("RTC set to    : {}".format(rtc.now()))
    #rtc.ntp_sync(ntp_settings['NTP'], update_period = 900)

    # Initialise "not too often" counters
    next_ntp_sync = last_update = ds.rtc

    try:
        while True:
            # Tell the UI what the time is
            ui.now_tm = ds.rtc_tod_tm

            # Move the clock to show current TOD unless stopped
            if ui.mode == 'Normal' or ui.mode == 'Set':
                clock.move(ds.rtc_tod)

            # LED states
            if clock.mode == "Run" and ui.now_tm[3] == 23 and ui.now_tm[4] == 0:
                # Run mode  - on at 22:00:00 until 22:01:00
                led.value(1)
            elif clock.mode == "Wait":
                # Wait mode - on
                led.value(1)
            elif clock.mode == "Fast" and clock.hands_tm[5] % 2 == 0:
                # Fast mode - on for even seconds
                led.value(1)
            else:
                # Otherwise off
                led.value(0)

            # Update the non-volatile copy of the hand position
            ds.alarm1_tm  = clock.hands_tm

            # Tell the UI where the clock thinks the hands are
            ui.hands_tm   = clock.hands_tm
            ui.clock_mode = clock.mode

            # Handle any button presses
            if ui.handle_buttons():  # Adjust hands was selected, so copy from UI to the clock
                clock.hands_tm = ui.time_to_set

            # Update the screen
            ui.update_screen()

            # Periodically re-sync the clocks
            if ds.rtc > next_ntp_sync:
                ntp_time  = ntptime.ntp_query(ntp_settings['NTP'])
                if ntp_time is not None:
                    ds.rtc        = ntp_time
                    next_ntp_sync = ntp_time + 3654 # Just a bit less than once an hour
                    ui.ntp_sync   = True
                    print("Synced RTC to NTP - {}".format(ds.rtc_tod_tm))
                else:
                    ui.ntp_sync   = False
                    next_ntp_sync = ds.rtc + 321 # Just a bit more than five minutes
                    print("NTP sync failed at  {}".format(ui.now_tm))
            else:
                gc.collect()

    except KeyboardInterrupt:
        # Try to relinquish the I2C bus
        print("Hands left at : {}".format(ds.alarm1_tm))
        i2c.deinit()
        ui.tft.deinit()

if __name__ == "__main__":
    main()