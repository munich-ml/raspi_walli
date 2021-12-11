SIMULATION = True      # Sensors are simulated if True


# configure logging
import logging
logging.getLogger().setLevel(logging.NOTSET)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)-7s | %(funcName)s() %(filename)s line=%(lineno)s thread=%(thread)s | %(message)s')
handler.setFormatter(formatter)
logging.getLogger().addHandler(handler)
