import piplates.DAQC2plate as DAQC2
import time

class Stepper_Motor:

    __REVOLUTIONS = 10 * 400.0  # number of steps per revolution
    __JOG_FREQ = 10 * 10 # 10 Hz

    def __init__(self, motor_addr=1, addr=0, torque_addr=0, channel=1, drive_fault_pin=0, e_stop_pin=1):
        self.motor_addr = motor_addr
        self.addr = addr
        self.torque_addr = torque_addr
        self.channel = channel
        self.ch_mult = 100
        self.freq = 10
        self.type = 3               # square wave
        self.level = 4              # 1:1
        self.set_square_wave()
        self.set_level(self.level)
        self.stop()
        self.drive_fault_pin = drive_fault_pin
        self.e_stop_pin = e_stop_pin

    def get_frequency(self):
        try:
            return DAQC2.getFREQ(1)
        except Exception:
            return 0

    def is_drive_fault_active(self):
        try:
            if DAQC2.getDINbit(self.addr, self.drive_fault_pin):
                return False
            else:
                return True
        except Exception:
            return False

    def is_e_stop_active(self):
        try:
            if DAQC2.getDINbit(self.addr, self.e_stop_pin):
                return False
            else:
                return True
        except Exception:
            return False

    def get_torque(self) -> float:
        try:
            Nm = abs(round(DAQC2.getADC(self.addr, self.torque_addr) * 0.05, 4))
            return Nm
        except:
            print("Error: Torque sensor not connected")
            return 0.0

    def set_square_wave(self):
        try:
            DAQC2.fgTYPE(self.motor_addr, self.channel, self.type)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def set_level(self, level):
        try:
            self.level = level
            DAQC2.fgLEVEL(self.motor_addr, self.channel, self.level)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def start(self):
        try:
            DAQC2.fgON(self.motor_addr, self.channel)
            DAQC2.fgTYPE(self.motor_addr, self.channel, self.type)
            DAQC2.fgLEVEL(self.motor_addr, self.channel, self.level)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def jog(self):
        try:
            DAQC2.fgON(self.motor_addr, self.channel)
            DAQC2.fgTYPE(self.motor_addr, self.channel, self.type)
            DAQC2.fgLEVEL(self.motor_addr, self.channel, self.level)
            DAQC2.fgFREQ(self.motor_addr, self.channel, 10)
        except:
            # print("Error: Frequency sensor not connected")
            pass


    def update_freq(self, freq):
        try:
            DAQC2.fgTYPE(self.motor_addr, self.channel, self.type)
            DAQC2.fgLEVEL(self.motor_addr, self.channel, self.level)
            DAQC2.fgFREQ(self.motor_addr, self.channel, freq)
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

        self.update_freq(self.freq)
        return self.freq

    def get_rpm(self):
        freq = self.get_frequency()
        rpm = int((freq * 60.0)/1000)/10
        return rpm

    def stop(self):
        try:
            DAQC2.fgOFF(self.motor_addr, self.channel)
        except:
            # print("Error: Frequency sensor not connected")
            pass

    def __destroy__(self):
        self.stop()
