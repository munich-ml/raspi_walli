# Modbus
Within this project, a Raspberry Pi will be connected to a **Heidelbert Wallbox Energy Control** via **Modbus RTU**. Here is how the wallbox looks like: 
![Heidelbert Wallbox Energy Control image](imgs/Heidelberg-Wallbox-Energy-Control.jpg)

Thus, this folder is dedicated to the **Modbus RTU**. **RTU** stands for *Remote Terminal Unit* and is serial communication over RS485 (or even RS232) in contrast to **Modbus TCP** over Ethernet.

## General Modbus info resources
- [Modbus 101 - Introduction to Modbus](https://www.csimn.com/CSI_pages/Modbus101.html)
- [Youtube video](https://www.youtube.com/watch?v=yRpWjjRNE-c) showing Modbus RTU communication from a Raspberry Pi Koyo DL06 PLC

## ``PyModbus`` simple rtu server and client
[PyModbus](https://pymodbus.readthedocs.io/) is a Python package that implements the Modbus protocol stack. A simple Modbus server and client have been implemented:
- [simple_modbus_rtu_server.ipynb](simple_modbus_rtu_server.ipynb)
- [simple_modbus_rtu_client.ipynb](simple_modbus_rtu_client.ipynb)

The server and client have successfully been tested with [com0com Null Modem Emulator](http://com0com.sourceforge.net/) as well as with two USB-RS485 sticks and a loop cable. 

## Wallbox doesn't respond
Although the [simple_modbus_rtu_client](simple_modbus_rtu_client.ipynb) works well with its [simple_modbus_rtu_server](simple_modbus_rtu_server.ipynb), there is no response, yet, wallbox:
![](imgs\Walli_not_responding_2021-17-11.png)