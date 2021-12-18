import piplates.DAQC2plate as DAQC2
import time 

class Stepper_Motor:
    def __init__(self, addr=0):
        self.addr = addr
        self.channel = 0
    
    def get_frequency(self):
        try:
            return abs(DAQC2.getFREQ(0))
        except:
            print("Error: Frequency sensor not connected")
            return 0.0

    def set_motor(self, freq):
        try:
            DAQC2.setPWM(self.addr, self.channel, freq)
            return True
        except:
            print("error writing to motor prin")
            return False

    def on(self) -> bool:
        # try:
        DAQC2.clrDOUTbit(0, 0)
        return True 
        # except:
        #     print("error writing to motor prin")
        #     return False

    def off(self):
        # try:
        DAQC2.setDOUTbit(0, 0)
        return True
        # except:
        #     print("error writing to motor prin")
        #     return False

if __name__ == '__main__':
    motor = Stepper_Motor()
    while True:
        freq = motor.get_frequency()
        print(f"freq: {freq}")
        print("set the motor")
        print("")
        motor.set_motor(512)
        time.sleep(.1)
