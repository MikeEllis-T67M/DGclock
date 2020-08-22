""" User Interface for the DG's clock
"""

from machine import Pin
from utime   import mktime, sleep_ms
import network
import display
class DGUI:
    def __init__(self, current_hands):
        # Fixed initialisation
        self.mode            = "Normal"
        self.clock_mode      = "Starting"
        self.redraw          = True         # The screen changes completely - clear and re-write
        self.setmode         = 0
        self.pressed_top     = False
        self.pressed_bottom  = False
        self.now_tm          = (0,0,0,0,0,0,0,0)
        self.ntp_sync        = False

        # Input parameter initialisation
        self.current_h       = current_hands[3]
        self.current_m       = current_hands[4]
        self.current_s       = current_hands[5]

        # Functional initialisation
        self.button1         = Pin( 0, Pin.IN, Pin.PULL_UP, handler = self._B1interrupt, trigger = Pin.IRQ_RISING) # Button released
        self.button2         = Pin(35, Pin.IN,              handler = self._B2interrupt, trigger = Pin.IRQ_RISING) # Button released
        self.tft             = display.TFT()
        self.sta             = network.WLAN(network.STA_IF)
        
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

    def text_alignYX(self, text, vpos, hpos = False, align = 'Centre', color = False):
        """ Display some text on the screen

        Args:
            text  (string)    : The text to display
            vpos  (int)       : The vertical position on the screen
            hpos  (int)       : The horizontal position on the screen (defaults to edges/middle)
            align (string)    : Left, Centre or Right
            color (int)       : Colour code (0xffffff = black, 0x00ffff = red etc)
        """    
        if not color:
            color = self.tft.get_fg()

        if align == 'Left':
            offset = 0
        elif align == 'Right':
            offset = self.tft.textWidth(text)
        else: # Assume centre/center
            offset = self.tft.textWidth(text) // 2

        if not hpos:
            if align == 'Left':
                hpos = 0
            elif align == 'Right':
                hpos = 240
            else: # Assume centre/center
                hpos = 120

        self.tft.text(hpos - offset, vpos - self.tft.fontSize()[1] //2, text, color)

    def handle_buttons(self):
        if not self.pressed_top and not self.pressed_bottom:
            return False # Nothing to do
        
        # Make sure the screen is redrawn next time around
        self.redraw  = True

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
                self.setmode = (self.setmode + 1) % 14 # Modes are Current / HH:M5:00 / [1-12]:00:00

        return False

    @property
    def time_to_set(self):
        return self.time_seq(self.setmode)

    def time_seq(self, index):
        if index % 14 == 0: 
            # Current hand position - i.e. no change
            return self.hands_tm
        elif index % 14 == 1: 
            # Current time rounded up to the next easy five minutes
            # Take current displayed time, convert to mins past midnight aligned to 5 minute, 
            # up to 7 minutes in the future, then convert to HH:MM making sure
            # to stay in the range 1-12, not 0-11
            now = self.now_tm
            hm  = (((now[3]-1) * 60 + now[4] + 7) // 5) * 5       
            return (0,0,0, (hm // 60) % 12 + 1, hm % 60, 0,0,0)   
        else:
            # Round to hours in the future (HH:00)
            return (0,0,0, (self.current_h + index - 2) % 12 + 1, 0, 0, 0, 0)

    def time_seq_pr(self, index):
        tm = self.time_seq(index)

        return "{:2d}:{:02d}:{:02d}".format(tm[3], tm[4], tm[5])

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
        return (0, 0, 0, self.current_h, self.current_m, self.current_s, 0, 0)
        
    @hands_tm.setter
    def hands_tm(self, value):
        if self.current_h != value[3]:
            if value[3] == 0:
                self.current_h = 12
            else:
                self.current_h = value[3]
            self.redraw = True
                
        if self.current_m != value[4]:
            self.current_m = value[4]
            self.redraw = True

        if self.current_s != value[5]:
            self.current_s = value[5]
            self.updated = True

    def update_screen(self):
        """ Update the screen at any time, but don't repeatedly update the screen if nothing's changed.
        """
        if self.redraw:
            self._doredraw()
        else:
            self._doupdate()

        self.redraw      = False

    ###############################################################################
    ###############################################################################
    # Draw screen function use the following row -> pixel conversion for text     #
    #                                                                             #
    # Row 0 - Top    : 8                                                          #
    # Row 1          : 38                                                         #
    # Row 2          : 60                                                         #
    # Row 3          : 82                                                         #
    # Row 4          : 104                                                        #
    # Row 5 - Bottom : 126                                                        #
    #                                                                             #
    ###############################################################################
    ###############################################################################


    def drawscreen_normal(self):
        # Title the display
        self.text_alignYX("DG Clock", 8)
        
        # Show the current network config
        if not self.sta.active():
            self.text_alignYX("WiFi not active",                     38, color = 0x0088ff)   # Amber
        elif not self.sta.isconnected():
            self.text_alignYX(" WiFi not connected ",                38, color = 0x00ffff)   # Red
        else:
            self.text_alignYX(" {} ".format(self.sta.ifconfig()[0]), 38, color = 0xff00ff)   # Green
        
        # Tell the user whether the NTP sync is good or not
        if self.ntp_sync:
            self.text_alignYX("NTP Sync OK",                         60, color = 0xff00ff)   # Green
        else:
            self.text_alignYX("No NTP Sync",                          60, color = 0x0088ff)   # Amber

        now_str  = " {:02.0f}:{:02.0f}:{:02.0f} ".format(self.now_tm[3], self.now_tm[4], self.now_tm[5])
        hand_str = " {:.0f}:{:02.0f}:{:02.0f} ".format(self.current_h, self.current_m, self.current_s)

        self.text_alignYX("Time:",                  82,  90, 'Right')
        self.text_alignYX(now_str,                  82, 180, 'Centre')
        self.text_alignYX(" "+self.clock_mode+":", 104,  90, 'Right')
        self.text_alignYX(hand_str,                104, 180, 'Centre')

        self.text_alignYX(self.mode, 126, align = 'Right', color = 0x0088ff)   # UI mode
        self.text_alignYX("<INFO",   126, align = 'Left',  color = 0xff8800)   # Button label

    def drawscreen_info(self):
        self.text_alignYX(self.mode, 126, align = 'Right', color = 0x0088ff)
        self.text_alignYX("<Back",     8, align = 'Left',  color = 0xff8800)
        self.text_alignYX("<STOP",   126, align = 'Left',  color = 0xff8800)

    def drawscreen_stop(self):
        self.text_alignYX(self.mode,  126, align = 'Right', color = 0x0088ff)
        self.text_alignYX("<Adjust",    8, align = 'Left',  color = 0xff8800)
        self.text_alignYX("<Back",    126, align = 'Left',  color = 0xff8800)

    def drawscreen_adjust(self):

        middle_colour = 0x000000 # White

        if self.setmode == 0:
            middle_colour = 0xff00ff # Make the supposedly correct hand position green
            self.text_alignYX("Leave hands as-is", 38,                  color = 0xff00ff)
            self.text_alignYX("<Abort  ",           8, align = 'Left',  color = 0xff00ff)
        else:
            self.text_alignYX("Set hands to...",   38,                  color = 0x00ffff)
            self.text_alignYX("<Restart",           8, align = 'Left',  color = 0x00ffff)

        self.text_alignYX(self.mode,  126, align = 'Right', color = 0x0088ff)
        self.text_alignYX("<Change",  126, align = 'Left',  color = 0xff8800)

        self.text_alignYX("    {}    ".format(self.time_seq_pr(self.setmode - 1)),  60, color = 0x7f7f7f)
        self.text_alignYX("--> {} <--".format(self.time_seq_pr(self.setmode    )),  82, color = middle_colour)
        self.text_alignYX("    {}    ".format(self.time_seq_pr(self.setmode + 1)), 104, color = 0x7f7f7f)




if __name__ == "dggui":
    dgdev()