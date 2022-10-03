import RPi.GPIO as GPIO
import time
import serial
GPIO.setmode(GPIO.BOARD)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("opening serial port ...")
with serial.Serial("/dev/ttyS0", 19200, timeout=1) as ser:
    print(ser)
     
    tx_data = b"Hello Raspi! How are you?" 
    print("writing '{}' ...".format(tx_data))
    ser.write(tx_data)

    time.sleep(1)


    print("receiving data ...")
    rx_data = ser.read(1000)
    print("received '{}'".format(rx_data))

    if rx_data == tx_data:
        print("rx_data == tx_data  all good!")
    else:
        print("rx_data != tx_data  ERROR!")    

    print("closing serial port ...")

