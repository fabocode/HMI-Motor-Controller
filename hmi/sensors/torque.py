import piplates.DAQC2plate as DAQC2
import time
import sys, yaml

class Torque_Sensor:
    def __init__(self, addr, channel):
        self.addr = addr
        self.channel = channel
    
    def get_torque(self) -> float:
        try:
            Nm = round(DAQC2.getADC(self.addr, self.channel) * 0.05, 2)
            print("Torque Sensor: Nm = {}".format(Nm))
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
