from machine import I2C, Pin
from utime import sleep_ms
import ds3231
import pulseclock

i2c = I2C(0, scl=22, sda=21)
ds = ds3231.DS3231(i2c)

# Read the NV stored hand position
hand_position = ds.alarm1_tm
invert = hand_position[5] % 2 == 1 # Is the second hand pointing to an even or odd number?

pc = pulseclock.PulseClock(Pin(26, Pin.OUT), Pin(25, Pin.OUT), Pin(27, Pin.OUT), 200, 200, invert)

while True:
    current_time = ds.rtc_tm
    hand_postion = ds.alarm1_tm

    # Convert both to seconds since midnight
    current = (current_time[3]  * 3600 + current_time[4]  * 60 + current_time[5]) % 43200 # Convert to 12-hour format
    display = hand_position[3] * 3600 + hand_position[4] * 60 + hand_position[5]  % 43200

    diff    = current - display # How far apart are the hands - allowing for wrap-around

    if diff > 0 or diff < -3600: # If the difference is around minus one hour, it's quicker just to stop the clock
        # Update the stored hand position and step the clock
        new_display = (display + 1) % 43200
        new_hand_position = (0, 0, 0, (new_display / 3600), (new_display / 60) % 60, new_display % 60, 0, 0) 

        # Update the stored hand position
        ds.alarm1_tm = new_hand_position

        # Move the clock - note that there is a potential race condition here
        pc.step()
    else:
        sleep_ms(100)

    print("RTC:{} Old:{} New:{}".format(current,display,new_display))
