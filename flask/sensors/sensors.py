import logging, random, threading, time
import time
import datetime as dt
from queue import Queue

LIGHT_SENSOR_SIMULATED = True      # True for debugging mode if no sensor is connected
WALLI_SIMULATED = True             # True for debugging mode if no sensor is connected
PORT = '/dev/ttyAMA0'              # Serial port of Modbus interface
BUS_ID = 1                         # Modbus ID
MAX_READ_ATTEMPTS = 8              # Max number of attempts for a Modbus read

if not WALLI_SIMULATED:
    from pymodbus.client.sync import ModbusSerialClient

if not LIGHT_SENSOR_SIMULATED:
    from smbus import SMBus

logger = logging.getLogger(__name__)


class SensorBase(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
    
    def _exit(self):
        self.exiting = True
    
    def run(self):
        TASK_FUNCS = {"connect": self._connect,
                      "capture": self._capture,
                      "exit": self._exit}
        
        logger.info(f"Sensor thread started for '{self.type}'")
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
                    logger.error(f"task {task} caused {e}")
                    continue
                
                if "callback" in task.keys():
                    return_dct["exec time"] = time.time() - start_time
                    return_dct["campaign_id"] = task["campaign_id"]   
                    task["callback"](return_dct)
                    
        logger.info(f"Sensor thread exiting for '{self.type}'")


class LightSensor(SensorBase):
    """ BH1750 digital light sensor 
    """ 
    def __init__(self, *args, **kwargs):
        self.type = "LightSensor BH1570"
        super().__init__(*args, **kwargs)
        
    def _connect(self):
        if not LIGHT_SENSOR_SIMULATED:
            self.sensor = SMBus(1)  # Rev 2 Pi uses 1
        self.connected = True
        logger.debug(f"{self.type} connected")
        
    def _capture(self):
        """ Returns light level in Lux
        """
        if LIGHT_SENSOR_SIMULATED:
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


class ModbusReadError(Exception):
    pass


class Wallbox(SensorBase):
    """ Heidelberg Wallbox Energy Control
    """
    def __init__(self, *args, **kwargs):
        self.type = "Heidelberg Wallbox Energy Control"
        super().__init__(*args, **kwargs)
        
    def _connect(self, ):
        if WALLI_SIMULATED:
            self.writeable_regs = {
                'watchdog': 10000,
                'standby': 4,
                'remote_lock': 1,
                'max_I_cmd': 100,
                'FailSafe_I': 100}
        
        else:
            self.mb = ModbusSerialClient(method="rtu",
                                         port=PORT,
                                         baudrate=19200,
                                         stopbits=1,
                                         bytesize=8,
                                         parity="E",
                                         timeout=10)

            if not self.mb.connect():
                raise ModbusReadError('Could not connect to the wallbox')       
             
        self.connected = True
        logger.debug(f"{self.type} connected")

    def _capture(self):
        if WALLI_SIMULATED:  # simulated Wallbox
            voltage = random.randint(200, 210)     # 200..210V, easy to distinguish from real voltage samples
            charge_state = random.choice([2, 7])   # 2=idle, 7=charging
            power = 0
            if charge_state == 7:
                power = 10000
            current = int(power / voltage / 3 * 10)   
            sim = {'datetime': dt.datetime.now(),
                'ver': 99,
                'charge_state': charge_state,
                'I_L1': current, 'I_L2': current, 'I_L3': current,
                'Temp': random.randint(200, 400),  # 20..40°C
                'V_L1': voltage, 'V_L2': voltage, 'V_L3': voltage,
                'ext_lock': 1,
                'P': power,
                'E_cyc_hb': 0, 'E_cyc_lb': 40000,
                'E_hb': 3, 'E_lb': 0,
                'I_max': 10, 'I_min': 7}
            sim.update(self.writeable_regs)
            return sim
        
        else:  # Real Wallbox (not simulated)
            read_attempts = 0
            regs = [dt.datetime.now().strftime("%H:%M:%S")]

            funcs = [lambda: self.mb.read_input_registers(4, count=15, unit=BUS_ID),
                     lambda: self.mb.read_input_registers(100, count=2, unit=BUS_ID),
                     lambda: self.mb.read_holding_registers(257, count=3, unit=BUS_ID),
                     lambda: self.mb.read_holding_registers(261, count=2, unit=BUS_ID),
                    ]
            for func in funcs:
                while True:
                    r = func()
                    if r.isError():
                        read_attempts += 1
                        if self.verbose:
                            print("Modbus read error, attempt", read_attempts)
                        if read_attempts > MAX_READ_ATTEMPTS:
                            raise ModbusReadError
                    else:
                        regs.extend(r.registers)
                        break
            
            keys = ['datetime', 'ver', 'charge_state', 'I_L1', 'I_L2', 'I_L3', 'Temp', 'V_L1', 'V_L2', 
                    'V_L3', 'ext_lock', 'P', 'E_cyc_hb', 'E_cyc_lb', 'E_hb', 'E_lb', 'I_max', 'I_min', 
                    'watchdog', 'standby', 'remote_lock', 'max_I_cmd', 'FailSafe_I']
            dct = {k: v for k, v in zip(keys, regs)}
            return dct
        
    def _exit(self):
        """ Overwrite _exit method of base class to support Modbus closing
        """
        if not WALLI_SIMULATED:
            self.mb.close()
        super()._exit()
      

class Camera(SensorBase):
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
        
        logger.info("SensorInterface initialized")
        for key, value in self.items():
            logger.info(f"- '{key}': {value}")
        
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
        if sensor.task_queue.full():
            logger.warning(f"Queue is full! Sipping {task}")
        else:    
            sensor.task_queue.put(task, timeout=1)
        
    
if __name__ == '__main__':
    def process_return_data(data):
        print(f"process_return_data: {data}")

    sensor = Wallbox()
    sensor.task_queue.put({"func": "connect"})
    for i in range(6):
        task = {"func": "capture",
                "campaign_id": 42, 
                "callback": process_return_data}
        sensor.task_queue.put(task)
        time.sleep(1)
    sensor.task_queue.put({"func": "exit"})
    sensor.join()
    print("finished")
