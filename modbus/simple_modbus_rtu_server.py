#!/usr/bin/env python
# coding: utf-8


from pymodbus.server.sync import StartSerialServer
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext, ModbusSequentialDataBlock
from pymodbus.transaction import ModbusRtuFramer
import logging

FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)



slave_context = ModbusSlaveContext(
        di = ModbusSequentialDataBlock(0, [11, 12, 13, 14, 15]),
        co = ModbusSequentialDataBlock(0, [21, 22, 23, 24, 25]),
        hr = ModbusSequentialDataBlock(0, [31, 32, 33, 34, 35]),
        ir = ModbusSequentialDataBlock(0, [41, 42, 43, 44, 45]),
        )


server_context = ModbusServerContext(slaves=slave_context, single=True)



StartSerialServer(server_context, framer=ModbusRtuFramer, port='COM6', baudrate=19200, stopbits=1, bytesize=8, parity="E")






