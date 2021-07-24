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
                           port='COM9',
                           port='/dev/ttyUSB0',
                           #baudrate=19200,
                           stopbits=1,
                           bytesize=8,
                           parity="E",
                           timeout=10)

walli.connect()
print("after connect:", walli)

r = walli.read_input_registers(4, count=15, unit=1)
print("initial read:", r.registers)

sleep(0.1)

walli.write_register(261, 120, unit=1)
walli.write_register(262, 120, unit=1)

sleep(0.1)

r = walli.read_input_registers(4, count=15, unit=1)
print("final read:", r.registers)

walli.close()

