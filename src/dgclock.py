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
        # Keep a copy of where the hands are pointing
        self._hands = hands % 43200 # Only care about the 12-hour portion, not the date and AM/PM

        # Read the config file describing the pulse clock setup
        clock_settings = settings.load_settings(config_filename)

        # Initialise the actual pulse clock
        self.pc   = pulseclock.PulseClock(clock_settings, hands % 2 == 0)
        self.mode = "Stopped"

    def __repr__(self):
        pass

    def _incr_hands(self):
        self._hands = (self._hands + 1) % 43200

    def adjust(self, new_hands):
        self._hands = new_hands

    @property
    def hands(self):
        return self._hands

    @property
    def hands_tm(self):
        return (0,0,0, (self._hands // 3600) % 24, (self._hands // 60) % 60, self._hands % 60, 0, 0) # TM structure YMDHMS00

    @hands.setter
    def hands(self, value):
        self._hands = value

    @hands_tm.setter
    def hands_tm(self, value):
        self._hands = value[3] * 3600 + value[4] * 60 + value[5]

    def move(self, wanted_time):
        wanted_time %= 43200 # Only care about the 12-hour portion of the time

        diff = self._hands - wanted_time

        if diff == 0:                          # Hands are correct
            self.mode = "Running"
        elif diff == 1:                        # Just need a single step
            self.mode = "Running"
            self._incr_hands()
            self.pc.step()
        elif diff < 3600 and hands % 60 == 0:  # <2hr difference and second hand on 12
            self.mode = "Stopped"
        else:                                  # Need to move fast to catch up
            self.mode = "Catch-up"
            self._incr_hands()
            self.pc.faststep()
