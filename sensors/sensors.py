import logging, threading, time
import datetime as dt
from queue import Queue

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s | %(threadName)-10s | %(message)s',)

SIMULATION = False

class SensorBaseClass(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connected = False
        self.exiting = False
        self.task_queue = Queue(maxsize=10)
        
    def connect(self):
        """ connect function to be implemented in sensor subclass """
        raise NotImplementedError()
        
    def capture(self):
        """ capture function to be implemented in sensor subclass """
        raise NotImplementedError()
    
    def exit(self):
        self.exiting = True
    
    def run(self):
        TASK_FUNCS = {"connect": self.connect,
                      "capture": self.capture,
                      "exit": self.exit}
        
        logging.debug("starting thread")
        while not self.exiting:
            while not self.task_queue.empty():
                task = self.task_queue.get()
                func = TASK_FUNCS[task["func"]]
                if "kwargs" in task.keys():
                    kwargs = task["kwargs"]
                else:
                    kwargs = {}
                    
                try:
                    data = func(**kwargs)
                except Exception as e:
                    logging.error(f"task {task} caused {e}")
                    continue
                
                if "callback" in task.keys():
                    data["exec time"] = (dt.datetime.now() - task["started"]) / dt.timedelta(seconds=1.0)
                    task["callback"](data)
                    
        logging.debug("exiting thread")


class LightSensor(SensorBaseClass):
    """ BH1750 digital light sensor """ 
    def connect(self):
        if not SIMULATION:
            from smbus import SMBus
            self.sensor = SMBus(1)  # Rev 2 Pi uses 1
        logging.debug("LightSensor BH1570 connected")
        
    def capture(self):
        """Returns light level in Lux"""
        if SIMULATION:
            time.sleep(1)    
            return {"result": 42}
        
        else:
            I2C_BH1750 = 0x23
            ONE_TIME_HIGH_RES_MODE_1 = 0x20  
            d = self.sensor.read_i2c_block_data(I2C_BH1750, ONE_TIME_HIGH_RES_MODE_1)
            lux = (d[1] + (256 * d[0])) / 1.2
            return {"result": lux}

    
if __name__ == '__main__':
    def process_return_data(data):
        logging.info(f"process_return_data: {data}")

    sensor = LightSensor()
    sensor.start()
    sensor.task_queue.put({"func": "connect"})
    for i in range(6):
        task = ({"func": "capture", 
                 "started": dt.datetime.now(),
                 "callback": process_return_data})
        sensor.task_queue.put(task)
        time.sleep(1)
    sensor.task_queue.put({"func": "exit"})
    sensor.join()
    logging.debug("finished")