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

        # Initialise the position sensor and error counters
        self.polarity   = 1
        self.edgecount  = 0
        self.maxcount   = 0
        self.mincount   = 100
        self.countzero  = 0
        self.whitephase = 0
        self.whitecount = 0

        self.record     = ""
        
        self.step()         # Ensure the mechanism is fully aligned not in some midway state
        
    def __repr__(self):
        """Returns representation of the object
        """
        return "{}({!r})".format(self.__class__.__name__, self.pin_plus, self.pin_minus, self.pin_enable, self.config, self.sensor)

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

        if state == 1:
            self.record += "W"

        if count < 10:
            self.record += str(count)
        else:
            self.record += " "+str(count)+" "

        if count > self.maxcount:
            self.maxcount = count

        if count < self.mincount:
            self.mincount = count

        # Update where the second hand SHOULD be - if it didn't move, don't update at all
        if 0 == count: # No edges detected - clock jammed! Try kicking it the other way in future...
            print("No pulses!")
            self.countzero += 1
            if self.countzero % 4 == 0: # Got four zeros in a row - flipping the polarity just in case that helps
                self.polarity = 1-self.polarity
                print("Inverting polarity - now {}".format(self.polarity))
        else:
            self.countzero = 0 # Got some motion - reset the zero counter

        # 1-8 edges is probably a single step
        if 0 < count and count <= 8: 
            self.sec_pos += 1
        
        # Far too many edges - assume the clock skipped forward by multiple seconds - try to guess how many...
        if 8 < count: 
            self.sec_pos += count // 4
            print("Got {} pulses - sec hand position adjusted by +{}".format(count, (count // 4)-1))

        # Make sure that the seconds counter remains in the range 0-59
        self.sec_pos %= 60
        
        if state == 1 and self.sec_pos % 4 != 0: # White when it shouldn't be!
            print("counted {} pulses - hand at {:02d} - sensor White".format(count, self.sec_pos))
        
        if state == 0 and self.sec_pos % 4 == 0: # Black when it shouldn't be!
            print("counted {} pulses - hand at {:02d} - sensor black".format(count, self.sec_pos))

        if self.sec_pos == 59:
            print("Min/max pulses {}/{}: {}".format(self.mincount, self.maxcount, self.record))
            self.mincount = 100
            self.maxcount = 0
            self.record   = ""

        # TODO - Add code to check for early/missed white sectors
        if state == 1:                                     # Detecting white
            if self.sec_pos % 4 == self.whitephase:          # White is in the "expected" phase
                self.whitecount += 1
            else:
                self.whitephase = self.sec_pos % 4           # White appears to be consistently in the same position
                self.whitecount = 0
                print("Unexpected white #{} (phase {})".format(self.whitecount, self.whitephase))

            if self.whitecount > 15 and self.whitephase != 0: # OK, we've seen more than 15 whites when we shouldn't have done
                print("Adjusting second hand by {}".format(self.whitephase))
                self.sec_pos -= self.whitephase # Move the second hand position back to make the phase align
                self.whitephase = 0
                self.whitecount = 0

    def read_secondhand(self):
        """ Report where the second hand SHOULD be
        """
        return self.sec_pos

    def step(self):
        """ Step the clock forward by one second
        """
        if self.sec_pos % 2 == self.polarity: # Determine the polarity of the pulse based upon the nominal current clock position
            self._dostep(self.pin_minus, self.pin_plus, self.pin_enable)
            #print("Positive pulse - ", end='')
        else:
            self._dostep(self.pin_plus, self.pin_minus, self.pin_enable)
            #print("Negative pulse - ", end='')
        
        self._update()

    def faststep(self):
        """ Step the clock forward by one second
        """
        if self.sec_pos % 2 == self.polarity: # Determine the polarity of the pulse based upon the nominal current clock position
            self._dofaststep(self.pin_minus, self.pin_plus, self.pin_enable)
            #print("Positive fast pulse - ", end='')
        else:
            self._dofaststep(self.pin_plus, self.pin_minus, self.pin_enable)
            #print("Negative fast pulse - ", end='')
        
        self._update()
