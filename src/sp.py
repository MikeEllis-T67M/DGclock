DS3231_I2C_ADDR = 104

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
    ds_format = bytearray((dec2bcd(second),
                           dec2bcd(minute),
                           dec2bcd(hour),
                           dec2bcd(day),
                           dec2bcd(date),
                           dec2bcd(month),
                           dec2bcd(year % 100)))
    if year < 1900 or year >= 2000:
        ds_format[5] += 128 # Set the century bit         
    return ds_format

def read_ds3231_rtc(i2c):
    """ Read the RTC from the DS3231

    Args:
        i2c: The I2C bus to which the DS3231 is connected

    Returns:
        A DS3231 formatted bytearray for addresses 0-6 inclusive
    """    
    buffer = bytearray(7)
    readfrom_mem_into(DS3231_I2C_ADDR, 0, buffer)
    return buffer
