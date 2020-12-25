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
        self.speed      = "S"
        
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
        en.value(1)                    # Ensure the motor is enabled
        ld.value(1)                    # Set up the pulse
        tr.value(0)
        sleep_ms(self.config["Pulse"])
        tr.value(1)
        sleep_ms(self.config["Stop"])
    
        #for _ in range(self.config["PulseCount"]):
        #    tr.value(0)
        #    en.value(1)                    # Kick the motor
        #    sleep_ms(self.config["Pulse"])
        #    tr.value(1)                    # Stop 
        #    sleep_ms(self.config["Dwell"])
        # 
        #sleep_ms(self.config["Stop"])
        #en.value(0)                    # Disable the driver ready for the next pulse
        #sleep_ms(self.config["Recover"])
        
    def _dofaststep(self, ld, tr, en):
        """ Step the clock forward one second

        Args:
            ld (pin): Leading pin
            tr (pin): Trailing pin
            en (pin): Enable pin
        """        """ 
        """   
        en.value(1)                    # Ensure the motor is enabled
        ld.value(1)                    # Set up the pulse
        tr.value(0)
        sleep_ms(self.config["FastPulse1"])
        tr.value(1)
        sleep_ms(self.config["FastStop"])

        #en.value(1)                          # Ensure the motor is always enabled
        #ld.value(1)                          # Set up the pulse
        #tr.value(0)

        #en.value(1)                               # Kick the motor
        #sleep_ms(self.config["FastPulse1"])        # Full pulse to start with
        #tr.value(1)                               # Actively stop the motor
        #sleep_ms(self.config["FastDwell"])
        #tr.value(0)                               # Second pulse half size
        #sleep_ms(self.config["FastPulse2"])
        #tr.value(1)                               # Second stop
        #sleep_ms(self.config["FastStop"])

    def _update(self):
        """ Update the internal hand position reporting - should ONLY be called when stepping the clock
        """
        (count, self.edgecount, state) = (self.edgecount, 0, self.sensor.value()) # Copy the count and then reset it - semi-atomic!

        # Debug: construct a record and print it once per minute
        if state == 1: # Recording seeing white
            self.record += "-" # Use a dash for whites since it is easier to scan in the resulting log

        if count < 10: # Record the number of pulses we got to get to this state
            self.record += str(count)
        else:
            self.record += " "+str(count)+" "

        if count > self.maxcount:
            self.maxcount = count

        if count < self.mincount:
            self.mincount = count

        # Update where the second hand SHOULD be - if it didn't move, don't update at all
        if 0 == count: # No edges detected - clock jammed! Try kicking it the other way in future...
            #print("No pulses!")
            self.countzero += 1
            if self.countzero % 4 == 0: # Got four zeros in a row - flipping the polarity just in case that helps
                self.polarity = 1-self.polarity
                print("Inverting polarity - now {}".format(self.polarity))
        else:
            self.countzero = 0 # Got some motion - reset the zero counter

        # 0-9 edges is probably a single step
        if 0 <= count and count <= 9: 
            self.sec_pos += 1
        
        # More than 9 edges - assume the clock skipped forward by multiple seconds - try to guess how many...
        if 9 < count: 
            self.sec_pos += count // 5
            print("Got {} pulses - sec hand position adjusted by +{}".format(count, count // 5))

        # Make sure that the seconds counter remains in the range 0-59
        self.sec_pos %= 60
        
        # TODO - Add code to check for early/missed white sectors
        if state == 1:                                     # Detecting white
            if self.sec_pos % 4 == self.whitephase:          # White is in the "expected" phase
                self.whitecount += 1
                if self.whitephase != 0:
                    print("Offset white     #{} (second {} phase {})".format(self.whitecount, self.sec_pos, self.whitephase))
            else:
                self.whitephase = self.sec_pos % 4           # White appears to be consistently in the same position
                self.whitecount = 0
                if self.whitephase != 0:
                    print("Unexpected white #{} (second {} phase {})".format(self.whitecount, self.sec_pos, self.whitephase))
                else:
                    print("White phase restored (second {})".format(self.sec_pos))

            if self.whitecount > 4 and self.whitephase != 0: # OK, we've seen more than 15 whites when we shouldn't have done
                print("Adjusting second hand by {} - from {} to {}".format(self.whitephase,self.sec_pos,self.sec_pos - self.whitephase))
                self.sec_pos -= self.whitephase # Move the second hand position back to make the phase align
                if self.whitephase % 2 == 1: # If it's an odd-even change then we also need to flip the polarity...
                    self.polarity = 1-self.polarity
                self.whitephase = 0
                self.whitecount = 0

        if self.sec_pos == 59: # Print the debugging at the top of each minute
            print("Min/max pulses {}/{}: {}".format(self.mincount, self.maxcount, self.record))
            self.mincount = 100
            self.maxcount = 0
            self.record   = ""

    def read_secondhand(self):
        """ Report where the second hand SHOULD be
        """
        return self.sec_pos

    def step(self):
        """ Step the clock forward by one second
        """
        if self.speed == "F":
            self.speed   = "S"
            self.record += self.speed

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
        if self.speed == "S":
            self.speed   = "F"
            self.record += self.speed

        if self.sec_pos % 2 == self.polarity: # Determine the polarity of the pulse based upon the nominal current clock position
            self._dofaststep(self.pin_minus, self.pin_plus, self.pin_enable)
            #print("Positive fast pulse - ", end='')
        else:
            self._dofaststep(self.pin_plus, self.pin_minus, self.pin_enable)
            #print("Negative fast pulse - ", end='')
        
        self._update()
