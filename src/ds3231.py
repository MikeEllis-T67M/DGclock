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
        if DS3231_I2C_ADDR not in self.ds3231.scan():
            raise RuntimeError("DS3231 not found on I2C bus at %d" % DS3231_I2C_ADDR)

    def __repr__(self):
        '''Returns representation of the object'''
        return("{}({!r})".format(self.__class__.__name__, self.ds3231))

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
    def tm2dsrtc(tm):
        """ Convert tm format tuple into DS3231 RTC register format
        Args:
            tm (tuple): The alarm time in TM format - can specify day of week or date, not both. Will default to date if both are set.
        Returns:
            bytearray in DS time format
        """        
        ds_format = bytearray((DS3231.dec2bcd(tm[5]),        # Seconds
                               DS3231.dec2bcd(tm[4]),        # Minutes
                               DS3231.dec2bcd(tm[3]),        # Hours
                               DS3231.dec2bcd(tm[6] + 1),    # Day of week - TM has days 0-6, DS has 1-7
                               DS3231.dec2bcd(tm[2]),        # Day of month
                               DS3231.dec2bcd(tm[1]),        # Month
                               DS3231.dec2bcd(tm[0] % 100))) # Only the year within the century
        if tm[0] < 1900 or tm[0] >= 2000:
            ds_format[5] += 128 # Set the century bit (embedded in the month)        
        return ds_format

    @staticmethod
    def dsrtc2tm(ds_format):
        """ Convert DS3231 register format into tm-format
        Args:
            ds_format : bytearray(7) containing the DS format data

        Returns:
            A mktime-compatible tuple. Day of week is as in the DS format message, and day of year is zero
        """        
        second = DS3231.bcd2dec(ds_format[0])
        minute = DS3231.bcd2dec(ds_format[1])
        hour   = DS3231.bcd2dec(ds_format[2] & 0x3f) # Filter off the 12/24 bit
        day    = DS3231.bcd2dec(ds_format[3])
        date   = DS3231.bcd2dec(ds_format[4])
        month  = DS3231.bcd2dec(ds_format[5] & 0x1f) # Filter off the century bit
        year   = DS3231.bcd2dec(ds_format[6]) + 1900 # Assume 1900-1999

        if (ds_format[2] & 0x60) == 0x60:
            hour -= 8 # In 12 hour mode, and PM set, but BCD conversion will have +20, so -8

        if (ds_format[5] & 0x80) != 0:
            year += 100 # Update the year if the century bit is set

        return (year, month, day, hour, minute, second, day-1, 0) # Build localtime format

    @staticmethod
    def tm2dsal1(tm):
        """ Convert tm format tuple into DS3231 RTC register format
        Args:
            tm (tuple): The alarm time in TM format - can specify day of week or date, not both. Will default to date if both are set.
        Returns:
            bytearray in DS alarm1 format
        """        
        if tm[2] == 0:
            # Day of week mode since date is outside the valid range (1-31)
            ds_format = bytearray((DS3231.dec2bcd(tm[5]),               # Seconds
                                   DS3231.dec2bcd(tm[4]),               # Minutes
                                   DS3231.dec2bcd(tm[3]),               # Hours
                                   DS3231.dec2bcd(tm[6] + 1) + 0x40))   # Day of week
        else:
            # Date mode since date is outside the valid range (1-31)
            ds_format = bytearray((DS3231.dec2bcd(tm[5]),               # Seconds
                                   DS3231.dec2bcd(tm[4]),               # Minutes
                                   DS3231.dec2bcd(tm[3]),               # Hours
                                   DS3231.dec2bcd(tm[2])))              # Date
        return ds_format

    @staticmethod
    def dsal12tm(ds_format):
        """ Convert DS3231 register format into tm-format
        Args:
            ds_format : bytearray(4) containing the DS format data

        Returns:
            A mktime-compatible tuple. Day of week is as in the DS format message, and day of year is zero
        """        
        second = DS3231.bcd2dec(ds_format[0] & 0x7f) # Filter off the alarm mask bit
        minute = DS3231.bcd2dec(ds_format[1] & 0x7f) # Filter off the alarm mask bit
        hour   = DS3231.bcd2dec(ds_format[2] & 0x3f) # Filter off the alarm mask and 12/24 bits

        if (ds_format[2] & 0x60) == 0x60:
            hour -= 8 # In 12 hour mode, and PM set, but BCD conversion will have +20, so -8

        if ds_format[3] & 0x40: 
            # Alarm in "day of week" mode
            day    = DS3231.bcd2dec(ds_format[3] & 0x0f) - 1 # DS range 1-7, TM range 0-6. Filter off the alarm mask bit.
            date   = 0                                       # TM valid range is 1-31
        else:
            day    = 0                                       # Strictly speaking not correct
            date   = DS3231.bcd2dec(ds_format[3] & 0x3f)     # Filter off the alarm mask and day/date mode bits

        month  = 0
        year   = 0

        return (year, month, day, hour, minute, second, day-1, 0) # Build localtime format

    def read_ds3231_rtc(self):
        """ Read the RTC from the DS3231

        Args:

        Returns:
            A DS3231 formatted bytearray for addresses 0-6 inclusive
        """    
        buffer = bytearray(7)
        self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, buffer)
        return buffer

    def read_ds3231_alarm1(self):
        """ Read the Alarm1 from the DS3231

        Args:

        Returns:
            A DS3231 formatted bytearray for addresses 7-10 inclusive, including all Alarm Mask bits but NOT the Alarm Interupt Enable bit
        """    
        buffer = bytearray(4)
        self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 7, buffer)
        return buffer

    @property
    def rtc_tm(self):
        """ Read the DS3231 RTC and return the time as a tm tuple
        """
        return DS3231.dsrtc2tm(self.read_ds3231_rtc())

    @property
    def rtc(self):
        """ Read the DS3231 RTC and return the time as seconds since epoch
        """
        return utime.mktime(self.rtc_tm)

    @rtc.setter
    def rtc(self, time_to_set):
        """ Set the DS3231 RTC

        Args:
            time_to_set (number): Seconds since epoch
        """
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 0, DS3231.tm2dsrtc(utime.localtime(time_to_set)))

    @property
    def alarm1_tm(self):
        """ Read the DS3231 RTC and return the time as a tm tuple

        Returns:
            tuple: Standard tm date tuple
            
        Note:
            AL1 only has Day/Date:HH:MM:SS fields. YY and MON will therefore always be zero.
            If the DS AL1 is in Date mode, then Date will be in the range 1-31 and Day will be 0.
            if the DS AL1 is in Day of Week mode, then Date will be 0 Day will be in the range 0-6.
        """
        return DS3231.dsal12tm(self.read_ds3231_alarm1())

    @alarm1_tm.setter
    def alarm1_tm(self, time_to_set):
        """ Set the DS3231 RTC to the tm tuple given

        Args:
            time_to_set (tuple): The standard tm tuple description of the desired alarm time. 
        
        Notes:
            AL1 only uses Day/Date:HH:MM:SS fields. 
            If Date=0 then Day mode is used, otherwise the date mode is used.
            The alarm interrupt will be set to "precise match" - i.e. Day/Date, HH:MM:SS must match exactly.
            The alarm interrupt enable will not be altered.        
        """
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 7, DS3231.tm2dsal1(time_to_set))
