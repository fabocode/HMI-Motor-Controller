import piplates.DAQC2plate as DAQC2
import time 

class Stepper_Motor:

    __REVOLUTIONS = 398.93  # number of steps per revolution
    __JOG_FREQ = 10 # 10 Hz

    def __init__(self, addr=0, channel=1):
        self.addr = addr
        self.channel = channel
        self.ch_mult = 100
        self.freq = 10
        self.type = 3               # square wave
        self.level = 4              # 1:1
        self.set_square_wave()
        self.set_level(self.level)
        self.stop()

    def set_square_wave(self):
        DAQC2.fgTYPE(self.addr, self.channel, self.type)
    
    def set_level(self, level):
        self.level = level
        DAQC2.fgLEVEL(self.addr, self.channel, self.level)

    def start(self):
        DAQC2.fgON(self.addr, self.channel)
        DAQC2.fgTYPE(self.addr, self.channel, self.type)
        DAQC2.fgLEVEL(self.addr, self.channel, self.level)
    
    def jog(self):
        DAQC2.fgON(self.addr, self.channel)
        DAQC2.fgTYPE(self.addr, self.channel, self.type)
        DAQC2.fgLEVEL(self.addr, self.channel, self.level)
        self.update_freq(0)    # lowest level possible 

    def update_freq(self, freq):
        DAQC2.fgFREQ(self.addr, self.channel, freq)

    def set_rpm(self, rpm_input):
        self.freq = round((rpm_input / 60.0) * self.__REVOLUTIONS, 2)

        # check if freq is within limits
        if self.freq <= 10:
            self.freq = 10
        elif self.freq >= 20000:
            self.freq = 20000

        print("Frequency: ", self.freq)
        self.update_freq(self.freq)
        return self.freq
    
    def get_frequency(self):
        try:
            return abs(DAQC2.getFREQ(0))
        except:
            print("Error: Frequency sensor not connected")
            return 0.0

    def stop(self):
        DAQC2.fgOFF(self.addr, self.channel)

if __name__ == '__main__':
    motor = Stepper_Motor()
    motor.on()
    print("starting on the motor for 30 seconds")
    # print("setting rpm input")
    # desired_rpm = float(input("Enter desired rpm: "))
    # motor.set_rpm(desired_rpm)
    time.sleep(30)
    motor.stop()


