from I2C_devices import get_lux

from time import sleep

if __name__ == "__main__":
    while True:
        print("Light: {} lux".format(get_lux()))
        sleep(1)