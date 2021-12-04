import logging, threading, time
import time
import datetime as dt
from queue import Queue


SIMULATION = True

class SensorBaseClass(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "unknown sensor"   # to be filled by sensor subclass
        self.connected = False
        self.exiting = False
        self.task_queue = Queue(maxsize=10)
        self.start()
        
    def __repr__(self):
        connected = {True: "connected", False: "not connected"}[self.connected]
        return f"{self.type}, {connected}"
        
    def _connect(self):
        """ connect function to be implemented in sensor subclass """
        raise NotImplementedError()
        
    def _capture(self):
        """ capture function to be implemented in sensor subclass """
        raise NotImplementedError()
    
    def exit(self):
        self.exiting = True
    
    def run(self):
        TASK_FUNCS = {"connect": self._connect,
                      "capture": self._capture,
                      "exit": self.exit}
        
        logging.debug("starting thread")
        while not self.exiting:
            time.sleep(0.01)    # without this sleep, the processor goes busy
            while not self.task_queue.empty():
                start_time = time.time()
                task = self.task_queue.get()
                func = TASK_FUNCS[task["func"]]
                if "kwargs" in task.keys():
                    kwargs = task["kwargs"]
                else:
                    kwargs = {}
                    
                try:
                    return_dct = func(**kwargs)
                except Exception as e:
                    logging.error(f"task {task} caused {e}")
                    continue
                
                if "callback" in task.keys():
                    return_dct["exec time"] = time.time() - start_time
                    return_dct["campaign_id"] = task["campaign_id"]   
                    task["callback"](return_dct)
                    
        logging.debug("exiting thread")


class LightSensor(SensorBaseClass):
    """ BH1750 digital light sensor """ 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "LightSensor BH1570"
        
    def _connect(self):
        if not SIMULATION:
            from smbus import SMBus
            self.sensor = SMBus(1)  # Rev 2 Pi uses 1
        self.connected = True
        logging.debug(f"{self.type} connected")
        
    def _capture(self):
        """Returns light level in Lux"""
        if SIMULATION:
            time.sleep(0.01)
            t = dt.datetime.now() 
            lux = float(t.hour + t.minute/100)   
            return {"lux": lux}
        
        else:
            I2C_BH1750 = 0x23
            ONE_TIME_HIGH_RES_MODE_1 = 0x20  
            d = self.sensor.read_i2c_block_data(I2C_BH1750, ONE_TIME_HIGH_RES_MODE_1)
            lux = (d[1] + (256 * d[0])) / 1.2
            return {"lux": lux}


class Wallbox(SensorBaseClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "Heidelberg Wallbox Energy Control"

    def _connect(self):
        logging.warning(f"{self.type} has no 'connect' method, yet!")

    def _capture(self):
        logging.warning(f"{self.type} has no 'capture' method, yet!")
        return {}
                

class Camera(SensorBaseClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "Camera"


class SensorInterface(dict):
    """Container holding all sensors"""
    def __init__(self):
        self["light"] = LightSensor()
        self["walli"] = Wallbox()
        
        # connect all sensors
        for sensor in self.values():
            sensor.task_queue.put({"func": "connect"})
        time.sleep(0.01)  # wait for all sensor threads to connect
        
        logging.info("SensorInterface initialized")
        for key, value in self.items():
            logging.info(f"- '{key}': {value}")
        
    def do_task(self, task):
        """
        Executes a task 
        
        task is a <dict> with the items:
            "sensor": <str> sensor key like "light", "walli" or "cam"
            "func": <str> function key like "capture", "connect" or "exit"
            "campaign_id": <int> e.g. 42
            "callback": <func> callback function line process_return_data
        """
        sensor_key = task["sensor"]
        sensor = self[sensor_key]
        sensor.task_queue.put(task)
        
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(threadName)-10s | %(funcName)-16s | %(message)s',)

    def process_return_data(data):
        logging.info(f"process_return_data: {data}")

    sensor = LightSensor()
    sensor.start()
    sensor.task_queue.put({"func": "connect"})
    for i in range(6):
        task = {"func": "capture",
                "campaign_id": 42, 
                "callback": process_return_data}
        sensor.task_queue.put(task)
        time.sleep(1)
    sensor.task_queue.put({"func": "exit"})
    sensor.join()
    logging.debug("finished")