import machine import Pin
import time, utime

# Next thing - get the motor driver working to step the hands
motor_en = machine.Pin(36, Pin.OUT)
motor_A  = machine.Pin(37, Pin.OUT)
motor_B  = machine.Pin(38, Pin.OUT)

motor_en.off()
motor_A.off()
motor_B.off()

import utime

# Let's start off with 200ms pulses once per second
pulse_duration = 200
pulse_rate     = 1000

while True:
    # Pulse polarity positive
    print("Positive pulse")
    motor_A.on()
    motor_en.on()
    utime.sleep_ms(pulse_duration)
    motor_en.off() # Keep the driver disabled as much as possible to save power/heat
    motor_A.off()

    # Wait
    print("Pause")
    utime.sleep_ms(pulse_rate - pulse_duration)

    # Pulse polarity negative
    print("Negative pulse")
    motor_B.on()
    motor_en.on()
    utime.sleep_ms(pulse_duration)
    motor_en.off() # Keep the driver disabled as much as possible to save power/heat
    motor_B.off()

    # Wait
    print("Pause again")
    utime.sleep_ms(pulse_rate - pulse_duration)