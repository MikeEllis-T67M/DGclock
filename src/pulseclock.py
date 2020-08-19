from utime import sleep_ms
from machine import Pin

class PulseClock:
    def __init__(self, config, invert):
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
        self.config     = config
        self.invert     = invert
        self.pin_plus   = Pin(config['Plus'],   Pin.OUT)
        self.pin_minus  = Pin(config['Minus'],  Pin.OUT)
        self.pin_enable = Pin(config['Enable'], Pin.OUT)

        self.step() # Ensure the mechanism is fully aligned not in some midway state

    def __repr__(self):
        """Returns representation of the object
        """
        return "{}({!r})".format(self.__class__.__name__, self.pin_plus, self.pin_minus, self.pin_enable, 
                                self.pulse_time, self.pulse_count, self.dwell_time, self.stop_time, self.recover_time, self.invert)

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

        for _ in range(self.config["PulseCount"]):
            tr.value(0)
            en.value(1)                    # Kick the motor
            sleep_ms(self.config["Pulse"])
            tr.value(1)                    # Stop 
            sleep_ms(self.config["Dwell"])
        
        sleep_ms(self.config["Stop"])
        en.value(0)                    # Disable the driver ready for the next pulse
        sleep_ms(self.config["Recover"])
        
    def _dofaststep(self, ld, tr, en):
        """ Step the clock forward one second

        Args:
            ld (pin): Leading pin
            tr (pin): Trailing pin
            en (pin): Enable pin
        """        """ 
        """   
        en.value(0)                          # Ensure the motor is disabled
        ld.value(1)                          # Set up the pulse
        tr.value(0)

        en.value(1)                               # Kick the motor
        sleep_ms(self.config["FastPulse1"])        # Full pulse to start with
        tr.value(1)                               # Actively stop the motor
        sleep_ms(self.config["FastDwell"])
        tr.value(0)                               # Second pulse half size
        sleep_ms(self.config["FastPulse2"])
        tr.value(1)                               # Second stop
        sleep_ms(self.config["FastStop"])
        
    def step(self):
        """ Step the clock forward by one second
        """
        if self.invert:
            self._dostep(self.pin_minus, self.pin_plus, self.pin_enable)
        else:
            self._dostep(self.pin_plus, self.pin_minus, self.pin_enable)
        
        self.invert = not self.invert  # Flip the internal state here as there is this reduces any race condition

    def faststep(self):
        """ Step the clock forward by one second
        """
        if self.invert:
            self._dofaststep(self.pin_minus, self.pin_plus, self.pin_enable)
        else:
            self._dofaststep(self.pin_plus, self.pin_minus, self.pin_enable)
        
        self.invert = not self.invert  # Flip the internal state here as there is this reduces any race condition
