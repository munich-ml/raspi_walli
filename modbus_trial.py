from pymodbus.client.sync import ModbusSerialClient

walli = ModbusSerialClient(method="rtu",
                           port="/dev/ttyAMA0",
                           baudrate=19200,
                           stopbits=1,
                           bytesize=8,
                           parity="E")

walli.connect()

r = walli.read_input_registers()

print(r)
