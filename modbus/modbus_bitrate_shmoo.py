
import numpy as np
from time import sleep
from pymodbus.client.sync import ModbusSerialClient

for baudrate in np.linspace(start=18000, stop=20000, num=50):
    client = ModbusSerialClient(method="rtu", port="COM6", baudrate=baudrate, 
                                timeout=4, stopbits=1, bytesize=8, parity="E")
    
    print()
    print("connecting at {}bps, ... success={}".format(baudrate, client.connect()))
    print(client)
    
    for adr in (0, 5):
        sleep(0.5)
        r = client.read_input_registers(adr, count=1)
        print("adr={} --> {}".format(adr, r))

    sleep(0.1)
    client.close()
    sleep(0.1)