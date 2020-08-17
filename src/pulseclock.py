from utime import sleep_ms
from machine import Pin

class PulseClock:
    def __init__(self, drive_plus, drive_minus, drive_enable, pulse_time, dwell_time, invert):
        """ Initialise the pulse clock

        Args:
            drive_plus   (Pin):     The pin used to drive the motor "+ve" terminal
            drive_minus  (Pin):     The pin used to drive the motor "-ve" terminal
            drive_enable (Pin):     The pin used to enable the motor driver
            pulse_time   (number):  The duration of the pulse to step in milliseconds
            dwell_time   (number):  The duration of the dwell time after a step in milliseconds.
            invert       (boolean): Should the next pulse by inverted (True/False). 
            
        Notes:
            The next pulse should be inverted if the second hand is currently pointing to an odd number of seconds.
        """        
        self.pin_plus   = drive_plus
        self.pin_minus  = drive_minus
        self.pin_enable = drive_enable
        self.pulse_time = pulse_time
        self.dwell_time = dwell_time
        self.invert     = invert
        self.step() # Ensure the mechanism is fully aligned not in some midway state

    def __repr__(self):
        """Returns representation of the object
        """
        return "{}({!r})".format(self.__class__.__name__, self.pin_plus, self.pin_minus, self.pin_enable, self.pulse_time, self.dwell_time, self.invert)

    def _dostep(self, ld, tr, en):
        """ Step the clock forward one second

        Args:
            ld (pin): Leading pin
            tr (pin): Trailing pin
            en (pin): Enable pin
        """        """ 
        """   
        en.value(0)                    # Ensure the motor is disabled
        ld.value(1)                    # Set up the pulse
        tr.value(0)

        #print("Lead/Trail {}/{}".format(ld, tr))

        # Do a double pulse just in case the mechanism sticks
        en.value(1)                    # Enable the motor for half the "pulse" duration
        sleep_ms(self.pulse_time // 2)
        en.value(0)                    # Disable the motor for a short time
        sleep_ms(self.dwell_time)
        en.value(1)                    # Re-enable the motor for the second half of the "pulse" duration
        sleep_ms(self.pulse_time // 2)
        tr.value(1)                    # Actively stop the motor
        en.value(0)                    # Disable the driver ready for the next pulse
        
    def step(self):
        """ Step the clock forward by one second
        """
        if self.invert:
            self._dostep(self.pin_minus, self.pin_plus, self.pin_enable)
        else:
            self._dostep(self.pin_plus, self.pin_minus, self.pin_enable)
        
        self.invert = not self.invert  # Flip the internal state here as there is this reduces any race condition
