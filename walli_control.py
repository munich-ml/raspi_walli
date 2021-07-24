from pymodbus.client.sync import ModbusSerialClient
import datetime as dt
from time import sleep
import json, os
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

        funcs = [lambda: self.mb.read_input_registers(4, count=15, unit=BUS_ID),
                 lambda: self.mb.read_input_registers(100, count=2, unit=BUS_ID),
                 lambda: self.mb.read_holding_registers(257, count=3, unit=BUS_ID),
                 lambda: self.mb.read_holding_registers(261, count=2, unit=BUS_ID),
                ]
        for func in funcs:
            while True:
                r = func()
                if r.isError():
                    read_attempts += 1
                    if self.verbose:
                        print("Modbus read error, attempt", read_attempts)
                    if read_attempts > MAX_READ_ATTEMPTS:
                        raise ModbusReadError
                else:
                    regs.extend(r.registers)
                    break
        
        if self.verbose:
            print(regs)

        return regs

    def enable_standby(self, enabled=True):
        value = {True: 0, False: 4}[enabled]
        self.mb.write_register(258, value, unit=BUS_ID)

    @staticmethod
    def safe_regs_to_csv(regs):
        fn = os.path.join(os.getcwd(), "logs", dt.datetime.now().strftime("%Y-%m-%d") + "csv")
        
        if not os.path.isfile(fn):  # create a new csv file incl. header
            header = "Version,charge_state,I_L1,I_L2,I_L3,Temp,V_L1,V_L2,V_L3,ext_lock,"
            header+= "P,E_cyc_hb,E_cyc_lb,E_hb,E_lb,I_max,I_min,watchdog,standby,"
            header+= "remote_lock,max_I_cmd,FailSafe_I\n"
            with open(fn, "w") as file:
                file.write(header)

        # make str line from list
        s = ""
        for element in regs:
            s += "{},".format(element)
        s = s[:-2] + "\n"

        with open(fn, "a") as file:
            file.write(s)


if __name__ == "__main__":
    
    w = Wallbox(port='/dev/ttyUSB0', verbose=True)

    w.read_registers()    # initial read
    w.enable_standby(False)
    w.read_registers()    # check read

    while True:
        with open("control.json", "r") as file:
            ctrl = json.load(file)    

        regs = w.read_registers()
        if ctrl["safe_as_csv"]:
            w.safe_regs_to_csv(regs)

        try:
            sleep(ctrl["polling_interval"])
        except KeyboardInterrupt as e:
            print(e)
            break

    w.close
