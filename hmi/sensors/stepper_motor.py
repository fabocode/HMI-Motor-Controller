import piplates.DAQC2plate as DAQC2
import time 

class Stepper_Motor:
    def __init__(self, dir_pin=0, addr=0, channel=0):
        self.addr = addr
        self.dir_pin = dir_pin
        self.channel = channel
    
    def get_frequency(self):
        try:
            return abs(DAQC2.getFREQ(0))
        except:
            print("Error: Frequency sensor not connected")
            return 0.0

    def set_direction(self, direction: bool) -> bool:
        try:
            if direction:
                DAQC2.setDOUTbit(0, self.dir_pin)
            else:
                DAQC2.clrDOUTbit(0, self.dir_pin)
            return True
        except:
            print("error writing to motor prin")
            return False

    def set_clockwise(self):
        self.set_direction(True)
    
    def set_counter_clockwise(self):
        self.set_direction(False)

    def set_motor(self, freq):
        try:
            DAQC2.setPWM(self.addr, self.channel, freq)
            return True
        except:
            print("error writing to motor prin")
            return False

    def on(self):
        DAQC2.clrDOUTbit(self.addr, 0)

    def off(self):
        DAQC2.setDOUTbit(self.addr, 0)

if __name__ == '__main__':
    motor = Stepper_Motor()
    fixed_pulse_rev = 800
    while True:
        for i in range(fixed_pulse_rev):
            motor.on()
            motor.off()

        # time.sleep(5)
        # break
