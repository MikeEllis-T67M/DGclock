from machine import I2C, Pin, RTC
from utime import sleep_ms, time
import ujson
import display

import settings
import wifi

from microWebSrv import MicroWebSrv

# ----------------------------------------------------------------------------

@MicroWebSrv.route('/test')
def _httpHandlerTestGet(httpClient, httpResponse) :
	content = """\
	<!DOCTYPE html>
	<html lang=en>
        <head>
        	<meta charset="UTF-8" />
            <title>TEST GET</title>
        </head>
        <body>
            <h1>TEST GET</h1>
            Client IP address = %s
            <br />
			<form action="/test" method="post" accept-charset="ISO-8859-1">
				First name: <input type="text" name="firstname"><br />
				Last name: <input type="text" name="lastname"><br />
				<input type="submit" value="Submit">
			</form>
        </body>
    </html>
	""" % httpClient.GetIPAddr()
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )


@MicroWebSrv.route('/test', 'POST')
def _httpHandlerTestPost(httpClient, httpResponse) :
	formData  = httpClient.ReadRequestPostedFormData()
	firstname = formData["firstname"]
	lastname  = formData["lastname"]
	content   = """\
	<!DOCTYPE html>
	<html lang=en>
		<head>
			<meta charset="UTF-8" />
            <title>TEST POST</title>
        </head>
        <body>
            <h1>TEST POST</h1>
            Firstname = %s<br />
            Lastname = %s<br />
        </body>
    </html>
	""" % ( MicroWebSrv.HTMLEscape(firstname),
		    MicroWebSrv.HTMLEscape(lastname) )
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )


@MicroWebSrv.route('/edit/<index>')             # <IP>/edit/123           ->   args['index']=123
@MicroWebSrv.route('/edit/<index>/abc/<foo>')   # <IP>/edit/123/abc/bar   ->   args['index']=123  args['foo']='bar'
@MicroWebSrv.route('/edit')                     # <IP>/edit               ->   args={}
def _httpHandlerEditWithArgs(httpClient, httpResponse, args={}) :
	content = """\
	<!DOCTYPE html>
	<html lang=en>
        <head>
        	<meta charset="UTF-8" />
            <title>TEST EDIT</title>
        </head>
        <body>
	"""
	content += "<h1>EDIT item with {} variable arguments</h1>"\
		.format(len(args))
	
	if 'index' in args :
		content += "<p>index = {}</p>".format(args['index'])
	
	if 'foo' in args :
		content += "<p>foo = {}</p>".format(args['foo'])
	
	content += """
        </body>
    </html>
	"""
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )

# ----------------------------------------------------------------------------

def _acceptWebSocketCallback(webSocket, httpClient) :
	print("WS ACCEPT")
	webSocket.RecvTextCallback   = _recvTextCallback
	webSocket.RecvBinaryCallback = _recvBinaryCallback
	webSocket.ClosedCallback 	 = _closedCallback

def _recvTextCallback(webSocket, msg) :
	print("WS RECV TEXT : %s" % msg)
	webSocket.SendText("Reply for %s" % msg)

def _recvBinaryCallback(webSocket, data) :
	print("WS RECV DATA : %s" % data)

def _closedCallback(webSocket) :
	print("WS CLOSED")

# ----------------------------------------------------------------------------

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

    # ----------------------------------------------------------------------------

    #routeHandlers = [
    #	( "/test",	"GET",	_httpHandlerTestGet ),
    #	( "/test",	"POST",	_httpHandlerTestPost )
    #]

    # Initialise the demo website
    srv = MicroWebSrv(webPath='/flash/www')
    srv.MaxWebSocketRecvLen     = 256
    srv.AcceptWebSocketCallback = _acceptWebSocketCallback
    srv.Start(threaded = True)

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

    except KeyboardInterrupt:
        # Try to relinquish the I2C bus
        tft.deinit()
