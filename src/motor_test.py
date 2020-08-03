from machine import Pin
import time, utime

print("Starting")

# Next thing - get the motor driver working to step the hands
motor_en = Pin(25, Pin.OUT)
motor_A  = Pin(26, Pin.OUT)
motor_B  = Pin(27, Pin.OUT)

motor_en.off()
motor_A.off()
motor_B.off()

import utime

# Let's start off with 200ms pulses once per second
pulse_duration = 200
pulse_rate     = 1000

print("Using pins", motor_A, motor_B, motor_en)

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