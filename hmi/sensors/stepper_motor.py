import piplates.DAQC2plate as DAQC2
import time 

class Stepper_Motor:

    __REVOLUTIONS = 398.93

    def __init__(self, dir_pin=0, addr=0, channel=1):
        self.addr = addr
        self.dir_pin = dir_pin
        self.channel = channel
        self.ch_mult = 100
        self.freq = 10
        self.type = 3   # square wave
        self.level = 4  # 1:1
        self.initFG()

    def initFG(self):
        DAQC2.fgON(self.addr, 1)
        DAQC2.fgTYPE(self.addr, self.channel, self.type)
        DAQC2.fgLEVEL(self.addr, self.channel, self.level)
        DAQC2.fgFREQ(self.addr, self.channel, self.freq)

    def update_freq(self, freq):
        DAQC2.fgFREQ(self.addr, self.channel, freq)

    def set_rpm(self, rpm_input):
        self.freq = round((rpm_input / 60.0) * self.__REVOLUTIONS, 2)
        self.update_freq(self.freq)
        return self.freq
    
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

    def stop(self):
        DAQC2.fgOFF(self.addr, self.channel)

if __name__ == '__main__':
    motor = Stepper_Motor()
    motor.initFG()
    print("setting rpm input")
    desired_rpm = float(input("Enter desired rpm: "))
    motor.set_rpm(desired_rpm)
    time.sleep(30)
    motor.stop()


