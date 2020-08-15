from machine import I2C, Pin, RTC
from utime import sleep_ms, time
import ujson
import display

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

def dggui():
    # Initialise the display
    tft = display.TFT() 
    tft.init(tft.ST7789,bgr=False,rot=tft.LANDSCAPE, miso=17,backl_pin=4,backl_on=1, mosi=19, clk=18, cs=5, dc=16,splash = False)
    tft.setwin(40,52,320,240)
    tft.font(tft.FONT_Comic) # It's big and easy to read...
    text_centred(tft, "DG GUI", 8)

    # Connect to the WiFi 
    wifi_settings = settings.load_settings("wifi.json")
    ip_addr       = wifi.connect_sta(wifi_settings['SSID'], wifi_settings['Password'], wifi_settings['Hostname'])
    text_centred(tft, "{}".format(ip_addr), 38)

    ap_settings   = settings.load_settings("wifi_ap.json")
    ap_info       = wifi.setup_ap(ap_settings['SSID'], ap_settings['Password'], ap_settings['Hostname'])
    print('AP config: {}'.format(ap_info))
    text_centred(tft, "{}".format(ap_info[0]), 60)

    # Initialise the FreeRTOS RTC and set up NTP sync every 15 minutes
    rtc = RTC()
    print("RTC set to    : {}".format(rtc.now()))
    rtc.ntp_sync("pool.ntp.org", update_period = 900)
    recent_sync = False

    # Initialise the input buttons
    button_top = machine.Pin(0,  machine.Pin.IN, machine.Pin.PULL_UP) # No external pull-up
    button_bot = machine.Pin(35, machine.Pin.IN)                      # No internal pull-up

    try:
        while True:
            # Convert current time to seconds since 00:00:00 (12-hour clock mode)
            current_time = rtc.now()

            # Update the display
            text_centred(tft, "Time {:2d}:{:02d}:{:02d}".format(current_time[3],      current_time[4],      current_time[5]),      60)

            if rtc.synced():
                text_centred(tft, "NTP Sync OK", 100)
            else:
                text_centred(tft, "No NTP sync", 100)

            if button_top

    except KeyboardInterrupt:
        # Try to relinquish the I2C bus
        tft.deinit()
