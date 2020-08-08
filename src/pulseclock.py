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
            dwell_time   (number):  The duration of the dwell time after a step in milliseconds
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

    def __repr__(self):
        """Returns representation of the object
        """
        return "{}({!r})".format(self.__class__.__name__, self.pin_plus, self.pin_minus, self.pin_enable, self.pulse_time, self.dwell_time, self.invert)

    def _step_even(self):
        """ Step the clock forward one even second (0-1, 2-3, 4-5 etc)
        """   
        #print("Even")     
        self.pin_enable.value(0)        # Ensure the motor is disabled

        self.pin_plus.value(1)          # Set up an "even" pulse
        self.pin_minus.value(0)

        self.pin_enable.value(1)        # Enable the motor for the "pulse" duration
        self.invert = True              # Flip the internal state here as there is this reduces any race condition
        sleep_ms(self.pulse_time)

        self.pin_minus.value(1)         # Actively stop (short out) the motor for the "dwell" duration
        sleep_ms(self.dwell_time)

        self.pin_enable.value(0)        # Disable the driver ready for the next pulse


    def _step_odd(self):
        """ Step the clock forward one off second (1-2, 3-4, 5-6 etc)
        """
        #print("Odd")
        self.pin_enable.value(0)        # Ensure the motor is disabled

        self.pin_plus.value(0)          # Set up an "even" pulse
        self.pin_minus.value(1)

        self.pin_enable.value(1)        # Enable the motor for the "pulse" duration
        self.invert = False             # Flip the internal state here as there is this reduces any race condition
        sleep_ms(self.pulse_time)

        self.pin_plus.value(1)         # Actively stop (short out) the motor for the "dwell" duration
        sleep_ms(self.dwell_time)
        self.pin_enable.value(0)        # Disable the driver ready for the next pulse    

    def step(self):
        """ Step the clock forward by one second
        """
        if self.invert:
            self._step_odd()
        else:
            self._step_even()
