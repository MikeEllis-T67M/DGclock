""" User Interface for the DG's clock
"""

from machine import RTC, Pin
from utime   import mktime, sleep_ms
import network
import display
class DGUI:
    def __init__(self, current_hands):
        """ Constructor
        Args:
            callback (function): Function to call to set the hands to a specific value
        """            
        self.mode            = "Normal"
        self.current_hands   = current_hands
        self.setmode         = 0
        self.last_update     = 0
        self.pressed_top     = False
        self.pressed_bottom  = False
        self.button1         = Pin( 0, Pin.IN, Pin.PULL_UP, handler = self._B1interrupt, trigger = Pin.IRQ_RISING) # Button released
        self.button2         = Pin(35, Pin.IN,              handler = self._B2interrupt, trigger = Pin.IRQ_RISING) # Button released
        self.tft             = display.TFT()
        self.rtc             = RTC()
        self.sta             = network.WLAN(network.STA_IF)
        self.updated         = True         # New info needs to be displayed
        self.redraw          = True         # The screen changes completely - clear and re-write
        
        # Configure the display
        tft = self.tft
        tft.init(tft.ST7789, bgr=False, rot=tft.LANDSCAPE, 
                 miso=17, backl_pin=4, backl_on=1, mosi=19, clk=18, cs=5, dc=16, 
                 splash = False)
        tft.setwin(40,52,320,240)
        tft.font(tft.FONT_Comic) # It's big and easy to read...
        tft.set_bg(0xffffff)     # Should be black
        tft.set_fg(0x000000)     # Should be white
        tft.clear()

    def _B1interrupt(self, pin):
        self.pressed_top = True

    def _B2interrupt(self, pin):
        self.pressed_bottom = True

    def __repr__(self_):
        """ Returns representation of the object
        """
        return("{}({!r})".format(self.__class__.__name__, self.button1, self.button2, self.tft))

    def text_centred(self, text, vpos, color = False):
        """ Display some text centred on the screen

        Args:
            tft  (TFT display): The display to use
            text (string)     : The text to display
            vpos (int)        : The vertical position on the screen
        """    
        if not color:
            color = self.tft.get_fg()

        self.tft.text(120 - int(self.tft.textWidth(text)/2), vpos - int(self.tft.fontSize()[1]/2), text, color)

    def text_right(self, text, vpos, color = False):
        """ Display some text centred on the screen

        Args:
            tft  (TFT display): The display to use
            text (string)     : The text to display
            vpos (int)        : The vertical position on the screen
        """    
        if not color:
            color = self.tft.get_fg()

        self.tft.text(240 - int(self.tft.textWidth(text)), vpos - int(self.tft.fontSize()[1]/2), text, color)

    def text_left(self, text, vpos, color = False):
        """ Display some text centred on the screen

        Args:
            tft  (TFT display): The display to use
            text (string)     : The text to display
            vpos (int)        : The vertical position on the screen
        """    
        if not color:
            color = self.tft.get_fg()

        self.tft.text(0, vpos - int(self.tft.fontSize()[1]/2), text, color) # Orange for buttons

    def handle_buttons(self):
        if not self.pressed_top and not self.pressed_bottom:
            return False # Nothing to do
        
        # Make sure the screen is redrawn next time around
        self.redraw  = True
        self.updated = True

        # Simple state machine to got through Info -> Normal, Stop -> Adjust -> Normal
        if self.pressed_top: # Back button
            self.pressed_top = False # Acknowledge the button press
            self.pressed_bottom = False # Both buttons at the same time not allowed
            if self.mode == "Info":
                self.mode = "Normal"
            elif self.mode == "Stop":
                self.mode = "Adjust"
                self.setmode = 0 # Should be no change
            elif self.mode == "Adjust":
                self.mode = "Normal"
                return True                 # Only executive exit - flag True to say read set_time and execute

        # Simple state machine to go through Normal -> Info -> Stop -> Adjust -> Normal
        if self.pressed_bottom:
            self.pressed_bottom = False # Acknowledge the button press
            if self.mode == "Normal":
                self.mode = "Info"
            elif self.mode == "Info":
                self.mode = "Stop"
            elif self.mode == "Stop":
                self.mode = "Normal"
            elif self.mode == "Adjust":
                self.setmode = (self.setmode + 1) % 4 # Modes are Current / HH:MM:00 / 12:00:00 / 6:00:00

        return False

    def _doredraw(self):
        """ Clear and redraw the screen right now
        """
        self.tft.clear()   
        self._doupdate()

    def _doupdate(self):
        """ Do update the screen immediately
        """
        if self.mode == "Info":
            self.drawscreen_info()
        elif self.mode == "Stop":
            self.drawscreen_stop()
        elif self.mode == "Adjust":
            self.drawscreen_adjust()
        else:
            self.mode = "Normal"       # Catch an illegal mode
            self.drawscreen_normal()

    @property
    def hands_tm(self):
        return self.current_hands
        
    @hands_tm.setter
    def hands_tm(self, value):
        self.current_hands = value
        self.updated       = True

    def update_screen(self):
        """ Update the screen at any time, but don't repeatedly update the screen if nothing's changed.
        """
        now = mktime(self.rtc.now())
        
        if self.redraw:
            self._doredraw()
        elif self.updated or now > self.last_update:
            self._doupdate()

        self.last_update = now
        self.redraw      = False
        self.updated     = False

    def drawscreen_normal(self):
        # Title the display
        self.text_centred("DG Clock", 8)
        
        # Show the current network config
        if not self.sta.active():
            self.text_centred("WiFi not active", 38, 0x0088ff)                          # Amber
        elif not self.sta.isconnected():
            self.text_centred("WiFi not connected", 38, 0x00ffff)                       # Red
        else:
            self.text_centred("WiFi {}".format(self.sta.ifconfig()[0]), 38, 0xff00ff)   # Green
        
        # Tell the user whether the NTP sync is good or not
        if self.rtc.synced():
            self.text_centred("NTP Sync OK", 104, 0xff00ff)                             # Green
        else:
            self.text_centred("No NTP Sync", 104, 0x0088ff)                             # Amber

        self.text_right(self.mode, 126, 0x0088ff)
        self.text_left("<INFO",    126, 0xff8800)

    def drawscreen_info(self):
        # Show the current network config
        if not self.sta.active():
            self.text_centred("WiFi not active", 38)
        elif not self.sta.isconnected():
            self.text_centred("WiFi not connected", 38)
        else:
            self.text_centred("WiFi {}".format(self.sta.ifconfig()[0]), 38)
        
        # Tell the user whether the NTP sync is good or not
        if self.rtc.synced():
            self.text_centred("NTP Sync OK", 104)
        else:
            self.text_centred("No NTP Sync", 104)

        self.text_right(self.mode, 126, 0x0088ff)
        self.text_left("<Back",      8, 0xff8800)
        self.text_left("<STOP",    126, 0xff8800)

    def drawscreen_stop(self):
        self.text_right(self.mode, 126, 0x0088ff)
        self.text_left("<Adjust",    8, 0xff8800)
        self.text_left("<Back",    126, 0xff8800)

    def drawscreen_adjust(self):
        self.text_centred("{}".format(self.setmode), 104)

        self.text_right(self.mode, 126, 0x0088ff)
        self.text_left("<Select",    8, 0xff8800)
        self.text_left("<Change",  126, 0xff8800)

def set_hands_callback(value):
    print("Request to set hands to {}".format(value))

def dgdev():
    ui  = DGUI(set_hands_callback)
    cur = 0

    while True:
        ui.update(cur)
        sleep_ms(200)
        cir += 1

if __name__ == "dggui":
    dgdev()