from machine import I2C 
print("Initialising...")
i2c = I2C(0, scl=22, sda=21)
ds = ds3231.DS3231(i2c)
print(i2c)
print(ds)