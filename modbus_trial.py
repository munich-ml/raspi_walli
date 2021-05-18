import serial
from pymodbus.client.sync import ModbusSerialClient
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.OUT)
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

walli = ModbusSerialClient(method="rtu",
                           port="/dev/ttyAMA0",
                           baudrate=19200,
                           stopbits=1,
                           bytesize=8,
                           parity="E")

walli.connect()

r = walli.read_input_registers(13, 1)

print(r)
