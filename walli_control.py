from pymodbus.client.sync import ModbusSerialClient
import datetime as dt
from time import sleep
import json
"""
import serial
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.OUT)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
"""

MAX_READ_ATTEMPTS = 8
BUS_ID = 1

class ModbusReadError(Exception):
    pass


class Wallbox():
    def __init__(self, port, verbose=False):
        self.verbose = verbose
        self.mb = ModbusSerialClient(method="rtu",
                                     port=port,
                                     baudrate=19200,
                                     stopbits=1,
                                     bytesize=8,
                                     parity="E",
                                     timeout=10)

        if not self.mb.connect():
            print("Error: Could not connect to the wallbox")
            raise ModbusReadError

    def close(self):
        self.mb.close()

    def read_registers(self):
        read_attempts = 0
        regs = [dt.datetime.now().strftime("%H:%M:%S")]

        funcs = {"mon":   lambda: self.mb.read_input_registers(4, count=15, unit=BUS_ID),
                 "HW":    lambda: self.mb.read_input_registers(100, count=2, unit=BUS_ID),
                 "WD":    lambda: self.mb.read_holding_registers(257, count=3, unit=BUS_ID),
                 "FS":    lambda: self.mb.read_holding_registers(261, count=2, unit=BUS_ID),
                 }
        for label, func in funcs.items():
            while True:
                r = func()
                if r.isError():
                    read_attempts += 1
                    if self.verbose:
                        print("Modbus read error, attempt", read_attempts)
                    if read_attempts > MAX_READ_ATTEMPTS:
                        raise ModbusReadError
                else:
                    regs.extend([label])
                    regs.extend(r.registers)
                    break
        
        if self.verbose:
            print(regs)

        return regs

    def enable_standby(self, enabled=True):
        value = {True: 0, False: 4}[enabled]
        self.mb.write_register(258, value, unit=BUS_ID)



w = Wallbox(port='/dev/ttyUSB0', verbose=True)

w.read_registers()    # initial read
w.enable_standby(False)
w.read_registers()    # check read

while True:
    with open("control.json", "r") as file:
        ctrl = json.load(file)    

    w.read_registers()

    try:
        sleep(ctrl["polling_interval"])
    except KeyboardInterrupt as e:
        print(e)
        break

w.close
