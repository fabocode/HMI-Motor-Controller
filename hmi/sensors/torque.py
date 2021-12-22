import piplates.DAQC2plate as DAQC2
import time
import sys, yaml

class Torque_Sensor:
    def __init__(self, addr=0, channel=0):
        self.addr = addr
        self.channel = channel
    
    def get_torque(self) -> float:
        try:
            Nm = abs(round(DAQC2.getADC(self.addr, self.channel) * 0.05, 4))
            return Nm
        except:
            print("Error: Torque sensor not connected")
            return 0.0


if __name__ == "__main__":
    torque = Torque_Sensor(0, 0)
    while True:
        torque.get_torque()
        time.sleep(1)
        print("\n")
