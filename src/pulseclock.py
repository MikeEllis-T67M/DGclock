from utime import sleep_ms
from machine import Pin

class PulseClock:
    def __init__(self, config, second_hand_position):
        """ Initialise the pulse clock

        Args:
            config (dict):              All the required configuration parameters - pin allocation etc
            second_hand_position (int): The current second hand position in the range 0-59
        """        
        self.config     = config
        self.pin_plus   = Pin(config['Plus'],   Pin.OUT)
        self.pin_minus  = Pin(config['Minus'],  Pin.OUT)
        self.pin_enable = Pin(config['Enable'], Pin.OUT)
        self.sensor     = Pin(config["Sense"],  Pin.IN,  handler = self._sensorinterrupt, trigger = Pin.IRQ_RISING | Pin.IRQ_FALLING)
        self.sec_pos    = second_hand_position % 60

        # Initialise the position sensor
        self.edgecount  = 0
        self.maxcount   = 0
        self.mincount   = 100
        #self.sense_edgecount = ((second_hand_position * 6) + (second_hand_position % 4)) // 4 # There are six edges for every four seconds
        
        self.step() # Ensure the mechanism is fully aligned not in some midway state

        self.maxcount   = 0 # Reset the min/max in case the first step wasn't a truly valid step
        self.mincount   = 100

    def __repr__(self):
        """Returns representation of the object
        """
        return "{}({!r})".format(self.__class__.__name__, self.pin_plus, self.pin_minus, self.pin_enable, 
                                self.config, self.sensor, self.sense_edgecount)

    def _sensorinterrupt(self, pin):
        """ Sensor interrupt routine
        Count the number of edges detected
        """        
        self.edgecount += 1
        
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

    def _update(self):
        """ Update the internal hand position reporting - should ONLY be called when stepping the clock
        """
        (state, count, self.edgecount) = (self.sensor.value(), self.edgecount, 0) # Copy the count and then reset it - semi-atomic!

        if count > self.maxcount:
            self.maxcount = count

        if count < self.mincount:
            self.mincount = count

        # Update where the second hand SHOULD be - if it didn't move, don't update at all
        if 0 == count: # No edges detected - clock jammed!
            pass
        elif 0 < count and count < 8: # 1-7 edges is probably a single step
            self.sec_pos += 1
        else: # Too many edges - assume the clock skipped forward by multiple seconds
            # Try to guess how many seconds were skipped, but err on the high side because the white sector will always round down
            self.sec_pos += count // 4 

        # Make sure that the seconds counter remains in the range 0-59
        self.sec_pos %= 60
        
        # Check that the currently being read value matches the expected state
        if state == 1: # White for positions 0, 4, 8, 12, ... only
            if self.sec_pos % 4 != 0:
                print("Hand mis-alignment detected - White at {} seconds - adjusted".format(self.sec_pos))
                self.sec_pos -= self.sec_pos % 4
        else:
            if self.sec_pos % 4 == 0:
                print("Hand mis-alignment detected - Black at {} seconds".format(self.sec_pos))

        #if state == 1:
        #    print("Counted {} pulses - hand at {:02d} - sensor White (min/max {}/{})".format(count, self.sec_pos, self.mincount, self.maxcount))
        #else:
        #    print("Counted {} pulses - hand at {:02d} - sensor black (min/max {}/{})".format(count, self.sec_pos, self.mincount, self.maxcount))

    def read_secondhand(self):
        """ Report where the second hand SHOULD be
        """
        return self.sec_pos

    def step(self):
        """ Step the clock forward by one second
        """
        if self.sec_pos % 2: # Determine the polarity of the pulse based upon the nominal current clock position
            self._dostep(self.pin_minus, self.pin_plus, self.pin_enable)
        else:
            self._dostep(self.pin_plus, self.pin_minus, self.pin_enable)
        
        self._update()

    def faststep(self):
        """ Step the clock forward by one second
        """
        if self.sec_pos % 2: # Determine the polarity of the pulse based upon the nominal current clock position
            self._dofaststep(self.pin_minus, self.pin_plus, self.pin_enable)
        else:
            self._dofaststep(self.pin_plus, self.pin_minus, self.pin_enable)
        
        self._update()
