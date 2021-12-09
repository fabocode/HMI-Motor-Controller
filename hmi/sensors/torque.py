import piplates.DAQC2plate as DAQC2
import time
import sys, yaml

class Torque_Sensor:
    def __init__(self, addr, channel):
        self.addr = addr
        self.channel = channel
    
    def get_torque(self):
        Nm = round(DAQC2.getADC(self.addr, self.channel) * 0.05, 2)
        return Nm

