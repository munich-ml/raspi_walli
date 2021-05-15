#!/usr/bin/python
from smbus import SMBus


bus = SMBus(1)  # Rev 2 Pi uses 1


def get_lux():
    """
    Read data from a BH1750 digital light sensor.
    Returns light level in Lux
    """ 
    I2C_BH1750 = 0x23
    ONE_TIME_HIGH_RES_MODE_1 = 0x20  
    
    data = bus.read_i2c_block_data(I2C_BH1750, ONE_TIME_HIGH_RES_MODE_1)
    return (data[1] + (256 * data[0])) / 1.2

