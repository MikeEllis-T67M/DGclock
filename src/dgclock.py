from machine import I2C, Pin, RTC
from utime import sleep_ms, time, mktime
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

def init_display():
    # Initialise the display
    tft = display.TFT() 
    tft.init(tft.ST7789, bgr=False, rot=tft.LANDSCAPE, miso=17, backl_pin=4, backl_on=1, mosi=19, clk=18, cs=5, dc=16, splash = False)
    tft.setwin(40,52,320,240)
    tft.font(tft.FONT_Comic) # It's big and easy to read...
    text_centred(tft, "DG Clock", 8)
    return tft

def update_clock(pc, ds, rtc, tft, hands):
    """ Update the mechanical clock

    Args:
        pc (PulseClock): The pulse clock which (may) need to be stepped

    Returns:
        True is the clock was stepped, otherwise False
    """  
    current_time = rtc.now()
    current = (current_time[3]  * 3600 + current_time[4]  * 60 + current_time[5]) % 43200

    # How far apart are the hands - allowing for wrap-around
    diff = current - hands 

    if -7200 < diff and diff <= 0: # If the difference is less than two hours, it's quicker just to stop the clock
        sleep_ms(100) # A little bit of idle time for background threads to run in - but not too much so that the hand movement looks jerky
        return hands

    # Update the stored hand position
    hands             = (hands + 1) % 43200
    new_hand_position = (0, 0, 0, (hands // 3600), (hands // 60) % 60, hands % 60, 0, 0) 
    ds.alarm1_tm      = new_hand_position

    # Move the clock - note that there is a potential race condition here
    pc.step()

    # Update the display
    text_centred(tft, "Actual {:2d}:{:02d}:{:02d}".format(current_time[3],      current_time[4],      current_time[5]),      60)
    text_centred(tft, "Hands  {:2d}:{:02d}:{:02d}".format(new_hand_position[3], new_hand_position[4], new_hand_position[5]), 82)

    return hands

def align_clocks(rtc, ds):
    now = mktime(rtc.now()) #  Get the current time as seconds from epoch

    if rtc.synced():
        print("RTC synced  : DS {} <- RTC {}".format(ds.rtc_tm, rtc.now())) # DEBUG
        ds.rtc_tm   = rtc.now() # Copy from RTC to DS if the RTC is NTP synced
    else:
        print("RTC non-sync: DS {} -> RTC {}".format(ds.rtc_tm, rtc.now())) # DEBUG
        rtc.init(ds.rtc_tm) # Otherwise copy from the DS to the RTC

    return now

def dgclock():
    # Intialised the display
    tft = init_display()

    # Initialise the DS3231 battery-backed RTC
    i2c = I2C(0, scl=22, sda=21)
    ds  = ds3231.DS3231(i2c)
    print("DS3231 time   : {}".format(ds.rtc_tm))
    print("Hands position: {}".format(ds.alarm1_tm))

    # Connect to the WiFi 
    wifi_settings = settings.load_settings("wifi.json")
    ip_addr       = wifi.connect_sta(wifi_settings['SSID'], wifi_settings['Password'], wifi_settings['Hostname'])
    text_centred(tft, "{}".format(ip_addr), 38)

    # Initialised the FreeRTOS RTC from the DS3231 battery-backed RTC, and set up NTP sync every 15 minutes
    rtc = RTC()
    rtc.init(ds.rtc_tm)
    print("RTC set to    : {}".format(rtc.now()))
    rtc.ntp_sync("pool.ntp.org", update_period = 900)
    last_sync  = ds.rtc
    ntp_synced = False

    # Initialise the hand position using the value stored in NV-RAM in the DS chip
    hand_position = ds.alarm1_tm
    invert        = hand_position[5] % 2 == 0 # Is the second hand pointing to an even or odd number?
    hands         = hand_position[3] * 3600 + hand_position[4] * 60 + hand_position[5]  % 43200

    # Initialise the pulse clock itself - pulses of 200/100 seem reliable
    clock_settings = settings.load_settings("clock.json")
    pc = pulseclock.PulseClock(Pin(clock_settings['Plus'],   Pin.OUT), 
                               Pin(clock_settings['Minus'],  Pin.OUT), 
                               Pin(clock_settings['Enable'], Pin.OUT), 
                               clock_settings['Pulse'],
                               clock_settings['Dwell'], 
                               invert)

    try:
        while True:
            hands = update_clock(pc, ds, rtc, tft, hands)

            # Periodically re-sync the clocks
            if mktime(rtc.now()) > last_sync + 900:
                last_sync = align_clocks(rtc, ds)

            # Tell the user whether the NTP sync is good or not
            if rtc.synced():
                text_centred(tft, "NTP Sync OK", 104)
                if not ntp_synced: # Just achieved sync - set the clock immediately
                    last_sync  = align_clocks(rtc, ds)
                    ntp_synced = True
            else:
                text_centred(tft, "No NTP Sync", 104)
                ntp_synced = False
    

    except KeyboardInterrupt:
        # Try to relinquish the I2C bus
        print("Hand position: {}".format(ds.alarm1_tm))
        i2c.deinit()
        tft.deinit()
        # del i2c