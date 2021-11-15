from machine import I2C, Pin, RTC
from utime import sleep_ms, time, mktime, ticks_ms, ticks_add, ticks_diff
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

    # Read the WiFi settings
    wifi_settings = settings.load_settings("wifi.json")
    network       = wifi.wifi(wifi_settings)

    # Read the NTP server to use
    ntp_settings  = settings.load_settings("ntp.json")
    next_ntp_sync = ds.rtc + 120 # First sync attempt after 120 seconds
    set_time      = 0            # Resetting the DS RTC not needed

    try:
        while True:
            # Tell the UI what the time is
            ui.now_tm = ds.rtc_tod_tm
            now       = ds.rtc_tod

            # Move the clock to show current TOD unless stopped
            if ui.mode == 'Normal' or ui.mode == 'Set':
                clock.move(now)

            # Update the non-volatile copy of the hand position
            ds.alarm1_tm  = clock.hands_tm
            sleep_ms(10) # Allow time for this to complete - DS3231 write can fail otherwise

            # LED states
            if clock.mode == "Run" and ui.now_tm[3] == 22 and ui.now_tm[4] == 0:
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

            # Tell the UI where the clock thinks the hands are
            ui.hands_tm   = clock.hands_tm
            ui.clock_mode = clock.mode

            # Check that we have a WiFi connection, and attempt to reconnect if it's dropped
            network.connect()

            # Handle any button presses
            if ui.handle_buttons():  # Adjust hands was selected, so copy from UI to the clock
                clock.hands_reset(ui.time_to_set)

            # Update the screen
            ui.update_screen()

            # Periodically re-sync the clocks to NTP
            if ds.rtc > next_ntp_sync:
                print("Querying {}".format(ntp_settings['NTP']))
                (ntp_time, millis, ticks) = ntptime.ntp_query(ntp_settings['NTP'])
                old_time                = ds.rtc
                if ntp_time is not None:
                    #ds.rtc        = ntp_time        # Copy the received time into the RTC as quickly as possible to minimise error

                    error_ms = 1000 - millis # Convert fractional part to error in milliseconds

                    set_at_ticks = ticks_add(ticks, error_ms)
                    set_time     = ntp_time + 1

                    print("Got {}.{:03d} @ {} - error in milliseconds {} - setting {} @ {}".format(ntp_time, millis, ticks, error_ms, set_time, set_at_ticks))

                    next_ntp_sync = ntp_time + 3654 # Just a bit less than once an hour
                    #print("Sync (disabled) RTC to NTP - {} (delta {})".format(ds.rtc_tod_tm, old_time - ntp_time))
                else:
                    ui.ntp_sync   = False
                    next_ntp_sync = ds.rtc + 321 # Just a bit more than five minutes
                    print("NTP sync failed at  {}".format(ui.now_tm))
            else:
                gc.collect() # Don't waste time garbage collecting if we're also setting the clock

            if set_time > 0:
                tick_err = ticks_diff(ticks_ms(), set_at_ticks)
                if -100 < tick_err and tick_err < 100: # Allow a 100ms "buffer"
                    ds.rtc = set_time
                    ui.ntp_sync   = True
                    print("Set DS RTC {} ({}) @ {}".format(set_time, ds.rtc_tm, ticks_ms()))
                    set_time = 0
                elif tick_err > 100: # Missed - try again on the next second
                    set_time += 1
                    set_at_ticks = ticks_add(set_at_ticks, 1000)
                    print("Missed the ticks - trying again @ {}".format(set_at_ticks))
                else:
                    print("Tick error {}".format(tick_err))

    except KeyboardInterrupt:
        # Try to relinquish the I2C bus
        print("Hands left at : {}".format(ds.alarm1_tm))
        i2c.deinit()
        ui.tft.deinit()

if __name__ == "__main__":
    main()