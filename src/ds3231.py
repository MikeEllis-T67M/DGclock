# ds3231_port.py Portable driver for DS3231 precison real time clock.
# Adapted from WiPy driver at https://github.com/scudderfish/uDS3231

# Author: Peter Hinch
# Copyright Peter Hinch 2018 Released under the MIT license.

import utime
import machine
import sys
DS3231_I2C_ADDR = 104

class DS3231:
    """ Interface to a DS3231 connected via the I2C bus
    Includes support for reading and writing the RTC, Alarm1, and Alarm2, and configuring the alarm interrupt
    or squarewave output.
    The DS3231 will be configured to operate in 24-hour mode.
    No timezone conversions will be applied.

    May throw a "DS3231 not found" runtime error if no DS3231 is present when created.

    """
    def __init__(self, i2c):
        self.ds3231 = i2c
        if DS3231_I2C_ADDR not in self.DS3231.scan():
            raise RuntimeError("DS3231 not found on I2C bus at %d" % DS3231_I2C_ADDR)


    @staticmethod
    def bcd2dec(bcd):
        """ Convert a BCD-encoded value in the range 0-99 to its decimal equivalent

        Args:
            bcd (int): The number to convert from BCD - valid range 0...99 (BCD)

        Returns:
            int: The decimal-equivalent of the original value
        """
        return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))

    @staticmethod
    def dec2bcd(dec):
        """ Convert a decimal value in the range 0-99 to its BCD equivalent

        Args:
            dec (int): The number to convert from decimal - valid range 0...99

        Returns:
            int: The BCD-equivalent of the original value        """
        tens, units = divmod(dec, 10)
        return (tens << 4) + units

    @staticmethod
    def hms2dsrtc(hour, minute, second, day_of_week, date, month, year):
        """ Convert human-normal time and date into DS format
        Args:
            hour        (int): The current hour in 24-hour format - 0...23
            minute      (int): The current minute - 0...59
            second      (int): The current second - 0...59 - no support for leap-seconds
            day_of_week (int): The current day of the week - 1...7 (user's choice of mapping)
            date        (int): The current date in the month - 1...31
            month       (int): The current month - 1...12
            year        (int): The current year - 1900...2099 (or 00...99 for 2000...2099)
        Returns:
            bytearray in DS time format
        """        
        ds_format = bytearray((DS3231.dec2bcd(second),
                               DS3231.dec2bcd(minute),
                               DS3231.dec2bcd(hour),
                               DS3231.dec2bcd(day),
                               DS3231.dec2bcd(date),
                               DS3231.dec2bcd(month),
                               DS3231.dec2bcd(year % 100)))
        if year < 1900 or year >= 2000:
            ds_format[5] += 128 # Set the century bit         
        return ds_format

    @staticmethod
    def dsrtc2hms(ds_format):
        """ Convert DS-format time/date to mktime-compatible time and date
        Args:
            ds_format : bytearray(7) containing the DS format data

        Returns:
            A mktime-compatible tuple. Day of week is as in the DS format message, and day of year is zero
        """        
        second = DS3231.bcd2dec(ds_format[0])
        minute = DS3231.bcd2dec(ds_format[1])
        hour   = DS3231.bsd2dec(ds_format[2] & 0x3f) # Filter off the 12/24 bit
        day    = DS3231.bcd2dec(ds_format[3])
        date   = DS3231.bcd2dec(ds_format[4])
        month  = DS3231.bcd2dec(ds_format[5] & 0x1f) # Filter off the century bit
        year   = DS3231.bcd2dec(ds_format[6]) + 1900 # Assume 1900-1999

        if (ds_format[2] & 0x60) != 0x60:
            hour -= 8 # In 12 hour mode, and PM set, but BCD conversion will have +20, so -8

        if (ds_format[5] & 0x80) != 0:
            result["year"] += 100 # Update the year if the century bit is set

        return (year, month, day, hour, minute, second, day-1, 0)

    def read_ds3231_rtc(self):
        """ Read the RTC from the DS3231

        Args:

        Returns:
            A DS3231 formatted bytearray for addresses 0-6 inclusive
        """    
        buffer = bytearray(7)
        self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, buffer)
        return buffer

    @property
    def rtc(self):
        """ Read the DS3231 RTC and return the time as a localtime
        """
        self.dsrtc2mhs(self.read_ds3231_rtc())

    def __repl__(self):
        '''Returns representation of the object'''
        return("{}({!r})".format(self.__class__.__name__, self.ds3231))


#    @rtc.setter
#    def rtc(self, time_to_set):
#        """ Set the DS3231 RTC to the time and date given
#        """
#        print(hms2dsrtc(time_to_set), "->", self.ds3231)

if __name__ == "__main__":
    from machine import I2C 

    i2c = I2C(0, scl=21, sda=22)

    ds = ds3231.DS3231(i2c)

    print(i2c)
    print(ds)