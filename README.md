# raspi_walli
Raspberry Pi controlling Heidelberger wallbox

# Heidelberger Wallbox control via ModBus RS485
Within this project, a Raspberry Pi will be connected to a **Heidelbert Wallbox Energy Control** via **Modbus RTU**. Here is how the wallbox looks like: 

![Heidelberg Wallbox Energy Control image](modbus/imgs/Heidelberg-Wallbox-Energy-Control.jpg)

This **modbus** folder is dedicated to the **Modbus RTU**. **RTU** stands for *Remote Terminal Unit* and is serial communication over RS485 (or even RS232) in contrast to **Modbus TCP** over Ethernet.

## General Modbus info resources
- [Modbus 101 - Introduction to Modbus](https://www.csimn.com/CSI_pages/Modbus101.html)
- [Youtube video](https://www.youtube.com/watch?v=yRpWjjRNE-c) showing Modbus RTU communication from a Raspberry Pi Koyo DL06 PLC

## PyModbus simple rtu server and client
[PyModbus](https://pymodbus.readthedocs.io/) is a Python package that implements the Modbus protocol stack. A simple Modbus server and client have been implemented:
- [simple_modbus_rtu_server.ipynb](simple_modbus_rtu_server.ipynb)
- [simple_modbus_rtu_client.ipynb](simple_modbus_rtu_client.ipynb)

The server and client have successfully been tested with [com0com Null Modem Emulator](http://com0com.sourceforge.net/) as well as with two USB-RS485 sticks and a loop cable. 

## How to make the Heidelberg Wallbox Energy Control respond
It took me quite some trial-and-error, to get the communication running. In summary, the following items need to be configured:
- ``Follower``: If the wallbox is configured as ``Leader``, it sends out reads but doesn't respond. Thus, the wallbox must be configured as ``Follower``.
- ``Bus-ID`` must be 1..15, not 0. By default, the ``Bus-ID`` is 0 and its ``Follower``. Apparantly, that combination puts the wallbox in some kind of stand-alone mode. 
- Set ``holding_register 261`` to the desired current limit. Otherwise ``262`` shows ``error state``. The current limt can't be set higher than the hardware switch current. 
- Disable the Standby function by writing at ``4`` to the ``holding_register 258``. Otherwise the wallbox stops responding after about 12 minutes.  

The notebook [read_from_walli.ipynb](read_from_walli.ipynb) demonstrates successful communication and this is how it looks like
![successful_wallbox_read_2021-07-18.png](modbus/imgs/successful_wallbox_read_2021-07-18.png)


# Mutli-threading
The **raspi_walli** webserver project requires concurrent operations. It need to serve the Webpage and do sensor polling (e.g. the wallbox) at the same time. I considered two libraries for this task:
- **`threading`**, Pythons stardard concurrency library with **preemptive scheduling**, meaning the os pauses a thread at any time, putting its state on the stack and continuous with another thread.
- **`asyncio`**, the modern library with **cooperative scheduling**. Each thread is assumed to be cooperative, meaning each thread gives back the CPU voluntarily, reducing the task switching overhead.

Here is a nice article comparing the two approaches: [Concurrency in Python: Cooperative vs Preemptive Scheduling](https://medium.com/fullstackai/concurrency-in-python-cooperative-vs-preemptive-scheduling-5feaed7f6e53)

I chosed to use the old-fashioned `threading` because `asyncio` isn't fully supported by `Flask`, at least as of December 2021.

# ToDos
- Use BH1750 light sensor to implement a **Garage left open detector** an send a warning E-mail.