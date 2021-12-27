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

    def get_torque(self) -> float:
        try:
            Nm = abs(round(DAQC2.getADC(self.addr, self.channel) * 0.05, 4))
            return Nm
        except:
            print("Error: Torque sensor not connected")
            return 0.0

    def set_square_wave(self):
        try:
            DAQC2.fgTYPE(self.addr, self.channel, self.type)
        except:
            # print("Error: Frequency sensor not connected")
            pass 
    
    def set_level(self, level):
        try:
            self.level = level
            DAQC2.fgLEVEL(self.addr, self.channel, self.level)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def start(self):
        try:
            DAQC2.fgON(self.addr, self.channel)
            DAQC2.fgTYPE(self.addr, self.channel, self.type)
            DAQC2.fgLEVEL(self.addr, self.channel, self.level)
        except:
            # print("Error: Frequency sensor not connected")
            pass
    
    def jog(self):
        try:
            DAQC2.fgON(self.addr, self.channel)
            DAQC2.fgTYPE(self.addr, self.channel, self.type)
            DAQC2.fgLEVEL(self.addr, self.channel, self.level)
            DAQC2.fgFREQ(self.addr, self.channel, 10)
        except:
            # print("Error: Frequency sensor not connected")
            pass


    def update_freq(self, freq):
        try:
            DAQC2.fgTYPE(self.addr, self.channel, self.type)
            DAQC2.fgLEVEL(self.addr, self.channel, self.level)
            DAQC2.fgFREQ(self.addr, self.channel, freq)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def set_rpm(self, rpm_input):
        self.freq = round((rpm_input / 60.0) * self.__REVOLUTIONS, 2)

        # check if freq is within limits
        if self.freq <= 10:
            self.freq = 10
        elif self.freq >= 10000:
            self.freq = 10000

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
        try:
            DAQC2.fgOFF(self.addr, self.channel)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def __destroy__(self):
        self.stop()


