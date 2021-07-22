import RPi.GPIO as GPIO
import time
import serial
GPIO.setmode(GPIO.BOARD)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
ser=serial.Serial("/dev/ttyS0",9600)
 
while True:
    ser.write(b"a")
    print("write 1")
    time.sleep(2)
    print("read 1")
    #print("read start")
    received_data=ser.read()
    #print("read end")
    print("read 1\n")
    print(received_data)