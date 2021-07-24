from pymodbus.client.sync import ModbusSerialClient
from time import sleep
"""
import serial
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.OUT)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
"""

walli = ModbusSerialClient(method="rtu",
                           port='/dev/ttyUSB0',
                           baudrate=19200,
                           stopbits=1,
                           bytesize=8,
                           parity="E",
                           timeout=10)

print(walli)
walli.connect()

print(walli)

while True:
    try:
        r = walli.read_input_registers(4, count=15, unit=1)
        if r.isError():
            print("Error")
            print(r)
        else:
            print(r.registers)

        r = walli.read_holding_registers(261, count=2, unit=1)
        if r.isError():
            print("Error")
        else:
            print(r.registers)    

    except KeyboardInterrupt as e:
        print(e)
        break
    sleep(2)

walli.close()

