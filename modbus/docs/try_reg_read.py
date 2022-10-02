import threading, time

global_cache = {}

def get_data(callback):
    time.sleep(0.9)
    data = [42]
    callback(data)


def config_view_function():
    event = threading.Event()
    def save_to_global_cache(data):
        global_cache["data"] = data
        event.set()
    
    threading.Thread(target=get_data, kwargs={"callback": save_to_global_cache}).start()
    
    success = event.wait(timeout=1)
    print(global_cache)
    print(f"config finished, {success=}")
    

if __name__ == "__main__":
    config_view_function()