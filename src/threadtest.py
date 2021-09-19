from machine import I2C, Pin, RTC
from utime import sleep_ms, time, mktime
import _thread

def thread_test():

    t1 = _thread.start_new_thread('LED1', led1_thread, ())
    t2 = _thread.start_new_thread('LED2', led2_thread, ())

def led1_thread():
    _thread.allowsuspend(True)
    led1 = Pin(26, Pin.OUT)

    while True:
        ntf = _thread.getnotification()
        if ntf == _thread.EXIT:
            return
        if ntf == _thread.SUSPEND:
            while _thread.wait() != _thread.RESUME:
                pass

        led1.value(1)
        sleep_needed = 5000
        while sleep_needed > 0:
            sleep_needed -= sleep_ms(sleep_needed, True)
        led1.value(0)
        sleep_needed = 200
        while sleep_needed > 0:
            sleep_needed -= sleep_ms(sleep_needed, True)

def led2_thread():
    _thread.allowsuspend(True)
    led1 = Pin(25, Pin.OUT)

    while True:
        ntf = _thread.getnotification()
        if ntf == _thread.EXIT:
            return
        if ntf == _thread.SUSPEND:
            while _thread.wait() != _thread.RESUME:
                pass

        led1.value(1)
        sleep_needed = 5000
        sleep_needed -= sleep_ms(sleep_needed, True)
        led1.value(0)
        sleep_needed = 200
        sleep_needed -= sleep_ms(sleep_needed, True)
