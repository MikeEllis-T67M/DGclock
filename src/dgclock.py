from utime import sleep_ms

import pulseclock
import settings

class DGClock:
    def __init__(self, config_filename, hands):
        """ Constructor

        Args:
            config_filename (string): Name of the file to read
            hands           (int)   : The current hand position as seconds from 12:00:00
        """        
        # Read the config file describing the pulse clock setup
        clock_settings = settings.load_settings(config_filename)

        # Initialise the actual pulse clock
        self.pc = pulseclock.PulseClock(clock_settings, hands % 2 == 0)

        # Keep a copy of where the hands are pointing
        #print("Initialising hands to {}".format(hands))
        self.hands = hands
        self.mode  = "Wait"

    def __repr__(self):
        pass

    def adjust(self, new_hands):
        self.hands = new_hands

    @property
    def hands(self):
        return self._hands

    @property
    def hands_tm(self):
        value = (0,0,0, (self._hands // 3600) % 24, (self._hands // 60) % 60, self._hands % 60, 0, 0) # TM structure YMDHMS00
        return value

    @hands.setter
    def hands(self, value):
        self._hands    = int(value % 43200)       # Must be an integer in the range 00:00:00 to 11:59:59
        self.pc.invert = self._hands % 2 == 0     # Make sure the pulse phase is correct
        
    @hands_tm.setter
    def hands_tm(self, value):
        self.hands = value[3] * 3600 + value[4] * 60 + value[5]

    def move(self, wanted_time):
        wanted_time %= 43200 # Only care about the 12-hour portion of the time

        diff = (wanted_time - self._hands) % 43200

        #print("Want:{} Show:{} Diff:{}".format(wanted_time, self._hands, diff))

        if diff == 0:                                 # Hands are correct
            self.mode = "Run"
        elif diff == 1:                               # Just need a single step
            self.mode   = "Run"
            self.hands += 1
            self.pc.step()
        elif diff > 36000 and self._hands % 60 == 0:  # >10hr difference and second hand on 12
            self.mode = "Wait"
        else:                                         # Need to move fast to catch up
            self.mode   = "Fast"
            self.hands += 1
            self.pc.faststep()
