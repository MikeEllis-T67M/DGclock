from machine import I2C, Pin, RTC
from utime import sleep_ms, time
import ujson

import pulseclock

def load_settings(settings_file):
  try:
    fd = open(settings_file)
    encoded = fd.read()
    fd.close()
    settings = ujson.loads(encoded)
    return settings
  except Exception as e:
    print(settings_file + ": read error: " + str(e))
import ds3231

def do_connect(ssid, password, hostname):
    import network
    
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sleep_ms(100)
        sta_if.config(dhcp_hostname=hostname)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            sleep_ms(100)

    print('network config:', sta_if.ifconfig())

def dgclock():
    try:
        # Initialise the DS3231 battery-backed RTC
        i2c = I2C(0, scl=22, sda=21)
        ds  = ds3231.DS3231(i2c)

        print("DS3231 time   : {}".format(ds.rtc_tm))
        print("Hands position: {}".format(ds.alarm1_tm))

        # Connect to the WiFi
        wifi = load_settings("wifi.json")
        do_connect(wifi['SSID'], wifi['Password'], wifi['Hostname'])

        # Initialised the FreeRTOS RTC from the DS3231 battery-backed RTC, and set up NTP sync every 15 minutes
        rtc = RTC()
        rtc.init(ds.rtc_tm)
        print("RTC set to    : {}".format(rtc.now()))
        rtc.ntp_sync("pool.ntp.org", update_period = 900)
        recent_sync = False

        # Read the NV stored hand position
        hand_position = ds.alarm1_tm
        invert        = hand_position[5] % 2 == 1 # Is the second hand pointing to an even or odd number?
        display       = hand_position[3] * 3600 + hand_position[4] * 60 + hand_position[5]  % 43200

        # Initialise the pulse clock itself - pulses of 175/100 seem reliable
        pc = pulseclock.PulseClock(Pin(26, Pin.OUT), Pin(25, Pin.OUT), Pin(27, Pin.OUT), 175, 100, invert)

        while True:
            # Convert current time to seconds since 00:00:00 (12-hour clock mode)
            current_time = rtc.now()
            current = (current_time[3]  * 3600 + current_time[4]  * 60 + current_time[5]) % 43200

            # How far apart are the hands - allowing for wrap-around
            diff = current - display 
            #print("Time:{} Hands:{} Delta:{}".format(current, display, diff))
            if diff > 0 or diff < -7200: # If the difference is less than two hours, it's quicker just to stop the clock
                # Update the stored hand position
                display           = (display + 1) % 43200
                new_hand_position = (0, 0, 0, (display // 3600), (display // 60) % 60, display % 60, 0, 0) 
                ds.alarm1_tm      = new_hand_position

                # Move the clock - note that there is a potential race condition here
                pc.step()
            else:
                sleep_ms(100)

            # Re-sync the clocks every 15 minutes at HH:01:02, HH:16:02, HH:31:02 and HH:46:02
            #if (current % 900) == 62:  DEBUG
            if (current % 60) == 2:
                if not recent_sync:
                    recent_sync = True
                    if rtc.synced():
                        print("RTC synced  : DS {} <- RTC {}".format(ds.rtc_tm, rtc.now()))
                        ds.rtc_tm = rtc.now() # Copy from RTC to DS if the RTC is NTP synced
                    else:
                        print("RTC non-sync: DS {} -> RTC {}".format(ds.rtc_tm, rtc.now()))
                        rtc.init(ds.rtc_tm) # Otherwise copy from the DS to the RTC
            else:
                recent_sync = False
    finally:
        # Try to relinquish the I2C bus
        i2c.deinit()
        del i2c