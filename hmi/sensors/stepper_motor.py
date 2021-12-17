import piplates.DAQC2plate as DAQC2
import time 

class Stepper_Motor:
    def __init__(self):
        # self.addr = addr
        pass
    
    def get_frequency(self):
        try:
            return abs(DAQC2.getFREQ(0))
        except:
            print("Error: Frequency sensor not connected")
            return 0.0

    def turn_on_motor(self) -> bool:
        try:
            DAQC2.setDOUTbit(0, 0)
            return True 
        except:
            print("error writing to motor prin")
            return False

    def turn_off_motor(self) -> bool:
        try:
            DAQC2.clrDOUTbit(0, 0)
            return True
        except:
            print("error writing to motor prin")
            return False

if __name__ == '__main__':
    motor = Stepper_Motor()
    while True:
        freq = motor.get_frequency()
        print(f"freq: {freq}")
        print("set the motor")
        motor.turn_on_motor()
        time.sleep(.1)
        motor.turn_off_motor()
        time.sleep(.1)
