from machine import I2C, Pin, RTC
from utime import sleep_ms, time
import ujson
import display

import ds3231
import pulseclock
import settings
import wifi

def text_centred(tft, text, vpos):
    """ Display some text centred on the screen

    Args:
        tft  (TFT display): The display to use
        text (string)     : The text to display
        vpos (int)        : The vertical position on the screen
    """    
    tft.text(120 - int(tft.textWidth(text)/2), vpos - int(tft.fontSize()[1]/2), text)

def dgclock():
    # Initialise the display
    tft = display.TFT() 
    tft.init(tft.ST7789,bgr=False,rot=tft.LANDSCAPE, miso=17,backl_pin=4,backl_on=1, mosi=19, clk=18, cs=5, dc=16,splash = False)
    tft.setwin(40,52,320,240)
    tft.font(tft.FONT_Comic) # It's big and easy to read...
    text_centred(tft, "DG Clock", 8)

    try:
        # Initialise the DS3231 battery-backed RTC
        i2c = I2C(0, scl=22, sda=21)
        ds  = ds3231.DS3231(i2c)

        print("DS3231 time   : {}".format(ds.rtc_tm))
        print("Hands position: {}".format(ds.alarm1_tm))

        # Connect to the WiFi 
        wifi_settings = settings.load_settings("wifi.json")
        ip_addr       = wifi.connect(wifi_settings['SSID'], wifi_settings['Password'], wifi_settings['Hostname'])
        text_centred(tft, "{}".format(ip_addr), 20)

        # Initialised the FreeRTOS RTC from the DS3231 battery-backed RTC, and set up NTP sync every 15 minutes
        rtc = RTC()
        rtc.init(ds.rtc_tm)
        print("RTC set to    : {}".format(rtc.now()))
        rtc.ntp_sync("pool.ntp.org", update_period = 900)
        recent_sync = False

        # Read the NV stored hand position
        hand_position = ds.alarm1_tm
        invert        = hand_position[5] % 2 == 0 # Is the second hand pointing to an even or odd number?
        display       = hand_position[3] * 3600 + hand_position[4] * 60 + hand_position[5]  % 43200

        # Initialise the pulse clock itself - pulses of 200/100 seem reliable
        pc = pulseclock.PulseClock(Pin(26, Pin.OUT), Pin(25, Pin.OUT), Pin(27, Pin.OUT), 300, 50, invert)

        while True:
            # Convert current time to seconds since 00:00:00 (12-hour clock mode)
            current_time = rtc.now()
            current = (current_time[3]  * 3600 + current_time[4]  * 60 + current_time[5]) % 43200

            # How far apart are the hands - allowing for wrap-around
            diff = current - display 
            #print("Time:{} Hands:{} Delta:{}".format(current, display, diff))  # DEBUG
            if diff > 0 or diff < -7200: # If the difference is less than two hours, it's quicker just to stop the clock
                # Update the stored hand position
                display           = (display + 1) % 43200
                new_hand_position = (0, 0, 0, (display // 3600), (display // 60) % 60, display % 60, 0, 0) 
                if new_hand_position[6] > 0:
                    print("Hands moved to {}".format(new_hand_position))  # DEBUG
                ds.alarm1_tm      = new_hand_position

                # Move the clock - note that there is a potential race condition here
                pc.step()

                # Update the display
                text_centred(tft, "Actual {:2d}:{:02d}:{:02d}".format(current_time[3],      current_time[4],      current_time[5]),      32)
                text_centred(tft, "Hands  {:2d}:{:02d}:{:02d}".format(new_hand_position[3], new_hand_position[4], new_hand_position[5]), 32)
            else:
                sleep_ms(100)

            # Re-sync the clocks every 15 minutes at HH:01:02, HH:16:02, HH:31:02 and HH:46:02
            if (current % 900) == 62:  
                if not recent_sync: # Needed to avoid multiple sync attempts within a single second
                    recent_sync = True
                    if rtc.synced():
                        print("RTC synced  : DS {} <- RTC {}".format(ds.rtc_tm, rtc.now())) # DEBUG
                        ds.rtc_tm = rtc.now() # Copy from RTC to DS if the RTC is NTP synced
                    else:
                        print("RTC non-sync: DS {} -> RTC {}".format(ds.rtc_tm, rtc.now())) # DEBUG
                        rtc.init(ds.rtc_tm) # Otherwise copy from the DS to the RTC
            else:
                recent_sync = False
    except KeyboardInterrupt:
        # Try to relinquish the I2C bus
        i2c.deinit()
        # del i2c