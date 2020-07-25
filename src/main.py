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

ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)

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

text = "IP address".format(sta_if.ifconfig()[0])
tft.text(120 - int(tft.textWidth(text)/2), 90 - int(tft.fontSize()[1]/2), text, 0xFFFFFF)

text = "{}".format(sta_if.ifconfig()[0])
tft.text(120 - int(tft.textWidth(text)/2), 120 - int(tft.fontSize()[1]/2), text, 0xFFFFFF)