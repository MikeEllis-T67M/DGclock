import machine, display, time, math, network, utime

tft = display.TFT() 
tft.init(tft.ST7789,bgr=False,rot=tft.LANDSCAPE, miso=17,backl_pin=4,backl_on=1, mosi=19, clk=18, cs=5, dc=16)
tft.setwin(40,52,320,240)

for i in range(0,241): 
    color = tft.hsb2rgb(i/241*360, 1, 1)
    tft.line(i, 0, i, 135, color)

tft.set_fg(0xFFFFFF)

tft.ellipse(120,67,120,67)

tft.line(0,0,240,135)

tft.font(tft.FONT_Comic)

text = "DG Clock"
tft.text(120 - int(tft.textWidth(text)/2), 8, text, 0xFFFFFF)

# Turn off the access point
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)

# Connect as a station
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
if sta_if.isconnected():
    print('Already connected!')
else:
    sta_if.connect("Claremont", "1025Anne2018")
    for t in range(0, 120):
        print('.', end='')
        if sta_if.isconnected():
            print('success!')
            break
        time.sleep_ms(500)

# Display IP address
text = "IP address".format(sta_if.ifconfig()[0])
tft.text(120 - int(tft.textWidth(text)/2), 90 - int(tft.fontSize()[1]/2), text, 0xFFFFFF)

text = "{}".format(sta_if.ifconfig()[0])
tft.text(120 - int(tft.textWidth(text)/2), 120 - int(tft.fontSize()[1]/2), text, 0xFFFFFF)

# Try to get the current time from NTP
#import ntplib
#c = ntplib.NTPClient()
#response = c.request('192,168,16,10', version=3)
#ntp_tm = utime.localtime(response.tx_time)

import ntptime

utc = ntptime.time()
tm = utime.localtime(utc)

text = "{0:02}:{1:02}:{2:02}".format(tm[3], tm[4], tm[5])
tft.text(120 - int(tft.textWidth(text)/2), 60 - int(tft.fontSize()[1]/2), text, 0xFFFFFF)

# How do the touch-pads work?
# Answer - they aren't an answer!
#from machine import TouchPad, Pin
#
#t = TouchPad(Pin(2))
#while True:
#    print("Touch read: {}".format(t.read()))

# Next thing - get the motor driver working to step the hands
motor_en = machine.Pin(36, Pin.OUT)
motor_A  = machine.Pin(37, Pin.OUT)
motor_B  = machine.Pin(38, Pin.OUT)

motor_en.off()
motor_A.off()
motor_B.off()

import utime

# Let's start off with 200ms pulses once per second
pulse_duration = 200
pulse_rate     = 1000

while True:
    # Pulse polarity positive
    motor_A.on()
    motor_en.on()
    utime.sleep_ms(pulse_duration)
    motor_en.off() # Keep the driver disabled as much as possible to save power/heat
    motor_A.off()

    # Wait
    utime.sleep_ms(pulse_rate - pulse_duration)

    # Pulse polarity negative
    motor_B.on()
    motor_en.on()
    utime.sleep_ms(pulse_duration)
    motor_en.off() # Keep the driver disabled as much as possible to save power/heat
    motor_B.off()

    utime.sleep_ms(pulse_rate - pulse_duration)