""" User Interface for the DG's clock
"""

from machine import RTC
import network
class DGUI:
    def __init__(self, button1, button2, tft):
        """ Constructor
        Args:
            button1 (Pin): Button 1 (back) input pin
            button2 (Pin): Button 2 (action) input pin
            tft     (TFT): Display
        """            
        self.button1         = button1
        self.button1_pressed = False
        self.button2         = button2
        self.button2_pressed = False
        self.tft             = tft
        self.mode            = "Normal"
        self.setmode         = 0
        self.rtc             = RTC()
        self.last_update     = 0
        self.sta             = network.WLAN(network.STA_IF)
        
        # Configure the display
        tft.init(tft.ST7789, bgr=False, rot=tft.LANDSCAPE, miso=17, backl_pin=4, backl_on=1, mosi=19, clk=18, cs=5, dc=16, splash = False)
        tft.setwin(40,52,320,240)
        tft.font(tft.FONT_Comic) # It's big and easy to read...
        tft.set_bg(0xffffff)     # Should be black
        tft.set_fg(0x000000)     # Should be white

        # Set up interrupt handlers to capture button presses
        button1.irq(trigger = Pin.IRQ_FALLING, handler = self._B1interrupt)
        button2.irq(trigger = Pin.IRQ_FALLING, handler = self._B2interrupt)

    def _B1interrupt(self, pin):
        self.button1_pressed = True

    def _B2interrupt(self, pin):
        self.button2_pressed = True

    def __repr__(self_):
        """ Returns representation of the object
        """
        return("{}({!r})".format(self.__class__.__name__, self.button1, self.button2, self.tft))

    def handleinput(self):
        if not button1_pressed and not button2_pressed:
            return False # Nothing to do
        
        # Simple state machine to got through Info -> Normal, Stop -> Adjust -> Normal
        if button1_pressed: # Back button
            button1_pressed = False # Acknowledge the button press
            button2_pressed = False # Both buttons at the same time not allowed
            if self.mode == "Normal":
                return False # Already at Normal screen
            elif self.mode == "Info":
                self.mode = "Normal"
                return True
            elif self.mode == "Stop":
                self.mode = "Adjust"
                return True
            elif self.mode == "Adjust":
                self.mode = "Normal"
                ### TODO Process the instruction to update the hand position
            else:
                return False # Further modes not yet implemented

        # Simple state machine to go through Normal -> Info -> Stop -> Adjust -> Normal
        if button2_pressed:
            button2_pressed = False # Acknowledge the button press
            if self.mode == "Normal":
                self.mode = "Info"
                return True
            elif self.mode == "Info":
                self.mode = "Stop"
                return True
            elif self.mode == "Stop":
                self.mode = "Adjust"
                self.setmode = 0 # Should be no change
                return True
            elif self.mode == "Adjust":
                self.setmode = (self.setmode + 1) % 4 # Modes are Current / HH:MM:00 / 12:00:00 / 6:00:00
                return True
            else: 
                return False # Further modes not yet implemented

    def _dodrawscreen(self):
        """ Clear and redraw the screen right now
        """
        self.tft.clear()   
        self._doupdate()

    def _doupdate(self):
        """ Do update the screen immediately
        """
        pass

    def update_screen(self):
        """ Update the screen at any time, but don't repeatedly update the screen if nothing's changed.
        """
        if self.handleinput() or self.rtc.now() > self.last_update:
            self.last_update = self.rtc.now()
            self._doupdate()

    def drawscreen_normal(self):
        # Title the display
        text_centred(self.tft, "DG Clock", 8)
        
        # Show the current network config
        if not self.sta.active():
            text_centred(self.tft, "WiFi not active", 38)
        elif not self.sta.isconnected():
            text_centred(self.tft, "WiFi not connected", 38)
        else:
            text_centred(self.tft, "WiFi {}".format(self.sta.ifconfig()[0]), 38)
        
        # Show the current time and hand position
        text_centred(self.tft, "Actual {:2d}:{:02d}:{:02d}".format(now[3], now[4], now[5]), 60) # 24-hour format
        text_centred(self.tft, "Hands  {:2d}:{:02d}:{:02d}".format(int(hands // 3600) % 12, int(hands // 60) % 60, int(hands) % 60), 82) # 12-hour format

        # Tell the user whether the NTP sync is good or not
        if self.rtc.synced():
            text_centred(self.tft, "NTP Sync OK", 104)
        else:
            text_centred(self.tft, "No NTP Sync", 104)
        text_centred(self.tft, self.mode, 126)
