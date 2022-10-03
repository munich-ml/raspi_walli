# raspi_walli
Raspberry Pi controlling Heidelberger wallbox

## Heidelberger Wallbox control via ModBus RS422
ModBus Serial


# Mutli-threading
The **raspi_walli** webserver project requires concurrent operations. It need to serve the Webpage and do sensor polling (e.g. the wallbox) at the same time. I considered two libraries for this task:
- **`threading`**, Pythons stardard concurrency library with **preemptive scheduling**, meaning the os pauses a thread at any time, putting its state on the stack and continuous with another thread.
- **`asyncio`**, the modern library with **cooperative scheduling**. Each thread is assumed to be cooperative, meaning each thread gives back the CPU voluntarily, reducing the task switching overhead.

Here is a nice article comparing the two approaches: [Concurrency in Python: Cooperative vs Preemptive Scheduling](https://medium.com/fullstackai/concurrency-in-python-cooperative-vs-preemptive-scheduling-5feaed7f6e53)

I chosed to use the old-fashioned `threading` because `asyncio` isn't fully supported by `Flask`, at least as of December 2021.

# ToDos
- Use BH1750 light sensor to implement a **Garage left open detector** an send a warning E-mail.